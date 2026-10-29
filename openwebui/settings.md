# Open WebUI settings (v0.12.4)

These are set in the admin panel, not in files. They're recorded here so they can be rebuilt.

## Connections (Admin → Settings → Connections → OpenAI)
| Base URL | Model |
|---|---|
| `https://api.runpod.ai/v2/c3lm36gdhpctl2/openai/v1` | `family-brain` (Qwen) |
| `https://api.runpod.ai/v2/936leprwfzb9gr/openai/v1` | `family-gemma` (Gemma) |

Both connections use the owner's RunPod API key, which is entered in the UI and never stored here.

## Models (Workspace → Models)
- **Family AI** (`family-gemma`): the public default. It has a family-assistant system prompt that answers in the user's language, Function Calling set to Native, and the `family_media` tool.
- **Family AI Pro** (`family-brain`): public, with the same prompt, function calling and tool.

## Features
- Web search: DDGS (DuckDuckGo), with `WEB_FETCH_MAX_CONTENT_LENGTH=4000`.
- Code execution and code interpreter: Pyodide.
- Memory: on.
- Documents/RAG: embedding model `intfloat/multilingual-e5-small`, which covers Swedish, Finnish and English.
- Users: sign-up off, default role `pending`.

## Audio (Admin → Settings → Audio)
- STT engine: OpenAI-compatible, `https://b8yk3ju5yc5kqx.api.runpod.ai/v1`, model `Systran/faster-whisper-large-v3`.
- TTS engine: OpenAI-compatible, same URL, model `speaches-ai/piper-*`. The voice endpoint picks the voice from the text's language: Finnish "harri", Swedish "nst", English "amy".

## Tools (Workspace → Tools)
- `family_media`: source in `tools/family_media.py`. The owner enters its valve `RUNPOD_API_KEY`.
