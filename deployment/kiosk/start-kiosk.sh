#!/usr/bin/env bash
set -u

URL="${CANVASOS_DISPLAY_URL:-http://127.0.0.1:8000/}"
LOG_DIR="${HOME}/.local/state/canvasos"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/kiosk.log"

exec >>"$LOG_FILE" 2>&1

echo "$(date --iso-8601=seconds) Starting CanvasOS kiosk"

# Wait for GalleryOS to become available. The currently displayed image remains
# local, so internet connectivity is not required.
for _ in $(seq 1 120); do
    if curl --silent --fail --max-time 2 "$URL" >/dev/null; then
        break
    fi
    sleep 1
done

# Hide the pointer after a short idle period.
if command -v unclutter >/dev/null 2>&1; then
    unclutter -idle 0.5 -root &
fi

CHROMIUM=""
for candidate in chromium chromium-browser; do
    if command -v "$candidate" >/dev/null 2>&1; then
        CHROMIUM="$candidate"
        break
    fi
done

if [[ -z "$CHROMIUM" ]]; then
    echo "Chromium was not found."
    exit 1
fi

# Chromium is relaunched if it exits unexpectedly.
while true; do
    "$CHROMIUM" \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-features=TranslateUI \
        --disable-pinch \
        --overscroll-history-navigation=0 \
        --autoplay-policy=no-user-gesture-required \
        --check-for-update-interval=31536000 \
        --user-data-dir="${HOME}/.config/canvasos-chromium" \
        "$URL"
    echo "$(date --iso-8601=seconds) Chromium exited; restarting in 3 seconds"
    sleep 3
done
