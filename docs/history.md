# History

## 2026-11-03: Shared text/voice modules and Gemma E2B
- Reused Fast endpoint `52cjk52hgbwag1` for Google Gemma 4 E2B IT, same 24GB
  pool and zero minimum workers. Eager/text-only serving avoids compilation,
  CUDA graphs and multimodal warmup. First startup delay 182.287s.
- Added shared deep-reasoning access to the existing image/video tool. Auto
  dispatches explicit deep requests directly as native tool calls; the real E2B
  worker ignored a forced named tool call. Existing larger Qwen is the initial
  specialist. Image attachments use the retained larger Gemma.
- Added manual Start voice Action; STT transcripts use the same router/tools,
  with final playback through existing Piper. No always-on speech worker.
- Prepared an optional self-deployed DeepSeek-R1-Distill-Qwen-14B profile at the
  checked $1.22/active-hour pool rate; not created without price approval.
- 33 local checks pass. Owner signed in securely; router, shared modules and
  manual voice Action were installed and enabled. Created private `family-auto`
  with native tools and the existing encrypted RunPod credential reused in-process.
- Live chat showed queue progress, then its view stopped updating. Browser URL
  policy rejected reload, so the saved reply, live tool loop, persisted media and
  microphone/playback remain unverified. Existing public default is retained.
- Small-model quality limits are recorded: factual error in a Finnish heat-pump
  response, and hidden reasoning returned despite requested non-thinking mode.
- After the owner topped up depleted RunPod credit, live Fast Finnish, larger
  Qwen reasoning, actual specialist-result continuation, FLUX image ($0.003) and
  Wan five-second video ($0.30) checks passed. GitHub CI passes all 33 tests.
  Browser access to the old chat view is still rejected; device/audio checks remain.
- No new paid endpoint, CPU migration, deletion or cloud-computer work occurred.
- See `docs/shared-modules-rollout.md` for exact state, install and rollback.

## 2026-11-01: Contabo fresh-start authorized; access blocked
- Owner explicitly selected the existing Contabo VPS and requested deleting its old contents.
- Recorded target is `37.60.226.214` / `vmi3634750.contaboserver.net`; its current
  identity still needs verification in an authenticated session before erasure.
- Prepared private-bootstrap Open WebUI/Caddy Compose files and fresh-host instructions.
- Bash syntax and YAML/private-binding checks passed; Docker runtime checks unavailable locally.
- Cloud browser returned "Site Unavailable" for both documented Contabo panels;
  there is no connected SSH credential. No remote wipe, installation or CPU cutover occurred.

## 2026-11-01: Owner approved upload and small GPU creation
- Uploaded the router implementation to branch `codex/gpu-router`, draft PR #1.
- Created one Qwen3.5-9B serverless endpoint: `52cjk52hgbwag1`, min=0/max=1,
  24GB GPU pool, 60-second idle timeout. The first request queued for 212.711s;
  Swedish/Finnish short warm jobs completed in 2.133s/2.453s. The initial longer
  Finnish response had errors and exceeded its length instruction. A forced tool
  call streamed correct arguments; live UI tool execution remains unverified.
- Existing CPU pod remains running; checked $0.08/hour cost and one utilization snapshot.
- Added CPU savings/migration guidance. No new CPU hosting was purchased and no data was moved.

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

## 2026-11-03/04: Chat app moved to the Contabo VPS
- The owner didn't want to pay for an always-on RunPod CPU pod, so Open WebUI now runs on the Contabo VPS (details in `docs/vps.md`).
- Fresh start: old chats on volume `vevppjlc9a` were not moved.
- Server hardened first: key-only SSH, firewall, fail2ban, swap, non-root `deploy` user.
- Open WebUI v0.12.4 behind Caddy with HTTPS at `https://37-60-226-214.sslip.io`. The new UI prototype is at `/preview/`.
- Plan: Open WebUI stays as the hidden engine, and the new UI replaces its screens part by part.
- First test: `family-gemma` answered in good Finnish after about 1.5 min of cold start.

## Open items
- 2026-11-04 startup: enabled eager mode on the existing larger Gemma after a
  bounded fresh-worker comparison. Provider delay 130.697s to 114.498s; full
  response 138.645s to 123.463s, but generation 4.857s to 7.392s. Weight-loading
  variance contributes; under 20s remains unmet. FlashBoot already enabled;
  min0/max1 retained. Two requests added USD 0.70 conservative budget held,
  cumulative USD 11.719672, with USD 2/day restored after each. See
  `docs/startup-20261104.md` for scope, limitations, sources and rollback.
- 2026-11-04 cost correction: separated explicit provider job costs from retained
  admission estimates; old ledger values keep their budget coverage and remain
  unconfirmed. No wallet balance or finalized invoice is inferred. Shortened
  existing Gemma/Qwen idle timeout 600s to 120s, voice 300s to 60s, Fast stays
  60s; min0/max1 retained. No inference was submitted for this change. See
  `docs/cost-accounting-20261104.md` for verification and remaining reconciliation.
- 2026-11-04 follow-up: owner approved USD 5 more (USD 12 cumulative). Existing
  larger Gemma passed a synthetic image probe and three-language comparison;
  its earlier weight failure did not recur on the cached worker. Implemented
  actual video-duration measurement/trimming before saving; a new Wan output
  saved/reopened at exactly 5.00s/150 frames. E2B still fails Finnish/Swedish with
  stronger instructions and deterministic sampling; both experiments were
  withdrawn. 101 Python and seven JS tests pass. Cumulative conservative estimate
  USD 11.019672; normal USD 2/day restored, usage retained. No new resource,
  model/default change or voice job. See `docs/acceptance-followup-20261104.md`.
- 2026-11-04 owner rule update: owner-performed login is not required when tests
  can use existing authorized access. Report actual test coverage and gaps.
  Existing-resource testing is pre-authorized up to USD 7 cumulatively, including
  estimated GPU idle time; obtain approval before exceeding it. Credentials and
  application authentication remain protected. See `AGENTS.md`.
- 2026-11-04: Integrated real `/preview/` with native Open WebUI accounts, saved
  chat/tools and added guarded manual speech. Reviewed plugins/private Auto
  installed on Contabo; public config/default retained.97Python and7JS checks
  pass. Native authenticated control routes and same-chat specialist continuation
  were tested; media reopened from persistent files and fi/sv/en speech API
  loopbacks passed. Acceptance found Gemma weight-loading failure, unnecessary
  Fast delegation/visible analysis, and a 5.37s output for a requested 5s video.
  Coordinator guidance/final-answer display were fixed; native E2B template and
  reviewed speech wrapper deployed on the existing endpoints. Browser/device
  gaps and bounded test costs are reported separately. PR #2 stays draft. See
  `docs/contabo-integration.md` for evidence, limitations and reversible rollback.
- Backups: a free sync of the volume to the owner's PC through RunPod's S3 API (EUR-IS-1). It needs an S3 key that the owner creates.
- Family accounts.
- Decide on cheaper hosting (see `docs/research/cheaper-hosting-2026-10.md`).
- A better Finnish voice.


