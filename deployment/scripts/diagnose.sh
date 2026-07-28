#!/usr/bin/env bash
set -u

echo "CanvasOS diagnostic report"
echo "=========================="
echo
printf "Time: "
date --iso-8601=seconds
printf "Hostname: "
hostname
printf "User: "
whoami
printf "IP addresses: "
hostname -I || true

echo
echo "Server service"
systemctl --no-pager --full status canvasos.service || true

echo
echo "Port 8000"
ss -ltnp 2>/dev/null | grep ':8000' || echo "Nothing is listening on port 8000."

echo
echo "Local display request"
curl --silent --show-error --fail --max-time 5 http://127.0.0.1:8000/ >/dev/null \
    && echo "Display page responds correctly." \
    || echo "Display page did not respond."

echo
echo "Recent service logs"
journalctl -u canvasos.service -n 40 --no-pager || true

echo
echo "Kiosk log"
tail -n 40 "$HOME/.local/state/canvasos/kiosk.log" 2>/dev/null || echo "No kiosk log yet."
