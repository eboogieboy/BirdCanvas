#!/usr/bin/env bash
# Idempotently install a separate, non-rebooting Wi-Fi watchdog.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo: sudo bash deployment/install-wifi-recovery.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v nmcli >/dev/null 2>&1; then
    echo "NetworkManager (nmcli) is not installed; skipping Wi-Fi watchdog."
    exit 0
fi

install -m 0755 "$SCRIPT_DIR/wifi-recovery.sh" /usr/local/sbin/birdcanvas-wifi-recovery
install -m 0644 "$SCRIPT_DIR/systemd/birdcanvas-wifi-recovery.service" /etc/systemd/system/birdcanvas-wifi-recovery.service
install -m 0644 "$SCRIPT_DIR/systemd/birdcanvas-wifi-recovery.timer" /etc/systemd/system/birdcanvas-wifi-recovery.timer
systemctl daemon-reload
systemctl enable --now birdcanvas-wifi-recovery.timer
echo "BirdCanvas Wi-Fi recovery timer installed and enabled."
echo "Check: systemctl status birdcanvas-wifi-recovery.timer"
echo "Logs:  journalctl -u birdcanvas-wifi-recovery.service -n 30 --no-pager"
