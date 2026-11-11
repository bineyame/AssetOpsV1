#!/usr/bin/env bash
# One-time setup of an Ubuntu VPS for AssetOps work (see .agent/vps-migration-plan.md).
# Installs: git, Docker Engine + compose plugin, Python 3.12 (+venv), Node 24, PowerShell 7, PostgreSQL 16 client.
# Safe to re-run. Run as a sudo-capable user:  bash tools/vps-setup-ubuntu.sh
set -euo pipefail

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
. /etc/os-release
echo "Ubuntu ${VERSION_ID} (${VERSION_CODENAME})"

$SUDO apt-get update -y
$SUDO apt-get install -y ca-certificates curl gnupg git lsb-release software-properties-common apt-transport-https wget

# Docker Engine + compose plugin (official docker.com repository)
if ! command -v docker >/dev/null 2>&1; then
  $SUDO install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
  $SUDO apt-get update -y
  $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  $SUDO usermod -aG docker "$USER" || true
  echo "NOTE: log out and back in (or run 'newgrp docker') so docker works without sudo."
fi

# Python 3.12 (Ubuntu 24.04 ships it; older releases use the deadsnakes PPA)
if ! command -v python3.12 >/dev/null 2>&1; then
  $SUDO add-apt-repository -y ppa:deadsnakes/ppa
  $SUDO apt-get update -y
fi
$SUDO apt-get install -y python3.12 python3.12-venv python3.12-dev build-essential

# Node 24 (NodeSource)
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | cut -d. -f1 | tr -d v)" -lt 24 ]; then
  curl -fsSL https://deb.nodesource.com/setup_24.x | $SUDO -E bash -
  $SUDO apt-get install -y nodejs
fi

# PowerShell 7 (Microsoft repository) for tools/check-all.ps1 and tools/check-architecture.ps1
if ! command -v pwsh >/dev/null 2>&1; then
  wget -q "https://packages.microsoft.com/config/ubuntu/${VERSION_ID}/packages-microsoft-prod.deb" -O /tmp/packages-microsoft-prod.deb
  $SUDO dpkg -i /tmp/packages-microsoft-prod.deb
  $SUDO apt-get update -y
  $SUDO apt-get install -y powershell
fi

# PostgreSQL 16 client (pg_dump / pg_restore / psql) from the PGDG repository
if ! command -v pg_restore >/dev/null 2>&1 || ! pg_restore --version | grep -q " 16\."; then
  $SUDO install -d /usr/share/postgresql-common/pgdg
  curl -fsSL -o /tmp/pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc
  $SUDO cp /tmp/pgdg.asc /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc
  echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" \
    | $SUDO tee /etc/apt/sources.list.d/pgdg.list >/dev/null
  $SUDO apt-get update -y
  $SUDO apt-get install -y postgresql-client-16
fi

echo
echo "Versions:"
git --version
docker --version || true
docker compose version || true
python3.12 --version
node --version
npm --version
pwsh --version
pg_restore --version
echo
echo "Next (see .agent/vps-migration-plan.md): clone the repo, 'docker compose up -d', create .venv and run npm ci in frontend/."
