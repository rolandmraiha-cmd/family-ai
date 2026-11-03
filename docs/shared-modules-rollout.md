# Shared model modules — 2026-11-03

## Exact deployment state

RunPod Fast endpoint `52cjk52hgbwag1` now serves `google/gemma-4-E2B-it` as
`family-fast`, on worker image `runpod/worker-v1-vllm:v2.30.1` (logs confirm
vLLM 0.32.0). Its current configuration is `runpod/fast-endpoint.json`.
Zero minimum / one maximum worker, 60-second idle timeout, FlashBoot, 8K
context, four sequences and eager execution. Text-only serving skips image,
video and audio profiling. Image attachments go to the larger Gemma endpoint.

The router/modules/manual voice action are **prepared, tested and committed**,
but **not installed in live Open WebUI**. Its existing sign-in page blocks app
configuration. No credentials were read, entered, copied or changed.

All other endpoint IDs, worker minimums and existing models are retained.
No cloud computer, CPU migration, new paid endpoint or volume was provisioned.

## Install together after admin sign-in

1. Preserve an application-consistent backup of the current Open WebUI data and
   existing application key using the established backup process. Never put the
   key or chat data into GitHub. Do not migrate or reinstall the host for this task.
2. Admin → Functions: create/replace `family_router` from
   `openwebui/functions/family_router.py` and enable it.
3. Workspace → Tools: update the existing **same ID** `family_media` from
   `openwebui/tools/family_media.py`. It now includes `ask_deep_reasoning` as well
   as the existing image/video methods. Preserve its current valves and key.
4. Admin → Functions: add the Action from `openwebui/actions/start_voice.py`.
   Enable it for the test workspace model. Its button appears on assistant messages.
5. The owner enters the existing RunPod key directly in any new component's
   valves. Do not copy keys through chat, source files or terminal commands.
6. Create a private test model based on `family_router.auto`, with the existing
   family system prompt, Native function calling, the `family_media` tool and
   the Start voice action. Attach the same tools/action to Fast, Pro and language
   workspace models if exposing those choices. Do not expose untested defaults.
7. Keep the existing speech configuration:
   STT `Systran/faster-whisper-large-v3` and language-selecting Piper TTS,
   both at `https://b8yk3ju5yc5kqx.api.runpod.ai/v1`.
8. Choose Auto in the chat before opening voice mode or the microphone. Press
   Start voice to warm it manually first if desired. The action sends one
   authenticated GET to `/v1/models`; it never raises minimum workers. A cold
   timeout is reported as unconfirmed startup, not a ready voice session.
9. Run the acceptance checks below before selecting Auto as the public default.

## Logic

| Trigger | Action | Result path |
| --- | --- | --- |
| Ordinary text or STT transcript | Fast Gemma E2B | Text; optional user-enabled Piper playback |
| Explicit deep/coding request, shared tool attached | Router emits one native `ask_deep_reasoning` call directly | Specialist answer returns to Fast for summary |
| A difficult task the rules miss | Coordinator can select `ask_deep_reasoning` | Same specialist/result path |
| Explicit deep task without the shared tool, or oversized specialist context | Direct existing Qwen Pro | No silent history truncation |
| Image attachment anywhere in retained context | Larger Gemma 31B | Vision answer with the same tools available |
| Image creation | Native `generate_image` → FLUX schnell/dev | Saved image + brief final reply |
| Video creation | Native `generate_video` → starting FLUX image if needed → Wan 2.2 | Saved video + brief final reply |
| Start voice button | One manual voice-endpoint probe | Existing Whisper/Piper wakes on demand |

Routing is rule-based, with Finnish/Swedish/English phrases and manual overrides;
it is not a learned difficulty estimator. Only Auto deterministically dispatches
explicit deep tasks. Manual model choices still have the specialist tools.
Old tool history does not permanently keep a new simple turn on Pro.

The router leaves tools to Open WebUI's native executor. It does not implement a
second tool-execution loop. The dedicated reasoning request has no tool definitions,
so it cannot recursively launch more modules. A successful deep call is not forced
again during that same user turn. Both typed input and voice STT use this flow.
The speech service handles recognition/synthesis; it is not a separate thinking LLM.

Final answers can be spoken through Open WebUI's voice playback. Images/videos
remain visible artifacts; voice gives a brief description. Actual browser audio,
microphone permissions and playback are still pending live acceptance.

## Optional DeepSeek activation — requires price approval

The default shared reasoning target remains the existing Qwen endpoint
`c3lm36gdhpctl2`, served model `family-brain`, style `qwen`.

