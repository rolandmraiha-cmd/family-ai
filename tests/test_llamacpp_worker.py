import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from aiohttp import web

spec = importlib.util.spec_from_file_location("llamacpp_worker", Path(__file__).parents[1] / "runpod/llamacpp_worker.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class CandidateWorkerTests(unittest.TestCase):
    def test_cached_boot_requires_both_files_at_pinned_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            snapshot = root / ("models--" + worker.REPO.replace("/", "--")) / "snapshots" / worker.REVISION
            snapshot.mkdir(parents=True)
            (snapshot / worker.MODEL).touch()
            with self.assertRaises(FileNotFoundError):
                worker.model_args(root)
            (snapshot / worker.PROJECTOR).touch()
            args, hit = worker.model_args(root)
            self.assertTrue(hit)
            self.assertEqual(args[1], str(snapshot / worker.MODEL))

    def test_cache_miss_does_not_download_or_accept_other_revision(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / ("models--" + worker.REPO.replace("/", "--")) / "snapshots" / "other-revision"
            snapshot.mkdir(parents=True)
            (snapshot / worker.MODEL).touch()
            (snapshot / worker.PROJECTOR).touch()
            with self.assertRaises(FileNotFoundError):
                worker.model_args(Path(folder))

    def test_lowercase_runpod_cache_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / ("models--" + worker.REPO.replace("/", "--").lower()) / "snapshots" / worker.REVISION
            snapshot.mkdir(parents=True)
            (snapshot / worker.MODEL).touch()
            (snapshot / worker.PROJECTOR).touch()
            self.assertTrue(worker.model_args(Path(folder))[1])

    def test_health_alone_cannot_mark_empty_router_ready(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        with patch.object(worker.urllib.request, 'urlopen', return_value=response):
            response.read.return_value = b'{"data": []}'
            self.assertFalse(worker.model_ready())
            response.read.return_value = b'{"data": [{"id": "unrelated-model"}]}'
            self.assertFalse(worker.model_ready())
            response.read.return_value = b'{"data": [{"id": "family-gemma"}]}'
            self.assertTrue(worker.model_ready())

    def test_preserves_extensions_and_streaming(self):
        payload = {"stream": True, "chat_template_kwargs": {"enable_thinking": False}, "tools": []}
        route, value = worker.request_input({"input": {"openai_route": "/v1/chat/completions", "openai_input": payload}})
        self.assertEqual(route, "/v1/chat/completions")
        self.assertEqual(value["chat_template_kwargs"], payload["chat_template_kwargs"])
        self.assertTrue(value["stream"])
        self.assertNotIn("model", payload)

    def test_rejects_other_routes_and_excess_images(self):
        with self.assertRaises(ValueError):
            worker.request_input({"input": {"openai_route": "/../props"}})
        with self.assertRaises(ValueError):
            worker.request_input({"input": {"messages": [{"content": [{"type": "image_url"}] * 5}]}})


class QueueBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.previous = worker.BASE
        self.requests = []
        async def completion(request):
            value = await request.json()
            self.requests.append(value)
            if not value.get("stream"):
                return web.json_response({"choices": [{"message": {"content": "Hyvää päivää"}}]})
            response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
            await response.prepare(request)
            encoded = 'data: {"content":"Hyvää"}\n\ndata: [DONE]\n\n'.encode()
            # Split inside UTF-8 as well as between SSE delimiters.
            for byte in encoded:
                await response.write(bytes([byte]))
            await response.write_eof()
            return response
        application = web.Application()
        application.router.add_post('/v1/chat/completions', completion)
        self.runner = web.AppRunner(application)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '127.0.0.1', 0)
        await site.start()
        worker.BASE = 'http://127.0.0.1:' + str(site._server.sockets[0].getsockname()[1])

    async def asyncTearDown(self):
        worker.BASE = self.previous
        await self.runner.cleanup()

    async def test_nonstream_forwards_template_options_without_sdk_filtering(self):
        payload = {"chat_template_kwargs": {"enable_thinking": False}, "stream": False}
        output = [item async for item in worker.handler({"input": {"openai_input": payload}})]
        self.assertEqual(output[0]['choices'][0]['message']['content'], 'Hyvää päivää')
        self.assertEqual(self.requests[0]['chat_template_kwargs'], payload['chat_template_kwargs'])

    async def test_stream_handles_fragmented_unicode_and_done(self):
        output = [item async for item in worker.handler({"input": {"openai_input": {"stream": True}}})]
        self.assertEqual(output, ['data: {"content":"Hyvää"}\n\n', 'data: [DONE]\n\n'])
