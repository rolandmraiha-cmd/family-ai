"""Manual, governed speech for the Contabo preview; native audio stays unchanged."""
import asyncio
import hashlib
import io
import json
import wave

from family_backend.control import (
    ControlError, Operation, OperationContext, default_ledger,
    operation_context, configured_runpod_key,
)

SPEECH_BASE = "https://b8yk3ju5yc5kqx.api.runpod.ai/v1"
SPEECH_VOICES = {
    "fi": ("speaches-ai/piper-fi_FI-harri-medium", "harri"),
    "sv": ("speaches-ai/piper-sv_SE-nst-medium", "nst"),
    "en": ("speaches-ai/piper-en_US-amy-medium", "amy"),
}
MAX_RECORDING_BYTES = 6 * 1024 * 1024


def validate_recording(data):
    if not data or len(data) > MAX_RECORDING_BYTES:
        raise ControlError("invalid_audio", "Recording must be a WAV file of at most 30 seconds.")
    try:
        with wave.open(io.BytesIO(data)) as audio:
            if (audio.getcomptype() != "NONE" or audio.getsampwidth() != 2
                    or audio.getnchannels() not in {1, 2}
                    or not 8000 <= audio.getframerate() <= 48000
                    or not 0 < audio.getnframes() / audio.getframerate() <= 30):
                raise ValueError()
            expected = audio.getnframes() * audio.getnchannels() * audio.getsampwidth()
            if len(audio.readframes(audio.getnframes())) != expected:
                raise ValueError()
    except (wave.Error, EOFError, ValueError, ZeroDivisionError):
        raise ControlError("invalid_audio", "Use a complete 16-bit WAV recording, at most 30 seconds.") from None


class SpeechService:
    def __init__(self, provider, save_audio):
        self.provider = provider
        self.save_audio = save_audio

    async def run(self, owner, conversation, turn, kind, language, value):
        if language not in SPEECH_VOICES or kind not in {"speech", "transcriptions"}:
            raise ControlError("invalid_speech", "Choose Finnish, Swedish or English.")
        if kind == "speech":
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 2000:
                raise ControlError("invalid_speech", "Speech text must contain 1–2000 characters.")
            fingerprint = hashlib.sha256(value.encode()).hexdigest()
        else:
            validate_recording(value)
            fingerprint = hashlib.sha256(value).hexdigest()
        ledger = default_ledger()
        intent = ledger.voice(owner)
        if intent["state"] == "off" or intent["conversation"] != conversation:
            raise ControlError("voice_off", "Press Start voice in this conversation first.")
        context = OperationContext(owner, conversation, turn)
        with operation_context(context):
            operation = Operation("b8yk3ju5yc5kqx", {
                "operation": kind, "language": language, "input_hash": fingerprint,
            }, timeout=180)
            replay = operation.replay()
            if replay is not None:
                return replay
            try:
                operation.submitting()
                result = await self.provider(kind, language, value)
                # A storage failure leaves an uncertain job and its reservation;
                # never automatically repeat an already-billed speech request.
                if kind == "speech":
                    operation.event("job.progress", {"phase": "saving_audio"})
                    saved = await self.save_audio(result, conversation, turn)
                    result = {"file": saved, "language": language}
                elif not isinstance(result, dict) or not isinstance(result.get("text"), str):
                    raise ControlError("invalid_provider_output", "Transcription returned no text.")
                else:
                    result = {"text": result["text"], "language": language}
                output = {**result, "job_id": operation.id}
                operation.complete(output)
                ledger.mark_voice_ready(owner)
                return output
            finally:
                operation.unresolved()


