"""
title: Family Media (images and video)
description: Create pictures (FLUX) and short videos (Wan 2.2) with RunPod public endpoints. Pay per item.
version: 1.1.0
requirements:
"""

import asyncio

import aiohttp
from fastapi.responses import HTMLResponse
from open_webui.models.chats import Chats
from open_webui.models.users import UserModel
from open_webui.routers.images import upload_image
from open_webui.utils.chat_id import is_saved_chat_id
from pydantic import BaseModel, Field

RUNPOD = "https://api.runpod.ai/v2"


class Tools:
    class Valves(BaseModel):
        RUNPOD_API_KEY: str = Field(default="", description="RunPod API key (entered by the admin)")
        IMAGE_MODEL_FAST: str = Field(default="black-forest-labs-flux-1-schnell")
        IMAGE_MODEL_QUALITY: str = Field(default="black-forest-labs-flux-1-dev")
        VIDEO_MODEL: str = Field(default="wan-2-2-i2v-720")
        MAX_VIDEO_SECONDS: int = Field(default=5, description="Hard cap on video length (cost: $0.30 per 5 s)")

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.valves.RUNPOD_API_KEY}", "Content-Type": "application/json"}

    async def _run(self, session: aiohttp.ClientSession, model: str, payload: dict, emit, label: str, timeout_s: int) -> dict:
        async with session.post(f"{RUNPOD}/{model}/run", headers=self._headers(), json={"input": payload}) as r:
            job = await r.json()
        if "id" not in job:
            raise RuntimeError(f"RunPod refused the job: {job}")
        waited = 0
        while waited < timeout_s:
            async with session.get(f"{RUNPOD}/{model}/status/{job['id']}", headers=self._headers()) as r:
                st = await r.json()
            status = st.get("status")
            if status == "COMPLETED":
                return st.get("output") or {}
            if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
                raise RuntimeError(st.get("error") or status)
            await emit(f"{label}… {waited}s")
            await asyncio.sleep(4)
            waited += 4
        raise RuntimeError("Timed out waiting for RunPod")

    async def _save(self, session, url: str, content_type: str, request, user: dict, chat_id, message_id) -> dict:
        """Copies a RunPod result into Open WebUI storage (RunPod links expire after 7 days)."""
        async with session.get(url) as r:
            data = await r.read()
        meta = {"chat_id": chat_id, "message_id": message_id} if is_saved_chat_id(chat_id) and message_id else {}
        _, info = await upload_image(request, data, content_type, meta, UserModel(**user))
        return info

    async def _attach(self, emitter, chat_id, message_id, files: list) -> None:
        if is_saved_chat_id(chat_id) and message_id:
            files = await Chats.add_message_files_by_id_and_message_id(chat_id, message_id, files) or files
        if emitter:
            await emitter({"type": "chat:message:files", "data": {"files": files}})

    async def _image(self, session, prompt: str, quality: bool, width: int, height: int, emit) -> dict:
        model = self.valves.IMAGE_MODEL_QUALITY if quality else self.valves.IMAGE_MODEL_FAST
        payload = {"prompt": prompt, "width": width, "height": height, "seed": -1, "image_format": "jpeg"}
        payload["num_inference_steps"] = 28 if quality else 4
        return await self._run(session, model, payload, emit, "Drawing the picture", 180)

    async def generate_image(
        self,
        prompt: str,
        high_quality: bool = False,
        landscape: bool = False,
        __request__=None,
        __user__: dict = None,
        __chat_id__: str = None,
        __message_id__: str = None,
        __event_emitter__=None,
    ) -> str:
        """
        Create a picture from a text description. Use this whenever the user asks to draw, make, paint or create an image or picture.
        Write the prompt in English, detailed and descriptive (subject, style, colours, lighting), even if the user wrote in Swedish or Finnish.
        :param prompt: Detailed English description of the picture.
        :param high_quality: True only if the user asks for high quality or detail (costs about 8x more).
        :param landscape: True for a wide picture, False for a square one.
        """

        async def emit(msg, done=False):
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": msg, "done": done}})

        if not self.valves.RUNPOD_API_KEY:
            return "The image tool is not set up yet: the admin must enter the RunPod API key in the tool settings."
        w, h = (1344, 768) if landscape else (1024, 1024)
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                out = await self._image(session, prompt, high_quality, w, h, emit)
                url = out.get("image_url") or out.get("result")
                info = await self._save(session, url, "image/jpeg", __request__, __user__, __chat_id__, __message_id__)
            await self._attach(__event_emitter__, __chat_id__, __message_id__, [{"type": "image", **info}])
        except Exception as e:
            await emit("Image failed", True)
            return f"Image generation failed: {e}"
        await emit(f"Picture ready (cost ${float(out.get('cost', 0) or 0):.4f})", True)
        return (
            "The picture has been shown to the user. Do not repeat it or include any image link. "
            f"Briefly describe what you made, in the user's language. Source link for an animation (valid 7 days): {url}"
        )

    async def generate_video(
        self,
        prompt: str,
        image_url: str = "",
        __request__=None,
        __user__: dict = None,
        __chat_id__: str = None,
        __message_id__: str = None,
        __event_emitter__=None,
    ):
        """
        Create a short 5-second video. Use this when the user asks for a video, animation or moving picture.
        If the user wants to animate a picture made earlier in this chat, pass its source link as image_url. Otherwise leave image_url empty and a starting picture is made from the prompt first.
        Write the prompt in English: describe the scene and the motion.
        :param prompt: English description of the scene and the movement.
        :param image_url: Optional https link of the picture to animate.
        """

        async def emit(msg, done=False):
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": msg, "done": done}})

        if not self.valves.RUNPOD_API_KEY:
            return "The video tool is not set up yet: the admin must enter the RunPod API key in the tool settings."
        cost = 0.0
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=900)) as session:
                if not image_url.startswith("http"):
                    img = await self._image(session, prompt, False, 1280, 704, emit)
                    image_url = img.get("image_url") or img.get("result")
                    cost += float(img.get("cost", 0) or 0)
                payload = {
                    "prompt": prompt,
                    "image": image_url,
                    "num_inference_steps": 30,
                    "guidance": 5,
                    "size": "1280*720",
                    "duration": min(5, self.valves.MAX_VIDEO_SECONDS),
                    "flow_shift": 5,
                    "seed": -1,
                    "enable_prompt_optimization": False,
                    "enable_safety_checker": True,
                }
                out = await self._run(session, self.valves.VIDEO_MODEL, payload, emit, "Making the video (1–3 min)", 840)
                cost += float(out.get("cost", 0) or 0)
                video = out.get("result") or out.get("video_url")
                info = await self._save(session, video, "video/mp4", __request__, __user__, __chat_id__, __message_id__)
            await self._attach(__event_emitter__, __chat_id__, __message_id__, [{"type": "file", **info, "name": "video.mp4"}])
        except Exception as e:
            await emit("Video failed", True)
            return f"Video generation failed: {e}"
        await emit(f"Video ready (cost ${cost:.2f})", True)
        # The embed iframe starts 150px tall; report the real height so the whole player shows
        player = (
            f'<body style="margin:0"><video id="v" src="{video}" controls playsinline '
            'style="display:block;width:100%;max-width:720px;aspect-ratio:16/9;border-radius:12px;background:#000"></video>'
            "<script>const s=()=>parent.postMessage({type:'iframe:height',height:Math.ceil(v.getBoundingClientRect().height)+8},'*');"
            "v.addEventListener('loadedmetadata',s);addEventListener('resize',s);s();</script></body>"
        )
        return (
            HTMLResponse(content=player, headers={"Content-Disposition": "inline"}),
            "The video is playing in the chat and is saved as a file below the answer. Do not include any link. "
            "Briefly say it is ready, in the user's language.",
        )
