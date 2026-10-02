# BirdCanvas disaster recovery

BirdCanvas code is protected by GitHub. This backup protects the mutable data that is not safely reproducible from GitHub.

## Nightly backup contents

The off-device archive contains:

- BirdCanvas `data/`
- `output/archive/` and `output/current/`
- BirdCanvas version and requirements
- BirdNET-Go application configuration and data, including the detection database
- Pi-specific BirdCanvas/BirdNET systemd units
- USB microphone module configuration
- system metadata that helps rebuild the host

By default BirdNET audio clips are not included because they can grow much faster than the detection database and artwork history. Set `BIRDCANVAS_INCLUDE_BIRDNET_CLIPS=1` in `/etc/default/birdcanvas-backup` if the raw clips must also be retained.

The archive deliberately excludes secrets: `.env`, the Samsung Frame token, rclone OAuth credentials and Wi-Fi credentials.

## Retention

- daily backups: 14 days
- Sunday backups: 56 days
- local SD-card copies: 2 days

The upload is verified by comparing the local and remote MD5 hashes.

## Install

```bash
sudo bash deployment/install-backup.sh
sudo -u dan -H rclone config
sudo bash deployment/configure-backup.sh 'REMOTE:BirdCanvas Backups'
```

The final command enables the nightly timer and immediately runs and verifies the first remote backup.

## Recovery after SD-card failure

1. Flash Raspberry Pi OS Lite 64-bit and restore networking/SSH.
2. Clone BirdCanvas from GitHub and run the normal headless installer.
3. Install/configure BirdNET-Go.
4. Configure rclone and download the latest archive and its `.sha256` file.
5. Restore it:

```bash
sudo bash deployment/restore-from-backup.sh /path/to/birdcanvas-backup-YYYYMMDD-HHMMSS.tar.gz
```

6. Recreate the BirdCanvas `.env`, including the OpenAI key.
7. Re-pair the Samsung Frame if its token was lost.
8. Verify BirdNET-Go, the microphone, GalleryOS and Frame delivery before re-enabling production.

The restore script restores data and machine-specific configuration. It intentionally does not overwrite the GitHub-managed BirdCanvas source code.
