# Gemma startup and European GPU availability trial

The owner approved another USD 5 for the existing-resource startup comparison,
bringing cumulative authorization to USD 17. The previous retained estimate was
USD 11.719672. These are admission estimates, not the RunPod wallet or invoice.

## Scope and geographic restriction

Before this trial, both larger language endpoints preferred Sweden `EU-SE-1`
and Iceland `EUR-IS-2`; they were not Sweden-only. At the catalog snapshot used
for this trial, compatible 48 GB European capacity was concentrated in Sweden.
An endpoint's configured locations and the locations with compatible free GPUs
are different constraints.

The existing Gemma endpoint `936leprwfzb9gr` was expanded to nine European data
centers: `EU-SE-1`, `EUR-IS-2`, `EU-CZ-1`, `EU-RO-1`, `EU-NL-1`, `EU-FR-1`,
`EUR-NO-1`, `EUR-IS-3`, `EUR-IS-4`. The other endpoints were unchanged. Worker
minimum 0, maximum 1, idle timeout 120s and FlashBoot were retained. No new pod,
endpoint, storage volume or recurring commitment was created.

## Reproducible experimental adapter

`scripts/build_llamacpp_candidate.py` generates a disabled candidate configuration
(maximum workers 0). It does not deploy anything or submit inference. The image
is the audited `eniewold/llama-cpp-runpod` b11723 Hub build, release tag
`0365854c9`, with observed digest
`sha256:750cfe205937664fee301fe7959f1e6ff5fbe938d117113b3cc21158c72e13c1`.
Attempting to use the digest as the image reference produced Hub registry-auth
errors on new workers; the retry uses the catalog's exact release tag. A tag is
not an immutable digest pin; compare the loaded digest before accepting results.
The candidate overrides its Python entrypoint with `runpod/llamacpp_worker.py`,
which calls the included llama-server directly, forwards OpenAI-compatible
requests over local HTTP, preserves template options, and bridges streaming SSE.
It retains images, an 8192-token context and a single inference slot. It has not
been accepted as a production engine merely because its adapter tests pass.

Both profiles pin model and image-projector revisions:

| Profile | Model repository | Revision | Weight file bytes |
|---|---|---|---:|
| Q8 | ggml-org/gemma-4-31B-it-GGUF | 3d47a7e680fb9526dcac74335858f0f31acc9c27 | 32,635,676,896 |
| QAT Q4 | google/gemma-4-31B-it-qat-q4_0-gguf | 59dde24573e7e61570dba08b18a2e1fe246955ed | 17,651,001,568 |

The Q8 projector is 809,541,728 bytes; the official Google QAT projector is
1,200,726,368 bytes. The Q8 repository also contains other quantizations and is
about 112 GiB in total. RunPod's model cache currently downloads all repository
quantizations, so selecting one GGUF does not restrict its staging download.
The QAT repository contains just its weight/projector pair and metadata.
QAT Q4 is a different quantization and requires language and vision acceptance.

The corrected adapter requires **both** pinned files in the cache, accepts the
case-preserving HF and lowercase Hub cache layouts, and requires the served
model alias as well as a healthy HTTP endpoint. It waits at most 60s for the
cache mount and then fails closed. It never downloads weights during paid
startup or chooses an arbitrary model revision. Model availability on disk
does not imply that a GPU is free, or that the weights are already in GPU memory.

## Measurements

The earlier vLLM eager baseline returned its short three-language answer in
123.463s: provider queue/startup delay 114.498s, execution 7.392s. See
`startup-20261104.md` for the limitations of that single comparison.

The Q8 request remained queued for its entire 600s TTL and expired. Three
prepared Sweden workers reported THROTTLED; no inference or engine-ready event
was observed. One worker loaded the image by 21:49:36 UTC and completed model
preparation at 21:54:27 UTC on November 4. Later inspection showed that this
staging still referred to the original FP8 repository, not the Q8 candidate.
This is a placement/preparation failure
to obtain a startup measurement, not evidence that llama.cpp generation failed.
The expired provider record subsequently returned HTTP404. Its durable ledger
entry was explicitly settled as timed out, retaining the conservative estimate.

