import asyncio
import importlib.util
import json
from pathlib import Path
import unittest

from aiohttp import web
from aiohttp.test_utils import TestServer
from control_support import isolate_controls

spec = importlib.util.spec_from_file_location(
    "family_router", Path(__file__).parents[1] / "openwebui/functions/family_router.py"
)
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


def request(text="Hello", mode="auto", stream=False):
    return {"model": f"family_router.{mode}", "messages": [{"role": "user", "content": text}], "stream": stream}


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.pipe = router.Pipe()

    def test_fast_default_and_language_fallback(self):
        self.assertEqual(self.pipe.select(request())[0], "fast")
        self.pipe.valves.FAST_ENDPOINT_ID = ""
        self.assertEqual(self.pipe.select(request())[0], "language")
        self.assertNotIn("fast", [m["id"] for m in self.pipe.pipes()])

    def test_fast_and_pro_can_be_selected(self):
        self.pipe.valves.FAST_ENDPOINT_ID = "smallgpu"
        self.assertEqual(self.pipe.select(request())[0], "fast")
        self.assertEqual(self.pipe.select(request("Debug this traceback"))[0], "pro")
        self.assertEqual(self.pipe.select(request("Moi", "language"))[0], "language")

    def test_old_tool_history_does_not_start_pro_on_simple_new_turn(self):
        body = request("Continue")
        body["messages"].insert(0, {"role": "assistant", "tool_calls": [{"id": "tool1"}]})
        self.assertEqual(self.pipe.select(body)[0], "fast")

    def test_payload_preserves_images_and_tool_calls_without_metadata(self):
        body = request()
        body.update(tools=[{"type": "function", "function": {"name": "generate_image"}}],
                    tool_choice="auto", metadata={"private": "not-for-inference"}, max_tokens=9000)
        body["messages"][0]["content"] = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}]
        result = self.pipe.payload(body, "large-gemma", "language")
        self.assertEqual(result["tools"], body["tools"])
        self.assertEqual(result["messages"][1:], body["messages"])
        self.assertEqual(result["max_tokens"], 2048)
        self.assertFalse(result["chat_template_kwargs"]["enable_thinking"])
        self.assertNotIn("presence_penalty", result)
        self.assertNotIn("metadata", result)
        self.assertNotIn("chat_template_kwargs", body)

    def test_manual_fast_rejects_image_context_before_gpu_start(self):
        body = request()
        body["messages"][0]["content"] = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}]
        with self.assertRaisesRegex(router.RouterError, "text only"):
            self.pipe.payload(body, "family-fast", "fast")

    def test_image_attachment_uses_large_gemma(self):
        body = request()
        body["messages"][0]["content"] = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}]
        self.assertEqual(self.pipe.select(body)[0], "language")

    def test_voice_transcripts_and_typed_requests_share_routes(self):
        for text in ["Think deeply about this decision", "Ajattele tarkasti tätä ongelmaa", "Resonera om detta"]:
            typed, voice = request(text), request(text)
            voice["metadata"] = {"source": "voice"}
            self.assertEqual(self.pipe.select(typed), self.pipe.select(voice))
            self.assertEqual(self.pipe.select(typed)[0], "pro")

    def test_media_stays_on_coordinator_even_with_complex_words(self):
        for text in ["Generate an image of a codebase architecture", "Luo kuva talosta", "Skapa en video av ett hus"]:
            self.assertEqual(self.pipe.select(request(text))[0], "fast")

    def test_specialist_called_once_then_result_returns_to_fast(self):
        body = request("Think deeply and prove that this works")
        body["tools"] = [{"type": "function", "function": {"name": "family_media_ask_deep_reasoning"}}]
        self.assertEqual(self.pipe.select(body)[0], "fast")
        call = self.pipe.delegation(body)
        self.assertEqual(call["function"]["name"], "family_media_ask_deep_reasoning")
        self.assertEqual(json.loads(call["function"]["arguments"])["question"], body["messages"][0]["content"])
        body["messages"] += [
            {"role": "assistant", "tool_calls": [{"id": "d1", "function": {"name": "family_media_ask_deep_reasoning", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "d1", "content": "Specialist answer"},
        ]
        result = self.pipe.payload(body, "family-fast", "fast")
        self.assertIsNone(self.pipe.delegation(body))
        self.assertNotIn("tool_choice", result)
        self.assertEqual(result["messages"][-1]["content"], "Specialist answer")

    def test_manual_choices_and_tool_choice_none_are_respected(self):
        for mode in ["fast", "pro", "language"]:
            body = request("Think deeply", mode)
            body["tools"] = [{"type": "function", "function": {"name": "ask_deep_reasoning"}}]
            self.assertEqual(self.pipe.select(body)[0], mode)
            self.assertNotIn("tool_choice", self.pipe.payload(body, "model", mode))
        body = request("Think deeply")
        body.update(tools=[{"type": "function", "function": {"name": "ask_deep_reasoning"}}], tool_choice="none")
        self.assertEqual(self.pipe.payload(body, "model", "fast")["tool_choice"], "none")

    def test_only_pro_enables_thinking_and_body_is_not_mutated(self):
        body = request("Hello")
        original = json.dumps(body)
        for mode in ["fast", "pro", "language"]:
            payload = self.pipe.payload(body, "model", mode)
            self.assertEqual(payload["chat_template_kwargs"]["enable_thinking"], mode == "pro")
        self.assertEqual(json.dumps(body), original)

    def test_sse_split_json_crlf_tool_calls_and_unicode(self):
        decoder = router.SSEDecoder()
        frame = {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": "ä"}}]}}]}
        wire = "data: " + json.dumps(frame, ensure_ascii=False) + "\r\n\r\n"
        results = []
        for char in wire:
            results.extend(decoder.feed(char))
        self.assertEqual(results, [frame])
        decoder.feed("data: [DONE]\n\n")
        self.assertTrue(decoder.done)

    def test_worker_errors_are_not_echoed(self):
        with self.assertRaises(router.RouterError) as error:
            router.SSEDecoder().feed({"error": "upstream details should stay private"})
        self.assertNotIn("upstream details", str(error.exception))

    def test_fast_and_language_do_not_emit_private_reasoning_fields(self):
        frame = {"choices": [{"message": {"content": "Final", "reasoning": "trace"}}]}
        for mode in ["fast", "language"]:
            cleaned = router.public_frame(frame, mode)
            self.assertNotIn("reasoning", cleaned["choices"][0]["message"])
        self.assertIn("reasoning", frame["choices"][0]["message"])

    def test_oversized_specialist_context_uses_direct_pro_without_truncation(self):
        body = request("Think deeply about this")
        body["messages"].insert(0, {"role": "user", "content": "x" * 25000})
        body["tools"] = [{"type": "function", "function": {"name": "ask_deep_reasoning"}}]
        self.assertIsNone(self.pipe.delegation(body))
        self.assertEqual(self.pipe.select(body)[0], "pro")


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        isolate_controls(self)
        self.pipe = router.Pipe()
        self.pipe.valves.RUNPOD_API_KEY = "unit-test-only"
        self.pipe.valves.POLL_SECONDS = 0.001
        self.calls = []
        self.states = []
        self.submission_status = 200
        self.posted = None
        app = web.Application()
        app.router.add_route("*", "/{endpoint}/{operation}/{job}", self.handle)
        app.router.add_route("*", "/{endpoint}/{operation}", self.handle)
        self.server = TestServer(app)
        await self.server.start_server()
        self.old_api = router.API
        router.API = str(self.server.make_url("")).rstrip("/")

    async def asyncTearDown(self):
        router.API = self.old_api
        await self.server.close()

    async def handle(self, req):
        op = req.match_info["operation"]
        self.calls.append(op)
        if op == "run":
            self.posted = await req.json()
            return web.json_response({"id": "job-1", "status": "IN_QUEUE"}, status=self.submission_status)
        if op == "cancel":
            return web.json_response({"status": "CANCELLED"})
        return web.json_response(self.states.pop(0) if self.states else {"status": "IN_QUEUE", "stream": []})

    async def test_nonstream_waits_and_submits_only_once(self):
        reply = {"choices": [{"message": {"role": "assistant", "content": "Hei!"}}]}
        self.states = [{"status": "IN_QUEUE"}, {"status": "IN_PROGRESS"}, {"status": "COMPLETED", "output": [reply]}]
        result = await self.pipe.pipe(request("Moi", "language"))
        self.assertEqual(result, reply)
        self.assertEqual(self.calls.count("run"), 1)
        self.assertNotIn("cancel", self.calls)
        self.assertEqual(self.posted["input"]["openai_input"]["model"], "family-gemma")

    async def test_explicit_deep_task_dispatches_tool_without_small_gpu_job(self):
        for stream in [True, False]:
            body = request("Think deeply about this", stream=stream)
            body["tools"] = [{"type": "function", "function": {"name": "ask_deep_reasoning"}}]
            result = await self.pipe.pipe(body)
            if stream:
                frame = json.loads((await anext(result))[6:])
                await result.aclose()
                call = frame["choices"][0]["delta"]["tool_calls"][0]
            else:
                call = result["choices"][0]["message"]["tool_calls"][0]
            self.assertEqual(call["function"]["name"], "ask_deep_reasoning")
        self.assertEqual(self.calls, [])

    async def test_stream_reassembles_and_drains_completed_batches(self):
        frames = [
            {"choices": [{"delta": {"content": "Hei "}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "t1", "type": "function", "function": {"name": "generate_image", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]},
        ]
        wire = "".join("data: " + json.dumps(f) + "\n\n" for f in frames) + "data: [DONE]\n\n"
        self.states = [
            {"status": "IN_QUEUE", "stream": []},
            {"status": "IN_PROGRESS", "stream": [{"output": wire[:17]}]},
            {"status": "COMPLETED", "stream": [{"output": wire[17:]}]},
            {"status": "COMPLETED", "stream": []},
        ]
        stream = await self.pipe.pipe(request(stream=True))
        output = [json.loads(s[6:]) async for s in stream]
        actual = [f for f in output if f["choices"][0]["delta"]]
        self.assertEqual(actual, frames)
        self.assertEqual(self.calls.count("run"), 1)
        self.assertEqual(self.pipe._inflight, 0)

    async def test_failed_submission_is_never_retried(self):
        self.submission_status = 503
        with self.assertRaises(router.RouterError):
            await self.pipe.pipe(request())
        self.assertEqual(self.calls, ["run"])

    async def test_timeout_cancels_queued_job(self):
        self.pipe.valves.REQUEST_TIMEOUT_SECONDS = 0.025
        with self.assertRaises(router.RouterError):
            await self.pipe.pipe(request())
        self.assertIn("cancel", self.calls)
        self.assertEqual(self.pipe._inflight, 0)

    async def test_closing_stream_cancels_job(self):
        stream = await self.pipe.pipe(request(stream=True))
        await anext(stream)
        await stream.aclose()
        self.assertIn("cancel", self.calls)
        self.assertEqual(self.pipe._inflight, 0)

    async def test_worker_failure_stops_without_fallback(self):
        self.states = [{"status": "FAILED", "error": "private diagnostic"}]
        with self.assertRaises(router.RouterError) as error:
            await self.pipe.pipe(request())
        self.assertNotIn("private diagnostic", str(error.exception))
        self.assertEqual(self.calls.count("run"), 1)

    async def test_missing_key_and_overload_do_not_submit(self):
        self.pipe.valves.RUNPOD_API_KEY = ""
        with self.assertRaises(router.RouterError):
            await self.pipe.pipe(request())
        self.pipe.valves.RUNPOD_API_KEY = "unit-test-only"
        self.pipe._inflight = self.pipe.valves.MAX_INFLIGHT
        with self.assertRaises(router.RouterError):
            await self.pipe.pipe(request())
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()


