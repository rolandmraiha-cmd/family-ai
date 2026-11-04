# Rules for AI assistants on this project

Read `README.md` first, then `docs/history.md`.

## The owner
- Usually on a phone. Keep replies short and simple; Swedish or English is fine.
- The assistant must speak Swedish, Finnish and English. Finnish quality is the hardest part, so test Finnish after any model change.

## Hard rules
- **Never write passwords, API keys or tokens** into files, commits, chats or forms. The owner enters new credentials in RunPod or Open WebUI when needed. Reuse existing authorized access securely in server memory.
- Owner-performed login is not an acceptance prerequisite when the tests can be completed through existing authorized access. Run those tests and report what was actually tested and what remains unverified. Keep application authentication enabled; do not claim browser/device testing from server-side checks.
- Necessary project work and testing on the existing approved resources is pre-authorized up to **USD 7 total for the authorized work/test run**, including estimated GPU idle costs. No separate cost approval is needed within that cumulative limit. Track and report estimated/known costs; ask before exceeding USD 7. Do not split work into multiple runs to evade the limit.
- The allowance does not authorize resources outside the README list or new recurring commitments. Obtain approval for those and for spending above USD 7.
- Change only the resources listed in `README.md`. Reuse the existing IDs instead of creating duplicates.
- Don't permanently delete data; ask the owner to do it.

## Gotchas learned the hard way
- RunPod `update-endpoint` with `env` **replaces the whole env**. `MAX_NUM_BATCHED_TOKENS` is shown as `[redacted]` but its value is `8192`: always send it.
- An env change cuts a new release, but old workers keep serving or failing jobs. Set max workers to 0 and then back to 1 to roll them.
- "Initializing" workers are pre-staged and not billed; only "Running" workers cost money.
- Qwen3.8 emits XML tool calls: `TOOL_CALL_PARSER=qwen3_coder`. `hermes` silently drops them, which gives empty answers.
- Gemma 4 31B on an A40 runs out of memory at 16k context, so keep `MAX_MODEL_LEN=8192`. Open WebUI `WEB_FETCH_MAX_CONTENT_LENGTH=4000` keeps fetched web pages from overflowing it.
- Open WebUI tools: with native function calling, `"type": "message"` events are dropped. Show images or files with `chat:message:files` and video with an inline `HTMLResponse` embed (see `openwebui/tools/family_media.py`).
- A RunPod load balancer polls `/ping`; the `HEALTH_CHECK_PATH` env is ignored.
- The first request to a cold endpoint through Open WebUI can return a 524 timeout (about 100 s proxy limit). Retrying when it's warm works.
