import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DeploymentHardeningTests(unittest.TestCase):
    def test_auto_deploy_shell_parses(self):
        script = ROOT / "deployment" / "auto-deploy.sh"
        result = subprocess.run(
            ["bash", "-n", str(script)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_auto_deploy_refreshes_installed_helpers(self):
        text = (ROOT / "deployment" / "auto-deploy.sh").read_text()
        self.assertIn(
            'refresh_installed_helper "$PROJECT_DIR/deployment/auto-deploy.sh" '
            '/usr/local/sbin/birdcanvas-auto-deploy',
            text,
        )
        self.assertIn(
            'refresh_installed_helper "$PROJECT_DIR/deployment/backup-to-rclone.sh" '
            '/usr/local/sbin/birdcanvas-backup',
            text,
        )
        self.assertLess(
            text.index("http://127.0.0.1:8000/api/health >/dev/null"),
            text.index('refresh_installed_helper "$PROJECT_DIR/deployment/auto-deploy.sh"'),
        )

    def test_backup_retention_checks_remote_folder_first(self):
        text = (ROOT / "deployment" / "backup-to-rclone.sh").read_text()
        self.assertIn('if rclone_as_user lsf "$REMOTE/daily"', text)
        self.assertIn('if rclone_as_user lsf "$REMOTE/weekly"', text)


if __name__ == "__main__":
    unittest.main()
