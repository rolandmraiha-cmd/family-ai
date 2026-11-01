# History

## 2026-11-01: Routing implementation prepared (not deployed)
- Reused the existing Family AI repository and read the three live Runpod endpoint configurations.
- Added an Open WebUI routing Pipe with Auto/Pro/language choices and an optional Fast model.
- Queued job polling handles cold starts without one blocking OpenAI-proxy request; native SSE/tool calls are preserved.
- Added local HTTP transport tests, cancellation, bounded runtime/output and no automatic submission retries.
- Added an unapplied official Qwen3.5-9B/24GB GPU proposal and rollout checklist.
- No new paid endpoint, CPU migration, live UI installation or live language test was performed.

## 2026-10-26 to 10-27: Research and first setup
- Researched open models: see `docs/research/`.
- Chose "everything on RunPod":
  - The Open WebUI CPU pod and its 10 GB volume are in EUR-IS-1, because EU-SE-1 has no network volumes.
  - Qwen3.8 27B FP8 runs as a serverless vLLM endpoint.
- Qwen settings:
  - `MAX_MODEL_LEN` was cut to 16384 after running out of memory at 32k.
  - `MAX_NUM_SEQS=16` is required: at 256 the worker crash-loops on the Mamba cache.
- Open WebUI features turned on: web search, code interpreter, memory, multilingual embedding and the system prompt.
- Fixed empty web-search answers by switching the tool parser `hermes` → `qwen3_coder`.

## 2026-10-28: Gemma added
- In the Finnish test, Qwen made 2–5 errors per answer. Gemma 4 31B wrote natural Finnish with about one slip per long answer.
- Added Gemma as the default "Family AI". Qwen stays as "Family AI Pro".
- Gemma runs out of memory at 16k on the A40, so it runs at 8k context, and fetched web pages are capped at 4000 characters.

## 2026-10-29: Voice, pictures, video and a faster start
- Both LLMs now stay warm for 10 min after the last message (was 2 min).
- Voice endpoint: Speaches with Whisper large-v3 and Piper voices.
  - Added a `/ping` route, because RunPod's load balancer polls it.
  - Added per-language voice choice (`voice/voice_start.py`).
  - Warm speed: TTS about 0.3 s, STT about 3 s.
- `family_media` tool for FLUX images and Wan 2.2 video.
  - v1.1 saves results into Open WebUI storage, because RunPod's links expire after 7 days.
  - Verified: an image took 30 s and cost $0.003; a 5 s video took 3.5 min and cost $0.30.
- Faster Gemma start, at no extra cost:
  - Turned off video/audio warmup and torch.compile (`LIMIT_MM_PER_PROMPT`, `COMPILATION_CONFIG`).
  - Container start → ready went from 218 s to 134 s.
  - Warm generation is about 6% slower.
- Found that the extra "initializing" workers are not billed.

## 2026-10-29 (evening): Qwen faster start and price research
- Applied the same settings to Qwen. Container start → ready went from 228 s to 202 s; reply speed is unchanged (500 tokens in 26 s), and tool calls work.
  - The gain is smaller than Gemma's: about 80 s now goes to profiling and warming Qwen's GDN/Mamba Triton kernels, which are rebuilt on every cold start.
- Decided against network storage: it would cost about $5/month for about 0 s gained (loading from it is about as slow as downloading), and EU-SE-1 doesn't support it.
- Research on cheaper hosting: `docs/research/cheaper-hosting-2026-10.md`. The always-on Open WebUI pod (about $58/month) is the biggest cost.

## Open items
- Backups: a free sync of the volume to the owner's PC through RunPod's S3 API (EUR-IS-1). It needs an S3 key that the owner creates.
- Family accounts.
- Decide on cheaper hosting (see `docs/research/cheaper-hosting-2026-10.md`).
- A better Finnish voice.

