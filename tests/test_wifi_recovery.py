"""Regression tests for the separate, conservative NetworkManager Wi-Fi watchdog."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deployment" / "wifi-recovery.sh"


class WifiRecoveryTests(unittest.TestCase):
    def test_shell_scripts_parse(self):
        for filename in ("wifi-recovery.sh", "install-wifi-recovery.sh"):
            with self.subTest(filename=filename):
                result = subprocess.run(
                    ["bash", "-n", str(ROOT / "deployment" / filename)],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_watcher_uses_only_local_gateway_without_reboot(self):
        script = SCRIPT.read_text()
        self.assertIn('ip -4 route show default dev "$interface"', script)
        self.assertIn('ping -n -I "$interface"', script)
        self.assertIn("FAIL_LIMIT=3", script)
        self.assertIn("COOLDOWN_SECONDS=1800", script)
        self.assertNotIn("reboot", script.replace("# Does not reboot", ""))
        self.assertNotIn("systemctl restart", script)

    def test_deployer_installs_only_after_health_check(self):
        deploy = (ROOT / "deployment" / "auto-deploy.sh").read_text()
        installer = 'bash "$PROJECT_DIR/deployment/install-wifi-recovery.sh"'
        self.assertIn(installer, deploy)
        self.assertLess(deploy.index("http://127.0.0.1:8000/api/ping >/dev/null"), deploy.index(installer))

    def _run(self, folder, wifi="enabled", ping_ok=False, connected=True):
        folder = Path(folder)
        bindir = folder / "bin"
        bindir.mkdir(exist_ok=True)
        nmcli = bindir / "nmcli"
        nmcli.write_text("""#!/bin/sh
if [ "$*" = "-t -f DEVICE,TYPE device status" ]; then echo 'wlan0:wifi'; exit 0; fi
if [ "$*" = "radio wifi" ]; then echo "$MOCK_WIFI"; exit 0; fi
if [ "$*" = "-g GENERAL.STATE device show wlan0" ]; then
    if [ "$MOCK_CONNECTED" = "1" ]; then echo '100 (connected)'; else echo '30 (disconnected)'; fi
    exit 0
fi
echo "$*" >> "$MOCK_EVENTS"
""")
        ip = bindir / "ip"
        ip.write_text("""#!/bin/sh
if [ "$*" = "-4 addr show dev wlan0" ]; then echo 'inet 192.168.1.5/24'; fi
if [ "$*" = "-4 route show default dev wlan0" ]; then echo 'default via 192.168.1.1 dev wlan0'; fi
""")
        ping = bindir / "ping"
        ping.write_text("#!/bin/sh\nexit ${MOCK_PING_STATUS:-1}\n")
        for executable in (nmcli, ip, ping):
            executable.chmod(0o755)
        events = folder / "events"
        env = os.environ.copy()
        env.update({
            "PATH": str(bindir) + os.pathsep + env["PATH"],
            "BIRDCANVAS_WIFI_STATE_DIR": str(folder / "state"),
            "MOCK_WIFI": wifi,
            "MOCK_CONNECTED": "1" if connected else "0",
            "MOCK_PING_STATUS": "0" if ping_ok else "1",
            "MOCK_EVENTS": str(events),
        })
        result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return events.read_text() if events.exists() else ""

    def test_good_connection_never_reconnects(self):
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(4):
                self.assertEqual(self._run(folder, ping_ok=True), "")

    def test_outage_requires_three_failures_then_cooldown(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self._run(folder), "")
            self.assertEqual(self._run(folder), "")
            self.assertIn("device disconnect wlan0", self._run(folder))
            actions = self._run(folder)
            self.assertEqual(actions.count("device connect wlan0"), 1)
            self.assertEqual(actions.count("device disconnect wlan0"), 1)

    def test_deliberately_disabled_radio_is_respected(self):
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(4):
                self.assertEqual(self._run(folder, wifi="disabled"), "")


if __name__ == "__main__":
    unittest.main()
