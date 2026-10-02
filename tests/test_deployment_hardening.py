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

    def test_auto_deploy_preflights_candidate_before_touching_live_code(self):
        text = (ROOT / "deployment" / "auto-deploy.sh").read_text()
        preflight = text.index("Running candidate preflight in writable sandbox before touching live code")
        rollback = text.index('ROLLBACK="$STATE_DIR/rollback-')
        first_live_rsync = text.index('rsync -a --delete --chown=')
        self.assertLess(preflight, rollback)
        self.assertLess(preflight, first_live_rsync)
        self.assertIn("Candidate compile preflight failed; live installation unchanged", text)
        self.assertIn("Candidate test preflight failed; live installation unchanged", text)
        self.assertIn("Candidate page-generation preflight failed; live installation unchanged", text)

    def test_preflight_uses_writable_sandbox_not_source_checkout(self):
        text = (ROOT / "deployment" / "auto-deploy.sh").read_text()
        self.assertIn('PREFLIGHT_DIR="$(mktemp -d "$STATE_DIR/preflight.XXXXXX")"', text)
        self.assertIn('"$SOURCE_DIR/" "$PREFLIGHT_DIR/"', text)
        self.assertIn('chmod -R u+rwX "$PREFLIGHT_DIR"', text)
        self.assertIn("cd '$PREFLIGHT_DIR'", text)
        self.assertNotIn("cd '$SOURCE_DIR' && PYTHONPATH=code", text)
        self.assertNotIn("cd '$SOURCE_DIR' && '$PROJECT_DIR/.venv/bin/python' code/display.py", text)

    def test_ci_simulates_full_production_preflight_sandbox(self):
        text = (
            ROOT / ".github" / "workflows" / "birdcanvas-checks.yml"
        ).read_text()
        self.assertIn("Simulate production preflight sandbox", text)
        self.assertIn("sudo chown -R root:root", text)
        self.assertIn('PREFLIGHT_DIR="$(sudo mktemp -d', text)
        self.assertIn('sudo chmod -R u+rwX "$PREFLIGHT_DIR"', text)
        self.assertIn("python code/display.py", text)
        self.assertIn('test -z "$(git status --porcelain)"', text)

    def test_backup_retention_checks_remote_folder_first(self):
        text = (ROOT / "deployment" / "backup-to-rclone.sh").read_text()
        self.assertIn('if rclone_as_user lsf "$REMOTE/daily"', text)
        self.assertIn('if rclone_as_user lsf "$REMOTE/weekly"', text)


if __name__ == "__main__":
    unittest.main()
