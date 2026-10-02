#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_FILE="/etc/default/birdcanvas-backup"
if [[ ! -r "$CONFIG_FILE" ]]; then
  echo "Missing $CONFIG_FILE"
  exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

: "${BIRDCANVAS_PROJECT_DIR:?Missing BIRDCANVAS_PROJECT_DIR}"
: "${BIRDCANVAS_USER:?Missing BIRDCANVAS_USER}"
: "${BIRDCANVAS_HOME:?Missing BIRDCANVAS_HOME}"
: "${BIRDCANVAS_BIRDNET_DIR:?Missing BIRDCANVAS_BIRDNET_DIR}"
: "${BIRDCANVAS_RCLONE_REMOTE:?Missing BIRDCANVAS_RCLONE_REMOTE}"

BIRDCANVAS_BIRDNET_SERVICE="${BIRDCANVAS_BIRDNET_SERVICE:-birdnet-go.service}"
BIRDCANVAS_INCLUDE_BIRDNET_CLIPS="${BIRDCANVAS_INCLUDE_BIRDNET_CLIPS:-0}"
BIRDCANVAS_DAILY_RETENTION_DAYS="${BIRDCANVAS_DAILY_RETENTION_DAYS:-14}"
BIRDCANVAS_WEEKLY_RETENTION_DAYS="${BIRDCANVAS_WEEKLY_RETENTION_DAYS:-56}"
BIRDCANVAS_LOCAL_RETENTION_DAYS="${BIRDCANVAS_LOCAL_RETENTION_DAYS:-2}"
BIRDCANVAS_LOCAL_BACKUP_DIR="${BIRDCANVAS_LOCAL_BACKUP_DIR:-/var/backups/birdcanvas}"

PROJECT_DIR="$BIRDCANVAS_PROJECT_DIR"
TARGET_USER="$BIRDCANVAS_USER"
TARGET_HOME="$BIRDCANVAS_HOME"
BIRDNET_DIR="$BIRDCANVAS_BIRDNET_DIR"
REMOTE="${BIRDCANVAS_RCLONE_REMOTE%/}"
LOCAL_DIR="$BIRDCANVAS_LOCAL_BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
NAME="birdcanvas-backup-$STAMP.tar.gz"
ARCHIVE="$LOCAL_DIR/$NAME"
CHECKSUM="$ARCHIVE.sha256"
WORKDIR="$(mktemp -d /var/tmp/birdcanvas-backup.XXXXXX)"
STAGE="$WORKDIR/stage"
BIRDNET_WAS_ACTIVE=0

log() {
  printf '[%s] %s\n' "$(date --iso-8601=seconds)" "$*"
}

cleanup() {
  local rc=$?
  if [[ "$BIRDNET_WAS_ACTIVE" -eq 1 ]]; then
    systemctl start "$BIRDCANVAS_BIRDNET_SERVICE" >/dev/null 2>&1 || true
  fi
  rm -rf "$WORKDIR"
  exit "$rc"
}
trap cleanup EXIT INT TERM

TARGET_GROUP="$(id -gn "$TARGET_USER")"
install -d -m 0750 -o root -g "$TARGET_GROUP" "$LOCAL_DIR"
mkdir -p "$STAGE/birdcanvas" "$STAGE/system/etc" "$STAGE/metadata"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "BirdCanvas project not found: $PROJECT_DIR"
  exit 1
fi
if [[ ! -d "$BIRDNET_DIR" ]]; then
  echo "BirdNET-Go directory not found: $BIRDNET_DIR"
  exit 1
fi

log "Collecting BirdCanvas runtime data"
for item in data output/archive output/current; do
  if [[ -e "$PROJECT_DIR/$item" ]]; then
    mkdir -p "$STAGE/birdcanvas/$(dirname "$item")"
    rsync -a "$PROJECT_DIR/$item" "$STAGE/birdcanvas/$(dirname "$item")/"
  fi
done
for item in VERSION requirements.txt; do
  [[ -f "$PROJECT_DIR/$item" ]] && cp -a "$PROJECT_DIR/$item" "$STAGE/birdcanvas/"
done

log "Collecting BirdNET-Go data"
if systemctl list-unit-files "$BIRDCANVAS_BIRDNET_SERVICE" >/dev/null 2>&1 &&    systemctl is-active --quiet "$BIRDCANVAS_BIRDNET_SERVICE"; then
  BIRDNET_WAS_ACTIVE=1
  log "Pausing $BIRDCANVAS_BIRDNET_SERVICE for a consistent database copy"
  systemctl stop "$BIRDCANVAS_BIRDNET_SERVICE"
fi

mkdir -p "$STAGE/birdnet-go"
if [[ "$BIRDCANVAS_INCLUDE_BIRDNET_CLIPS" == "1" ]]; then
  rsync -a "$BIRDNET_DIR/" "$STAGE/birdnet-go/"
else
  rsync -a --exclude='data/clips/***' "$BIRDNET_DIR/" "$STAGE/birdnet-go/"
  mkdir -p "$STAGE/birdnet-go/data/clips"
  printf '%s\n' "BirdNET audio clips were intentionally excluded from this nightly disaster-recovery backup."     > "$STAGE/birdnet-go/data/clips/NOT_BACKED_UP.txt"
fi

if [[ "$BIRDNET_WAS_ACTIVE" -eq 1 ]]; then
  systemctl start "$BIRDCANVAS_BIRDNET_SERVICE"
  BIRDNET_WAS_ACTIVE=0
