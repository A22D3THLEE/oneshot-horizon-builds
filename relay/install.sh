#!/usr/bin/env bash
# Installs the Horizon play-with-friends relay as a systemd service (Ubuntu/Debian, x86_64).
#   curl -fsSL https://github.com/A22D3THLEE/oneshot-horizon-builds/releases/download/relay/install.sh | sudo bash
# Options (environment): PORT=7000 (TCP port friends reach), OPEN_FIREWALL=1 (also run "ufw allow" for it).
set -euo pipefail
REPO="A22D3THLEE/oneshot-horizon-builds"
PORT="${PORT:-7000}"
[ "$(id -u)" = 0 ] || { echo "Run as root (sudo)."; exit 1; }
[ "$(uname -m)" = x86_64 ] || { echo "This build is for x86_64 only (this machine: $(uname -m))."; exit 1; }
base="https://github.com/$REPO/releases/download/relay"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/horizon-relay" "$base/horizon-relay-linux-x86_64"
want=$(curl -fsSL "$base/horizon-relay-linux-x86_64.sha256" | tr -d '[:space:]')
have=$(sha256sum "$tmp/horizon-relay" | cut -d' ' -f1)
[ "$want" = "$have" ] || { echo "Checksum mismatch, nothing installed."; exit 1; }
install -m 0755 "$tmp/horizon-relay" /usr/local/bin/horizon-relay
cat > /etc/systemd/system/horizon-relay.service <<UNIT
[Unit]
Description=Horizon play-with-friends relay
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/horizon-relay
Environment=PORT=$PORT
DynamicUser=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now horizon-relay
if [ "${OPEN_FIREWALL:-0}" = 1 ] && command -v ufw >/dev/null; then ufw allow "$PORT"/tcp; fi
sleep 1
systemctl is-active horizon-relay
echo "Relay is running on TCP port $PORT. Open this port in your hosting panel's firewall too, if it has one."
