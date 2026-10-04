#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run this installer with:"
    echo "  sudo deployment/install-mirror-delivery.sh http://MIRROR-IP:5050/api/birdcanvas-panel TOKEN"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"

TARGET_URL="${1:-}"
TOKEN="${2:-}"

if [[ -z "$TARGET_URL" || -z "$TOKEN" ]]; then
    echo "Usage:"
    echo "  sudo deployment/install-mirror-delivery.sh http://MIRROR-IP:5050/api/birdcanvas-panel TOKEN"
    exit 2
fi

if [[ "$TARGET_URL" != http://* && "$TARGET_URL" != https://* ]]; then
    echo "Mirror push URL must begin with http:// or https://"
    exit 2
fi

if (( ${#TOKEN} < 24 )); then
    echo "Token is too short. Use at least 24 characters."
    exit 2
fi

sed \
    -e "s|__USER__|$TARGET_USER|g" \
    -e "s|__GROUP__|$TARGET_GROUP|g" \
    -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
    "$PROJECT_DIR/deployment/systemd/birdcanvas-mirror-delivery.service.template" \
    > /etc/systemd/system/birdcanvas-mirror-delivery.service

install -m 0644 \
    "$PROJECT_DIR/deployment/systemd/birdcanvas-mirror-delivery.timer" \
    /etc/systemd/system/birdcanvas-mirror-delivery.timer

umask 077
cat > /etc/default/birdcanvas-mirror-delivery <<EOF
BIRDCANVAS_MIRROR_PUSH_URL='$TARGET_URL'
BIRDCANVAS_MIRROR_PUSH_TOKEN='$TOKEN'
BIRDCANVAS_MIRROR_PUSH_TIMEOUT='15'
EOF

systemctl daemon-reload
systemctl enable --now birdcanvas-mirror-delivery.timer

echo
echo "Sending initial BirdCanvas panel..."
systemctl start birdcanvas-mirror-delivery.service

echo
echo "Mirror delivery installed."
echo "Target: $TARGET_URL"
systemctl status birdcanvas-mirror-delivery.timer --no-pager
