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
        with patch.dict(sys.modules, {'open_webui.utils.auth': auth}):
            install_api(self.app)
            install_api(self.app)
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
