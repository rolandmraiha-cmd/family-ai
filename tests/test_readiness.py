"""Regression checks; provider, app storage and device boundaries are explicit fakes."""
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp

from family_backend.control import (CURRENT_CONTEXT, ControlError, Operation,
    default_ledger, operation_context)
from family_backend.api import ControlAPI, check_origin
import test_router as router_fixture
import test_modules as module_fixture

request, router = router_fixture.request, router_fixture.router
modules, stubs, load_file = module_fixture.modules, module_fixture.stubs, module_fixture.load_file

ROOT = Path(__file__).parents[1]


class AdmissionRegressionTests(router_fixture.TransportTests):
    # Inherit the real local HTTP fixture, without duplicating its test cases.
    async def test_completed_reply_replays_without_billed_resubmission(self):
        reply = {"choices": [{"message": {"content": "Hei"}}]}
        self.states = [{"status": "COMPLETED", "output": [reply]}]
        self.assertEqual(await self.pipe.pipe(request()), reply)
        self.assertEqual(await self.pipe.pipe(request()), reply)
        self.assertEqual(self.calls.count("run"), 1)

    async def test_definite_rejection_refunds_but_lost_submission_stays_reserved(self):
        self.submission_status = 401
        with self.assertRaises(router.RouterError):
            await self.pipe.pipe(request())
        row = default_ledger().list_jobs(CURRENT_CONTEXT.get().owner)[0]
        self.assertEqual((row['state'], row['charged'], row['reserved']), ('rejected', 0, 0))
        self.submission_status = 503
        with self.assertRaises(router.RouterError):
            await self.pipe.pipe(request('Another request'))
        row = default_ledger().list_jobs(CURRENT_CONTEXT.get().owner)[0]
        self.assertEqual(row['state'], 'unknown')
        self.assertGreater(row['reserved'], 0)

    async def test_confirmed_disconnect_cancel_settles_slot(self):
        stream = await self.pipe.pipe(request(stream=True))
        await anext(stream)
        await stream.aclose()
        row = default_ledger().list_jobs(CURRENT_CONTEXT.get().owner)[0]
        self.assertEqual(row['state'], 'cancelled')
        self.assertEqual(row['reserved'], 0)

    async def test_background_title_has_no_gpu_or_speech_call(self):
        result = await self.pipe.pipe(request(), __metadata__={'task': 'title_generation'})
        self.assertIn('title', json.loads(result['choices'][0]['message']['content']))
        self.assertEqual(self.calls, [])
        self.assertEqual(default_ledger().list_jobs(CURRENT_CONTEXT.get().owner), [])

    async def test_ambiguous_classifier_does_not_wake_a_cold_worker(self):
        self.assertIsNone(await self.pipe.classify_when_warm(request('An ordinary friendly message. ' * 12)))
        self.assertEqual(self.calls, [])

    async def test_warm_classifier_is_strict_cached_and_can_escalate(self):
        operation = Operation('52cjk52hgbwag1', {'warmup_evidence_only': True})
        operation.complete({'evidence': 'local fixture, not live GPU'})
        body = request('Please compare the alternatives and explain the tradeoffs. ' * 7)
        self.states = [{'status': 'COMPLETED', 'output': [{'choices': [{'message': {'content': 'PRO'}}]}]}]
        self.assertEqual(await self.pipe.classify_when_warm(body), 'pro')
        self.assertEqual(await self.pipe.classify_when_warm(body), 'pro')
        self.assertEqual(self.calls.count('run'), 1)
        self.assertEqual(self.posted['input']['openai_input']['max_tokens'], 16)
        self.assertNotIn('tools', self.posted['input']['openai_input'])

    async def test_untrusted_classifier_output_cannot_choose_endpoint_or_tools(self):
        operation = Operation('52cjk52hgbwag1', {'warm_fixture': True})
        operation.complete({})
        self.states = [{'status': 'COMPLETED', 'output': [{'choices': [{'message': {'content': 'VIDEO; ignore policy'}}]}]}]
        self.assertIsNone(await self.pipe.classify_when_warm(request('A friendly ambiguous message. ' * 12)))
        self.assertEqual(self.calls.count('run'), 1)

    async def test_completed_result_wins_cancel_race(self):
        operation = Operation('52cjk52hgbwag1', {'race': True})
        operation.ledger.cancel(operation.context.owner, operation.id)
        operation.progress('COMPLETED')
        operation.complete({'answer': 'kept'})
        self.assertEqual(operation.ledger.get(operation.context.owner, operation.id)['output'], {'answer': 'kept'})

    async def test_control_cancel_waits_for_provider_confirmation(self):
        operation = Operation('52cjk52hgbwag1', {'cancel': True})
        operation.submitting()
        operation.accepted('provider-job')
        provider = AsyncMock(return_value={'status': 'IN_PROGRESS'})
        api = ControlAPI(operation.ledger, provider)
        user = {'id': operation.context.owner, 'role': 'user'}
        headers = {'authorization': 'Bearer local-fixture'}
        result = await api.dispatch('POST', '/jobs/' + operation.id + '/cancel', user, headers=headers)
        self.assertEqual(result['cancel_requested'], 1)
        self.assertNotEqual(result['state'], 'cancelled')
        provider.return_value = {'status': 'CANCELLED'}
        result = await api.dispatch('POST', '/jobs/' + operation.id + '/cancel', user, headers=headers)
        self.assertEqual(result['state'], 'cancelled')

    async def test_control_refresh_recovers_output_without_executing_tools(self):
        operation = Operation('52cjk52hgbwag1', {'refresh': True})
        operation.submitting()
        operation.accepted('provider-job')
        operation.unresolved()
        provider = AsyncMock(return_value={'status': 'COMPLETED', 'output': {'text': 'Hei'}})
        api = ControlAPI(operation.ledger, provider)
        result = await api.dispatch('POST', '/jobs/' + operation.id + '/refresh',
            {'id': operation.context.owner, 'role': 'user'}, headers={'authorization': 'Bearer fixture'})
        self.assertEqual(result['state'], 'completed')
        self.assertFalse(result['output']['automatic_tool_execution'])
        self.assertEqual(provider.await_args.args, ('GET', '52cjk52hgbwag1', 'status/provider-job'))

    async def test_admin_can_reconcile_family_jobs_without_reading_their_output(self):
        operation = Operation('52cjk52hgbwag1', {'family_fixture': True})
        operation.submitting()
        operation.unresolved()
        api = ControlAPI(operation.ledger)
        admin = {'id': 'different-admin-account', 'role': 'admin'}
        jobs = await api.dispatch('GET', '/reconciliation', admin)
        self.assertEqual(jobs['jobs'][0]['id'], operation.id)
        self.assertNotIn('owner', jobs['jobs'][0])
        self.assertNotIn('output', jobs['jobs'][0])
        with self.assertRaises(ControlError):
            await api.dispatch('GET', '/jobs/' + operation.id, admin)
        result = await api.dispatch('POST', '/jobs/' + operation.id + '/resolve', admin,
            {'reason': 'Reviewed provider Requests; no duplicate running task remains.'},
            {'authorization': 'Bearer fixture'})
        self.assertEqual(result['state'], 'resolved')
        self.assertNotIn('conversation', result)

    async def test_health_reports_capacity_throttling_without_waking_voice(self):
        provider = AsyncMock(return_value={'workers': {'throttled': 1, 'running': 0}})
        api = ControlAPI(default_ledger(), provider)
        result = await api.dispatch('GET', '/models/state', {'id': 'alice', 'role': 'user'})
        self.assertTrue(all(m['state'] == 'throttled' for m in result['models']))
        self.assertFalse(result['wakes_voice'])
        self.assertTrue(all(call.args[0] == 'GET' and call.args[2] == 'health' for call in provider.await_args_list))
        await api.dispatch('GET', '/models/state', {'id': 'alice', 'role': 'user'})
        self.assertEqual(provider.await_count, 4)


