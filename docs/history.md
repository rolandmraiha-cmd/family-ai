# History

## 2026-11-05: Alternative HTTPS address for phone access
- The owner's iPhone reported that Safari could not find the sslip.io server.
  Public Google DNS and external HTTPS checks still resolved/reached the original
  address; the specific phone/network DNS cause is not established.
- Added `37-60-226-214.nip.io` to the same Caddy site on the existing Contabo VPS.
  Caddy configuration validation and graceful reload passed. Existing hostname,
  application authentication and stored data remain in place; no app restart,
  inference job, new resource, SSH or firewall change.
- Previous Caddyfile is saved at
  `/opt/family-ai/integration/20261105-access/Caddyfile-before` for rollback.
  Automatic certificate issuance succeeded. Public HTTPS health, preview and
  sign-in pages return 200 on the alternative address; original HTTPS still
  works. Native authenticated session, capabilities and account APIs return 200
  through the alternative HTTPS address; unsigned account access returns 401.
  The owner confirmed that the alternative address opens on the iPhone.

## 2026-11-05: RunPod balance and spending in the preview
- Added an administrator-only header balance and Activity account card with
  RunPod-reported daily/monthly spending (UTC), timestamps and hourly rate.
  Refreshes once per minute while visible; provider billing can lag. Account-wide
  figures remain separate from the preserved job estimates and budget controls.
- Installed the reviewed backend bundle on the existing VPS, restarted only
  Open WebUI and published the three preview assets. Saved prior plugin sources
  and assets for rollback; native `/` and the public default remain unchanged.
- Live admin API 200/no-store, unsigned 401, fresh provider figures, server cache
  reuse and exact public asset/source matches passed. All 78 ledger records,
  configuration, credential valves and normal USD 2/day / USD 20/month limits
  are unchanged. No inference jobs or additional GPU test costs.
- 121 Python and 10 JavaScript tests pass, including member 403, cache/outage
  and period rollover checks. No ordinary member exists for a live member test;
  browser/phone rendering remains unverified because browser URL safety stopped
  inspection. See `docs/account-tracker-20261105.md` for details and rollback.

## 2026-11-05: Faster Q8 serving on the existing Gemma endpoint
- Continued within the same USD 17 cumulative allowance. Matched FP8/vLLM
  baseline took 154.920s overall, including 122.484s provider delay.
- Switched only larger Gemma to pinned cached Q8 Gemma 31B with llama.cpp.
  Fresh cached process loaded in 9.466s, first full answer 22.417s. After
  natural shutdown, the same retained process resumed and answered in 6.718s;
  this second result is not a second fresh-process measurement.
- Longer fi/sv/en output was mostly readable, with an odd Finnish word and a
  short Swedish wording error documented. Simple image colours/positions,
  a clearly wide rectangle, native tool arguments, tool-result continuation,
  installed-router streaming and the existing OpenAI gateway worked. Detailed
  image parity and browser/device acceptance remain unverified.
- Kept the Q8 profile live with min0/max1, idle120 and nine European locations.
  Increased Q8 microbatch to 2048 to avoid the previous vision-budget cap.
  The original FP8 JSON remains the rollback configuration; the generator
  reproduces Q8 and its separate pinned cache-attachment plan.
- Initial model staging took 10m21s. Cached engine speed does not guarantee
  available capacity or an under-20s first answer on a new host.
- 113 Python tests and nine JavaScript tests pass in the project environment;
  bundle build, compilation and diff checks pass. The unrelated system Python
  lacks the project's timezone/dependencies and was not the validation runtime.
- Ten accepted probes in this continuation retained USD 1.779167 in estimates;
  one HTTP409 rejection retained zero. Cumulative USD 16.648839 of USD 17,
  78 settled records, zero reservations, normal USD 2/day and USD 20/month.
  These estimates are not a provider invoice. No new resources or keepalive.
- See `docs/startup-q8-20261105.md` for evidence, limitations and rollback.

## 2026-11-05: European capacity and llama.cpp startup trial
- Owner approved another USD 5, bringing cumulative test authorization to USD 17.
  Expanded only larger Gemma's preferred locations from Sweden/Iceland to nine
  European locations; no resources were created or made always-on.
- Tested a cached Google QAT Q4 Gemma 31B with llama.cpp on an A5000. The model
  loaded in 6.067s inside the adapter, but the request took 452.864s overall,
  mostly waiting for provider allocation. A fast model load does not remove
  capacity queues or guarantee an under-20s first response.
- Short fi/sv/en explanations, valid native tool arguments and SSE output worked.
  The longer Finnish answer had several errors; the image answer mislabeled a
  rectangle as a square. Rejected the candidate and restored the previous eager
  FP8 engine and its pinned cache attachment; wider European placement is kept.
- Found that REST/env updates leave a separate modelReferences attachment
  unchanged. Earlier failed probes had staged the old FP8 model. Corrected cache
  attachment, pinned-file validation and loaded-model readiness; no runtime
  weight-download fallback remains in the experimental adapter.
- Added a disabled candidate generator and cache attachment plan. 113 Python
  tests and nine JavaScript tests pass; bundle build and compilation pass.
- Restored-engine smoke completed in 129.335s. Nine probes retained USD 3.15 in
  estimates, bringing cumulative held estimates to USD 14.869672 of USD 17
  approved. All 67 ledger records settled, reservations zero, normal USD 2/day
  and USD 20/month restored. These estimates are not verified wallet spend.
- See `docs/startup-llamacpp-20261105.md` for measurements, failed attempts,
  accounting, acceptance limitations and rollback. Browser/device testing and
  candidate quality promotion are not claimed.

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


