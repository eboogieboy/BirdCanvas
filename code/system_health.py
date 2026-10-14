"""Read-only, bounded systemd checks for scheduled backup and mirror delivery."""
from __future__ import annotations

import re
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

LOCAL = ZoneInfo("Europe/London")


def _run(*args):
    try:
        response = subprocess.run(["systemctl", *args], capture_output=True, text=True, timeout=2)
        return response.stdout if response.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _properties(unit):
    output = _run("show", unit, "--no-pager",
                  "--property=LoadState,ActiveState,Result,ExecMainStatus,ExecMainExitTimestamp")
    return dict(line.split("=", 1) for line in output.splitlines() if "=" in line) if output is not None else None


def _completed(value):
    match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})", value)
    if not match:
        return None
    return datetime.strptime(" ".join(match.groups()), "%Y-%m-%d %H:%M:%S").replace(tzinfo=LOCAL)


def _job(timer, name, label):
    schedule = _properties(timer)
    if schedule is None:
        return {"status": "unknown", "message": f"{label} monitoring unavailable."}
    if schedule.get("LoadState") != "loaded":
        return {"status": "unknown", "message": f"{label} timer not installed."}
    if schedule.get("ActiveState") != "active":
        return {"status": "warning", "message": f"{label} timer is inactive."}
    service = _properties(name)
    if not service or service.get("LoadState") != "loaded":
        return {"status": "warning", "message": f"{label} service not available."}
    if service.get("Result") not in ("success", "") or service.get("ExecMainStatus") not in ("0", ""):
        return {"status": "error", "message": f"{label} most recent run failed."}
    ended = _completed(service.get("ExecMainExitTimestamp", ""))
    if ended is None:
        return {"status": "warning", "message": f"{label} has no completed run recorded."}
    if abs((datetime.now(LOCAL) - ended).total_seconds()) > 40 * 3600:
        return {"status": "warning", "message": f"{label} overdue; last run {ended.strftime('%d %b %H:%M')}."}
    return {"status": "ok", "message": f"Last completed {ended.strftime('%d %b %H:%M')}."}


def delivery_checks():
    backup = _job("birdcanvas-backup.timer", "birdcanvas-backup.service", "Backup")
    files = _run("list-unit-files", "--type=timer", "--no-pager", "--no-legend")
    if files is None:
        mirror = {"status": "unknown", "message": "Mirror delivery monitoring unavailable."}
    else:
        units = [line.split()[0] for line in files.splitlines() if line.strip()
                 and "mirror" in line.split()[0].lower()
                 and "birdcanvas" in line.split()[0].lower()
                 and line.split()[0].endswith(".timer")]
        if units:
            timer = sorted(units)[0]
            mirror = _job(timer, timer.replace(".timer", ".service"), "Mirror push")
        else:
            mirror = {"status": "unknown", "message": "No Mirror sender timer found; delivery unverified."}
    return {"backup": backup, "mirror": mirror}
