# Fresh Contabo host for Family AI

## Authorization and current state

On 2026-11-01 the owner explicitly instructed the assistant to erase everything
on the earlier Contabo server and start fresh for Family AI. This supersedes the
old project restriction against removing the Contabo application, for this host.
The existing Runpod GPU endpoints and Runpod chat-data volume are not part of
that erasure request.

Recorded target: `37.60.226.214`, `vmi3634750.contaboserver.net`.
Previous SSH account: `deploy`. Previous app: `/opt/roland-agent`.
Previous HTTPS host: `37-60-226-214.sslip.io`.
Verify these against the provider's current instance listing before a rebuild.
Reinstallation removes old applications, files and SSH credentials. No backup
of the disposable Contabo applications is required by the user's instruction.

**Nothing has been erased or installed remotely yet.** This session has no
connected SSH credential, and both documented Contabo control-panel addresses
returned "Site Unavailable" in the cloud browser. No suitable Contabo/SSH plugin
was found. Access is the current blocker, not authorization to replace the old app.

## Host reinstall

Use the Contabo control panel's Reinstall action for the verified target and
choose **Ubuntu 24.04 LTS**, without a paid control-panel add-on. The user must
enter any new authentication credential directly; never paste it into chat.
The provider's reinstall operation gives a truly fresh OS; this bootstrap script
does not pretend that deleting a few app directories is an OS reinstall.

## CPU installation once access is available

Transfer this directory to `/opt/family-ai/deploy/contabo` on the fresh host.
Run `sudo bash bootstrap.sh` there. It installs Docker from the official Docker
Ubuntu repository if missing, pulls Open WebUI v0.12.4 and Caddy, and starts only
Open WebUI bound to localhost. It does not start any CPU language-model service.

Open WebUI's own entrypoint generates and persists its application secret inside
the data volume on a genuinely fresh install. For a migration, restore the old
secret before first start instead, as described below. No secret values belong
in these source files.

Before exposing the server publicly, either restore the existing Runpod instance
or let the owner create the first admin through an SSH tunnel:

```powershell
ssh -L 3000:127.0.0.1:3000 root@37.60.226.214
```

Then open `http://localhost:3000` on that same computer. Replace `root` with the
verified login account if the provider uses another one. In v0.12.4 the first
admin can register even with `ENABLE_SIGNUP=false`; subsequent sign-ups are
disabled. Do not publish an empty first-admin registration screen.

## Preserve the Runpod app's existing data

The source is CPU pod `ix476koa61pd4o`, network volume `vevppjlc9a`, directory
`/app/backend/data`. The current source version/digest must be checked before
restoration. Start with the exact same version to avoid combining migration
with a database upgrade.

1. Make a consistent backup of the entire source data directory while writes are
   stopped, or using the app's supported consistent backup procedure. Do not copy
   a live SQLite database alone: WAL files may contain recent writes.
2. Preserve its current application key. The v0.12.4 container normally keeps
   `.webui_secret_key` under `/app/backend`, outside the data mount, unless
   `WEBUI_SECRET_KEY` or a custom key file is already configured. Verify the
   source's actual key mechanism without printing its contents.
3. Transfer the backup and key directly between authorized hosts using encrypted
   access, never through GitHub, chat, or these scripts. The destination uses
   `/app/backend/data/.webui_secret_key` so the same key survives container updates.
4. Restore before exposing the destination; verify login, chats, uploads, settings,
   saved GPU credentials, RAG, voice, media and streaming. If preserving the source
   key is impossible, the owner must re-enter affected credentials in the UI.

## GPU connections

| Function | URL | Served model |
| --- | --- | --- |
| Fast | `https://api.runpod.ai/v2/52cjk52hgbwag1/openai/v1` | `family-fast` |
| Pro | `https://api.runpod.ai/v2/c3lm36gdhpctl2/openai/v1` | `family-brain` |
| Finnish/Swedish | `https://api.runpod.ai/v2/936leprwfzb9gr/openai/v1` | `family-gemma` |
| Voice | `https://b8yk3ju5yc5kqx.api.runpod.ai/v1` | Existing Whisper/Piper setup |

Keep the existing media tool. Install the routing Function from
`openwebui/functions/family_router.py` after the baseline app works; the owner
enters its Runpod key directly and `FAST_ENDPOINT_ID` is `52cjk52hgbwag1`.
Actual UI tool-loop/vision testing is still required.

## HTTPS and cutover

The deployment defaults to the previously used hostname
`37-60-226-214.sslip.io`. Verify that it still resolves to the target IP.
Override the non-secret `FAMILY_AI_HOST` variable for another chosen hostname.
After admin/data setup, run `docker compose --profile public up -d` and verify
the HTTPS certificate and streaming. Only Caddy publishes 80/443; the app's
3000 mapping stays loopback-only. Docker-published ports can bypass UFW, so do
not rely on UFW to hide an accidentally published app port.

After the destination passes verification, stop the Runpod CPU pod to end its
$0.08/hour compute charge. Retain the source data volume for rollback until its
backup is verified. Do not terminate the CPU pod before preserving its key,
because the key may live on its container disk rather than the network volume.
Storage can continue billing even after compute is stopped.

## Verification performed locally

- YAML parses; service ports, persistent data/key path and private bootstrap are checked.
- Bash syntax checked; no destructive command is included in bootstrap.
- Docker runtime is unavailable locally; image pulling, Compose runtime validation,
  TLS, restoration and host installation have not been performed.

Sources checked 2026-11-01:

- [Docker Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/)
- [Open WebUI v0.12.4 entrypoint](https://github.com/open-webui/open-webui/blob/v0.12.4/backend/start.sh)
- [Open WebUI v0.12.4 signup](https://github.com/open-webui/open-webui/blob/v0.12.4/backend/open_webui/routers/auths.py)
- [Open WebUI migration](https://docs.openwebui.com/tutorials/maintenance/database/)
- [Contabo reinstall instructions](https://help.contabo.com/en/support/solutions/articles/103000271913-how-do-i-install-my-contabo-server-)
