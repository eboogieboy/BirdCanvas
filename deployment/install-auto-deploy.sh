#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Run this installer with:"
    echo "  sudo deployment/install-auto-deploy.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"
TARGET_GROUP="$(id -gn "$TARGET_USER")"
REPO_URL="$(git -C "$PROJECT_DIR" remote get-url origin)"
DEPLOY_BRANCH="${BIRDCANVAS_DEPLOY_BRANCH:-main}"

apt-get update
apt-get install -y git rsync curl

install -m 0755     "$PROJECT_DIR/deployment/auto-deploy.sh"     /usr/local/sbin/birdcanvas-auto-deploy

{
    printf 'BIRDCANVAS_PROJECT_DIR=%q\n' "$PROJECT_DIR"
    printf 'BIRDCANVAS_DEPLOY_REPO=%q\n' "$REPO_URL"
    printf 'BIRDCANVAS_DEPLOY_BRANCH=%q\n' "$DEPLOY_BRANCH"
    printf 'BIRDCANVAS_DEPLOY_USER=%q\n' "$TARGET_USER"
    printf 'BIRDCANVAS_DEPLOY_GROUP=%q\n' "$TARGET_GROUP"
} > /etc/default/birdcanvas-auto-deploy
chmod 0644 /etc/default/birdcanvas-auto-deploy

install -m 0644     "$PROJECT_DIR/deployment/systemd/birdcanvas-auto-deploy.service"     /etc/systemd/system/birdcanvas-auto-deploy.service
install -m 0644     "$PROJECT_DIR/deployment/systemd/birdcanvas-auto-deploy.timer"     /etc/systemd/system/birdcanvas-auto-deploy.timer

systemctl daemon-reload
systemctl enable --now birdcanvas-auto-deploy.timer

echo
echo "BirdCanvas automatic deployment installed."
echo "Repository: $REPO_URL"
echo "Branch:     $DEPLOY_BRANCH"
echo "Live path:  $PROJECT_DIR"
echo "Checks:     every 5 minutes"
echo
echo "Run an immediate check with:"
echo "  sudo systemctl start birdcanvas-auto-deploy.service"
echo
echo "Follow deployment logs with:"
echo "  sudo journalctl -fu birdcanvas-auto-deploy.service"
