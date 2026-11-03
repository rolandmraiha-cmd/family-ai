"""
title: Start voice
description: Manually wake the existing Whisper/Piper GPU. Does not keep it running.
version: 0.1.0
requirements: aiohttp
"""

import asyncio

import aiohttp
from pydantic import BaseModel, Field

VOICE_URL = "https://b8yk3ju5yc5kqx.api.runpod.ai/v1/models"


class Action:
    class Valves(BaseModel):
        RUNPOD_API_KEY: str = Field(default="", description="Admin enters the existing RunPod key here.")

    def __init__(self):
        self.valves = self.Valves()

    async def action(self, body: dict, __event_emitter__=None):
        async def status(text):
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": text, "done": True}})

        if not self.valves.RUNPOD_API_KEY:
            await status("The admin must configure the Start voice action's RunPod key.")
            return body
        # This action runs only after a person presses its button. Ordinary
        # typed chat never probes voice or holds a minimum GPU worker open.
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=25), trust_env=True,
                headers={"Authorization": f"Bearer {self.valves.RUNPOD_API_KEY}"},
            ) as session:
                async with session.get(VOICE_URL) as response:
                    if response.status == 200:
                        await response.read()
                        await status("Voice is ready. Select Family AI Auto and use Standard call mode or the microphone.")
                    elif response.status in {502, 503, 504}:
                        await status("Voice startup requested. It may take a few minutes; press Start voice again to check.")
                    else:
                        await status(f"Voice could not start (HTTP {response.status}). Check its endpoint settings.")
        except (aiohttp.ClientError, asyncio.TimeoutError):
            await status("Voice did not confirm readiness. Check RunPod before trying again.")
        return body