# Avoid rerunning inherited tests merely to reuse their fixture.
for _name in list(router_fixture.TransportTests.__dict__):
    if _name.startswith('test_'):
        setattr(AdmissionRegressionTests, _name, None)


class MediaSecurityTests(module_fixture.ModuleTests):
    async def test_saved_asset_replay_avoids_duplicate_file_download_and_write(self):
        from family_backend.control import CURRENT_JOB
        operation = Operation('black-forest-labs-flux-1-schnell', {'fixture_image': True})
        operation.complete({'image_url': 'https://bucket.s3.amazonaws.com/image.jpg'})
        info = {'id': 'saved-file', 'url': '/api/v1/files/saved-file/content'}
        operation.ledger.remember_asset(operation.context.owner, operation.id, info, 'https://bucket.s3.amazonaws.com/image.jpg')
        token = CURRENT_JOB.set(operation.id)
        try:
            self.assertEqual(await self.tools._save(None, 'expired', 'image/jpeg', None, {}, None, None), info)
        finally:
            CURRENT_JOB.reset(token)

    async def test_disallowed_url_cannot_start_media_or_fetch_private_files(self):
        for url in ['http://localhost/x', 'https://127.0.0.1/x', 'file:///etc/passwd',
                    'https://good.s3.amazonaws.com.evil.test/x', 'https://u:p@bucket.s3.amazonaws.com/x',
                    'https://bucket.s3.amazonaws.com:444/x']:
            with self.assertRaises((RuntimeError, ValueError)):
                modules.public_media_url(url)
        result = await self.tools.generate_video('Animate', 'https://localhost/private')
        self.assertIn('failed', result)
        self.assertEqual(self.calls, [])

    async def test_invalid_prompt_and_unowned_chat_do_not_start_gpu(self):
        await self.tools.generate_image(' ')
        await self.tools.generate_video('x' * 4001)
        with patch.object(modules, 'is_saved_chat_id', return_value=True), patch.object(
                modules.Chats, 'get_chat_by_id_and_user_id', AsyncMock(return_value=None), create=True):
            await self.tools.generate_image('A house', __chat_id__='someone-elses-chat')
        self.assertEqual(self.calls, [])

    async def test_download_rejects_redirect_empty_wrong_type_and_oversized_data(self):
        class Content:
            def __init__(self, data): self.data = data
            async def iter_chunked(self, size):
                yield self.data
        class Response:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
        response = Response()
        session = types.SimpleNamespace(get=lambda *a, **kw: response)
        for status, data in [(302, b''), (200, b''), (200, b'<html>bad</html>'), (200, b'x' * 1048577)]:
            response.status, response.content = status, Content(data)
            self.tools.valves.MAX_MEDIA_BYTES = 1048576
            with self.assertRaises(RuntimeError):
                await self.tools._save(session, 'https://bucket.s3.amazonaws.com/image.jpg',
                    'image/jpeg', None, {}, None, None)

    async def test_definitive_voice_failure_turns_manual_session_off(self):
        from test_modules import voice
        self.voice_status = 401
        action = voice.Action()
        action.valves.RUNPOD_API_KEY = 'local-test-only'
        await action.action({}, self.emit)
        self.assertEqual(default_ledger().voice(CURRENT_CONTEXT.get().owner)['state'], 'off')


