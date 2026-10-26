#!/usr/bin/env python3
"""End-to-end tests for the cleanyourdroid tools, with no phone attached.

`tests/fake_adb.py` stands in for adb, so these run in CI on Windows, macOS and
Linux alike:

    python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "tools" / "audit.py"
PLAN = ROOT / "tools" / "plan.py"
FAKE_ADB = ROOT / "tests" / "fake_adb.py"


class ToolTestCase(unittest.TestCase):
    def setUp(self):
        # Some sandboxes only allow writes to a directory that already exists
        # (CYD_TEST_TMP); everywhere else a fresh temp dir is used.
        override = os.environ.get("CYD_TEST_TMP")
        if override:
            self.workdir = Path(override)
        else:
            self.workdir = Path(tempfile.mkdtemp(prefix="cyd-test-"))
        self.env = dict(os.environ)
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.env["CLEANYOURDROID_ADB"] = json.dumps([sys.executable, str(FAKE_ADB)])
        self.env["FAKE_CYD_STATE"] = "before"
        self.env.pop("FAKE_CYD_FAIL", None)

    def run_tool(self, script, *args):
        return subprocess.run(
            [sys.executable, "-B", str(script)] + [str(a) for a in args],
            cwd=str(self.workdir),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )


class PlanTests(ToolTestCase):
    def test_databases_validate(self):
        result = self.run_tool(PLAN, "--validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Databases OK", result.stdout)

    def test_plan_never_proposes_blacklisted_packages(self):
        result = self.run_tool(PLAN)
        self.assertEqual(result.returncode, 0, result.stderr)
        for protected in ("com.miui.securitycenter", "com.miui.powerkeeper", "com.google.android.gms"):
            self.assertNotIn(protected, result.stdout.split("installed")[0])

    def test_plan_lists_known_bloat(self):
        result = self.run_tool(PLAN)
        self.assertIn("com.miui.msa.global", result.stdout)
        self.assertIn("Group A", result.stdout)

    def test_plan_json_is_machine_readable(self):
        result = self.run_tool(PLAN, "--format", "json")
        payload = json.loads(result.stdout)
        self.assertGreater(payload["counts"]["installed"], 0)
        self.assertIn("ads_and_telemetry", payload["groups"])
        self.assertTrue(payload["counts"]["candidates"] > 0)
        self.assertNotIn("com.miui.securitycenter", payload["groups"]["ads_and_telemetry"])

    def test_multiple_devices_is_a_clear_error(self):
        self.env["FAKE_CYD_FAIL"] = "multiple"
        result = self.run_tool(PLAN)
        self.assertEqual(result.returncode, 1)
        self.assertIn("--serial", result.stderr)

    def test_packages_file_offline(self):
        listing = self.workdir / "pkgs.txt"
        listing.write_text("package:com.miui.msa.global\n# comment\ncom.android.systemui\n", encoding="utf-8")
        result = self.run_tool(PLAN, "--packages-file", listing)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("com.miui.msa.global", result.stdout)


class AuditTests(ToolTestCase):
    def setUp(self):
        super().setUp()
        # Unique per test and per run: a sandbox may refuse to delete files
        # between tests, and stale state must never leak into a run.
        unique = "%s_%s" % (self.id().split(".")[-1], uuid.uuid4().hex[:8])
        self.actions = self.workdir / ("actions_%s.json" % unique)
        self.restore_output = self.workdir / ("restore_%s.sh" % unique)
        self.before = "before_%s" % unique
        self.after = "after_%s" % unique

    def snapshot_pair(self):
        first = self.run_tool(AUDIT, "--backups", self.workdir, "snapshot", self.before)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.env["FAKE_CYD_STATE"] = "after"
        second = self.run_tool(AUDIT, "--backups", self.workdir, "snapshot", self.after)
        self.assertEqual(second.returncode, 0, second.stderr)

    def compare(self):
        return self.run_tool(
            AUDIT, "--backups", self.workdir, "compare", self.before, self.after, "--actions", self.actions
        )

    def test_snapshot_writes_consistent_metrics(self):
        result = self.run_tool(AUDIT, "--backups", self.workdir, "snapshot", self.before)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((self.workdir / ("%s.json" % self.before)).read_text(encoding="utf-8"))
        memory = data["memory"]
        self.assertAlmostEqual(
            memory["available_ram_mb"], memory["total_ram_mb"] - memory["used_ram_mb"], places=1
        )
        self.assertGreater(memory["total_ram_mb"], 0)
        self.assertTrue(data["packages"]["list"])

    def test_compare_card_has_straight_borders(self):
        self.snapshot_pair()
        result = self.compare()
        self.assertEqual(result.returncode, 0, result.stderr)
        borders = ("\u250c", "\u2502", "\u251c", "\u2514")  # ┌ │ ├ └
        card = [line for line in result.stdout.splitlines() if line.startswith(borders)]
        self.assertTrue(card)
        widths = {len(line) for line in card}
        self.assertEqual(len(widths), 1, "card borders are ragged: %s" % sorted(widths))

    def test_report_does_not_claim_unperformed_work(self):
        self.snapshot_pair()
        self.compare()
        html = (self.workdir / "report.html").read_text(encoding="utf-8")
        self.assertNotIn("bg-dexopt-job completed", html)
        self.assertIn("not recorded", html)
        self.assertIn("No reversal script recorded", html)

    def test_actions_drive_report_and_restore_script(self):
        self.snapshot_pair()
        logged = self.run_tool(
            AUDIT,
            "--backups",
            self.workdir,
            "--adb",
            self.env["CLEANYOURDROID_ADB"],
            "log-action",
            "--actions",
            self.actions,
            "--kind",
            "package",
            "--target",
            "com.miui.msa.global",
            "--command",
            "adb shell pm uninstall -k --user 0 com.miui.msa.global",
            "--restore",
            "adb shell cmd package install-existing com.miui.msa.global",
        )
        self.assertEqual(logged.returncode, 0, logged.stderr)

        output = self.restore_output
        script = self.run_tool(
            AUDIT, "--backups", self.workdir, "restore-script", "--actions", self.actions, "--output", output
        )
        self.assertEqual(script.returncode, 0, script.stderr)
        text = output.read_text(encoding="utf-8")
        self.assertIn("install-existing com.miui.msa.global", text)
        self.assertIn("ADB=${ADB:-adb}", text)

        report = self.compare()
        self.assertEqual(report.returncode, 0, report.stderr)
        html = (self.workdir / "report.html").read_text(encoding="utf-8")
        self.assertIn("1 logged", html)
        self.assertNotIn("No reversal script recorded", html)

    def test_restore_script_without_log_fails_cleanly(self):
        result = self.run_tool(
            AUDIT, "--backups", self.workdir, "restore-script", "--actions", self.actions
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("nothing to reverse", result.stderr)


if __name__ == "__main__":
    unittest.main()
