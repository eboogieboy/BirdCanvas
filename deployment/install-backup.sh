#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run with: sudo bash deployment/install-backup.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${SUDO_USER:-$(stat -c %U "$PROJECT_DIR")}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
CONFIG=/etc/default/birdcanvas-backup

apt-get update
apt-get install -y rclone rsync

install -m 0755 "$PROJECT_DIR/deployment/backup-to-rclone.sh" /usr/local/sbin/birdcanvas-backup
install -m 0644 "$PROJECT_DIR/deployment/systemd/birdcanvas-backup.service" /etc/systemd/system/birdcanvas-backup.service
install -m 0644 "$PROJECT_DIR/deployment/systemd/birdcanvas-backup.timer" /etc/systemd/system/birdcanvas-backup.timer

if [[ ! -f "$CONFIG" ]]; then
cat > "$CONFIG" <<EOF
BIRDCANVAS_PROJECT_DIR=$PROJECT_DIR
BIRDCANVAS_USER=$TARGET_USER
BIRDCANVAS_HOME=$TARGET_HOME
BIRDCANVAS_BIRDNET_DIR=$TARGET_HOME/birdnet-go-app
BIRDCANVAS_BIRDNET_SERVICE=birdnet-go.service
BIRDCANVAS_RCLONE_REMOTE=
BIRDCANVAS_INCLUDE_BIRDNET_CLIPS=0
BIRDCANVAS_DAILY_RETENTION_DAYS=14
BIRDCANVAS_WEEKLY_RETENTION_DAYS=56
BIRDCANVAS_LOCAL_RETENTION_DAYS=2
BIRDCANVAS_LOCAL_BACKUP_DIR=/var/backups/birdcanvas
EOF
chmod 0600 "$CONFIG"
fi

systemctl daemon-reload
systemctl disable --now birdcanvas-backup.timer 2>/dev/null || true

echo
echo "BirdCanvas backup tooling installed."
echo "The nightly timer is NOT enabled yet."
echo "Configure an rclone Google Drive remote as $TARGET_USER, then run:"
echo "  sudo bash deployment/configure-backup.sh 'REMOTE:BirdCanvas Backups'"