fi

log "Collecting Pi-specific service and audio configuration"
copy_etc_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    mkdir -p "$STAGE/system/etc/$(dirname "${path#/etc/}")"
    cp -a "$path" "$STAGE/system/etc/${path#/etc/}"
  fi
}
copy_etc_file /etc/modprobe.d/alsa-birdnet.conf
copy_etc_file /etc/default/birdcanvas-auto-deploy
copy_etc_file /etc/default/birdcanvas-backup
for path in   /etc/systemd/system/canvasos.service   /etc/systemd/system/birdcanvas-production.service   /etc/systemd/system/birdcanvas-production.timer   /etc/systemd/system/birdcanvas-auto-deploy.service   /etc/systemd/system/birdcanvas-auto-deploy.timer   /etc/systemd/system/birdcanvas-backup.service   /etc/systemd/system/birdcanvas-backup.timer   "/etc/systemd/system/$BIRDCANVAS_BIRDNET_SERVICE"
do
  copy_etc_file "$path"
done

{
  echo "BirdCanvas disaster-recovery backup"
  echo "Created: $(date --iso-8601=seconds)"
  echo "Hostname: $(hostname)"
  echo "Kernel: $(uname -srmo)"
  echo "Timezone: $(timedatectl show -p Timezone --value 2>/dev/null || true)"
  echo "Project: $PROJECT_DIR"
  echo "Git commit: $(git -C "$PROJECT_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "BirdNET directory: $BIRDNET_DIR"
  echo "BirdNET clips included: $BIRDCANVAS_INCLUDE_BIRDNET_CLIPS"
  echo
  echo "USB devices:"
  lsusb 2>/dev/null || true
  echo
  echo "ALSA capture devices:"
  arecord -l 2>/dev/null || true
  echo
  echo "Enabled BirdCanvas units:"
  systemctl is-enabled canvasos.service birdcanvas-production.timer birdcanvas-auto-deploy.timer birdcanvas-backup.timer 2>/dev/null || true
} > "$STAGE/metadata/system.txt"

cat > "$STAGE/SECRETS_NOT_INCLUDED.txt" <<'EOF'
This archive deliberately does not contain:
- BirdCanvas .env / OPENAI API key
- Samsung Frame pairing token
- rclone OAuth configuration
- Wi-Fi credentials

After an SD-card replacement, restore these credentials separately.
EOF

python3 - "$STAGE/metadata/manifest.json" <<PY
import json, pathlib, socket, subprocess, datetime
path = pathlib.Path(__import__("sys").argv[1])
def cmd(*args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"
payload = {
    "format": 1,
    "created_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "hostname": socket.gethostname(),
    "birdcanvas_version": pathlib.Path("$PROJECT_DIR/VERSION").read_text().strip() if pathlib.Path("$PROJECT_DIR/VERSION").exists() else "unknown",
    "git_commit": cmd("git", "-C", "$PROJECT_DIR", "rev-parse", "HEAD"),
    "birdnet_clips_included": "$BIRDCANVAS_INCLUDE_BIRDNET_CLIPS" == "1",
    "secrets_included": False,
}
path.write_text(json.dumps(payload, indent=2) + "\n")
PY

log "Creating compressed archive"
tar -C "$STAGE" -czf "$ARCHIVE" .
sha256sum "$ARCHIVE" > "$CHECKSUM"
chown "$TARGET_USER:$TARGET_GROUP" "$ARCHIVE" "$CHECKSUM"
chmod 0600 "$ARCHIVE" "$CHECKSUM"

rclone_as_user() {
  runuser -u "$TARGET_USER" -- env HOME="$TARGET_HOME" rclone "$@"
}

log "Uploading daily backup to $REMOTE/daily"
rclone_as_user copyto "$ARCHIVE" "$REMOTE/daily/$NAME"
rclone_as_user copyto "$CHECKSUM" "$REMOTE/daily/$NAME.sha256"

local_md5="$(rclone_as_user md5sum "$ARCHIVE" | awk 'NR==1 {print $1}')"
remote_md5="$(rclone_as_user md5sum "$REMOTE/daily/$NAME" | awk 'NR==1 {print $1}')"
if [[ -z "$local_md5" || "$local_md5" != "$remote_md5" ]]; then
  echo "Remote verification failed for $NAME"
  exit 1
fi
log "Remote MD5 verified"

if [[ "$(date +%u)" == "7" ]]; then
  log "Creating weekly retention copy"
  rclone_as_user copyto "$ARCHIVE" "$REMOTE/weekly/$NAME"
  rclone_as_user copyto "$CHECKSUM" "$REMOTE/weekly/$NAME.sha256"
fi

log "Applying retention"
rclone_as_user delete "$REMOTE/daily" --min-age "${BIRDCANVAS_DAILY_RETENTION_DAYS}d" --include 'birdcanvas-backup-*.tar.gz*' || true
rclone_as_user rmdirs "$REMOTE/daily" --leave-root || true
rclone_as_user delete "$REMOTE/weekly" --min-age "${BIRDCANVAS_WEEKLY_RETENTION_DAYS}d" --include 'birdcanvas-backup-*.tar.gz*' || true
rclone_as_user rmdirs "$REMOTE/weekly" --leave-root || true
find "$LOCAL_DIR" -type f -name 'birdcanvas-backup-*.tar.gz*' -mtime "+$BIRDCANVAS_LOCAL_RETENTION_DAYS" -delete

log "Backup complete: $NAME"
