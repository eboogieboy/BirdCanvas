#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo."
  exit 1
fi
if [[ $# -ne 1 || "$1" != *:* ]]; then
  echo "Usage: sudo deployment/configure-backup.sh 'REMOTE:BirdCanvas Backups'"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG=/etc/default/birdcanvas-backup
[[ -f "$CONFIG" ]] || { echo "Run sudo deployment/install-backup.sh first."; exit 1; }

# shellcheck disable=SC1090
source "$CONFIG"
TARGET_USER="${BIRDCANVAS_USER:-${SUDO_USER:-$(stat -c %U "$PROJECT_DIR")}}"
TARGET_HOME="${BIRDCANVAS_HOME:-$(getent passwd "$TARGET_USER" | cut -d: -f6)}"
REMOTE="$1"
REMOTE_NAME="${REMOTE%%:*}:"

if ! runuser -u "$TARGET_USER" -- env HOME="$TARGET_HOME" rclone lsd "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "rclone remote $REMOTE_NAME is not available for $TARGET_USER."
  echo "Run: sudo -u $TARGET_USER -H rclone config"
  exit 1
fi

python3 - "$CONFIG" "$REMOTE" <<'PY'
from pathlib import Path
import sys
path=Path(sys.argv[1])
remote=sys.argv[2]
lines=path.read_text().splitlines()
out=[]
found=False
for line in lines:
    if line.startswith("BIRDCANVAS_RCLONE_REMOTE="):
        out.append("BIRDCANVAS_RCLONE_REMOTE="+remote)
        found=True
    else:
        out.append(line)
if not found:
    out.append("BIRDCANVAS_RCLONE_REMOTE="+remote)
path.write_text("\n".join(out)+"\n")
PY
chmod 0600 "$CONFIG"

systemctl daemon-reload
systemctl enable --now birdcanvas-backup.timer
echo "Running the first backup now..."
systemctl start birdcanvas-backup.service
systemctl status birdcanvas-backup.service --no-pager
echo
systemctl list-timers birdcanvas-backup.timer --no-pager
