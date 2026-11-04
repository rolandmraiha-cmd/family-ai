# Contabo integration — 2026-11-04 review deployment

**Follow-up:** the owner approved another USD 5 (USD 12 cumulative). See
[follow-up acceptance](acceptance-followup-20261104.md) for the successful new
vision probe, enforced saved-video duration and continuing E2B language failures.
The observations and USD 5.361336 accounting below describe the earlier phase.

The existing VPS runs Open WebUI v0.12.4 and Caddy in `/opt/family-ai`.
`/preview/` now serves the real review UI; `/` remains native Open WebUI. PR #2
stays draft. The initial installation made no inference request. Subsequent live
acceptance uses the owner's USD 7 allowance below. No new paid resource,
SSH/firewall change or data deletion was made. Live acceptance subsequently
deployed the reviewed speech command and adjusted the existing Fast template;
details below. No new endpoint, volume or recurring resource was created.

## Implemented and installed

- Existing Open WebUI identity, owned saved chats, background completions and
  native server-side tools; browser polls saved chat state and never rewrites
  complete history or automatically retries a lost completion submission.
- Auto/Fast/Pro/language choices, shared reasoning/media tools, persistent jobs,
  progress, cancel requests, result recovery and estimated household admission
  limits: $2/day, $20/month, two concurrent operations, five-second video.
- Manual guarded Whisper/Piper routes with short-lived chat-bound intent,
  bounded WAV/text input, per-operation reservations and saved owned audio.
  Native audio and direct models still bypass these controls.
- Four reviewed plugin IDs: `family_router`, `family_start_voice`,
  `family_runtime`, `family_media`; private review model `family-auto`. The Action
  is scoped rather than enabled globally. Existing public default/config remains.
- Existing RunPod connection credentials are reused only in server memory. No
  new credential, browser token store or copied key valve was created.

Native startup installs added APIs before the existing SPA fallback mount. Live
checks caught HTML/405 fallthrough and, after authentication, an unresolved
`Request` annotation inherited through native plugin `exec()`. Both are fixed;
regression tests exercise the SPA mount and native postponed-annotation loading.

## Evidence and boundaries

| Check | Result |
|---|---|
| Local Python 3.12 suite | 97 tests pass, including native plugin loading, admission/recovery, speech bounds/replay and ownership/origin |
| Node 24 browser-helper suite | 7 tests pass: stable turns/history, vision input, owned file URLs, final-answer filtering, cycles and bounded PCM |
| Existing Linux app container | All 97 Python tests pass without installing dependencies |
| Live native health | `/health` returns 200 JSON |
| Live added routes without login | GET capabilities and POST manual voice session return 401 JSON |
| Native authenticated control API | Capabilities, policy and usage return 200 using a short-lived session held only in server memory through authorized SSH; native verification remains enabled |
| Actual phone-sized preview | Renders real signed-out gate; message input disabled; no inference submitted |
| Stored Open WebUI configuration | Same SHA-256 fingerprint before/after installation and restart |
| RunPod read-only check | All four existing endpoints min0/max1; per-worker lists showed zero RUNNING workers at 16:58 UTC after tests; idle/throttled entries remain and rollups can lag |
| Signed-in chat/tools/media/voice | Server/API acceptance observations below; real browser/device acceptance remains separate |

## Live acceptance observations

The real native background-chat API saved Finnish, Swedish and English turns in
one owned conversation. Each initially delegated a simple ice/water plus 17+25
question to Qwen and continued on Fast. Swedish and English final answers were
correct. Finnish had a correct final answer but also English pre-tool narration
in native aggregated `content`. The preview now reads public structured message
items after the last tool boundary, including for playback/history. A regression
case reproduces the native aggregate shape; this does not hide unmarked analysis
inside an actual final answer.

