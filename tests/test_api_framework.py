"""Real FastAPI/ASGI adapter tests. Only Open WebUI identity is a test seam."""
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

try:
    from fastapi import FastAPI, Header, HTTPException
    import httpx
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False

from family_backend.api import install_api
from family_backend.control import default_ledger, OperationContext


@unittest.skipUnless(FRAMEWORK_AVAILABLE, 'Install tests/requirements.txt for real FastAPI adapter tests')
class FrameworkTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        environment = patch.dict(os.environ, {'FAMILY_CONTROL_DB': str(Path(self.directory.name) / 'control.sqlite3')})
        environment.start()
        self.addCleanup(environment.stop)

        # The deployed app uses its existing JWT/cookie/API-key verifier. This
        # fixture exercises FastAPI dependency wiring, not production login.
        async def verified(authorization: str = Header(default='')):
            if authorization not in {'Bearer alice', 'Bearer bob', 'Bearer admin'}:
                raise HTTPException(401, 'Test identity required')
            identity = authorization.split()[-1]
            return types.SimpleNamespace(id=identity, role='admin' if identity == 'admin' else 'user')
        auth = types.ModuleType('open_webui.utils.auth')
        auth.get_verified_user = verified
        self.app = FastAPI()
        @self.app.get('/native-sentinel')
        async def native(): return {'untouched': True}
        fallback = FastAPI()
        @fallback.get('/{path:path}')
        async def spa(path: str): return {'spa': True}
        self.app.mount('/', fallback)
        installer = install_api
        if getattr(self, 'native_bundle', False):
            # Native v0.12.4 exec() inherits postponed annotations from its
            # loader. Normal importlib loading does not reproduce that boundary.
            import __future__
            from scripts.build_openwebui_bundle import build
            output = Path(self.directory.name) / 'bundle'
            build(Path(__file__).resolve().parents[1], output)
            module = types.ModuleType('family_native_runtime_test')
            patcher = patch.dict(sys.modules, {module.__name__: module})
            patcher.start()
            self.addCleanup(patcher.stop)
            source = (output / 'family_runtime.py').read_text(encoding='utf-8')
            exec(compile(source, 'family_runtime.py', 'exec',
                         flags=__future__.annotations.compiler_flag, dont_inherit=True), module.__dict__)
            installer = module.install_api
        with patch.dict(sys.modules, {'open_webui.utils.auth': auth}):
            installer(self.app)
            installer(self.app)
        self.account_type = installer.__globals__['RunPodAccount']
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='https://family.test')

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_real_framework_auth_registration_and_disable(self):
        result = await self.client.get('/api/v1/family/usage')
        self.assertEqual(result.status_code, 401)
        result = await self.client.get('/api/v1/family/usage', headers={'Authorization': 'Bearer alice'})
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json()['provider_hard_cap'])
        self.assertEqual((await self.client.get('/native-sentinel')).json(), {'untouched': True})
        paths = [r.path for r in self.app.routes]
        self.assertEqual(paths.count('/api/v1/family/usage'), 1)
        self.app.state.family_control_api_active = False
        result = await self.client.get('/api/v1/family/usage', headers={'Authorization': 'Bearer alice'})
        self.assertEqual(result.status_code, 503)

    async def test_account_auth_admin_scope_and_no_browser_cache(self):
        from unittest.mock import AsyncMock
        with patch.object(self.account_type, 'get', new=AsyncMock(return_value={'balance': {'amount_usd': 15.53}})) as monitor:
            path = '/api/v1/family/account'
            self.assertEqual((await self.client.get(path)).status_code, 401)
            self.assertEqual((await self.client.get(path, headers={'Authorization':'Bearer alice'})).status_code, 403)
            monitor.assert_not_awaited()
            result = await self.client.get(path, headers={'Authorization':'Bearer admin'})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()['balance']['amount_usd'], 15.53)
            self.assertEqual(result.headers['cache-control'], 'private, no-store')

    async def test_manual_voice_intent_uses_verified_owner_and_same_origin_without_gpu_work(self):
        chats = types.ModuleType('open_webui.models.chats')
        from unittest.mock import AsyncMock
        chats.Chats = types.SimpleNamespace(get_chat_by_id_and_user_id=AsyncMock(
            side_effect=lambda conversation, owner: object() if conversation == 'chat-a' and owner == 'alice' else None))
        path = '/api/v1/family/voice/session?chat_id=chat-a&turn=manual-click'
        with patch.dict(sys.modules, {'open_webui.models.chats': chats}):
            self.assertEqual((await self.client.post(path)).status_code, 401)
            headers = {'Authorization': 'Bearer alice', 'Origin': 'https://evil.test'}
            self.assertEqual((await self.client.post(path, headers=headers)).status_code, 403)
            headers['Origin'] = 'https://family.test'
            result = await self.client.post(path, headers=headers)
            self.assertEqual(result.status_code, 200)
            self.assertFalse(result.json()['wakes_voice'])
            headers['Authorization'] = 'Bearer bob'
            self.assertEqual((await self.client.post(path, headers=headers)).status_code, 404)
        self.assertEqual(default_ledger().list_jobs('alice'), [])
        self.assertEqual(default_ledger().voice('alice')['conversation'], 'chat-a')

    async def test_real_framework_body_limits_origin_and_policy(self):
        path = '/api/v1/family/policy'
        result = await self.client.post(path, json={'daily_usd': '5'}, headers={'Authorization': 'Bearer admin', 'Origin': 'https://evil.test'})
        self.assertEqual(result.status_code, 403)
        result = await self.client.post(path, content=b'x' * 65537, headers={'Authorization': 'Bearer admin'})
        self.assertEqual(result.status_code, 413)
        result = await self.client.post(path, json={'daily_usd': '5'}, headers={'Authorization': 'Bearer admin', 'Origin': 'https://family.test'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['daily_usd'], '5')

    async def test_real_framework_owned_sse_and_last_event_id(self):
        ledger = default_ledger()
        row, _ = ledger.reserve(OperationContext('alice', 'chat', 'turn'), '52cjk52hgbwag1', {'fixture': True})
        ledger.finish('alice', row['id'], 'completed', {'answer': 'Hei'})
        path = '/api/v1/family/jobs/' + row['id'] + '/events'
        result = await self.client.get(path, headers={'Authorization': 'Bearer bob'})
        self.assertEqual(result.status_code, 404)
        first = ledger.events('alice', row['id'])[0]['id']
        result = await self.client.get(path, headers={'Authorization': 'Bearer alice', 'Last-Event-ID': str(first)})
        self.assertEqual(result.status_code, 200)
        self.assertIn('text/event-stream', result.headers['content-type'])
        self.assertIn('job.finished', result.text)
        self.assertNotIn('job.created', result.text)


class NativePluginFrameworkTests(FrameworkTests):
    native_bundle = True
