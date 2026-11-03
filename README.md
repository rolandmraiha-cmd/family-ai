# Family AI

Private chat in Finnish, Swedish and English, using Open WebUI and on-demand RunPod GPUs.

## Current deployment (checked 2026-11-03)

| Part | Model / resource | State |
| --- | --- | --- |
| Chat app | Existing CPU pod `ix476koa61pd4o`, Open WebUI; data volume `vevppjlc9a` | Running; live UI currently requires admin sign-in |
| Lightweight coordinator | Google Gemma 4 E2B IT, endpoint `52cjk52hgbwag1`, served as `family-fast` | **Updated and response-tested on RunPod** |
| Larger reasoning | Qwen3.8 27B FP8, `c3lm36gdhpctl2`, `family-brain` | Existing endpoint; shared reasoning tool targets this initially |
| Larger vision / language | Gemma 4 31B FP8, `936leprwfzb9gr`, `family-gemma` | Existing endpoint retained |
| Speech | Whisper large-v3 + Finnish/Swedish/English Piper voices, `b8yk3ju5yc5kqx` | Existing endpoint; manual voice-start action prepared |
| Image generation | FLUX schnell/dev public endpoints | Existing tools retained |
| Video generation | Wan 2.2 I2V public endpoint | Existing tool retained; can create a starting image first |
| Optional DeepSeek specialist | DeepSeek-R1-Distill-Qwen-14B, proposed 48GB GPU | **Not created: price approval and live validation pending** |

All four owned GPU endpoints have zero minimum / one maximum worker.
Fast uses FlashBoot, an 8K context, text-only mode and eager execution to skip
multimodal warmup, compilation and CUDA graph capture. Image attachments route
to larger Gemma. Fast's first measured request queued for **182.287s**, then
executed in 5.416s. This is not instant startup or a latency guarantee.

## Shared routing and voice

The reviewed implementation is in `openwebui/functions/family_router.py`.
**Installed and enabled in live Open WebUI.** The private workspace model is
`family-auto` (Family AI Auto), with native tool calling and `family_media`
attached. Start voice is enabled globally as a manual action. Existing direct
models and the existing default remain available. No credential was changed.

- Auto uses the small coordinator for everyday requests.
- Explicit hard requests emit a native `ask_deep_reasoning` call directly,
  without first starting the small GPU. The real Gemma test ignored a forced
  named tool, so deterministic dispatch lives in the router.
- The model can also call the reasoning tool when a rule misses a difficult task.
- Images and videos use the attached shared tools. Media generation and image
  understanding use different paths.
- STT text goes to the same selected Auto model and tools as typed text.
  Open WebUI sends the final reply to Piper when the user enables voice playback.
- The Start voice action manually wakes the speech endpoint. It does not change
  worker minimums, keep it alive, or run during ordinary typed chat.

The module transport submits once, polls through cold starts, bounds duration and
output, and requests cancellation on timeout/disconnect. These are per-instance
limits, not an account spending cap. Existing direct models stay available.

## Review / activation

See [deployment and acceptance checklist](docs/shared-modules-rollout.md).
The router, updated `family_media` tool and manual voice action are installed.
The new components reuse the admin-owned RunPod key through Open WebUI’s
encrypted tool-valve API, inside the app process. No key was copied into code or
chat. Live Auto chat showed queue progress; the view then stopped updating.
A browser URL-policy rejection blocked reloading it to confirm the saved answer.
Full UI/tool-loop/audio acceptance therefore remains incomplete; keep Auto in
review rather than replacing the existing public default.

The optional DeepSeek profile is ready in
`runpod/deepseek-endpoint.proposed.json`. The checked AMPERE_48 rate is
**$1.22 per active GPU hour**, including startup/idle time, before tax and any
storage charges. It has no always-on worker. Do not create it before the owner
approves this additional endpoint. Qwen is the usable larger-model target until
then; no DeepSeek or Kimi deployment is claimed.

Fast stays in its existing $0.75/hour pool; no new GPU resource, storage volume,
CPU host or cloud computer was created. The current CPU app remains $0.08/hour
and its 10GB volume is listed at $0.70/month.

## Verification and limits

`python -m unittest discover -s tests -v` runs the router/module/action checks
without billed inference. GitHub Actions also runs these checks.
The tests use local HTTP servers and replace Open WebUI storage/HTML boundaries;
they do not establish real browser audio or file persistence.

Live E2B tests: Finnish image request selected `generate_image` correctly
(1.055s warm execution); a Swedish RAM/storage answer was coherent.
A Finnish heat-pump answer incorrectly mentioned rotational motion. A forced
reasoning-tool test produced text instead. Keep larger Gemma available and review
small-model factual/Finnish quality before making Auto the public default.

No CPU migration or cloud-computer work is included.

## Layout

- `runpod/`: deployed endpoint snapshots, rollback and explicitly proposed profiles.
- `openwebui/functions/`: shared Auto/Fast/Pro/language routing.
- `openwebui/tools/family_media.py`: reasoning, image and video modules.
- `openwebui/actions/start_voice.py`: manual speech startup.
- `voice/voice_start.py`: existing speech service and per-language voice selection.
- `tests/`: routing, transport, module and manual voice checks.
- `docs/`: rollout, history and previous research.


