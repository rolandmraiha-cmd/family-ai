import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer

ROOT = Path(__file__).parents[1]


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Open WebUI/FastAPI are not installed here. Stub storage and the HTML response
# boundary; all RunPod transport and module methods below run as real code.
stubs = {name: types.ModuleType(name) for name in [
    "fastapi", "fastapi.responses",
    "open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.users",
    "open_webui.routers", "open_webui.routers.images", "open_webui.utils", "open_webui.utils.chat_id",
]}
stubs["fastapi.responses"].HTMLResponse = lambda content, headers: {"content": content, "headers": headers}
stubs["open_webui.models.chats"].Chats = types.SimpleNamespace(add_message_files_by_id_and_message_id=AsyncMock())
stubs["open_webui.models.users"].UserModel = dict
stubs["open_webui.routers.images"].upload_image = AsyncMock()
stubs["open_webui.utils.chat_id"].is_saved_chat_id = lambda value: False
with patch.dict(sys.modules, stubs):
    modules = load_file("family_modules", "openwebui/tools/family_media.py")
voice = load_file("start_voice", "openwebui/actions/start_voice.py")


class ModuleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tools = modules.Tools()
        self.tools.valves.RUNPOD_API_KEY = "local-test-only"
        self.calls = []
        self.outputs = []
        self.events = []
        self.fail_submit = False
        self.queue = False
        self.voice_status = 200
        self.pending = asyncio.Event()
        app = web.Application()
        app.router.add_route("*", "/{model}/{operation}/{job}", self.handle)
        app.router.add_route("*", "/{model}/{operation}", self.handle)
        app.router.add_get("/voice", self.voice_handler)
        self.server = TestServer(app)
        await self.server.start_server()
        self.old_url, self.old_voice = modules.RUNPOD, voice.VOICE_URL
        modules.RUNPOD = str(self.server.make_url("")).rstrip("/")
        voice.VOICE_URL = str(self.server.make_url("/voice"))

    async def asyncTearDown(self):
        modules.RUNPOD, voice.VOICE_URL = self.old_url, self.old_voice
        await self.server.close()

    async def emit(self, event):
        self.events.append(event)

    async def handle(self, req):
        op = req.match_info["operation"]
        data = await req.json() if op == "run" else None
        self.calls.append((req.match_info["model"], op, data))
        if op == "run":
            if self.fail_submit:
                return web.json_response({"error": "private upstream detail"}, status=503)
            return web.json_response({"id": f"job-{len(self.calls)}"})
        if op == "cancel":
            return web.json_response({"status": "CANCELLED"})
        if self.queue:
            self.pending.set()
            return web.json_response({"status": "IN_QUEUE"})
        return web.json_response({"status": "COMPLETED", "output": self.outputs.pop(0)})

    async def voice_handler(self, req):
        self.calls.append(("voice", "models", None))
        return web.json_response({"data": []}, status=self.voice_status)

    async def test_reasoning_returns_final_answer_without_private_trace_or_recursive_tools(self):
        self.outputs = [[{"choices": [{"message": {"content": "Vastaus", "reasoning": "private trace"}, "finish_reason": "stop"}]}]]
        result = await self.tools.ask_deep_reasoning("Kysymys", "Faktat", "Finnish", self.emit)
        self.assertIn("Vastaus", result)
        self.assertNotIn("private trace", result)
        self.assertEqual([op for _, op, _ in self.calls], ["run", "status"])
        payload = self.calls[0][2]["input"]["openai_input"]
        self.assertNotIn("tools", payload)
        self.assertTrue(payload["chat_template_kwargs"]["enable_thinking"])
        self.assertIn("Finnish", payload["messages"][0]["content"])
        self.assertEqual(self.tools._inflight, 0)

    async def test_reasoning_failure_is_sanitized_and_never_retried(self):
        self.fail_submit = True
        result = await self.tools.ask_deep_reasoning("Hard question", __event_emitter__=self.emit)
        self.assertIn("HTTP 503", result)
        self.assertNotIn("private upstream", result)
        self.assertEqual(len(self.calls), 1)

    async def test_deepseek_profile_uses_single_user_prompt_without_tools(self):
        self.tools.valves.REASONING_STYLE = "deepseek_r1"
        self.tools.valves.REASONING_MODEL = "family-deepseek"
        self.outputs = [{"choices": [{"message": {"content": "Answer"}}]}]
        await self.tools.ask_deep_reasoning("Question", "Constraints", "Swedish")
        payload = self.calls[0][2]["input"]["openai_input"]
        self.assertEqual([m["role"] for m in payload["messages"]], ["user"])
        self.assertEqual(payload["temperature"], 0.6)
        self.assertNotIn("chat_template_kwargs", payload)
        self.assertNotIn("tools", payload)

    async def test_reasoning_never_uses_trace_as_final_answer(self):
        self.outputs = [[{"choices": [{"message": {"reasoning": "private trace"}}]}]]
        self.assertIn("no final answer", await self.tools.ask_deep_reasoning("Question"))

    async def test_input_limits_and_missing_key_do_not_submit(self):
        await self.tools.ask_deep_reasoning(" ")
        await self.tools.ask_deep_reasoning("x" * 24001)
        self.tools.valves.RUNPOD_API_KEY = ""
        await self.tools.ask_deep_reasoning("Question")
        self.assertEqual(self.calls, [])

    async def test_client_cancellation_cancels_specialist_job(self):
        self.queue = True
        async with aiohttp.ClientSession() as session:
            task = asyncio.create_task(self.tools._run(session, "specialist", {}, AsyncMock(), "Thinking", 60))
            await asyncio.wait_for(self.pending.wait(), 2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertIn("cancel", [op for _, op, _ in self.calls])
        self.assertEqual(self.tools._inflight, 0)

    async def test_media_tools_share_the_same_transport_and_save_results(self):
        self.tools._save = AsyncMock(return_value={"url": "/files/test", "id": "file1"})
        self.outputs = [{"image_url": "https://example.test/image.jpg", "cost": 0.003}]
        result = await self.tools.generate_image("A house", __event_emitter__=self.emit)
        self.assertIn("shown to the user", result)
        self.assertEqual(self.calls[0][0], "black-forest-labs-flux-1-schnell")
        self.assertEqual(self.tools._save.await_count, 1)
        self.assertTrue(any(e.get("type") == "chat:message:files" for e in self.events))

    async def test_video_chains_start_image_then_wan_and_caps_duration(self):
        self.tools._save = AsyncMock(return_value={"url": "/files/video", "id": "file2"})
        self.outputs = [{"image_url": "https://example.test/image.jpg"}, {"video_url": "https://example.test/video.mp4"}]
        result = await self.tools.generate_video("A moving house", __event_emitter__=self.emit)
        submitted = [(name, data) for name, op, data in self.calls if op == "run"]
        self.assertEqual([name for name, _ in submitted], ["black-forest-labs-flux-1-schnell", "wan-2-2-i2v-720"])
        self.assertEqual(submitted[1][1]["input"]["duration"], 5)
        self.assertIn("video is playing", result[1])

    async def test_voice_starts_only_on_manual_action_and_does_not_change_history(self):
        action = voice.Action()
        action.valves.RUNPOD_API_KEY = "local-test-only"
        self.assertEqual(self.calls, [])
        body = {"messages": [{"role": "assistant", "content": "Answer"}]}
        result = await action.action(body, self.emit)
        self.assertIs(result, body)
        self.assertEqual(self.calls, [("voice", "models", None)])
        self.assertIn("ready", self.events[-1]["data"]["description"])

    async def test_cold_voice_does_not_claim_readiness_or_auto_retry(self):
        action = voice.Action()
        action.valves.RUNPOD_API_KEY = "local-test-only"
        self.voice_status = 503
        await action.action({}, self.emit)
        self.assertIn("startup requested", self.events[-1]["data"]["description"])
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
