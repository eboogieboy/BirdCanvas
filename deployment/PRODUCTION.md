# BirdCanvas on one headless Raspberry Pi

Install BirdNET-Go on the Pi using its own current installation guide, configure the USB microphone and verify that its detection page and `/api/v2/detections` respond at `http://127.0.0.1:8080`. Its detection database is the authoritative bird ledger. BirdCanvas reads it; BirdCanvas does not manage or install BirdNET-Go.

Use Raspberry Pi OS Lite 64-bit and run `sudo deployment/install-headless.sh` from the BirdCanvas checkout. Supply `.env` in the project root (owned by the service user, mode 0600), for example:

```
OPENAI_API_KEY=...
BIRDCANVAS_BIRDNET_URL=http://127.0.0.1:8080
BIRDCANVAS_MIN_CONFIDENCE=0.5
BIRDCANVAS_FRAME_ENABLED=true
BIRDCANVAS_FRAME_HOST=192.168.x.x
```

The optional Frame token file uses the Samsung CLI default `~/.birdcanvas-frame-token` under the service user's home. Pair the TV once while logged in as that user. Give the TV a stable IP address. Leave `BIRDCANVAS_FRAME_ENABLED=false` while testing without the TV.

The installer starts the GalleryOS service and a 15-minute systemd timer. The timer checks the frequency selected on `/control/` and retries delivery of previously generated images. Daily is 04:00, twice weekly is Monday/Thursday 04:00, weekly is Monday 04:00, all Europe/London. It never generates a replacement merely because Frame delivery failed. `sudo journalctl -u birdcanvas-production.service -n 100` shows generation failures; `/api/health` shows state. The phone's Generate now button closes the current collection at that moment, then the next scheduled boundary resumes collection.

BirdNET-Go needs its own startup service. Confirm its API response and a real microphone detection before relying on unattended runs. Do not expose the unauthenticated GalleryOS control port outside the trusted home network.


## Optional self-healing Wi-Fi watchdog

For headless Raspberry Pis using **NetworkManager** (the `nmcli` utility),
install the non-rebooting network recovery timer once after the updated code is
on the Pi:

```bash
cd /home/dan/BirdCanvas   # or your actual BirdCanvas project directory
sudo bash deployment/install-wifi-recovery.sh
systemctl is-enabled birdcanvas-wifi-recovery.timer
systemctl status birdcanvas-wifi-recovery.timer --no-pager
```

The timer checks every three minutes. It only monitors an enabled,
NetworkManager-managed Wi-Fi device. An associated device must have a local IPv4
address, default gateway and a responding **local router**; no public internet
host or BirdCanvas service is probed. Three consecutive failed observations
trigger a NetworkManager reconnect attempt. Another attempt cannot happen for
at least 30 minutes. The watchdog never changes saved Wi-Fi credentials,
turns on intentionally disabled radios, restarts BirdNET-Go, or reboots the Pi.
The router needs to answer ICMP ping. If it blocks ping, **do not enable**
this watchdog without adjusting the probe.

A new version of the BirdCanvas auto-deployer installs/refreshes the units
after a successful update. Because the original runner cannot invoke
installation code it has only just downloaded, the *first* update that
introduces this feature may only refresh the runner itself. The one-time
installation command above activates it immediately and is safe to repeat.

Diagnostics:
```bash
sudo journalctl -u birdcanvas-wifi-recovery.service -n 50 --no-pager
sudo systemctl list-timers birdcanvas-wifi-recovery.timer --no-pager
```

A complete kernel/system freeze cannot be recovered by software on the same Pi.
