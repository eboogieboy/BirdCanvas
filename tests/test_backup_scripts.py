import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "deployment" / "backup-to-rclone.sh",
    ROOT / "deployment" / "restore-from-backup.sh",
    ROOT / "deployment" / "install-backup.sh",
    ROOT / "deployment" / "configure-backup.sh",
]


class BackupScriptTests(unittest.TestCase):
    def test_backup_shell_scripts_parse(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    ["bash", "-n", str(script)],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_backup_excludes_secrets_and_verifies_remote_copy(self):
        text = (ROOT / "deployment" / "backup-to-rclone.sh").read_text()
        self.assertIn("SECRETS_NOT_INCLUDED.txt", text)
        self.assertIn("Remote MD5 verified", text)
        self.assertNotIn('cp -a "$PROJECT_DIR/.env"', text)
        self.assertNotIn(".birdcanvas-frame-token", text)

    def test_backup_has_daily_and_weekly_retention(self):
        text = (ROOT / "deployment" / "backup-to-rclone.sh").read_text()
        self.assertIn('BIRDCANVAS_DAILY_RETENTION_DAYS', text)
        self.assertIn('BIRDCANVAS_WEEKLY_RETENTION_DAYS', text)
        self.assertIn('$REMOTE/daily', text)
        self.assertIn('$REMOTE/weekly', text)


if __name__ == "__main__":
    unittest.main()