The coordinator/tool guidance now reserves Qwen for difficult multi-step tasks.
A fresh Finnish retest used Fast alone but still exposed analysis in its final
content. The existing vLLM template adds an empty thought channel for all Gemmas;
the [Google E2B template](https://huggingface.co/google/gemma-4-E2B-it/blob/main/chat_template.jinja)
and [Google's thinking guidance](https://ai.google.dev/gemma/docs/capabilities/thinking)
use a different non-thinking prefix for E2B. The existing Fast endpoint now uses
its native model template. Other environment values were retained, sending the
owner-documented `MAX_NUM_BATCHED_TOKENS=8192` explicitly instead of its redacted
API value. Workers were cycled and returned to min0/max1/60s. The post-change
three-language check completed with one Fast job per turn, no Qwen delegation
and no visible analysis. English was correct; Finnish used awkward wording
(“ottaa halutun tilan”), and Swedish mixed Finnish into its answer (“Is är
kiinteä aine…”). Routing/output separation improved, but Nordic-language quality
does **not** pass. One cold queued request took several minutes to obtain a
usable worker. Do not claim fast cold starts or production language acceptance.

The larger Gemma failed cold startup with `Cannot find any model weights` for
the configured RedHat FP8 model. Its queued synthetic vision job was cancelled
through the owned job API and native chat stop; the provider independently
reported `CANCELLED`. No replacement was submitted automatically. Its worker was
cycled with the original min0/max1/600s settings; no model/image/env was changed.
This is not a successful image-understanding test.

FLUX generated a red cabin beside a lake (visually inspected). Both its saved
1024×1024 JPEG and Wan's saved H.264 video reopened twice through authenticated
native file URLs with identical SHA-256 hashes. The video is 960×960, 161 frames,
**5.366667 seconds**, despite requesting five seconds. Generation/persistence
works, but the strict five-second output cap does not pass acceptance. Provider
request limits are not proof of actual output duration.

Guarded manual voice API tests completed for all three languages: activate intent,
Piper, save/attach the owned WAV, reopen it, replay the identical operation without
a second provider job, convert the test loopback to microphone-format PCM16, and
Whisper. Finnish returned “Hei, tämä on perheen puhetesti. Tänään kokeilemme kuvaa.”
English matched the supplied sentence; Swedish changed singular “taltest” to
“taltester”. This proves an API loopback, not microphone capture or human-rated
pronunciation/playback. Two malformed test fixtures were correctly rejected by
the 30-second STT guard; the Windows test script's encoding was repaired before
the successful run. Their two completed Piper jobs remain in the cost estimate.

During typed server/API chat checks no speech operation was submitted; speech
had no running worker at the read-only checks. Voice first started through the
explicit manual test. Browser network/device behavior remains unverified. Live
voice-off and cross-origin requests returned 403 without creating a speech job;
unsigned control/voice requests still returned 401 after deployment.

### Final test accounting and restored limits

The ledger recorded **28 jobs: 27 completed, one provider-confirmed cancellation,
zero active or unknown**. The cumulative conservative admission estimate is
**USD 5.361336**, including configured GPU idle tails and the two invalid-fixture
Piper jobs. FLUX/Wan returned $0.003/$0.30. This is an estimate, not a finalized
provider invoice; the billing feed had not yet published the test hour.

The daily allowance was restored to **$2**, monthly **$20**, concurrency **2**,
video admission **5 seconds**, one video per turn. Test usage stays in the ledger,
so governed preview requests will hit today's $2 cap until the period resets or
the owner adjusts it; existing native direct models remain available. Voice
intent is off. No test job is left pending and no paid retry is scheduled.

At 16:58 UTC the four per-worker lists reported zero RUNNING workers after the
last completions; all endpoints retained min0/max1. Qwen/voice were observed
after their idle period, Fast after its 60-second tail. The failed Gemma worker
had been manually recycled, so this is not a successful natural idle test of a
completed vision job. Do not infer exact billing from a lagging rollup or from
the presence/absence of idle/throttled entries.

Local checks use test identities/provider seams. They do not establish live
cookie isolation, model quality, actual GPU cancellation, durable media playback
or a working microphone/speaker. Earlier RunPod probes in historical notes are
not acceptance of this fresh Contabo interface.

## Allowance and remaining acceptance

The owner updated project rules: owner-performed login is not a prerequisite
when existing authorized access supports the tests. Authentication stays enabled;
report server/API evidence separately from browser and real-device evidence.
Testing on existing resources is pre-authorized up to USD 7 cumulatively for
this run, including estimated idle time. Ask before exceeding that amount.
Quick FLUX image estimate is $0.003, Wan 5s $0.30; the ledger uses conservative
$0.75/h Fast/voice and $1.75/h Qwen/Gemma estimates including idle tails.
Temporarily raise only the governed daily test allowance from $2 to $7 and
restore $2 afterward; retain the $20 monthly limit and other controls. No new
resource or recurring commitment is authorized by the testing allowance.

1. Resolve Fast's Finnish wording and mixed Swedish/Finnish responses in a
   multilingual saved conversation. Routing and analysis separation passed the
   final ordinary-chat probe; language quality did not.
2. Resolve the larger Gemma's cold-start weight-loading failure and verify image
   understanding; retain the completed Qwen/same-chat continuation evidence.
3. Enforce the actual video duration limit, then verify saved output duration.
   Existing image/video persistence and provider-confirmed cancellation passed.
4. On a real device: microphone permission/deny/revoke, audible playback and
   interruption. API loopback/replay/storage tests already passed in fi/sv/en.
5. Inspect actual worker scale-down; distinguish idle observations from manual
   worker recycling and configured minimums.

Do not promote `/preview/`, change the public default or mark PR #2 ready until
the results are recorded. DeepSeek, the future cloud computer and old RunPod
volume `vevppjlc9a` remain untouched.

## Reproduce and roll back

Build with `python scripts/build_openwebui_bundle.py`. Copy reviewed source and
`dist/openwebui` to the existing VPS integration folder. Run
`scripts/install_openwebui_bundle.py dist/openwebui` inside the existing Open
WebUI container with its native backend on `PYTHONPATH`, then restart that
container. The installer requires one existing admin, updates only these named
plugin sources, preserves valves and never replaces an existing review model.
Do not copy the server `.env`, database or secret-key file into the package.

Publish `web/index.html`, `app.mjs` and `api.mjs` to `/opt/family-ai/web/build/`.
The original prototype is preserved at
`/opt/family-ai/web/preview-before-integration-20261104.html`. To restore that
preview, as `deploy`:

```bash
cd /opt/family-ai
cp web/preview-before-integration-20261104.html web/build/index.html
```

To withdraw backend review, use native admin Functions to disable
`family_runtime`, `family_router` and `family_start_voice`, then restart Open
WebUI. The preview is already restored; keep `family_media`, private model,
ledger, chats and files stored for recovery. No deletion or full-database restore
is needed. Native `/` and original provider configuration remain available.
