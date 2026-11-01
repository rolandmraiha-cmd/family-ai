# GPU routing: first implementation

Status: code and mocked transport tests complete. **Not installed in the live app.**
No new endpoint has been created. Existing endpoints and Open WebUI data are unchanged.

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

## Proposed small worker — requires approval before creation

`runpod/fast-endpoint.proposed.json` is an **unapplied proposal**:

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

The project's AGENTS.md requires a price and approval before creating a paid
resource, and limits changes to the resources already recorded in README.md.
Approval must include adding this fourth endpoint to the resource inventory.

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
6. After cost/resource approval, create the proposed small endpoint once. Record
   its returned ID in README and a deployed config snapshot. Measure cold/warm
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
