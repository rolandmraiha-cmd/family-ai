import json
import re

import uvicorn
from speaches.main import create_app

app = create_app()
app.add_api_route("/ping", lambda: {"status": "ok"}, methods=["GET"])
MAX_SPEECH_BYTES = 65536
MAX_SPEECH_CHARS = 2000

VOICES = {
    "fi": ("speaches-ai/piper-fi_FI-harri-medium", "harri"),
    "sv": ("speaches-ai/piper-sv_SE-nst-medium", "nst"),
    "en": ("speaches-ai/piper-en_US-amy-medium", "amy"),
}
WORDS = {
    "fi": set("ja on ei olen olet minä sinä hän me te he että mutta kun jos mitä miten miksi kiitos hei moi tämä se oli ovat voin voit kanssa myös vain tänään huomenna kyllä".split()),
    "sv": set("och är jag du det inte att en ett som på med för har var hej tack vad hur varför kan vill ska till av den de vi ni idag imorgon ja blir om så men eller också när bara mycket".split()),
    "en": set("the and is are you it to of a in that this what how why can will hello thanks with for today tomorrow yes".split()),
}


def detect(text: str) -> str:
    t = text.lower()
    words = re.findall(r"[a-zåäö]+", t)
    score = {k: sum(w in v for w in words) for k, v in WORDS.items()}
    score["sv"] += 2 * t.count("å")
    score["fi"] += 0.5 * len(re.findall(r"(aa|ää|ii|uu|yy|öö|ee|oo)", t))
    best = max(score, key=score.get)
    return best if score[best] > 0 else "sv"


class PickVoice:
    """Rewrites Piper TTS requests so the voice matches the language of the text."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] != "/v1/audio/speech" or scope["method"] != "POST":
            return await self.inner(scope, receive, send)
        body, more = b"", True
        while more:
            msg = await receive()
            if msg.get("type") == "http.disconnect":
                return
            body += msg.get("body", b"")
            if len(body) > MAX_SPEECH_BYTES:
                return await self.error(send, 413, "Speech request is too large")
            more = msg.get("more_body", False)
        try:
            data = json.loads(body)
            if not isinstance(data, dict) or not isinstance(data.get("input"), str):
                return await self.error(send, 400, "Speech input must be text")
            if not data["input"].strip() or len(data["input"]) > MAX_SPEECH_CHARS:
                return await self.error(send, 400, "Speech text must contain 1–2000 characters")
            language = data.pop("language", None)
            if language is not None and (not isinstance(language, str) or language not in VOICES):
                return await self.error(send, 400, "Supported speech languages are fi, sv and en")
            if "piper" in str(data.get("model", "")):
                data["model"], data["voice"] = VOICES[language or detect(data["input"])]
                body = json.dumps(data).encode()
        except (ValueError, UnicodeDecodeError):
            return await self.error(send, 400, "Speech request must be valid JSON")
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        headers = [(k, v) for k, v in scope["headers"] if k != b"content-length"]
        headers.append((b"content-length", str(len(body)).encode()))
        return await self.inner({**scope, "headers": headers}, replay, send)

    @staticmethod
    async def error(send, status, detail):
        encoded = json.dumps({"error": detail}).encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(encoded)).encode())]})
        await send({"type": "http.response.body", "body": encoded})


if __name__ == "__main__":
    uvicorn.run(PickVoice(app), host="0.0.0.0", port=8000)

