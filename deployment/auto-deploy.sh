#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/etc/default/birdcanvas-auto-deploy"
STATE_DIR="/var/lib/birdcanvas-auto-deploy"

if [[ ! -r "$CONFIG_FILE" ]]; then
    echo "Missing $CONFIG_FILE"
    exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

: "${BIRDCANVAS_PROJECT_DIR:?Missing BIRDCANVAS_PROJECT_DIR}"
: "${BIRDCANVAS_DEPLOY_REPO:?Missing BIRDCANVAS_DEPLOY_REPO}"
: "${BIRDCANVAS_DEPLOY_BRANCH:=main}"
: "${BIRDCANVAS_DEPLOY_USER:?Missing BIRDCANVAS_DEPLOY_USER}"
: "${BIRDCANVAS_DEPLOY_GROUP:?Missing BIRDCANVAS_DEPLOY_GROUP}"

PROJECT_DIR="$BIRDCANVAS_PROJECT_DIR"
SOURCE_DIR="$STATE_DIR/repo"
LAST_SUCCESS="$STATE_DIR/last-successful-commit"
LOCK_FILE="$STATE_DIR/deploy.lock"

mkdir -p "$STATE_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

log() {
    printf '[%s] %s\n' "$(date --iso-8601=seconds)" "$*"
}

if [[ ! -d "$PROJECT_DIR/.venv" ]]; then
    log "Refusing deploy: missing BirdCanvas virtual environment at $PROJECT_DIR/.venv"
    exit 1
fi

if [[ ! -d "$SOURCE_DIR/.git" ]]; then
    log "Creating clean deployment checkout"
    rm -rf "$SOURCE_DIR"
    git clone --single-branch --branch "$BIRDCANVAS_DEPLOY_BRANCH"         "$BIRDCANVAS_DEPLOY_REPO" "$SOURCE_DIR"
else
    git -C "$SOURCE_DIR" fetch --prune origin "$BIRDCANVAS_DEPLOY_BRANCH"
    git -C "$SOURCE_DIR" checkout -B "$BIRDCANVAS_DEPLOY_BRANCH"         "origin/$BIRDCANVAS_DEPLOY_BRANCH"
    git -C "$SOURCE_DIR" reset --hard "origin/$BIRDCANVAS_DEPLOY_BRANCH"
fi

REMOTE_COMMIT="$(git -C "$SOURCE_DIR" rev-parse HEAD)"
LAST_COMMIT="$(cat "$LAST_SUCCESS" 2>/dev/null || true)"

if [[ "$REMOTE_COMMIT" == "$LAST_COMMIT" ]]; then
    exit 0
fi

log "Candidate commit: $REMOTE_COMMIT"

# Fail before touching the live checkout if the new Python code is not syntactically valid.
python3 -m compileall -q "$SOURCE_DIR/code"

STAMP="$(date +%Y%m%d-%H%M%S)"
ROLLBACK="$STATE_DIR/rollback-$STAMP"
mkdir -p "$ROLLBACK"

for item in code deployment tests requirements.txt VERSION; do
    if [[ -e "$PROJECT_DIR/$item" ]]; then
        cp -a "$PROJECT_DIR/$item" "$ROLLBACK/"
    fi
done

rollback() {
    log "Deployment failed; restoring previous live code"
    for item in code deployment tests; do
        if [[ -e "$ROLLBACK/$item" ]]; then
            rm -rf "$PROJECT_DIR/$item"
            cp -a "$ROLLBACK/$item" "$PROJECT_DIR/$item"
        fi
    done
    for item in requirements.txt VERSION; do
        if [[ -f "$ROLLBACK/$item" ]]; then
            cp -a "$ROLLBACK/$item" "$PROJECT_DIR/$item"
        fi
    done
    chown -R "$BIRDCANVAS_DEPLOY_USER:$BIRDCANVAS_DEPLOY_GROUP"         "$PROJECT_DIR/code" "$PROJECT_DIR/deployment" "$PROJECT_DIR/tests"         "$PROJECT_DIR/requirements.txt" "$PROJECT_DIR/VERSION" 2>/dev/null || true

    runuser -u "$BIRDCANVAS_DEPLOY_USER" -- bash -lc         "cd '$PROJECT_DIR' && '$PROJECT_DIR/.venv/bin/python' code/display.py" || true
    systemctl restart canvasos.service || true
}
trap rollback ERR

OLD_REQUIREMENTS="$(sha256sum "$PROJECT_DIR/requirements.txt" 2>/dev/null | awk '{print $1}' || true)"
NEW_REQUIREMENTS="$(sha256sum "$SOURCE_DIR/requirements.txt" | awk '{print $1}')"

rsync -a --delete --chown="$BIRDCANVAS_DEPLOY_USER:$BIRDCANVAS_DEPLOY_GROUP"     "$SOURCE_DIR/code/" "$PROJECT_DIR/code/"
rsync -a --delete --chown="$BIRDCANVAS_DEPLOY_USER:$BIRDCANVAS_DEPLOY_GROUP"     "$SOURCE_DIR/deployment/" "$PROJECT_DIR/deployment/"

if [[ -d "$SOURCE_DIR/tests" ]]; then
    mkdir -p "$PROJECT_DIR/tests"
    rsync -a --delete --chown="$BIRDCANVAS_DEPLOY_USER:$BIRDCANVAS_DEPLOY_GROUP"         "$SOURCE_DIR/tests/" "$PROJECT_DIR/tests/"
fi

install -o "$BIRDCANVAS_DEPLOY_USER" -g "$BIRDCANVAS_DEPLOY_GROUP" -m 0644     "$SOURCE_DIR/requirements.txt" "$PROJECT_DIR/requirements.txt"
install -o "$BIRDCANVAS_DEPLOY_USER" -g "$BIRDCANVAS_DEPLOY_GROUP" -m 0644     "$SOURCE_DIR/VERSION" "$PROJECT_DIR/VERSION"

if [[ "$OLD_REQUIREMENTS" != "$NEW_REQUIREMENTS" ]]; then
    log "Python requirements changed; updating virtual environment"
    runuser -u "$BIRDCANVAS_DEPLOY_USER" --         "$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
fi

# Run the regression suite against the live payload before restarting the server.
if [[ -d "$PROJECT_DIR/tests" ]]; then
    runuser -u "$BIRDCANVAS_DEPLOY_USER" -- bash -lc         "cd '$PROJECT_DIR' && PYTHONPATH=code '$PROJECT_DIR/.venv/bin/python' -m unittest discover -s tests -v"
fi

# Rebuild the generated control/gallery pages. Runtime data, artwork, .env,
# BirdNET-Go data and the Samsung token are deliberately outside the deploy payload.
runuser -u "$BIRDCANVAS_DEPLOY_USER" -- bash -lc     "cd '$PROJECT_DIR' && '$PROJECT_DIR/.venv/bin/python' code/display.py"

systemctl restart canvasos.service

for _ in $(seq 1 20); do
    if curl --silent --fail --max-time 2         http://127.0.0.1:8000/api/health >/dev/null; then
        break
    fi
    sleep 1
done

curl --silent --fail --max-time 3     http://127.0.0.1:8000/api/health >/dev/null

printf '%s\n' "$REMOTE_COMMIT" > "$LAST_SUCCESS"
rm -rf "$ROLLBACK"
trap - ERR

log "BirdCanvas deployed successfully: $REMOTE_COMMIT"
