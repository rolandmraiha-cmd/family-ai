# GPU routing: first implementation

Status: code and mocked transport tests complete. **Not installed in the live app.**
The owner approved creation on 2026-11-01. The small endpoint is now
`52cjk52hgbwag1`; its configuration is recorded in `runpod/fast-endpoint.json`.
Initial live smoke tests completed; see results below. Do not create another endpoint from the proposal.
The original three endpoints and Open WebUI data are unchanged.

## What this adds

`openwebui/functions/family_router.py` is an Open WebUI manifold Pipe, checked
against the source of the deployed version, v0.12.4. It adds these model choices:

| Choice | Destination |
| --- | --- |
| Family AI · Auto | Small GPU when configured; existing Gemma otherwise. Requests matching coding keywords, a long latest message, or tool-call history go to Qwen Pro. |
| Family AI · Pro | Existing Qwen3.8 endpoint `c3lm36gdhpctl2` |
| Family AI · Finnish / Swedish | Existing Gemma endpoint `936leprwfzb9gr` |
| Family AI · Fast | Small GPU; hidden until its endpoint ID is entered |

Auto is an explicit rule-based first version, not a learned difficulty detector.
It can miss difficult questions and over-route simple ones. Manual model selection
overrides it. It does not launch a second model because the first answer was weak.
Once a conversation contains a tool call, Auto stays on Pro for that conversation.
Finnish/Swedish mode remains available because the existing language tests favored Gemma.

Voice, `family_media`, chat storage, RAG and existing direct connections remain
managed by Open WebUI. This Pipe forwards native tool definitions, tool results,
image messages, tool-call deltas and reasoning deltas, but does not itself execute
tools. Attach the existing media tool and use Native function calling on each new
workspace model. Live tool-loop compatibility still requires verification.

## Cold starts and cost controls

The Pipe submits one `/run` job using the vLLM worker's `openai_input` format.
It polls `/stream` (or `/status` for non-streaming calls). Empty deltas and progress
events keep streaming chat active during cold starts. This avoids one blocking
Runpod OpenAI-proxy request, but does **not** make the GPU load faster or guarantee
that every frontend/proxy timeout disappears. Non-streaming callers receive no
heartbeat and can still hit an outer proxy timeout.

- Never automatically retries a submission or switches endpoints after failure.
- Default two in-flight jobs per loaded Pipe instance (not a global rate limit).
- Default 2,048 output tokens, bounded by the valve setting.
- Default ten-minute wall-clock wait and Runpod execution/TTL policy.
- Requests cancellation on timeout or stream disconnect; cancellation is best effort.
- No extra GPU classifier, CPU inference or hosted-model fallback.
- No credentials or private chat contents in errors emitted by the transport.

This is not a billing cap. Open WebUI background title/tag jobs can also invoke
models; configure those to use the cheapest tested model and measure their cost.
No context truncation is performed: an overlong conversation gets the worker's
error rather than silently dropping earlier instructions or tool results.

## Small worker — creation approved and completed

`runpod/fast-endpoint.proposed.json` is the original proposal;
`runpod/fast-endpoint.json` records the created endpoint with its returned ID:

- Official `Qwen/Qwen3.5-9B` weights, using the same vLLM worker version as Pro.
- One 24GB GPU, zero minimum / one maximum worker.
- 8K context, four sequences, one image per prompt; thinking disabled per Fast request.
- 60-second idle timeout as an initial cost/latency tradeoff. Measure before tuning.
- Runpod currently lists this class at **$0.75 per billed hour**, plus any storage
  and applicable tax. Startup and idle waiting are billable. No monthly minimum
  GPU compute with min=0, but storage may persist.

This intentionally starts with official BF16 weights to avoid introducing a
third-party quantization before a baseline is measured. The vLLM recipe identifies
24GB as a target for this model; memory at our exact settings has not been tested.
If the worker runs out of memory, stop it and evaluate a supported FP8 checkpoint
before changing hardware. Do not create a second endpoint to fix the first.

The owner approved both the private repository upload and this paid endpoint
after the price was stated. The endpoint is listed in README.md. No new CPU host
or higher-priced GPU was approved or provisioned.

## Install after review

1. Back up the existing Open WebUI data volume with the established backup process.
2. Admin → Functions: create a function with ID `family_router`, paste the Pipe source,
   and enable it. This is a Function, not a Workspace Tool.
3. The owner enters the Runpod key in its valves directly. Do not put it in files,
   terminal commands, commits, or chat. Keep `FAST_ENDPOINT_ID` blank initially.
4. Create private test workspace models based on `family_router.auto`,
   `family_router.pro`, and `family_router.language`. Copy the existing assistant
   system prompt, Native function calling and `family_media` attachment.
