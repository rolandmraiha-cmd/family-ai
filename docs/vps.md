# Contabo VPS: the always-on part

Since 2026-11-03 the chat app runs on the owner's Contabo VPS instead of a RunPod CPU pod. All AI still runs on RunPod GPUs, which scale to zero.

**URL:** https://37-60-226-214.sslip.io (sign-up off; new users are "pending" until the admin approves them)

## The server

| | |
|---|---|
| Machine | Contabo Cloud VPS 4: 4 vCPU, 8 GB RAM, 100 GB disk, 2 GB swap, EU |
| OS | Ubuntu 24.04, Docker + Compose |
| Address | 37.60.226.214 (the domain is the free `sslip.io` name for that IP) |
| Project folder | `/opt/family-ai`, owned by user `deploy`, Compose project `familyai` |
| Config in this repo | `vps/docker-compose.yml` and `vps/Caddyfile` are copies of the live files. The server's `.env` and `data/` are never copied here. |

## What runs

| Container | What it does |
|---|---|
| `openwebui` | Open WebUI v0.12.4, a fresh install with no old chats. Only reachable from the server itself (127.0.0.1:3000). Data in `/opt/family-ai/data/openwebui`. |
| `caddy` | HTTPS with an automatic Let's Encrypt certificate, HTTP/3. Forwards everything to Open WebUI, except `/preview/`, which serves the integrated review UI from `web/build`. |
| `gateway` | Off (Compose profile `gateway`). Its job/budget role moves into the `family_backend` plugins from branch `codex/shared-model-modules`. |

## Connections in Open WebUI (entered by the owner; keys only in Open WebUI)

| Model id | Endpoint | Base URL |
|---|---|---|
| `family-gemma` | `936leprwfzb9gr` | `https://api.runpod.ai/v2/936leprwfzb9gr/openai/v1` |
| `family-brain` | `c3lm36gdhpctl2` | `https://api.runpod.ai/v2/c3lm36gdhpctl2/openai/v1` |
| `family-fast` | `52cjk52hgbwag1` | `https://api.runpod.ai/v2/52cjk52hgbwag1/openai/v1` |
| Voice STT / TTS | `b8yk3ju5yc5kqx` | `https://b8yk3ju5yc5kqx.api.runpod.ai/v1`, STT `Systran/faster-whisper-large-v3`, TTS `speaches-ai/piper-fi_FI-harri-medium` voice `harri` |

Model ids are typed in each connection, because a sleeping endpoint can't answer `/models`. Don't press "verify connection": it wakes a GPU.

## Security

- SSH is key-only; root can log in only with a key. Password login is off (`/etc/ssh/sshd_config.d/01-familyai-hardening.conf`). **Never turn password login back on.**
- Firewall (ufw): only 22, 80 and 443 (tcp + udp) are open. Docker ports skip ufw, so the app port is bound to 127.0.0.1 only.
- fail2ban guards SSH.
- AI assistants work as user `deploy` (`ssh deploy@37.60.226.214`), not root. `deploy` can run Docker but has no sudo.

## Everyday commands (as `deploy`, in `/opt/family-ai`)

```bash
docker compose --profile public ps                 # what is running
docker compose logs -f openwebui                   # Open WebUI log
docker compose --profile public pull && docker compose --profile public up -d   # after changing OWUI_TAG in .env
```

The server folder is its own git repo (local commits only). When you change `vps/` here, copy the change to the server too, and the other way round.

## Done so far (2026-11-03 → 04)

1. Read-only inspection of the freshly reinstalled server.
2. Hardening: firewall, fail2ban, swap, `deploy` user, then key-only SSH (tested by the owner).
3. Fresh Open WebUI + Caddy on the VPS; the admin account was created over an SSH tunnel before the site went public.
4. The owner connected the three chat models and voice. First test: `family-gemma` answered in good Finnish after about 1.5 min of cold start.
5. Installed the reviewed router, media tool, lifecycle API and manual voice Action;
   created private `family-auto`. Connected `/preview/` to native authentication,
   saved chats and tools, with ledger-controlled speech. No provider request or
   default/configuration change was made. See [acceptance status](contabo-integration.md).

## Next

- Complete chat/routing, images/video, cancellation, saved media and all three
  voice-language checks under the owner's USD 7 test allowance. Existing
  authorized access may be used; report browser/device checks separately.
- Keep `/` and the public default until those checks pass; PR #2 remains draft.
- Backups of `/opt/family-ai/data` (nightly, off the server).
- The owner: the Oct 10 Contabo snapshot expires 2026-11-09; back up the PC's SSH key.
