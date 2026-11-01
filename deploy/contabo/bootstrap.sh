#!/usr/bin/env bash
# Run on the intended, freshly reinstalled Contabo host only.
# This installs the CPU interface; it never deletes data or reinstalls the OS.
set -euo pipefail

if [[ $(id -u) != 0 ]]; then
    echo "Run this script with sudo on the fresh target server." >&2
    exit 1
fi
source /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_ID" != 24.04 ]]; then
    echo "This bootstrap targets Ubuntu 24.04 LTS." >&2
    exit 1
fi
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ! -f compose.yaml || ! -f Caddyfile ]]; then
    echo "Keep compose.yaml and Caddyfile alongside this script." >&2
    exit 1
fi

if ! command -v docker >/dev/null; then
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker
docker compose version
docker compose config --quiet
docker compose pull webui caddy
docker compose up -d --wait --wait-timeout 600 webui
echo "Private bootstrap is ready on 127.0.0.1:3000. Public HTTPS has NOT started."
echo "Restore the existing Runpod data/key or create the admin through an SSH tunnel."
echo "After login/settings are verified: docker compose --profile public up -d"
