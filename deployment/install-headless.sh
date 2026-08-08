#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run this installer with:"
    echo "  sudo deployment/install-headless.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"

HOSTNAME_VALUE="${BIRDCANVAS_HOSTNAME:-birdcanvas}"

if [[ ! -f "$PROJECT_DIR/code/server.py" ]]; then
    echo "BirdCanvas code/server.py was not found in:"
    echo "  $PROJECT_DIR"
    exit 1
fi

echo
echo "BirdCanvas headless installation"
echo "-------------------------------"
echo "Project: $PROJECT_DIR"
echo "User:    $TARGET_USER"
echo "Host:    $HOSTNAME_VALUE"
echo

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    avahi-daemon

echo
echo "Creating BirdCanvas Python environment..."

if [[ ! -d "$PROJECT_DIR/.venv" ]]; then
    sudo -u "$TARGET_USER" \
        python3 -m venv "$PROJECT_DIR/.venv"
fi

sudo -u "$TARGET_USER" \
    "$PROJECT_DIR/.venv/bin/python" \
    -m pip install --upgrade pip

sudo -u "$TARGET_USER" \
    "$PROJECT_DIR/.venv/bin/pip" \
    install -r "$PROJECT_DIR/requirements.txt"

echo
echo "Checking Samsung CLI..."

if [[ ! -x "$PROJECT_DIR/.venv/bin/samsungtv" ]]; then
    echo "ERROR: samsungtv CLI was not installed."
    exit 1
fi

"$PROJECT_DIR/.venv/bin/samsungtv" --help >/dev/null

echo "Samsung CLI installed successfully."

# ---------------------------------------------------------
# Build current GalleryOS pages
# ---------------------------------------------------------

echo
echo "Building GalleryOS pages..."

sudo -u "$TARGET_USER" bash -lc \
    "cd '$PROJECT_DIR' && '$PROJECT_DIR/.venv/bin/python' code/display.py"

# ---------------------------------------------------------
# GalleryOS web server
# ---------------------------------------------------------

SERVICE_SOURCE="$PROJECT_DIR/deployment/systemd/canvasos.service.template"

sed \
    -e "s|__USER__|$TARGET_USER|g" \
    -e "s|__GROUP__|$TARGET_GROUP|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$SERVICE_SOURCE" \
    > /etc/systemd/system/canvasos.service

# ---------------------------------------------------------
# Artwork generation service
# ---------------------------------------------------------

COMPOSE_SOURCE="$PROJECT_DIR/deployment/systemd/birdcanvas-compose@.service.template"

sed \
    -e "s|__USER__|$TARGET_USER|g" \
    -e "s|__GROUP__|$TARGET_GROUP|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$COMPOSE_SOURCE" \
    > /etc/systemd/system/birdcanvas-compose@.service

# ---------------------------------------------------------
# Only the 04:00 previous-day generation timer
# ---------------------------------------------------------

install -m 0644 \
    "$PROJECT_DIR/deployment/systemd/birdcanvas-morning.timer" \
    /etc/systemd/system/birdcanvas-morning.timer

# Remove/disable obsolete multi-edition timers if they exist
systemctl disable --now birdcanvas-midday.timer 2>/dev/null || true
systemctl disable --now birdcanvas-evening.timer 2>/dev/null || true

rm -f \
    /etc/systemd/system/birdcanvas-midday.timer \
    /etc/systemd/system/birdcanvas-evening.timer

# ---------------------------------------------------------
# Permissions
# ---------------------------------------------------------

chown -R \
    "$TARGET_USER:$TARGET_GROUP" \
    "$PROJECT_DIR"

# ---------------------------------------------------------
# Hostname
# ---------------------------------------------------------

if [[ "$(hostname)" != "$HOSTNAME_VALUE" ]]; then
    hostnamectl set-hostname "$HOSTNAME_VALUE"
fi

# ---------------------------------------------------------
# Services
# ---------------------------------------------------------

systemctl enable --now avahi-daemon

systemctl daemon-reload

systemctl enable --now canvasos.service
systemctl enable --now birdcanvas-morning.timer

echo
echo "Checking GalleryOS..."

for _ in $(seq 1 20); do
    if curl \
        --silent \
        --fail \
        --max-time 2 \
        http://127.0.0.1:8000/ \
        >/dev/null
    then
        break
    fi

    sleep 1
done

echo
echo "BirdCanvas headless installation complete."
echo
echo "Gallery:"
echo "  http://${HOSTNAME_VALUE}.local:8000/gallery/"
echo
echo "Phone control:"
echo "  http://${HOSTNAME_VALUE}.local:8000/control/"
echo
echo "Daily artwork:"
echo "  04:00 Europe/London"
echo
echo "Samsung Frame:"
echo "  Controlled through BirdCanvas when enabled in .env"
echo
echo "No Chromium kiosk or local display has been installed."
echo
