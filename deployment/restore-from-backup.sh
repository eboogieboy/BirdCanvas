#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run this restore with sudo."
  exit 1
fi
if [[ $# -ne 1 ]]; then
  echo "Usage: sudo deployment/restore-from-backup.sh /path/to/birdcanvas-backup-YYYYMMDD-HHMMSS.tar.gz"
  exit 1
fi

ARCHIVE="$(readlink -f "$1")"
[[ -f "$ARCHIVE" ]] || { echo "Backup not found: $ARCHIVE"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${SUDO_USER:-$(stat -c %U "$PROJECT_DIR")}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
BIRDNET_DIR="$TARGET_HOME/birdnet-go-app"
WORKDIR="$(mktemp -d /var/tmp/birdcanvas-restore.XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

if [[ -f "$ARCHIVE.sha256" ]]; then
  echo "Verifying SHA-256..."
  (cd "$(dirname "$ARCHIVE")" && sha256sum -c "$(basename "$ARCHIVE").sha256")
fi

echo "Extracting backup..."
tar -C "$WORKDIR" -xzf "$ARCHIVE"
[[ -f "$WORKDIR/metadata/manifest.json" ]] || { echo "Not a recognised BirdCanvas backup."; exit 1; }

echo
echo "This restores BirdCanvas runtime data, artwork, BirdNET-Go data and relevant system configuration."
echo "It does NOT restore .env/API keys, Samsung pairing tokens, rclone credentials or Wi-Fi credentials."
echo

systemctl stop canvasos.service 2>/dev/null || true
if systemctl list-unit-files birdnet-go.service >/dev/null 2>&1; then
  systemctl stop birdnet-go.service 2>/dev/null || true
fi

mkdir -p "$PROJECT_DIR/data" "$PROJECT_DIR/output/archive" "$PROJECT_DIR/output/current"
[[ -d "$WORKDIR/birdcanvas/data" ]] && rsync -a "$WORKDIR/birdcanvas/data/" "$PROJECT_DIR/data/"
[[ -d "$WORKDIR/birdcanvas/output/archive" ]] && rsync -a "$WORKDIR/birdcanvas/output/archive/" "$PROJECT_DIR/output/archive/"
[[ -d "$WORKDIR/birdcanvas/output/current" ]] && rsync -a "$WORKDIR/birdcanvas/output/current/" "$PROJECT_DIR/output/current/"
chown -R "$TARGET_USER:$TARGET_GROUP" "$PROJECT_DIR/data" "$PROJECT_DIR/output/archive" "$PROJECT_DIR/output/current"

if [[ -d "$WORKDIR/birdnet-go" ]]; then
  mkdir -p "$BIRDNET_DIR"
  rsync -a "$WORKDIR/birdnet-go/" "$BIRDNET_DIR/"
  chown -R "$TARGET_USER:$TARGET_GROUP" "$BIRDNET_DIR"
fi

if [[ -d "$WORKDIR/system/etc" ]]; then
  rsync -a "$WORKDIR/system/etc/" /etc/
fi

systemctl daemon-reload
if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  runuser -u "$TARGET_USER" -- bash -lc "cd '$PROJECT_DIR' && '$PROJECT_DIR/.venv/bin/python' code/display.py"
fi
systemctl restart canvasos.service 2>/dev/null || true
if systemctl list-unit-files birdnet-go.service >/dev/null 2>&1; then
  systemctl restart birdnet-go.service 2>/dev/null || true
fi

echo
echo "Restore complete."
echo "Now restore BirdCanvas .env, re-pair the Samsung Frame if needed, and configure rclone before enabling unattended operation."
