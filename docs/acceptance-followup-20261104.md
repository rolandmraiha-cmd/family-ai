# Acceptance follow-up — 2026-11-04

The owner approved another USD 5 for the same test allowance: **USD 12 total**,
including the preceding USD 5.361336 conservative estimate. This is a run-specific
exception to the standing USD 7 rule, not a new recurring allowance. Existing
resources only; daily test admission temporarily USD 12, restored to USD 2 after
each sequential phase. Monthly USD 20 and other controls remain unchanged.

## Baseline and diagnosis

Six native saved-chat turns tested Finnish, Swedish and English separately and
then switched languages within one conversation. Every turn used one Fast job.
Finnish grammar failed even in a fresh chat ("Vesi jää kelluvan"). Fresh Swedish
gave a wrong volume explanation; the switched Swedish answer contained Finnish
("sen tiheys"). English was correct. The problem is broader than history mixing.

One bounded synthetic vision retry completed on the existing larger Gemma with
unchanged endpoint configuration. It named the red/green/blue stripes correctly
in Finnish. Worker logs showed both safetensors shards loaded (31.72 GiB GPU
model memory), followed by healthy serving. The prior missing-weight failure did
not recur on this cached worker; this does not establish a permanent fix for all
future workers. No new weights/image/model configuration was deployed.

## Implemented change and rejected experiments

- A stronger latest-language instruction was compared on six baseline turns and
  four new family-message/time prompts. It did not improve the failed ice
  explanations; the switched Swedish answer still contained Finnish. Both time
  answers were correct (15:35), but family messages added awkward, unintended
  statements. The ineffective instruction is withdrawn rather than presented as
  a fix. E2B remains the ordinary-chat coordinator, as the owner requested.
- Media saving now measures the actual MP4 before upload. Outputs above the cap
  are re-encoded to the limit and measured again. Invalid duration, failed tools,
  oversized output or an excessive final duration fails without a new GPU job.
  Existing persisted media is retained unchanged.
- The real earlier Wan file (5.366667 seconds, 161 frames) was trimmed on the VPS
  to **5.000000 seconds, 150 frames**, H.264, 3,518,306 bytes. A second bounds pass
  returned identical bytes. This reused the saved output with **zero inference**.
  SHA-256: `50cc940e7a6c734abed9eaadd8f0b7f61c9c9272d9778ca3ccc011911c9d331c`.

## New saved video and language comparison

One new Wan job reused the earlier saved cabin image. The actual saved H.264 MP4
is **5.000000 seconds, 150 frames, 960×960, 3,551,267 bytes**. It reopened twice
through authenticated owned file routes with identical SHA-256
`517b80f2e4d0a9d837cf59bea29479fdbddc3e9816f43770ef1054fc084d9e88`.
Three sampled frames were visually inspected: the cabin/lake scene remains
coherent, with subtle water movement. This verifies saved-file decoding and
duration; actual browser/device playback is separate.

The manual existing larger-Gemma language choice was also tested in one saved
chat across Finnish → Swedish → English. Finnish and English answers were
grammatical and factually correct. Swedish correctly explained the larger ice
crystal volume, with a minor spelling error ("krystallstruktur" instead of
"kristallstruktur"). It is substantially better on this small sample than Fast,
not a guarantee of general language accuracy. The public default and Auto route
were not changed to hide E2B's failures.

Browser microphone permissions and audible real-device playback still require
separate device evidence; server/API checks do not prove them.

Four further same-chat probes used per-request temperature 0 with the original
router guidance restored. Both bus-time answers were correct, but Finnish again
had poor grammar and incorrectly compared ice with air density; the Swedish ice
answer was mostly Finnish. Deterministic sampling is **not** a language fix and
was not made the default. No further speculative prompt/sampling edit was stacked
on the failed experiments. Fast language acceptance remains blocked; use the
existing manual Finnish / Swedish choice when better language quality is needed.

## Verification and accounting

- 101 Python tests pass locally and in the actual Linux container, including
  four new duration-bound regression cases. Seven JavaScript tests pass.
- The final source retains only the video-duration fix; the ineffective router
  instruction was removed. Existing native plugin loading compares DB content
  before reuse, so the original router was restored without another restart.
- There were **27 additional provider jobs**: 22 Fast, four larger Gemma, one
  Wan. No new voice, Qwen or FLUX job was submitted during this follow-up.
- Cumulative ledger estimate: **USD 11.019672**, an increase of **USD 5.658336**
  from the preceding USD 5.361336 phase. This includes conservative configured
  idle tails; it is not a finalized provider invoice. About **USD 0.98** of the
  USD 12 allowance remains unused. The new Wan output reported USD 0.30.
- Accounting reads all owned run rows from durable SQLite. The Activity API
  intentionally lists only the newest 50 jobs; that list is not a cumulative
  usage total. Native admission always counted the full ledger.
- Normal limits are restored: daily USD 2, monthly USD 20, concurrency two,
  maximum five seconds/one video per turn. Test usage is retained, so today's
  governed preview is over its restored daily cap. Native direct models remain
  outside that governed limit. Voice intent stays off.

Final durable state is **55 jobs: 54 completed, one cancelled, zero active or
unknown**. Authenticated capabilities/policy/usage return 200; native health 200;
unsigned controls still return 401. No further inference is scheduled.

The larger Gemma naturally returned to zero RUNNING workers after its configured
600-second idle period. Qwen and voice also showed zero RUNNING workers and were
not invoked in this follow-up. Fast was still reported RUNNING at 20:36 UTC,
despite its last job finishing at 20:33:59, zero queued/in-progress provider jobs,
and a 60-second configured idle timeout. Its worker was therefore manually
recycled (max0, then restored to max1 after shutdown). **Fast natural scale-down
did not pass this observation.** Provider state and billing feeds can lag; no
exact billing-stop claim is inferred from idle/throttled entries.

The existing public default and native `/` remain unchanged. PR #2 stays draft.
SSH/firewall/password-login settings and the old RunPod volume are untouched.
