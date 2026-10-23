#!/usr/bin/env bash
# Conservative, local-network-only Wi-Fi recovery for a headless BirdCanvas Pi.
# Does not reboot, change saved Wi-Fi profiles, or contact public endpoints.
set -euo pipefail

STATE_DIR="${BIRDCANVAS_WIFI_STATE_DIR:-/var/lib/birdcanvas-wifi-recovery}"
FAIL_LIMIT=3
COOLDOWN_SECONDS=1800

log() { printf '[BirdCanvas Wi-Fi] %s\n' "$*"; }

# Do not take over networking on systems without NetworkManager.
if ! command -v nmcli >/dev/null 2>&1; then
    log "NetworkManager is unavailable; no changes made"
    exit 0
fi

devices="$(nmcli -t -f DEVICE,TYPE device status 2>/dev/null)" || {
    log "NetworkManager is not responding; no changes made"
    exit 0
}

# Respect intentionally disabled Wi-Fi, unmanaged devices and wired setups.
if [[ "$(nmcli radio wifi 2>/dev/null || true)" != "enabled" ]]; then
    log "Wi-Fi radio disabled; leaving it disabled"
    exit 0
fi

interface="$(printf '%s\n' "$devices" | awk -F: '$2 == "wifi" {print $1; exit}')"
if [[ -z "$interface" ]]; then
    log "No NetworkManager Wi-Fi device found; no changes made"
    exit 0
fi

state="$(nmcli -g GENERAL.STATE device show "$interface" 2>/dev/null || true)"
if [[ "$state" == *unmanaged* || "$state" == *unavailable* ]]; then
    log "$interface is $state; no changes made"
    exit 0
fi

healthy=0
reason="Wi-Fi not connected"
if [[ "$state" == 100* ]]; then
    if ip -4 addr show dev "$interface" | grep -q 'inet '; then
        gateway="$(ip -4 route show default dev "$interface" | awk '$1 == "default" && $2 == "via" {print $3; exit}')"
        if [[ -n "$gateway" ]]; then
            if ! command -v ping >/dev/null 2>&1; then
                # No reliable reachability probe: don't disrupt an associated link.
                healthy=1
            elif ping -n -I "$interface" -c 1 -W 2 "$gateway" >/dev/null 2>&1; then
                healthy=1
            else
                reason="local gateway $gateway unreachable from $interface"
            fi
        else
            reason="no default IPv4 gateway on $interface"
        fi
    else
        reason="no IPv4 address on $interface"
    fi
fi

mkdir -p "$STATE_DIR"
chmod 0700 "$STATE_DIR"
misses_file="$STATE_DIR/consecutive-failures"
last_file="$STATE_DIR/last-recovery-attempt"
misses="$(cat "$misses_file" 2>/dev/null || echo 0)"
[[ "$misses" =~ ^[0-9]+$ ]] || misses=0

if (( healthy )); then
    if (( misses > 0 )); then
        log "Local Wi-Fi connectivity restored on $interface"
    fi
    printf '0\n' > "$misses_file"
    exit 0
fi

misses=$((misses + 1))
printf '%s\n' "$misses" > "$misses_file"
if (( misses < FAIL_LIMIT )); then
    log "$reason; observation $misses/$FAIL_LIMIT, waiting before intervening"
    exit 0
fi

now="$(date +%s)"
last="$(cat "$last_file" 2>/dev/null || echo 0)"
[[ "$last" =~ ^[0-9]+$ ]] || last=0
if (( now >= last && now - last < COOLDOWN_SECONDS )); then
    log "$reason; recovery cooldown active"
    exit 0
fi
printf '%s\n' "$now" > "$last_file"
printf '0\n' > "$misses_file"

if [[ "$state" == 100* ]]; then
    log "$reason across $FAIL_LIMIT checks; reconnecting $interface once"
    # Disconnect only when the device claims to be associated but the router
    # cannot be reached. Always try reconnecting even if disconnect fails.
    nmcli -w 15 device disconnect "$interface" || true
else
    log "$reason across $FAIL_LIMIT checks; requesting reconnection of $interface"
fi

if nmcli -w 45 device connect "$interface"; then
    log "Reconnect requested; next check will verify gateway reachability"
else
    log "NetworkManager could not reconnect $interface; will retry after cooldown"
fi