`runpod/deepseek-endpoint.proposed.json` defines a separate **self-deployed**
DeepSeek-R1-Distill-Qwen-14B specialist on one AMPERE_48 GPU, min=0/max=1,
60-second idle timeout, 16K context, BF16 weights and `deepseek_r1` parser.
The checked pool price is **$1.22 per active hour**, including worker startup
and idle time, before tax and any storage charges. Hardware fit and cold-start
performance are proposed, not live validated. This is the distilled 14B model,
not the full 671B R1 model. No DeepSeek or Kimi endpoint has been created.

After the owner approves the additional endpoint and it passes a real request:

- Set `family_media.REASONING_ENDPOINT_ID` to its actual returned ID.
- Set `REASONING_MODEL=family-deepseek`, `REASONING_STYLE=deepseek_r1`.
- The tool sends one user message, temperature 0.6 and no tool definitions,
  following DeepSeek's guidance. It consumes only the final `content` field.
- Retain Qwen as the direct Pro fallback; do not overwrite or delete it.

## Verification

Local command: `python -m unittest discover -s tests -v`.
32 tests passed under Python 3.12, aiohttp 3.14.4 and pydantic 2.14.1.
CI pins the checked Open WebUI v0.12.4 dependency versions (aiohttp 3.14.5,
pydantic 2.13.4); that exact CI environment must also pass before merging.
Open WebUI storage and FastAPI HTML responses are test doubles; local tests
verify real module/HTTP transport without generating billed media.

Coverage includes streaming tool-call preservation, direct deep dispatch,
tool-result continuation, voice/text route parity, image/video module chains,
DeepSeek payload style, manual voice startup, timeouts, cancellation, submission
failures, input bounds, overload and keeping reasoning fields out of Fast/language
responses. Limits are per loaded instance, not a daily/account billing cap.
Submissions are never automatically retried or moved to another paid model.

Live Fast checks:

| Check | Queue / startup delay | Execution | Outcome |
| --- | --- | --- | --- |
| First E2B Finnish request | 182.287s | 5.416s | Answered; factual error about heat pumps, so quality review remains necessary |
| Finnish image request, native auto tools | 0.052s | 1.055s | Correct `generate_image` call and `tool_calls` finish reason; no actual image generated in this probe |
| Forced named reasoning tool | 0.052s | 9.417s | Ignored tool choice, produced text; deterministic dispatch replaces this approach |
| Swedish RAM/storage explanation | 0.056s | 5.847s | Coherent Swedish; returned a reasoning field despite requested non-thinking mode |
| Finnish continuation after a supplied successful image-tool result | 96.847s | 5.157s | Short final Finnish confirmation, no repeated call; result supplied as a fixture, not a real generated image |

Fast/language responses strip reasoning fields before display/playback. The
request still asks for non-thinking mode, but the live test shows that hidden
reasoning computation may occur. Do not claim guaranteed non-thinking inference,
instant startup, or uniformly better factual/language quality than larger models.

## Live acceptance still required

- Finnish, Swedish and English factual questions; review small-model accuracy.
- One explicit deep request in typed chat, then the same through the microphone.
  Confirm the specialist runs once and the summary returns to the same chat.
- One image and one video request from text and voice; verify saved files after
  reopening the chat. These incur existing media fees (quick image previously
  $0.003; checked Wan price $0.30/5s, plus a starting image if needed).
- Spoken final answer in all three languages; no URLs or trace read aloud.
- Cancel a queued job and confirm cancellation without a second submission.
- Let endpoints scale down; confirm typed chat does not wake voice.
- Preserve login, prior chats, web search, RAG and existing direct models.

Rollback: disable the new Function/Action and select an existing direct model.
Fast's prior Qwen settings are in `runpod/fast-endpoint.previous.json` for updating
the **same** endpoint if desired. Never create a duplicate from a rollback file.

## Checked primary sources

- [Gemma E2B model card](https://huggingface.co/google/gemma-4-E2B-it)
- [vLLM E2B recipe](https://recipes.vllm.ai/Google/gemma-4-E2B-it)
- [RunPod worker v2.30.1 source](https://github.com/runpod-workers/worker-vllm/tree/v2.30.1)
- [vLLM v0.32.0 Gemma tool template](https://github.com/vllm-project/vllm/blob/v0.32.0/examples/tool_chat_template_gemma4.jinja)
- [Open WebUI v0.12.4 action runtime](https://github.com/open-webui/open-webui/blob/v0.12.4/backend/open_webui/utils/actions.py)
- [Open WebUI v0.12.4 native tool runtime](https://github.com/open-webui/open-webui/blob/v0.12.4/backend/open_webui/utils/middleware.py)
- [DeepSeek R1 model instructions](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B)
- [vLLM v0.32.0 reasoning output support](https://docs.vllm.ai/en/v0.32.0/features/reasoning_outputs/)
