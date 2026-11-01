"""
title: Family AI Router
description: Routes chat to your own Runpod models and waits through cold starts.
version: 0.1.0
requirements: aiohttp
"""

import asyncio
import copy
from contextlib import aclosing
import json
import re
import time
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

API = "https://api.runpod.ai/v2"
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}
COMPLEX = re.compile(
    r"```|\b(debug|refactor|traceback|architecture|implement|codebase|repository|"
    r"unit tests?|security audit|race condition|sql query)\b", re.I
)


class RouterError(RuntimeError):
    pass


def last_user_text(messages):
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
    return ""


class SSEDecoder:
    """Worker yields arbitrary pieces of SSE, including split JSON frames."""

    def __init__(self):
        self.pending = ""
        self.done = False

    def feed(self, output):
        if isinstance(output, dict):
            if "error" in output:
                raise RouterError("The model worker returned an error. Check its Runpod logs.")
            return [output]
        if not isinstance(output, str):
            raise RouterError("Unexpected model stream format.")
        self.pending = (self.pending + output).replace("\r\n", "\n")
        frames = []
        while "\n\n" in self.pending:
            event, self.pending = self.pending.split("\n\n", 1)
            data = "\n".join(line[5:].lstrip() for line in event.splitlines() if line.startswith("data:"))
            if not data:
                continue
            if data == "[DONE]":
                self.done = True
                continue
            try:
                frame = json.loads(data)
            except ValueError:
                raise RouterError("The model returned an invalid stream frame.") from None
            if not isinstance(frame, dict) or "error" in frame:
                raise RouterError("The model worker returned an error. Check its Runpod logs.")
            frames.append(frame)
        return frames


