# Contabo integration — 2026-11-04 review deployment

The existing VPS runs Open WebUI v0.12.4 and Caddy in `/opt/family-ai`.
`/preview/` now serves the real review UI; `/` remains native Open WebUI. PR #2
stays draft. The initial installation made no inference request. Subsequent live
acceptance uses the owner's USD 7 allowance below. No new paid resource,
RunPod configuration change, SSH/firewall change or data deletion was made.

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
| Node 24 browser-helper suite | 6 tests pass: stable turns/history, vision input, owned file URLs, output filtering, cycles and bounded PCM |
| Existing Linux app container | All 97 Python tests pass without installing dependencies |
| Live native health | `/health` returns 200 JSON |
| Live added routes without login | GET capabilities and POST manual voice session return 401 JSON |
| Native authenticated control API | Capabilities, policy and usage return 200 using a short-lived session held only in server memory through authorized SSH; native verification remains enabled |
| Actual phone-sized preview | Renders real signed-out gate; message input disabled; no inference submitted |
| Stored Open WebUI configuration | Same SHA-256 fingerprint before/after installation and restart |
| RunPod read-only check | All four existing endpoints min0/max1; no running workers at inspection; no inference used to check health |
| Signed-in chat/tools/media/voice | Pending live acceptance; owner authorizes existing-access testing up to USD 7 total |

Local checks use test identities/provider seams. They do not establish live
cookie isolation, model quality, actual GPU cancellation, durable media playback
or a working microphone/speaker. Earlier RunPod probes in historical notes are
not acceptance of this fresh Contabo interface.

## Next acceptance run

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

1. Finnish, Swedish and English ordinary chat; verify actual saved answers.
2. Qwen specialist and Fast continuation in the same chat; image understanding
   through larger Gemma; explicit model choices and progress.
3. Image/video generation, reload and reopen owned files; request cancellation,
   inspect confirmed/uncertain result and verify no replacement submission.
4. Manual microphone and Piper in all three languages, permission denial,
   interruption and reopened audio. Check whether the existing wrapper needs
   its reviewed explicit-language update before changing that endpoint.
5. Typed chat with speech off: observe no speech inference; observe actual
   running workers return to zero after configured idle time.

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
