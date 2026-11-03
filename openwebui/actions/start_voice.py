"""
title: Start voice
description: Manually wake the existing Whisper/Piper GPU. Does not keep it running.
version: 0.2.0
requirements: aiohttp
"""

import asyncio

import aiohttp
from pydantic import BaseModel, Field

from family_backend.control import ControlError, Operation, context_for, operation_context, default_ledger

VOICE_URL = "https://b8yk3ju5yc5kqx.api.runpod.ai/v1/models"


class Action:
    class Valves(BaseModel):
        RUNPOD_API_KEY: str = Field(default="", description="Admin enters the existing RunPod key here.")

    def __init__(self):
        self.valves = self.Valves()

    async def runpod_key(self):
        if self.valves.RUNPOD_API_KEY:
            return self.valves.RUNPOD_API_KEY
        try:
            from open_webui.models.tools import Tools
        except ImportError:
            return ""
        valves = await Tools.get_tool_valves_by_id("family_media") or {}
        return valves.get("RUNPOD_API_KEY", "")

    async def action(self, body: dict, __event_emitter__=None, __user__=None):
        async def status(text):
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": text, "done": True}})

        key = await self.runpod_key()
        if not key:
            await status("The admin must configure the Start voice action's RunPod key.")
            return body
        try:
            context = context_for(__user__, chat_id=body.get("chat_id"), message_id=body.get("id"))
        except ControlError as error:
            await status(str(error))
            return body
        # This action runs only after a person presses its button. Ordinary
        # typed chat never probes voice or holds a minimum GPU worker open.
        operation = None
        try:
            with operation_context(context):
                # A new manual click after 30s can check readiness; rapid
                # double clicks replay the same reservation instead of waking twice.
                bucket = int(__import__('time').time() // 30)
                operation = Operation("b8yk3ju5yc5kqx", {"manual_voice_start": bucket}, timeout=300)
                replay = operation.replay()
                if replay is not None:
                    await status(f"Voice session is {replay['state']}. No duplicate startup request was sent.")
                    return body
                ledger = default_ledger()
                ledger.voice(context.owner, context.conversation, activate=True)
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=25), trust_env=True,
                    headers={"Authorization": f"Bearer {key}"},
                ) as session:
                    operation.submitting()
                    async with session.get(VOICE_URL) as response:
                        if response.status == 200:
                            await response.read()
                            ledger.mark_voice_ready(context.owner)
                            operation.complete({"state": "ready"})
                            await status("Voice is ready. Select Family AI Auto and use Standard call mode or the microphone.")
                        elif response.status in {502, 503, 504}:
                            operation.complete({"state": "starting"})
                            await status("Voice startup requested. It may take a few minutes; no minimum worker was enabled.")
                        else:
                            operation.terminal("FAILED")
                            ledger.voice(context.owner, stop=True)
                            await status(f"Voice could not start (HTTP {response.status}). Check its endpoint settings.")
        except (aiohttp.ClientError, asyncio.TimeoutError, ControlError):
            await status("Voice did not confirm readiness or its budget was reached. Check the existing job before retrying.")
        finally:
            if operation:
                operation.unresolved()
        return body