class Pipe:
    class Valves(BaseModel):
        RUNPOD_API_KEY: str = Field(default="", description="Owner enters this in the admin panel only.")
        FAST_ENDPOINT_ID: str = Field(default="", description="Leave blank until the small GPU endpoint is tested.")
        FAST_MODEL: str = "family-fast"
        PRO_ENDPOINT_ID: str = "c3lm36gdhpctl2"
        PRO_MODEL: str = "family-brain"
        LANGUAGE_ENDPOINT_ID: str = "936leprwfzb9gr"
        LANGUAGE_MODEL: str = "family-gemma"
        REQUEST_TIMEOUT_SECONDS: int = Field(default=600, ge=30, le=1800)
        POLL_SECONDS: float = Field(default=1.5, ge=0.1, le=10)
        MAX_OUTPUT_TOKENS: int = Field(default=2048, ge=16, le=4096)
        MAX_INFLIGHT: int = Field(default=2, ge=1, le=4)

    def __init__(self):
        self.type = "manifold"
        self.valves = self.Valves()
        self._inflight = 0

    def pipes(self):
        models = [
            {"id": "auto", "name": "Family AI · Auto"},
            {"id": "pro", "name": "Family AI · Pro"},
            {"id": "language", "name": "Family AI · Finnish / Swedish"},
        ]
        if self.valves.FAST_ENDPOINT_ID:
            models.append({"id": "fast", "name": "Family AI · Fast"})
        return models

    def select(self, body):
        mode = body.get("model", "auto").rsplit(".", 1)[-1]
        if mode not in {"auto", "fast", "pro", "language"}:
            raise RouterError("Unknown Family AI model.")
        reason = "Selected by you"
        if mode == "auto":
            text = last_user_text(body.get("messages", []))
            # Deterministic first version: no extra paid classifier call and no
            # claim to measure difficulty. Keep complex tool chains on Pro.
            complex_history = any(m.get("tool_calls") for m in body.get("messages", []))
            if COMPLEX.search(text) or len(text) > 10000 or complex_history:
                mode, reason = "pro", "Coding, long request, or ongoing tool task"
            elif self.valves.FAST_ENDPOINT_ID:
                mode, reason = "fast", "Everyday request"
            else:
                mode, reason = "language", "Small GPU not configured; using existing Gemma"
        if mode == "fast":
            endpoint, model = self.valves.FAST_ENDPOINT_ID, self.valves.FAST_MODEL
        elif mode == "pro":
            endpoint, model = self.valves.PRO_ENDPOINT_ID, self.valves.PRO_MODEL
        else:
            endpoint, model = self.valves.LANGUAGE_ENDPOINT_ID, self.valves.LANGUAGE_MODEL
        if not endpoint or not re.fullmatch(r"[A-Za-z0-9_-]+", endpoint):
            raise RouterError("The selected GPU endpoint is not configured correctly.")
        return mode, endpoint, model, reason

    def payload(self, body, model, mode):
        # Forward only inference parameters, never Open WebUI metadata/user data.
        allowed = {
            "messages", "temperature", "top_p", "top_k", "min_p", "seed", "stop",
            "presence_penalty", "frequency_penalty", "repetition_penalty",
            "tools", "tool_choice", "parallel_tool_calls", "response_format",
        }
        payload = {k: copy.deepcopy(v) for k, v in body.items() if k in allowed}
        requested = body.get("max_completion_tokens", body.get("max_tokens", self.valves.MAX_OUTPUT_TOKENS))
        payload.update(model=model, stream=bool(body.get("stream", False)),
                       max_tokens=min(int(requested or self.valves.MAX_OUTPUT_TOKENS), self.valves.MAX_OUTPUT_TOKENS))
        if payload["max_tokens"] < 1:
            raise RouterError("max_tokens must be positive.")
        if mode == "fast":
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        return payload

    async def _request(self, session, method, path, payload=None):
        # Never retry a submission: a lost reply may already have queued a billed job.
        try:
            async with session.request(method, f"{API}/{path}", json=payload) as response:
                if response.status >= 400:
                    raise RouterError(f"Runpod returned HTTP {response.status}; no job was resubmitted.")
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            raise RouterError("Could not reach Runpod. No job was resubmitted; check Requests before retrying.") from None
        if not isinstance(data, dict):
            raise RouterError("Unexpected Runpod response.")
        return data

    async def _cancel(self, session, endpoint, job):
        try:
            await self._request(session, "POST", f"{endpoint}/cancel/{job}")
        except RouterError:
            pass  # Never mask the original timeout or client disconnect.

    async def _events(self, body, emit):
        if not self.valves.RUNPOD_API_KEY:
            raise RouterError("The admin must enter the Runpod key in this function's valves.")
        if self._inflight >= self.valves.MAX_INFLIGHT:
            raise RouterError("Family AI is busy. Wait for an existing task to finish.")
        mode, endpoint, model, reason = self.select(body)
        payload = self.payload(body, model, mode)
        self._inflight += 1
        job = None
        finished = False
        try:
            timeout = aiohttp.ClientTimeout(total=25, connect=10)
            headers = {"Authorization": f"Bearer {self.valves.RUNPOD_API_KEY}"}
            async with aiohttp.ClientSession(timeout=timeout, headers=headers, trust_env=True) as session:
                try:
                    async with asyncio.timeout(self.valves.REQUEST_TIMEOUT_SECONDS):
                        start = await self._request(session, "POST", f"{endpoint}/run", {
                            "input": {"openai_route": "/v1/chat/completions", "openai_input": payload},
                            "policy": {"executionTimeout": self.valves.REQUEST_TIMEOUT_SECONDS * 1000,
                                       "ttl": self.valves.REQUEST_TIMEOUT_SECONDS * 1000},
                        })
                        job = start.get("id")
                        if not isinstance(job, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", job):
                            raise RouterError("Runpod did not return a valid job ID.")
                        began = time.monotonic()
                        last_notice = -10.0
                        decoder = SSEDecoder()
                        while True:
                            operation = "stream" if payload["stream"] else "status"
                            state = await self._request(session, "GET", f"{endpoint}/{operation}/{job}")
                            status = state.get("status")
                            elapsed = time.monotonic() - began
                            if elapsed - last_notice >= 5:
                                if emit:
                                    await emit({"type": "status", "data": {
                                        "description": f"{mode.title()} · {reason} · {status} · {int(elapsed)}s",
                                        "done": False,
                                    }})
                                # Empty SSE deltas keep the connection alive during cold starts.
                                if payload["stream"]:
                                    yield {"object": "chat.completion.chunk", "model": model,
                                           "choices": [{"index": 0, "delta": {}, "finish_reason": None}]}
                                last_notice = elapsed
                            if status in TERMINAL - {"COMPLETED"}:
                                finished = True
                                raise RouterError(f"The GPU job ended with {status}. Check Runpod Requests.")
                            if payload["stream"]:
                                chunks = state.get("stream", [])
                                for chunk in chunks:
                                    for frame in decoder.feed(chunk.get("output")):
                                        yield frame
                                # Like Runpod's SDK, drain a terminal stream until
                                # it returns no more chunks. Do not replay /status output.
                                if status == "COMPLETED" and not chunks:
                                    finished = True
                                    if decoder.pending.strip() or not decoder.done:
                                        raise RouterError("The GPU stream ended before its completion marker.")
                                    break
                            elif status == "COMPLETED":
                                finished = True
                                output = state.get("output")
                                # vLLM handler is a generator: non-stream JSON is a list of one.
                                if isinstance(output, list) and len(output) == 1:
                                    output = output[0]
                                if not isinstance(output, dict) or "error" in output or "choices" not in output:
                                    raise RouterError("The model did not return a valid chat completion.")
                                yield output
                                break
                            await asyncio.sleep(self.valves.POLL_SECONDS)
                except asyncio.TimeoutError:
                    raise RouterError("The GPU request timed out and cancellation was requested.") from None
                finally:
                    if job and not finished:
                        await self._cancel(session, endpoint, job)
        finally:
            self._inflight -= 1
            if emit:
                await emit({"type": "status", "data": {"description": "Request finished", "done": True}})

    async def _stream(self, body, emit):
        try:
            async with aclosing(self._events(body, emit)) as events:
                async for frame in events:
                    yield "data: " + json.dumps(frame, ensure_ascii=False)
        except RouterError as error:
            yield "data: " + json.dumps({"error": {"message": str(error)}})

    async def pipe(self, body: dict, __event_emitter__=None):
        if body.get("stream", False):
            return self._stream(body, __event_emitter__)
        async with aclosing(self._events(body, __event_emitter__)) as events:
            async for response in events:
                return response
