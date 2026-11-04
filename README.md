# Family AI

A private AI assistant for the family that speaks Swedish, Finnish and English. The AI runs on [RunPod](https://runpod.io) GPUs; the chat app ([Open WebUI](https://openwebui.com)) runs on the owner's Contabo VPS (see `docs/vps.md`). The GPUs start when someone uses the assistant and shut down when nobody does, so you mostly pay only for what you use.

> This repo holds the **setup, scripts and notes**. It holds no passwords or API keys: those live only in RunPod and Open WebUI.

## What is running

| Part | What it is | Where | Cost |
|---|---|---|---|
| Chat app | Open WebUI v0.12.4 + Caddy in Docker, `/opt/family-ai` | Contabo VPS 37.60.226.214 | €6.90/month, always on |
| Old storage | Network volume `vevppjlc9a` (10 GB), old chats, not used since the move | RunPod EUR-IS-1 | $0.70/month |
| **Family AI Fast** | Gemma 4 E2B, serverless endpoint `52cjk52hgbwag1`, model id `family-fast` | 24 GB GPU | about $0.75/h while running |
| **Family AI** (default) | Gemma 4 31B FP8, serverless endpoint `936leprwfzb9gr`, model id `family-gemma` | Nine European locations, compatible 48 GB GPUs | A40 $1.22/h while running |
| **Family AI Pro** | Qwen3.8 27B FP8, serverless endpoint `c3lm36gdhpctl2`, model id `family-brain` | EU-SE-1 / EUR-IS-2 | $1.22/h while running |
| Voice | Speaches (Whisper STT + Piper TTS), load balancer endpoint `b8yk3ju5yc5kqx` | EU data centers | $0.58–0.69/h while running |
| Pictures / video | RunPod public endpoints: FLUX schnell/dev, Wan 2.2 I2V | RunPod | $0.003 per quick image, about $0.02 per high-quality image, $0.30 per 5 s video |

URL: `https://37-60-226-214.sslip.io` (sign-up off; new users are "pending" until the admin approves them).

The integrated UI is in review at [`/preview/`](https://37-60-226-214.sslip.io/preview/).
It uses existing Open WebUI accounts, saved conversations and server-side tools.
The router, job/budget ledger and guarded manual speech API are installed on the
VPS; live acceptance results and remaining device/model issues are recorded in
the integration notes. Follow-up tests passed image understanding and verified
five-second saved video, but E2B still fails Finnish/Swedish quality. See the
[follow-up report](docs/acceptance-followup-20261104.md). The public
default and native `/` interface remain unchanged. See
[integration status and rollback](docs/contabo-integration.md). PR #2 stays draft.

Idle shutdown is configured at 60 seconds for Fast/voice and two minutes for
Qwen/the larger Gemma. Shorter idle waits reduce paid waiting but can cause more
cold starts. Available GPU capacity can add several minutes. Fast's earlier
shutdown needed a manual worker recycle; natural shutdown is not yet proven.

The larger Gemma now uses eager mode to reduce startup work. Two fresh-worker
probes observed startup wait falling from 131s to 114s, with slower generation
in the second probe. FlashBoot is already enabled; under 20s after a retained
worker resumes is not a guarantee for a fresh boot. See the
[startup measurements and tradeoff](docs/startup-20261104.md).

The larger Gemma's locations have been widened from Sweden/Iceland to nine
European data centers. Available compatible GPUs can still be concentrated in
Sweden; a wider location list does not guarantee a free GPU. The separate
[llama.cpp trial](docs/startup-llamacpp-20261105.md) records model staging,
adapter failures, accounting and the acceptance requirements for an engine swap.

The preview distinguishes provider-reported job costs from **budget held as an
estimate**. Unknown compute costs stay covered by the admission limit; the
display is not your RunPod wallet or a finalized account bill. Historical test
estimates have not been reset. See the [cost correction](docs/cost-accounting-20261104.md).

## Repo layout

```
runpod/            Endpoint settings (env, GPUs, scaling) for each serverless endpoint
openwebui/         Open WebUI settings and the custom tools uploaded to it
  tools/family_media.py   Image + video tool (FLUX / Wan 2.2)
voice/voice_start.py      Start command for the voice endpoint (adds /ping and per-language voice choice)
family_backend/    Persistent jobs, budgets, authenticated controls and guarded speech
web/              Real preview UI source (index.html, app.mjs, api.mjs)
scripts/          Build isolated Open WebUI plugin imports and install reviewed IDs
vps/               Copies of the VPS docker-compose.yml and Caddyfile (no secrets)
docs/vps.md        The VPS: what runs, security, commands, what's next
docs/history.md    What was done, when, and why (decisions + problems solved)
docs/research/     Model research (October 2026)
AGENTS.md          Rules for AI assistants working on this project
```

## Languages

Finnish quality is the weak spot. Gemma 4 writes clearly better Finnish than Qwen: EuroEval scores 57.5 vs 49.3 for Finnish and 71.4 vs 67.0 for Swedish. That's why Gemma is the default.
