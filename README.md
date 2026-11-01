# Family AI

A private AI assistant for the family that speaks Swedish, Finnish and English. It runs on [RunPod](https://runpod.io) with [Open WebUI](https://openwebui.com) as the chat app. The GPUs start when someone uses the assistant and shut down when nobody does, so you mostly pay only for what you use.

> This repo holds the **setup, scripts and notes**. It holds no passwords or API keys: those live only in RunPod and Open WebUI.

## What is running

| Part | What it is | Where | Cost |
|---|---|---|---|
| Chat app | Open WebUI v0.12.4 on CPU pod `ix476koa61pd4o` | RunPod EUR-IS-1 (Iceland) | $0.08/h, always on |
| Storage | Network volume `vevppjlc9a` (10 GB) at `/app/backend/data` | EUR-IS-1 | $0.70/month |
| **Family AI** (default) | Gemma 4 31B FP8, serverless endpoint `936leprwfzb9gr`, model id `family-gemma` | EU-SE-1 / EUR-IS-2, A40 48 GB | $1.22/h while running |
| **Family AI Pro** | Qwen3.8 27B FP8, serverless endpoint `c3lm36gdhpctl2`, model id `family-brain` | EU-SE-1 / EUR-IS-2 | $1.22/h while running |
| **Family AI Fast** (testing; not connected to UI) | Qwen3.5-9B, serverless endpoint `52cjk52hgbwag1`, model id `family-fast` | EU-SE-1 / EUR-IS-2, 24GB GPU class | Listed $0.75/h while running |
| Voice | Speaches (Whisper STT + Piper TTS), load balancer endpoint `b8yk3ju5yc5kqx` | EU data centers | $0.58–0.69/h while running |
| Pictures / video | RunPod public endpoints: FLUX schnell/dev, Wan 2.2 I2V | RunPod | $0.003 per quick image, about $0.02 per high-quality image, $0.30 per 5 s video |

URL: `https://ix476koa61pd4o-8080.proxy.runpod.net` (sign-up off; new users are "pending" until the admin approves them).

Both LLM endpoints scale to zero and stay warm for 10 min after the last message. A cold start takes about 2–4 min.

## Prepared next step: smaller GPU + automatic routing

The first implementation is in `openwebui/functions/family_router.py`.
It adds Auto, Pro and Finnish/Swedish model choices to the existing Open WebUI.
Fast appears only after a tested small GPU endpoint is configured. It uses queued
Runpod requests to wait through cold starts and preserves native tool-call streams.

**Router not installed in the live UI.** The owner approved the new Fast endpoint
on 2026-11-01, and it has been created as `52cjk52hgbwag1`. Its deployed configuration
is in `runpod/fast-endpoint.json`: one 24GB GPU, min=0/max=1, 60-second idle timeout,
currently listed at $0.75 per billed hour plus storage/tax. Initial live smoke checks
completed: Swedish/Finnish short answers and streamed function-call arguments.
First queue/start delay was 212.7s; short warm jobs took 2.1–2.5s. These are
individual measurements, not latency guarantees or a language-quality benchmark.
The `.proposed.json` file is the original proposal; do not use it to create a duplicate.
See [rollout and verification](docs/router-rollout.md) before installing the router.

CPU cost: the current $0.08/hour is $57.60 per 30-day month before storage/tax.
See [the CPU savings and migration plan](docs/cpu-cost-plan.md) for reusing an
existing VPS or moving to a cheaper small CPU host. No CPU migration has occurred.

## Repo layout

```
runpod/            Endpoint settings (env, GPUs, scaling) for each serverless endpoint
openwebui/         Open WebUI settings and the custom tools uploaded to it
  functions/family_router.py   Proposed routing Pipe (not installed)
  tools/family_media.py   Image + video tool (FLUX / Wan 2.2)
voice/voice_start.py      Start command for the voice endpoint (adds /ping and per-language voice choice)
docs/history.md    What was done, when, and why (decisions + problems solved)
docs/research/     Model research (October 2026)
tests/             Local router/transport checks (no billed inference)
AGENTS.md          Rules for AI assistants working on this project
```

## Languages

Finnish quality is the weak spot. Gemma 4 writes clearly better Finnish than Qwen: EuroEval scores 57.5 vs 49.3 for Finnish and 71.4 vs 67.0 for Swedish. That's why Gemma is the default.