The QAT trial admits 24 GB cards as well as the existing 48 GB pools. Catalog
rates checked were USD 0.75/h for RTX A5000 / PRO 6000 MIG 24 GB and USD 1.34/h
for RTX 4090; availability varied by location. RunPod prepared three PRO 6000
MIG 24 GB workers in Iceland during the trial. Do not label these workers RTX
4090 or infer startup speed from the catalog.

The first QAT request failed after 454.372s (451.831s provider delay, 0.285s
handler execution). Container logs began at 22:06:18 UTC after allocation at
22:03:47. The adapter did not find its cached files and passed only download
URLs. In this llama.cpp version, a URL alone did not select a model: the server
entered empty router mode and the request returned HTTP400. Its apparent
0.255s HTTP-health time is **invalid as model startup**. This was an adapter
failure, not a language-quality, GPU-memory, or engine-speed result. The worker
was stopped before deploying the cache/readiness correction. Regression checks
now cover empty-router health, lowercase paths, and refusal of other revisions.

The corrected adapter then explicitly reported both expected QAT snapshot
directories absent. That request was cancelled after 473.317s, with the worker
stopped to prevent a startup loop. The missing-cache root cause was a separate
RunPod **modelReferences** attachment, omitted from REST v2 endpoint responses:
it still selected
`https://huggingface.co/RedHatAI/gemma-4-31B-it-FP8-dynamic:d4ab4f579dd3516f97d8a6a4c98d0653480bad15`.
Updating `MODEL_NAME` alone did not update it. The early staging durations must
therefore **not** be attributed to downloading the candidate GGUF repositories.

The original engine was restored during diagnosis. A subsequent candidate
deployment explicitly attached the exact QAT revision through GraphQL, round-
tripping every current endpoint field and checking that only modelReferences
changed. The generator now emits a separate `.model-cache.json` attachment plan;
this is not part of the REST body. A submission immediately after the change
returned HTTP409 without creating a provider job. Its reservation was released
as rejected, with no provider-reported charge invented. A replay guard prevented
another identical submission within its two-minute window.

The first accepted request with the **correct** QAT attachment was
`c16b473d-af4e-47d1-976a-51c036b1fe75-e2`. A Sweden A5000 worker reported
initializing model files at 22:19:30 UTC and model ready at 22:22:05 UTC.
These events describe preparation, not GPU-resident engine readiness. The
three prepared workers (two A5000 in Sweden and one RTX 3090 in Iceland)
initially remained THROTTLED. The A5000 worker `nsc4hir5f9xbz6` finally became
RUNNING at 22:28:45.926 UTC. Its adapter confirmed both pinned cached files,
started at 22:28:53.934, and reported a loaded model ready at 22:29:00.001:
**6.067s inside the adapter**, about 14.1s after GPU allocation. Generation
completed at 22:29:05.088. The first full request nevertheless took **452.864s**,
including 448.342s provider delay and 2.441s execution. Cached weights and a
faster engine did not remove the capacity queue.

This was a fresh llama.cpp process on an A5000, with a different quantization
and GPU from the earlier FP8/A40 vLLM baseline. It demonstrates a fast engine
load on that host, not a controlled engine-only comparison, a retained-worker
FlashBoot resume, or an under-20s end-to-end service guarantee.

| Correct-cache probe | Provider delay | Execution | Observed full request |
|---|---:|---:|---:|
| First short fi/sv/en answer | 448.342s | 2.441s | 452.864s |
| Longer fi/sv/en answer, warm | 0.089s | 13.727s | 17.210s |
| Synthetic image, warm | 0.088s | 1.809s | 3.201s |
| Native tool call, warm | 0.088s | 1.213s | 3.227s |
| Streaming response, warm | 0.093s | 1.217s | 3.246s |