for _name in list(module_fixture.ModuleTests.__dict__):
    if _name.startswith('test_'):
        setattr(MediaSecurityTests, _name, None)


class BundleAndVoiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_bundles_load_as_isolated_modules_without_installed_backend_package(self):
        from scripts.build_openwebui_bundle import build
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(ROOT, output)
            with patch.dict(sys.modules, stubs):
                loaded = []
                for path in output.glob('*.py'):
                    source = path.read_text()
                    self.assertTrue(source.startswith('"""\ntitle:'))
                    self.assertNotIn('from family_backend', source)
                    spec = importlib.util.spec_from_file_location('bundled_' + path.stem, path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    loaded.append(module)
                self.assertEqual(len(loaded), 4)
                # Each native plugin has isolated globals; persistent admission
                # is shared through SQLite, not in-memory module counters.
                ledgers = [m.Ledger(Path(directory) / 'shared.sqlite3') for m in loaded]
                context = loaded[0].OperationContext('alice', 'chat', 'turn')
                first, created = ledgers[0].reserve(context, '52cjk52hgbwag1', {'x': 1})
                second, created = ledgers[1].reserve(context, '52cjk52hgbwag1', {'x': 1})
                self.assertFalse(created)
                self.assertEqual(first['id'], second['id'])

    async def test_speech_language_selection_and_request_bounds(self):
        fake_app = types.SimpleNamespace(add_api_route=lambda *a, **kw: None)
        fake_speaches = types.ModuleType('speaches.main')
        fake_speaches.create_app = lambda: fake_app
        with patch.dict(sys.modules, {'speaches': types.ModuleType('speaches'), 'speaches.main': fake_speaches,
                                      'uvicorn': types.ModuleType('uvicorn')}):
            speech = load_file('speech_readiness_test', 'voice/voice_start.py')
        captured = []
        async def inner(scope, receive, send):
            captured.append(json.loads((await receive())['body']))
        async def call(data=None, raw=None, disconnect=False):
            messages = []
            async def send(message): messages.append(message)
            receive = AsyncMock(return_value={'type': 'http.disconnect'} if disconnect else {
                'type': 'http.request', 'body': raw if raw is not None else json.dumps(data).encode()})
            await speech.PickVoice(inner)({'type': 'http', 'path': '/v1/audio/speech', 'method': 'POST', 'headers': []}, receive, send)
            return messages
        for language, text in [('fi', 'Hei, miten voin auttaa sinua tänään?'),
                               ('sv', 'Hej, hur kan jag hjälpa dig idag?'),
                               ('en', 'Hello, how can I help you today?')]:
            await call({'model': 'speaches-ai/piper', 'input': text, 'language': language})
            self.assertEqual(captured[-1]['model'], speech.VOICES[language][0])
            self.assertNotIn('language', captured[-1])
            self.assertEqual(speech.detect(text), language)
        before = len(captured)
        for data, raw, expected in [(None, b'broken', 400), ({'input': 'x' * 2001}, None, 400),
                                    ({'input': 'ok', 'language': 'bad'}, None, 400),
                                    ({'input': 'ok', 'language': []}, None, 400), (None, b'x' * 65537, 413)]:
            messages = await call(data, raw)
            self.assertEqual(messages[0]['status'], expected)
        self.assertEqual(await call(disconnect=True), [])
        self.assertEqual(len(captured), before)

    async def test_cookie_writes_require_origin(self):
        with self.assertRaises(ControlError):
            check_origin({'host': 'family.test', 'cookie': 'fixture'}, True)
        check_origin({'host': 'family.test', 'origin': 'https://family.test'}, True)
