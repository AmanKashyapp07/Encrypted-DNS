"""Unit tests for the live demo runner (scripts/demo.py)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = ROOT / "scripts" / "demo.py"


class TestLiveDemoRunner(unittest.TestCase):
    def test_demo_script_exists_and_executable(self):
        self.assertTrue(DEMO_SCRIPT.exists(), "scripts/demo.py does not exist")

    def test_part_1_fingerprinting_batch(self):
        cmd = [sys.executable, str(DEMO_SCRIPT), "--part", "1", "--non-interactive", "--domain", "youtube.com"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Part 1 failed:\n{res.stderr}")
        self.assertIn("PART 1: INTERACTIVE LIVE TRAFFIC FINGERPRINTING", res.stdout)
        self.assertIn("youtube.com", res.stdout)
        self.assertIn("CLASSIFIER PREDICTION RESULTS", res.stdout)

    def test_part_3_verification(self):
        cmd = [sys.executable, str(DEMO_SCRIPT), "--part", "3"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Part 3 failed:\n{res.stderr}")
        self.assertIn("ALL 6 NUMERICAL CONSISTENCY & CLAIMS VERIFICATION CHECKS PASSED", res.stdout)

    def test_part_4_deliverables_tour(self):
        cmd = [sys.executable, str(DEMO_SCRIPT), "--part", "4"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Part 4 failed:\n{res.stderr}")
        self.assertIn("PRIMARY RESEARCH ARTIFACTS", res.stdout)
        self.assertIn("paper.pdf", res.stdout)

    def test_part_5_viva_cheatsheet(self):
        cmd = [sys.executable, str(DEMO_SCRIPT), "--part", "5"]
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Part 5 failed:\n{res.stderr}")
        self.assertIn("VIVA DEFENSE CHEAT SHEET", res.stdout)


if __name__ == "__main__":
    unittest.main()