Full-request measurements include the probe's three-second status polling.
The longer answer generated 437 tokens at about 33 tokens/s. Short explanations
were correct in all three languages. The longer Finnish answer did not meet
acceptance: examples include `perussyödyksiä`, `FIFO-periaannetta`, `ensiin`
and `uunipatina`. This small sample does not establish the cause or a general
quantization-quality difference. Swedish and English were readable, but no
comprehensive language evaluation was performed.

The image answer correctly located the red circle and blue shape, but called
the 230-by-195-pixel rectangle a square. Startup logs also show llama.cpp capping
the vision budget from 1120 to 512 because of the candidate's microbatch size;
image-detail parity is not established. The native tool response selected
`sum_numbers` with valid arguments `{"a":17,"b":25}`. The streaming output
contained intact SSE chunks, a terminal stop and `[DONE]`, reconstructing
`Solen skiner och dagarna är långa.\nThe snow falls softly over the quiet landscape.`
This verifies provider output, not an end-to-end browser tool execution or
incremental UI rendering.

**Decision: do not promote QAT Q4.** Finnish quality and exact image recognition
did not pass. A second candidate cold/resume probe was skipped after these
failures to avoid spending more on a rejected profile. The original eager FP8
engine, full environment, container defaults and pinned cache attachment were
restored, retaining only the expanded European location list. A bounded
`vllm-restored` smoke test checks the serving path after rollback.

The rollback smoke test completed in **129.335s** on A40 worker
`r46ekr8gzkod9l`: provider delay 121.020s, execution 7.901s. It returned the
same 50-token answer as the earlier FP8 baseline, including the previously
recorded Swedish error `Is kells`. Finnish and English were correct. This
confirms the restored inference path, not perfect language acceptance or a
startup improvement from broader placement in this one observation.

## Accounting and acceptance

Each submitted probe reserves USD 0.35, covering 600s execution plus 120s idle
at a conservative USD 1.75/h ceiling. The temporary daily admission cap is
USD 17 during a probe and is restored to USD 2 in its finally block. Monthly
USD 20 is unchanged; previous usage and estimates are retained. A queued job
does not establish actual billed compute; billing records can lag.

Nine submitted probes in this trial, including rollback verification, retained
USD 3.15 in estimates. The explicitly rejected HTTP409 submission retained zero;
deduplicated attempts created no reservation. Final cumulative retained estimate
is **USD 14.869672**, below USD 17 authorization, leaving USD 2.130328. It is
not verified account spend. All 67 ledger records are settled: 62 completed,
two cancelled, two failed, one rejected. Active reservations are zero; normal
daily USD 2 and monthly USD 20 limits are restored with usage history retained.

Language, synthetic image understanding, tool calls, streaming, and a second
cold/resume observation are required before promoting this candidate. The
candidate failed quality acceptance and remains experimental. No browser,
phone, microphone or live family chat acceptance can be inferred from API tests.

To restore the previous serving engine, drain active work, set maximum workers
to 0, restore the complete `runpod/gemma-endpoint.json` environment/image/GPU
configuration, explicitly clear container overrides with `args: ""`, then
restore the original pinned FP8 **modelReferences** attachment while maximum
workers is still 0, and only then restore maximum workers to 1. The REST body
does not restore this separate attachment. Retain `MAX_NUM_BATCHED_TOKENS=8192` in the full
environment. The expanded European location list is independently reversible.

## Primary sources

- [RunPod model caching and repository download limitations](https://docs.runpod.io/serverless/endpoints/model-caching)
- [RunPod worker states](https://docs.runpod.io/serverless/workers/overview)
- [RunPod GPU fallback and location settings](https://docs.runpod.io/serverless/endpoints/endpoint-configurations)
- [Exact llama.cpp b11723 server options](https://github.com/ggml-org/llama.cpp/blob/b11723/tools/server/README.md)
- [Exact Hub image Dockerfile](https://github.com/eniewold/llama-cpp-runpod/blob/b11723/Dockerfile)
- [Google's official Gemma QAT Q4 GGUF](https://huggingface.co/google/gemma-4-31B-it-qat-q4_0-gguf)
- [Google's llama.cpp deployment guidance](https://github.com/google-gemma/docs/blob/main/docs/deployment/llamacpp.md)
