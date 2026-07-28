#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run this script with sudo."
    exit 1
fi

TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"

systemctl disable --now canvasos.service 2>/dev/null || true
systemctl disable --now birdcanvas-morning.timer birdcanvas-midday.timer birdcanvas-evening.timer 2>/dev/null || true
rm -f /etc/systemd/system/canvasos.service
rm -f /etc/systemd/system/birdcanvas-compose@.service
rm -f /etc/systemd/system/birdcanvas-morning.timer
rm -f /etc/systemd/system/birdcanvas-midday.timer
rm -f /etc/systemd/system/birdcanvas-evening.timer
rm -f "$TARGET_HOME/.config/autostart/canvasos-kiosk.desktop"
systemctl daemon-reload

echo "CanvasOS automatic startup has been removed."
echo "The project, artwork library and data were not deleted."
