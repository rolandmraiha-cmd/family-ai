import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer

from family_backend.control import ControlError, Ledger, Limits, OperationContext, micros
from family_backend.api import ControlAPI, check_origin, public_job

FAST = '52cjk52hgbwag1'
PRO = 'c3lm36gdhpctl2'
VIDEO = 'wan-2-2-i2v-720'


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = datetime.fromisoformat('2026-11-03T12:00:00+00:00').timestamp()
        self.ledger = Ledger(Path(self.temp.name) / 'control.sqlite3', lambda: self.now)
        self.context = OperationContext('alice', 'chat-a', 'turn-a')

    def reserve(self, **kwargs):
        return self.ledger.reserve(self.context, FAST, {'prompt': 'Hello'}, **kwargs)

    def test_reservation_survives_restart_without_storing_prompt_or_key(self):
        job, created = self.reserve()
        self.assertTrue(created)
        restored = Ledger(self.ledger.path, lambda: self.now)
        same, created = restored.reserve(self.context, FAST, {'prompt': 'Hello'})
        self.assertFalse(created)
        self.assertEqual(job['id'], same['id'])
        self.assertNotIn('Hello', json.dumps(same))
        if os.name != 'nt':  # Windows uses ACLs, not Unix permission bits.
            self.assertEqual(os.stat(self.ledger.path).st_mode & 0o777, 0o600)

    def test_lost_reply_with_new_assistant_id_does_not_submit_twice(self):
        first, _ = self.reserve()
        self.ledger.transition('alice', first['id'], 'submitting')
        self.ledger.transition('alice', first['id'], 'unknown')
        self.now += 900  # Uncertain operations must outlive the short replay window.
        other = OperationContext('alice', 'chat-a', 'new-message-id')
        second, created = self.ledger.reserve(other, FAST, {'prompt': 'Hello'})
        self.assertFalse(created)
        self.assertEqual(first['id'], second['id'])

    def test_global_concurrency_is_atomic_across_connections(self):
        def attempt(n):
            try:
                return self.ledger.reserve(OperationContext(f'user-{n}', f'chat-{n}', 'turn'), FAST, {'n': n})[1]
            except ControlError as error:
                self.assertEqual(error.code, 'concurrency_limit')
                return False
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(attempt, range(20)))
        self.assertEqual(sum(results), 2)

    def test_daily_budget_stops_new_submissions_before_limit(self):
        policy = Limits(daily_usd='0.20')
        self.ledger.set_policy(policy.__dict__)
        first, _ = self.reserve()
        self.ledger.finish('alice', first['id'], 'completed')
        with self.assertRaisesRegex(ControlError, 'budget'):
            self.ledger.reserve(OperationContext('alice', 'chat-b', 'b'), FAST, {'prompt': 'Different'})

    def test_monthly_budget_is_independent_of_daily_rollover(self):
        policy = Limits(daily_usd='2.00', monthly_usd='0.20')
        self.ledger.set_policy(policy.__dict__)
        first, _ = self.reserve()
        self.ledger.finish('alice', first['id'], 'completed')
        self.now += 86400
        with self.assertRaisesRegex(ControlError, 'month'):
            self.ledger.reserve(OperationContext('alice', 'chat-b', 'b'), FAST, {'prompt': 'Different'})

    def test_budget_day_uses_helsinki_midnight(self):
        self.now = datetime.fromisoformat('2026-11-03T22:30:00+00:00').timestamp()
        self.assertEqual(self.ledger.periods()[0], '2026-11-04')

    def test_capability_limits_zero_disable_before_any_provider_call(self):
        policy = Limits()
        policy.daily_counts['video'] = 0
        self.ledger.set_policy(policy.__dict__)
        with self.assertRaises(ControlError):
            self.ledger.preflight_video(self.context, VIDEO, 840, 5, True)
        self.assertEqual(self.ledger.list_jobs('alice'), [])

    def test_changed_question_cannot_repeat_reasoning_in_same_turn(self):
        job, _ = self.ledger.reserve(self.context, PRO, {'question': 'one'})
        self.ledger.finish('alice', job['id'], 'completed')
        with self.assertRaisesRegex(ControlError, 'already used'):
            self.ledger.reserve(self.context, PRO, {'question': 'another'})

    def test_unknown_submission_retains_reservation_and_slot(self):
        first, _ = self.reserve()
        self.ledger.transition('alice', first['id'], 'submitting')
        self.ledger.transition('alice', first['id'], 'unknown')
        row = self.ledger.get('alice', first['id'])
        self.assertGreater(row['reserved'], 0)
        self.assertEqual(row['charged'], 0)

    def test_cancel_is_request_until_provider_confirmation(self):
        first, _ = self.reserve()
        row = self.ledger.cancel('alice', first['id'])
        self.assertEqual(row['cancel_requested'], 1)
        self.assertEqual(row['state'], 'reserved')
        self.ledger.finish('alice', first['id'], 'cancelled')
        self.assertEqual(self.ledger.get('alice', first['id'])['state'], 'cancelled')

    def test_completion_and_event_replay_are_persistent_and_owned(self):
        first, _ = self.reserve()
        self.ledger.event('alice', first['id'], 'model.delta', {'text': 'Hei'})
        self.ledger.finish('alice', first['id'], 'completed', {'text': 'Hei'}, '0.003')
        with self.assertRaises(ControlError):
            self.ledger.get('bob', first['id'])
        events = self.ledger.events('alice', first['id'])
        self.assertEqual([e['type'] for e in events], ['job.created', 'model.delta', 'job.finished'])
        self.assertEqual(len(self.ledger.events('alice', first['id'], events[0]['id'])), 2)
        self.assertEqual(self.ledger.get('alice', first['id'])['charged'], 3000)

    def test_terminal_job_cannot_be_reopened(self):
        first, _ = self.reserve()
        self.ledger.finish('alice', first['id'], 'completed', {'answer': 'yes'})
        self.ledger.transition('alice', first['id'], 'queued')
        self.assertEqual(self.ledger.get('alice', first['id'])['state'], 'completed')

    def test_video_duration_is_a_hard_input_limit(self):
        for duration in [-1, 0, 6, 100]:
            with self.assertRaises(ControlError):
                self.ledger.reserve(self.context, VIDEO, {'duration': duration}, duration=duration)

    def test_unsupported_short_video_never_starts_an_image(self):
        for duration in [1, 3, 4]:
            with self.assertRaisesRegex(ControlError, 'five-second'):
                self.ledger.preflight_video(self.context, VIDEO, 840, duration, True)
        self.assertEqual(self.ledger.list_jobs('alice'), [])

    def test_invalid_policy_does_not_replace_valid_policy(self):
        for values in [{'daily_usd': 'nan'}, {'max_concurrent': 1.5}, {'max_video_seconds': 6},
                       {'daily_counts': None}, {'mispelled_daily_limit': 5}]:
            with self.assertRaises(ControlError):
                self.ledger.set_policy(values)
        self.assertEqual(self.ledger.policy().daily_usd, '2.00')

    def test_partial_policy_update_preserves_disabled_capabilities_and_other_limits(self):
        self.ledger.set_policy({'monthly_usd': '7.00', 'daily_counts': {'video': 0}})
        self.ledger.set_policy({'daily_usd': '1.00'})
        policy = self.ledger.policy()
        self.assertEqual(policy.monthly_usd, '7.00')
        self.assertEqual(policy.daily_counts['video'], 0)
        self.assertEqual(policy.daily_counts['fast'], 100)

    def test_warnings_and_provider_billing_are_labeled_estimates(self):
        self.ledger.billing_snapshot('2026-11', '6.00591259')
        usage = self.ledger.usage()
        self.assertFalse(usage['provider_hard_cap'])
        self.assertEqual(usage['cost_kind'], 'conservative_estimate')
        self.assertEqual(usage['provider_billing'][0]['source'], 'RunPod billing API')

    def test_compute_estimate_remains_covered_without_becoming_reported_spend(self):
        first, _ = self.reserve()
        self.ledger.finish('alice', first['id'], 'completed')
        job = public_job(self.ledger.get('alice', first['id']))
        self.assertIsNone(job['provider_reported_usd'])
        self.assertEqual(job['cost_basis'], 'unreconciled_estimate')
        day = self.ledger.usage()['periods']['day']
        self.assertEqual(day['budget_held_usd'], first['reserved'] / 1_000_000)
        self.assertEqual(day['unreconciled_estimate_usd'], day['budget_held_usd'])
        self.assertEqual((day['provider_reported_jobs'], day['unreported_jobs']), (0, 1))
        self.ledger.set_policy({'daily_usd': str(day['budget_held_usd'])})
        self.ledger.billing_snapshot('partial-published-hour', '0.01')
        self.assertFalse(self.ledger.quote(FAST)['allowed_at_quote_time'])

    def test_partial_provider_costs_are_separate_from_pending_and_finished_estimates(self):
        image, _ = self.ledger.reserve(self.context, 'black-forest-labs-flux-1-schnell', {})
        self.ledger.finish('alice', image['id'], 'completed', charge='0.003')
        compute, _ = self.reserve()
        self.ledger.finish('alice', compute['id'], 'completed')
        active, _ = self.ledger.reserve(OperationContext('alice', 'other', 'b'), FAST, {'other': True})
        rejected, _ = self.ledger.reserve(OperationContext('alice', 'rejected', 'c'), FAST, {'rejected': True})
        self.ledger.finish('alice', rejected['id'], 'rejected', charge=0)
        day = self.ledger.usage()['periods']['day']
        self.assertEqual(day['provider_reported_usd'], 0.003)
        self.assertEqual((day['provider_reported_jobs'], day['unreported_jobs']), (1, 2))
        self.assertEqual(day['active_reserved_usd'], active['reserved'] / 1_000_000)
        self.assertEqual(day['budget_held_usd'], (3000 + compute['reserved'] + active['reserved']) / 1_000_000)
        self.assertEqual(public_job(self.ledger.get('alice', image['id']))['cost_basis'], 'provider_reported')
        self.assertEqual(public_job(self.ledger.get('alice', rejected['id']))['cost_basis'], 'not_submitted')

    def test_legacy_costs_migrate_once_without_relabeling_or_resetting_usage(self):
        first, _ = self.reserve()
        self.ledger.finish('alice', first['id'], 'completed', {'answer': 'saved'}, '0.003')
        before = self.ledger.usage()['periods']['day']['budget_held_usd']
        with self.ledger.connection() as db:
            db.execute('ALTER TABLE jobs DROP COLUMN provider_reported')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: Ledger(self.ledger.path, lambda: self.now), range(4)))
        row = self.ledger.get('alice', first['id'])
        self.assertIsNone(row['provider_reported'])
        self.assertEqual(row['output'], {'answer': 'saved'})
        day = self.ledger.usage()['periods']['day']
        self.assertEqual(day['budget_held_usd'], before)
        self.assertEqual(day['provider_reported_jobs'], 0)
        self.assertEqual(day['unreported_jobs'], 1)

    def test_admin_resolution_is_an_estimate_even_with_an_explicit_amount(self):
        first, _ = self.reserve()
        self.ledger.transition('alice', first['id'], 'unknown')
        self.ledger.resolve_unknown(first['id'], 'admin', 'Reviewed provider outcome manually', '0.01')
        job = public_job(self.ledger.get('alice', first['id']))
        self.assertEqual(job['cost_basis'], 'admin_estimate')
        self.assertIsNone(job['provider_reported_usd'])
        self.assertEqual(self.ledger.usage()['periods']['day']['budget_held_usd'], 0.01)

    def test_voice_session_does_not_exist_until_manual_activation_and_expires(self):
        self.assertEqual(self.ledger.voice('alice')['state'], 'off')
        self.ledger.voice('alice', 'chat-a', activate=True)
        self.ledger.mark_voice_ready('alice')
        self.assertEqual(self.ledger.voice('alice')['state'], 'ready')
        self.now += 301
        self.assertEqual(self.ledger.voice('alice')['state'], 'off')

    def test_asset_registry_does_not_cross_users(self):
        first, _ = self.reserve()
        self.ledger.remember_asset('alice', first['id'], {'id': 'file-a', 'url': '/files/a'}, 'https://example.test/object')
        self.assertEqual(self.ledger.asset_source('alice', 'file-a'), 'https://example.test/object')
        with self.assertRaises(ControlError):
            self.ledger.asset_source('bob', 'file-a')


class ControlHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = Ledger(Path(self.temp.name) / 'control.sqlite3')
        self.api = ControlAPI(self.ledger)
        self.job, _ = self.ledger.reserve(OperationContext('alice', 'chat', 'turn'), FAST, {'prompt': 'Hello'})
        self.ledger.finish('alice', self.job['id'], 'completed', {'answer': 'Hei'})
        app = web.Application()
        app.router.add_route('*', '/{path:.*}', self.handle)
        self.server = TestServer(app)
        await self.server.start_server()
        self.session = aiohttp.ClientSession()

    async def asyncTearDown(self):
        await self.session.close()
        await self.server.close()

    async def handle(self, request):
        # Local test identity verifier only. Production uses Open WebUI's real
        # get_verified_user dependency; no live auth is claimed by these tests.
        token = request.headers.get('Authorization', '')
        user = {'id': 'alice' if token == 'Bearer local-alice' else 'bob', 'role': 'admin' if token == 'Bearer local-admin' else 'user'} if token else None
        try:
            body = await request.json() if request.can_read_body else {}
            result = await self.api.dispatch(request.method, '/' + request.match_info['path'], user, body, dict(request.headers))
            return web.json_response(result)
        except ControlError as error:
            return web.json_response({'code': error.code}, status=401 if error.code == 'authentication_required' else 404 if error.code == 'not_found' else 403)

    async def test_real_http_auth_ownership_and_persisted_result(self):
        url = self.server.make_url(f'/jobs/{self.job["id"]}')
        async with self.session.get(url) as response:
            self.assertEqual(response.status, 401)
        async with self.session.get(url, headers={'Authorization': 'Bearer local-bob'}) as response:
            self.assertEqual(response.status, 404)
        async with self.session.get(url, headers={'Authorization': 'Bearer local-alice'}) as response:
            data = await response.json()
            self.assertEqual(data['output'], {'answer': 'Hei'})
            self.assertNotIn('digest', data)

    async def test_cross_origin_writes_and_non_admin_policy_are_rejected(self):
        url = self.server.make_url('/policy')
        async with self.session.post(url, json={'daily_usd': '5'}, headers={'Authorization': 'Bearer local-alice'}) as response:
            self.assertEqual(response.status, 403)
        async with self.session.post(url, json={'daily_usd': '5'}, headers={'Authorization': 'Bearer local-admin', 'Origin': 'https://attacker.test'}) as response:
            self.assertEqual(response.status, 403)

    async def test_sse_cursor_can_replay_after_reconnect(self):
        events = self.ledger.events('alice', self.job['id'])
        stream = self.api.stream_events('alice', self.job['id'], events[0]['id'], max_seconds=0.1)
        output = ''.join([chunk async for chunk in stream])
        self.assertIn('job.finished', output)
        self.assertNotIn('job.created', output)

    async def test_retry_endpoint_never_submits_a_provider_job(self):
        url = self.server.make_url(f'/jobs/{self.job["id"]}/retry')
        async with self.session.post(url, json={}, headers={'Authorization': 'Bearer local-alice'}) as response:
            data = await response.json()
            self.assertFalse(data['submitted'])
            self.assertFalse(data['retry_allowed'])


if __name__ == '__main__':
    unittest.main()
