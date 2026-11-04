# Voice: guarded Contabo preview and native audio limitations

## Current preview — 2026-11-04

`/preview/` now uses guarded `/api/v1/family/voice/*` routes from
`family_backend/speech.py`. Start voice activates a five-minute chat-bound intent
without contacting RunPod. Record requests microphone access and sends one
PCM16 WAV transcription (up to30seconds/6MiB/8–48kHz); review the transcript
before Send. Play explicitly synthesizes1–2000characters with Piper. Choose
Finnish, Swedish or English. There is no automatic playback.

The server checks verified identity, native speech permission, same origin,
saved-chat ownership, intent and input bounds. Each STT/TTS request uses the same
budget/concurrency/deduplication ledger. Piper WAV is saved as an owned native
file and attached to its assistant turn; completed replay uses that saved file.
The browser pauses playback and aborts its request on Interrupt. Synchronous
speech provides no queued-job ID, so disconnect cannot prove GPU work stopped.
An unconfirmed request or failed save retains its reservation and is never
automatically resubmitted.

The selected language/model/voice is sent explicitly. The RunPod wrapper update
below remains unapplied: its current heuristics may override the requested voice.
No speech endpoint configuration was changed. Device and paid acceptance remain
pending; see [Contabo integration](contabo-integration.md).

## Existing native Action and endpoint wrapper

The intended route is microphone → existing Whisper large-v3 → transcript in
`family-auto` → shared router/native tools → final text → existing Piper voice.
Speech recognition/synthesis is not a separate reasoning model. Typed and
transcribed input use the same backend selection/delegation. The shared reasoning
request has no tools of its own, preventing recursive specialist execution.

The existing Start voice Action makes one manually requested `/v1/models` probe
with bounded timeout, duplicate protection and an estimated reservation. It never
changes minimum workers, sends periodic keepalives or runs inside ordinary typed
chat. Ready means a200 from that probe, not proven microphone/playback readiness.
502/503/504 reports startup; a timeout remains uncertain. No startup retry loop
runs automatically. Voice still has min0/max1 and300s idle timeout. Whisper/Piper
TTL=-1 retains models within a running worker; it does not set a minimum worker.

`voice/voice_start.py` adds input bounds (64KiB JSON,1–2000 text characters),
disconnect handling and explicit `language=fi/sv/en` for Piper selection. Existing
heuristics remain for Standard mode, which may not send that override. Short
names or mixed-language text can select the wrong voice. Finnish harri, Swedish
nst and English amy are retained. Local language/bounds tests pass. This command
update has **not** been deployed to the existing speech endpoint.

## Standard mode limitations confirmed in source

The v0.12.4 native audio router directly calls the configured OpenAI-compatible
speech service. It does not call the Family ledger or require the new manual
voice-session record. It also fetches remote model/voice metadata when those
native routes are requested; such a load-balancer request may start speech.
This does not prove typed chat currently triggers it; that requires live network/
worker observation. The new chat adapter itself makes no speech request.

Consequences:

- Manual Start voice is a convenience; it cannot enforce a hard manual-session
  gate on native transcription, synthesis or metadata requests.
- Speech generation/recognition and their concurrency/costs bypass the new daily/
  monthly controls. The startup reservation alone does not meter an entire call.
- The new5min voice-session state is intent/readiness, not a live microphone,
  browser playback or worker lease. DELETE clears it; it cannot interrupt an
  already-running native request or guarantee immediate scale-down.
- Native TTS caching and audio playback are separate from durable conversation
  attachments. No permanent audio-result URL or guaranteed speech regeneration
  without another charge is implemented here.
- Device permission prompts, autoplay restrictions, audio decoding, wake-from-cold
  behavior and interruption have not been tested on a real device in this
  continuation. The fresh Contabo app is available, but signed-in device acceptance
  remains pending. Do not call this full voice acceptance.

## Native route guard proposal — still deferred

Keep Open WebUI. Add a backend guard around its native speech and metadata routes
that uses the **existing verified user** and same admission ledger. Metadata
should come from the configured cached three-language list without waking a GPU.
Require explicit short-lived session activation for actual STT/TTS, bounded audio
size/duration and text chunks, per-operation reservations and idempotency, and
owned persisted audio output. Use the same Whisper/Piper endpoint and settings.
Do not trust forwarded user headers as authentication or put a RunPod key in the
browser. Do not add a shared-key-only proxy that loses family-user attribution.

The preview implements a separate guarded path as described above. Replacing
native audio routes or middleware still needs acceptance testing to avoid
breaking the existing interface. Keep manual Record/Play controls, send transcripts to the
normal chat API, show the same specialist job events, and speak short final
summaries only after real success. Media remains a visual file plus spoken
explanation. No additional voice LLM or always-on GPU is required.

## Device acceptance

Follow the voice cases in [contabo-integration.md](contabo-integration.md). Check an HTTPS
secure context and both browser/OS microphone permissions. Record each language,
test explicit deny/revoke, preserve the original conversation while a video runs,
observe progress and spoken completion, then interrupt playback and generation
separately. Reopen the conversation and saved media. Keep speech off during typed
chat and inspect actual speech requests/worker state. Wait past300s idle and
confirm running workers return to zero; do not infer this from configured min0.

Do not replace Standard mode or enable a Realtime provider as a workaround before
these checks. Existing family accounts/default model must continue to function.
