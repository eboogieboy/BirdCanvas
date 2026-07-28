"""Backward-compatible morning BirdCanvas job.

The permanent schedule now uses scheduled_job.py with morning, midday and evening
slots. Keeping this wrapper means existing 04:00 cron or systemd entries continue
to work while deployment is upgraded.
"""

from scheduled_job import main as scheduled_main


if __name__ == "__main__":
    import sys

    sys.argv = [sys.argv[0], "morning"]
    raise SystemExit(scheduled_main())