def install_speech_api(app, router, origin_checker):
    from fastapi import Depends, HTTPException, Request
    from fastapi.responses import JSONResponse
    from open_webui.utils.auth import get_verified_user

    async def speech_route(request: Request, user=Depends(get_verified_user)):
        if not app.state.family_control_api_active:
            raise HTTPException(503, "Family backend is disabled")
        if user.role not in {"user", "admin"}:
            raise HTTPException(403, "A verified family account is required")
        try:
            origin_checker(dict(request.headers), True)
            conversation = request.query_params.get("chat_id", "")
            turn = request.query_params.get("turn", "")
            if not conversation or not turn or len(conversation) > 256 or len(turn) > 256:
                raise ControlError("missing_turn", "A saved conversation and stable operation ID are required.")
            from open_webui.models.chats import Chats
            if not await Chats.get_chat_by_id_and_user_id(conversation, user.id):
                raise ControlError("not_found", "Conversation not found.")
            kind = request.url.path.rsplit("/", 1)[-1]
            if kind == "session":
                return {**default_ledger().voice(user.id, conversation, activate=True), "wakes_voice": False}
            from open_webui.models.config import Config
            from open_webui.utils.access_control import has_permission
            permission = "chat.tts" if kind == "speech" else "chat.stt"
            if user.role != "admin" and not await has_permission(user.id, permission, await Config.get("user.permissions")):
                raise HTTPException(403, "Speech permission is required")
            language = request.query_params.get("language", "fi")
            limit = 65536 if kind == "speech" else MAX_RECORDING_BYTES
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > limit:
                    raise HTTPException(413, "Speech input is too large")
            value = bytes(data)
            if kind == "speech":
                try:
                    body = json.loads(value)
                    value = body.get("input") if isinstance(body, dict) else None
                except (ValueError, UnicodeDecodeError):
                    raise ControlError("invalid_speech", "Speech input must be JSON text.") from None

            key = await configured_runpod_key()
            if not key:
                raise ControlError("provider_unavailable", "Configure an existing RunPod connection in Open WebUI.")

            async def provider(kind, language, value):
                import aiohttp
                payload = {}
                if kind == "speech":
                    model, voice = SPEECH_VOICES[language]
                    payload["json"] = {"input": value, "model": model, "voice": voice,
                                       "language": language, "response_format": "wav"}
                else:
                    form = aiohttp.FormData()
                    form.add_field("file", value, filename="recording.wav", content_type="audio/wav")
                    form.add_field("model", "Systran/faster-whisper-large-v3")
                    form.add_field("language", language)
                    payload["data"] = form
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180),
                            headers={"Authorization": f"Bearer {key}"}, trust_env=True) as session:
                        return await read_provider(session, payload, kind)
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    raise ControlError("speech_unconfirmed", "Speech did not confirm completion. Inspect the existing job before retrying.") from None

            async def read_provider(session, payload, kind):
                async with session.post(f"{SPEECH_BASE}/audio/{kind}", allow_redirects=False, **payload) as response:
                    if response.status != 200:
                        raise ControlError("speech_unconfirmed", "Speech failed or is still starting. Inspect the job before retrying.")
                    chunks, size = [], 0
                    async for chunk in response.content.iter_chunked(65536):
                        size += len(chunk)
                        if size > 16 * 1024 * 1024:
                            raise ControlError("speech_too_large", "Speech output exceeded its size limit.")
                        chunks.append(chunk)
                    result = b"".join(chunks)
                    if kind == "speech":
                        if not result.startswith(b"RIFF") or result[8:12] != b"WAVE":
                            raise ControlError("invalid_provider_output", "Speech did not return WAV audio.")
                        return result
                    return json.loads(result)

            async def save_audio(data, conversation, turn):
                from starlette.datastructures import UploadFile, Headers
                from open_webui.routers.files import upload_file_handler
                file = UploadFile(io.BytesIO(data), filename="Speech.wav", size=len(data),
                                  headers=Headers({"content-type": "audio/wav"}))
                saved = await upload_file_handler(request, file=file, user=user,
                    metadata={"chat_id": conversation}, process=False, process_in_background=False,
                    background_tasks=None, db=None)
                file_id = saved["id"] if isinstance(saved, dict) else saved.id
                info = {"id": file_id, "type": "audio", "name": "Speech.wav",
                        "url": f"/api/v1/files/{file_id}/content", "content_type": "audio/wav"}
                message = await Chats.get_message_by_id_and_message_id(conversation, turn)
                if message and message.get("role") == "assistant":
                    await Chats.add_message_files_by_id_and_message_id(conversation, turn, [info])
                return info

            service = SpeechService(provider, save_audio)
            operation = asyncio.create_task(service.run(user.id, conversation, turn, kind, language, value))
            try:
                while not operation.done():
                    await asyncio.wait({operation}, timeout=0.5)
                    if await request.is_disconnected():
                        operation.cancel()
                        raise asyncio.CancelledError()
                return await operation
            finally:
                if not operation.done():
                    operation.cancel()
                await asyncio.gather(operation, return_exceptions=True)
        except ControlError as error:
            status = 404 if error.code == "not_found" else 403 if error.code.startswith("origin_") or error.code == "voice_off" else 400
            return JSONResponse({"error": {"code": error.code, "message": str(error)}}, status_code=status)
        except (ValueError, OSError, asyncio.TimeoutError):
            return JSONResponse({"error": {"code": "speech_unconfirmed", "message": "Speech did not confirm completion. Check the existing job before retrying."}}, status_code=502)

    speech_route.__annotations__["request"] = Request
    for suffix in ("session", "speech", "transcriptions"):
        router.add_api_route(f"/voice/{suffix}", speech_route, methods=["POST"])
