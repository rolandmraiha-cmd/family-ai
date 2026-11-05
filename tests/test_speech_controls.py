import asyncio
import io
import sys
import tempfile
import types
import unittest
import wave
from unittest.mock import AsyncMock, patch

from family_backend.control import ControlError, default_ledger, configured_runpod_key
from family_backend.speech import SpeechService, validate_recording
from control_support import isolate_controls


def recording(seconds=1, rate=8000):
    data = io.BytesIO()
    with wave.open(data, 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(b'\0\0' * rate * seconds)
    return data.getvalue()


class SpeechControlsTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        isolate_controls(self)
        self.provider = AsyncMock(return_value={'text': 'Hyvää huomenta!'})
        self.save = AsyncMock(return_value={'id': 'saved-file', 'type': 'audio', 'url': '/api/v1/files/saved-file/content'})
        self.service = SpeechService(self.provider, self.save)

    def activate(self):
        default_ledger().voice('alice', 'chat-a', activate=True)

    async def run_audio(self, **kwargs):
        return await self.service.run('alice', kwargs.get('chat', 'chat-a'), 'turn-a',
            kwargs.get('kind', 'transcriptions'), kwargs.get('language', 'fi'), kwargs.get('value', recording()))

    async def test_no_manual_session_means_no_paid_request(self):
        with self.assertRaisesRegex(ControlError, 'Start voice'):
            await self.run_audio()
        self.provider.assert_not_awaited()
        self.assertEqual(default_ledger().list_jobs('alice'), [])

    async def test_session_is_bound_to_its_owner_and_conversation(self):
        self.activate()
        with self.assertRaisesRegex(ControlError, 'Start voice'):
            await self.run_audio(chat='other-chat')
        self.provider.assert_not_awaited()

    async def test_session_activation_alone_does_not_submit_or_reserve(self):
        self.activate()
        self.assertEqual(default_ledger().list_jobs('alice'), [])
        self.provider.assert_not_awaited()

    async def test_all_languages_and_transcript_replay(self):
        self.activate()
        for language in ('fi', 'sv', 'en'):
            first = await self.run_audio(language=language)
            replay = await self.run_audio(language=language)
            self.assertEqual(first, replay)
            self.assertEqual(first['language'], language)
        self.assertEqual(self.provider.await_count, 3)
        self.assertEqual(len(default_ledger().list_jobs('alice')), 3)

    async def test_audio_bounds_and_language_block_before_submission(self):
        self.activate()
        for value in (b'not-wav', recording(31), recording()[:-8]):
            with self.assertRaises(ControlError):
                await self.run_audio(value=value)
        with self.assertRaises(ControlError):
            await self.run_audio(language='de')
        self.provider.assert_not_awaited()

    async def test_text_bounds_before_submission(self):
        self.activate()
        for value in ('', ' ' * 5, 'x' * 2001, None):
            with self.assertRaises(ControlError):
                await self.run_audio(kind='speech', value=value)
        self.provider.assert_not_awaited()

    async def test_piper_saved_file_is_replayed_without_second_charge(self):
        self.activate()
        self.provider.return_value = recording()
        first = await self.run_audio(kind='speech', value='Hei!')
        self.assertEqual(first['file']['id'], 'saved-file')
        self.assertEqual(first, await self.run_audio(kind='speech', value='Hei!'))
        self.provider.assert_awaited_once()
        self.save.assert_awaited_once()
        self.assertEqual(default_ledger().get('alice', first['job_id'])['state'], 'completed')

    async def test_lost_provider_reply_holds_reservation_and_blocks_replay(self):
        self.activate()
        self.provider.side_effect = asyncio.TimeoutError()
        with self.assertRaises(asyncio.TimeoutError):
            await self.run_audio()
        row = default_ledger().list_jobs('alice')[0]
        self.assertEqual(row['state'], 'unknown')
        self.assertGreater(row['reserved'], 0)
        with self.assertRaises(ControlError):
            await self.run_audio()
        self.provider.assert_awaited_once()

    async def test_cancelled_request_never_resubmits(self):
        self.activate()
        self.provider.side_effect = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await self.run_audio()
        self.assertEqual(default_ledger().list_jobs('alice')[0]['state'], 'unknown')

    async def test_audio_delivery_failure_does_not_rebuy_speech(self):
        self.activate()
        self.provider.return_value = recording()
        self.save.side_effect = OSError('storage unavailable')
        with self.assertRaises(OSError):
            await self.run_audio(kind='speech', value='Hei!')
        with self.assertRaises(ControlError):
            await self.run_audio(kind='speech', value='Hei!')
        self.provider.assert_awaited_once()

    async def test_budget_applies_to_each_speech_operation(self):
        self.activate()
        default_ledger().set_policy({'daily_counts': {'voice': 0}})
        with self.assertRaises(ControlError):
            await self.run_audio()
        self.provider.assert_not_awaited()


class CredentialReuseTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_exact_existing_runpod_connections_are_eligible(self):
        tools = types.ModuleType('open_webui.models.tools')
        tools.Tools = types.SimpleNamespace(get_tool_valves_by_id=AsyncMock(return_value={}))
        config = types.ModuleType('open_webui.models.config')
        values = {'openai.api_base_urls': ['https://api.runpod.ai.evil.test/v2/52cjk52hgbwag1/openai/v1',
                  'https://api.runpod.ai/v2/52cjk52hgbwag1/openai/v1'],
                  'openai.api_keys': ['wrong-fixture', 'existing-fixture']}
        config.Config = types.SimpleNamespace(get_many=AsyncMock(return_value=values))
        with patch.dict(sys.modules, {'open_webui.models.tools': tools, 'open_webui.models.config': config}):
            self.assertEqual(await configured_runpod_key(), 'existing-fixture')
            tools.Tools.get_tool_valves_by_id.return_value = {'RUNPOD_API_KEY': 'tool-fixture'}
            self.assertEqual(await configured_runpod_key(), 'tool-fixture')