5. Test existing endpoints first: Swedish/Finnish/English replies, web search,
   an image attachment, tool-call continuation, and chat reopening. A queued/cold
   job should show progress and deliver output without resubmitting.
6. Reuse the created endpoint `52cjk52hgbwag1`. Measure cold/warm
   times, peak VRAM, output quality and billed runtime. Do not assume it is faster.
7. Enter that ID in `FAST_ENDPOINT_ID`; run the acceptance prompts below. Only
   choose Auto as the default after these pass. Existing direct models remain
   available for rollback; disable the Function to remove the new choices.

## Live acceptance prompts

These prompts are human-written smoke checks, not training data.

| Check | Prompt / action | Acceptance |
| --- | --- | --- |
| Finnish | "Selitä suomeksi lyhyesti, miten lämpöpumppu toimii." | Natural Finnish; review grammar, factual content and register. |
| Swedish | "Förklara kort skillnaden mellan ett lån och en kredit." | Natural Swedish without language mixing. |
| English | "Explain GPU memory in three short sentences." | Direct response without a thinking preamble in Fast. |
| Coding | "Debug this Python traceback: TypeError: unsupported operand type(s) for +: int and str." | Auto selects Pro and gives a relevant fix. |
| Vision | Attach a known screenshot and ask what it shows. | Describes actual image details. |
| Tools | Request one quick image through the existing media tool. | Native tool executes once and the image remains after reopening chat. This test incurs the existing image fee. |
| Cold start | Let the chosen endpoint scale down; send one message. | Progress appears; exactly one Runpod job; eventual completion. |
| Cancel | Stop a response while its GPU job is queued. | Cancellation appears in Requests, with no replacement job. |

## Local verification

### Live endpoint checks on 2026-11-01

Hardware assigned by Runpod: RTX PRO 6000 Blackwell Server Edition MIG 24GB.
Model loaded in BF16 with 17.57GiB model memory reported by vLLM; the worker
reported 2.13GiB available KV cache memory. These logs establish that this
configuration started on this SKU, not on every GPU in the selected pool.

| Test | Queue delay | Worker execution | Result |
| --- | --- | --- | --- |
| Initial Finnish request, 180-token limit | 212.711s | 8.660s | Responded, but language errors and length instruction failure; cut off at token cap |
| Swedish one-sentence GPU explanation | 0.056s | 2.133s | Completed, coherent Swedish |
| Finnish one-sentence heat-pump explanation, explicit system instruction | 0.056s | 2.453s | Completed, coherent Finnish |
| Forced `get_weather` function call | Not measured here | Not measured here | Stream delivered function name, arguments `{"city": "Helsinki"}` and `[DONE]` |

The forced-call stream ended with finish_reason `stop`, not `tool_calls`; Open
WebUI's actual native tool execution therefore still needs an end-to-end check.
No real weather tool was executed. The shorter language checks used recommended
non-thinking sampling defaults and a clear system instruction. One good answer
does not establish general Finnish quality; keep the Gemma language option.
The first small-model cold start was not faster than the previously recorded Pro
startup. Optimize startup or warm retention only after measuring actual usage.

### Local transport checks

`python -m unittest discover -s tests -v`

Tests use a local fake Runpod HTTP server and do not start paid GPU jobs. They
cover routing, native tool/image payloads, fragmented SSE, terminal stream drain,
non-streaming results, submission failures, cancellation, timeout, and overload.
They do not establish live GPU quality, performance, or installed UI behavior.

## Next stages

1. Validate this router and small GPU; then switch the default.
2. Move Open WebUI off the $0.08/hour CPU pod to a cheaper CPU VPS, preserving its
   volume contents, encryption/session settings and accounts. Choose the target
   and price first; no migration or new CPU server is included in this change.
3. Add an isolated browser/terminal workspace with persistent files and a visible
   desktop. Existing Pyodide code execution is not a cloud computer. The desktop
   must be isolated from Open WebUI's database and Runpod credentials.
4. Evaluate self-deployed image generation if usage justifies its cold starts and
   storage compared with the existing per-image endpoints.

## Checked references (2026-11-01)

- [Open WebUI v0.12.4 function handling](https://github.com/open-webui/open-webui/blob/v0.12.4/backend/open_webui/functions.py)
- [Runpod vLLM v2.30.1 handler](https://github.com/runpod-workers/worker-vllm/blob/v2.30.1/src/handler.py)
- [Runpod Python client stream handling](https://github.com/runpod/runpod-python/blob/main/runpod/endpoint/runner.py)
- [Runpod request lifecycle](https://docs.runpod.io/serverless/endpoints/send-requests)
- [Runpod pricing](https://www.runpod.io/product/serverless)
- [Qwen3.5-9B vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.5-9B)
