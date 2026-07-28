#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run this installer with sudo: sudo deployment/install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
HOSTNAME_VALUE="${CANVASOS_HOSTNAME:-gallery}"

if [[ ! -f "$PROJECT_DIR/code/server.py" ]]; then
    echo "code/server.py was not found in $PROJECT_DIR"
    echo "Place the deployment folder at the top level of the BirdCanvas repository."
    exit 1
fi

echo "Installing CanvasOS from: $PROJECT_DIR"
echo "Runtime user: $TARGET_USER"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip curl avahi-daemon unclutter

if apt-cache show chromium >/dev/null 2>&1; then
    apt-get install -y chromium
elif apt-cache show chromium-browser >/dev/null 2>&1; then
    apt-get install -y chromium-browser
else
    echo "Chromium package was not found. Install Chromium manually before rebooting."
fi

sudo -u "$TARGET_USER" python3 -m venv "$PROJECT_DIR/.venv"
sudo -u "$TARGET_USER" "$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip
if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
    sudo -u "$TARGET_USER" "$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
fi

# Build the current static display and phone pages once before enabling startup.
sudo -u "$TARGET_USER" bash -lc "cd '$PROJECT_DIR' && '$PROJECT_DIR/.venv/bin/python' code/display.py"

SERVICE_SOURCE="$PROJECT_DIR/deployment/systemd/canvasos.service.template"
sed \
    -e "s|__USER__|$TARGET_USER|g" \
    -e "s|__GROUP__|$TARGET_GROUP|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$SERVICE_SOURCE" >/etc/systemd/system/canvasos.service

COMPOSE_SERVICE_SOURCE="$PROJECT_DIR/deployment/systemd/birdcanvas-compose@.service.template"
sed \
    -e "s|__USER__|$TARGET_USER|g" \
    -e "s|__GROUP__|$TARGET_GROUP|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$COMPOSE_SERVICE_SOURCE" >/etc/systemd/system/birdcanvas-compose@.service

install -m 0644 \
    "$PROJECT_DIR/deployment/systemd/birdcanvas-morning.timer" \
    "$PROJECT_DIR/deployment/systemd/birdcanvas-midday.timer" \
    "$PROJECT_DIR/deployment/systemd/birdcanvas-evening.timer" \
    /etc/systemd/system/

AUTOSTART_DIR="$TARGET_HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
sed -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$PROJECT_DIR/deployment/kiosk/canvasos-kiosk.desktop.template" \
    >"$AUTOSTART_DIR/canvasos-kiosk.desktop"

chmod +x \
    "$PROJECT_DIR/deployment/kiosk/start-kiosk.sh" \
    "$PROJECT_DIR/deployment/scripts/diagnose.sh" \
    "$PROJECT_DIR/deployment/uninstall.sh"
chown -R "$TARGET_USER:$TARGET_GROUP" "$PROJECT_DIR" "$AUTOSTART_DIR/canvasos-kiosk.desktop"

if [[ "$(hostname)" != "$HOSTNAME_VALUE" ]]; then
    hostnamectl set-hostname "$HOSTNAME_VALUE"
fi

systemctl enable --now avahi-daemon
systemctl daemon-reload
systemctl enable --now canvasos.service
systemctl enable --now \
    birdcanvas-morning.timer \
    birdcanvas-midday.timer \
    birdcanvas-evening.timer

# Wait briefly and report whether the server is reachable.
for _ in $(seq 1 20); do
    if curl --silent --fail --max-time 2 http://127.0.0.1:8000/ >/dev/null; then
        break
    fi
    sleep 1
done

echo
echo "CanvasOS appliance installation is complete."
echo "Display:       http://${HOSTNAME_VALUE}.local:8000/"
echo "Phone control: http://${HOSTNAME_VALUE}.local:8000/control/"
echo "Library:       http://${HOSTNAME_VALUE}.local:8000/gallery/"
echo "BirdCanvas:    04:00 morning, 12:00 midday, 17:00 evening"
echo
echo "Reboot to start Chromium kiosk mode: sudo reboot"
