"""Experimental queue adapter for the pinned llama.cpp Hub image; no secrets."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.error
import urllib.request

PROFILES = {
    "q8": ("ggml-org/gemma-4-31B-it-GGUF", "3d47a7e680fb9526dcac74335858f0f31acc9c27",
           "gemma-4-31B-it-Q8_0.gguf", "mmproj-gemma-4-31B-it-Q8_0.gguf"),
    "qat-q4": ("google/gemma-4-31B-it-qat-q4_0-gguf", "59dde24573e7e61570dba08b18a2e1fe246955ed",
               "gemma-4-31B_q4_0-it.gguf", "gemma-4-31B-it-mmproj.gguf"),
}
PROFILE = os.environ.get("FAMILY_GGUF_PROFILE", "q8")
REPO, REVISION, MODEL, PROJECTOR = PROFILES[PROFILE]
BASE = "http://127.0.0.1:3098"
ROUTES = {"/v1/models", "/v1/chat/completions", "/v1/completions"}


def model_args(cache=Path("/runpod-volume/huggingface-cache/hub")):
    # HF preserves case; the Hub's RunPod cache resolver also accepts lowercase.
    # Never choose an arbitrary snapshot or silently download during paid startup.
    name = "models--" + REPO.replace("/", "--")
    for folder in dict.fromkeys((name, name.lower())):
        snapshot = cache / folder / "snapshots" / REVISION
        if (snapshot / MODEL).is_file() and (snapshot / PROJECTOR).is_file():
            return ["-m", str(snapshot / MODEL), "--mmproj", str(snapshot / PROJECTOR)], True
    raise FileNotFoundError("Pinned cached model and projector are not available")


def model_ready():
    with urllib.request.urlopen(BASE + "/health", timeout=2) as response:
        if response.status != 200:
            return False
    with urllib.request.urlopen(BASE + "/v1/models", timeout=2) as response:
        models = json.load(response)
    return any(model.get("id") == "family-gemma" for model in models.get("data", []))


def request_input(job):
    value = job["input"]
    route = value.get("openai_route", "/v1/chat/completions")
    if route not in ROUTES:
        raise ValueError("Unsupported OpenAI route")
    payload = dict(value.get("openai_input", value))
    payload.setdefault("model", "family-gemma")
    images = 0
    for message in payload.get("messages", []):
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if part.get("type") == "image_url":
                    images += 1
                elif part.get("type") in {"input_audio", "input_video", "video_url"}:
                    raise ValueError("Only text and images are enabled")
    if images > 4:
        raise ValueError("At most four images per request")
    return route, payload


async def handler(job):
    import aiohttp
    route, payload = request_input(job)
    timeout = aiohttp.ClientTimeout(total=590)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        method = "GET" if route == "/v1/models" else "POST"
        async with session.request(method, BASE + route,
                                   json=payload if method == "POST" else None) as response:
            if response.status != 200:
                # Do not copy request content or local filesystem details into logs.
                raise RuntimeError("Local inference HTTP " + str(response.status))
            if not payload.get("stream"):
                yield await response.json()
                return
            # aiohttp's stream iterator yields complete lines, including split TCP chunks.
            async for line in response.content:
                if line.startswith(b"data:"):
                    yield line.decode("utf-8").rstrip("\r\n") + "\n\n"


def main():
    started = time.monotonic()
    # Cache mounts can settle after the container starts. Bound that wait and
    # fail closed instead of accidentally starting llama.cpp in empty router mode.
    while True:
        try:
            args, cached = model_args()
            break
        except FileNotFoundError:
            if time.monotonic() - started >= 60:
                root = Path("/runpod-volume/huggingface-cache/hub")
                names = {"models--" + REPO.replace("/", "--"),
                         "models--" + REPO.replace("/", "--").lower()}
                snapshots = {name: sorted(p.name for p in (root / name / "snapshots").glob("*"))
                             for name in sorted(names)}
                print(json.dumps({"event": "family_cache_missing", "snapshots": snapshots}), flush=True)
                raise
            time.sleep(1)
    print(json.dumps({"event": "family_engine_start", "engine": "llama.cpp",
                      "revision": REVISION, "cached_model_and_projector": cached}), flush=True)
    command = ["/app/llama-server", *args, "--host", "127.0.0.1", "--port", "3098",
               "--alias", "family-gemma", "--ctx-size", "8192", "--parallel", "1",
               "--n-gpu-layers", "999", "--jinja", "--flash-attn", "on",
               "--batch-size", "2048", "--ubatch-size", "2048" if PROFILE == "q8" else "512"]
    env = dict(os.environ, LD_LIBRARY_PATH="/app:" + os.environ.get("LD_LIBRARY_PATH", ""))
    server = subprocess.Popen(command, env=env)
    def stop(signum, frame):
        server.terminate()
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while time.monotonic() - started < 590:
            if server.poll() is not None:
                raise RuntimeError("llama-server exited: " + str(server.returncode))
            try:
                if model_ready():
                    break
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(.25)
        else:
            raise RuntimeError("llama-server startup deadline")
        print(json.dumps({"event": "family_engine_ready", "seconds": round(time.monotonic()-started, 3),
                          "cached_model_and_projector": cached}), flush=True)
        import runpod
        runpod.serverless.start({"handler": handler, "concurrency_modifier": lambda _: 1,
                                 "return_aggregate_stream": True})
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


if __name__ == "__main__":
    main()
