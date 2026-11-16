"""Regression tests for Jio report generation, accuracy, and statistical significance statements."""

import unittest
from pathlib import Path
import re
import tempfile
import pandas as pd

from scripts.run_jio_analysis import generate_report

ROOT = Path(__file__).resolve().parents[1]


class TestJioReport(unittest.TestCase):
    def setUp(self):
        self.report_path = ROOT / "results/jio_analysis_20261113/report.md"
        self.n1_path = ROOT / "results/jio_analysis_20261113/n1_within_jio.csv"

    def test_report_exists_and_n1_consistency(self):
        self.assertTrue(self.report_path.exists(), "results/jio_analysis_20261113/report.md must exist")
        self.assertTrue(self.n1_path.exists(), "results/jio_analysis_20261113/n1_within_jio.csv must exist")

        text = self.report_path.read_text(encoding="utf-8")
        df_n1 = pd.read_csv(self.n1_path)

        # AdGuard Global has p = 0.1244: must NOT claim p < 0.005 or blanket significance
        self.assertNotIn("AdGuard DoH: 5.4% average accuracy", text)
        self.assertIn("not statistically distinguishable from chance (nominal p = 0.1244)", text)

        # Google Global and India must be reported with nominal p = 0.005
        self.assertIn("Google DoH (Global):** Achieves **15.7%** accuracy", text)
        self.assertIn("Google DoH (India):** Achieves **12.3%** accuracy", text)

        # AdGuard India has p = 0.0249 with proper capitalization
        self.assertIn("AdGuard DoH (India):** Achieves **6.8%** accuracy", text)
        self.assertIn("nominal p = 0.0249", text)

        # Exactly 4 bullets in N1 section corresponding to the 4 N1 rows
        n1_section = re.search(r"## N1: Within-Jio Fingerprinting Performance.*?\n\n(.*?)\n\n---", text, re.DOTALL)
        self.assertIsNotNone(n1_section)
        bullets = [line for line in n1_section.group(1).splitlines() if line.startswith("- **")]
        self.assertEqual(len(bullets), len(df_n1), f"Expected {len(df_n1)} N1 finding bullets, found {len(bullets)}")

    def test_generate_report_dynamic_significance_and_no_hardcoded_bullets(self):
        """Ensure generate_report derives findings strictly from rows with zero hardcoded bullets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_out = Path(tmpdir)
            # Create a mock dataframe with 2 custom resolvers (one significant, one non-significant)
            mock_n1 = pd.DataFrame([
                {
                    "workload": "global",
                    "resolver": "adguard",  # Test standard capitalization
                    "protocol": "doh",
                    "domains": 50,
                    "n_train": 400,
                    "n_test": 100,
                    "train_repeats": "0-7",
                    "test_repeats": "8-9",
                    "accuracy": 0.25,
                    "accuracy_sd": 0.01,
                    "ci_low": 0.15,
                    "ci_high": 0.35,
                    "ci_boot_low": 0.15,
                    "ci_boot_high": 0.35,
                    "chance": 0.02,
                    "p_value": 0.0100,  # Significant
                    "dropped_domains": "",
                },
                {
                    "workload": "india",
                    "resolver": "customres",
                    "protocol": "doh",
                    "domains": 50,
                    "n_train": 400,
                    "n_test": 100,
                    "train_repeats": "0-7",
                    "test_repeats": "8-9",
                    "accuracy": 0.03,
                    "accuracy_sd": 0.01,
                    "ci_low": 0.00,
                    "ci_high": 0.08,
                    "ci_boot_low": 0.00,
                    "ci_boot_high": 0.08,
                    "chance": 0.02,
                    "p_value": 0.3500,  # Non-significant
                    "dropped_domains": "",
                }
            ])
            empty_df = pd.DataFrame()
            generate_report(tmp_out, mock_n1, empty_df, empty_df, empty_df, empty_df, empty_df, empty_df)

            gen_text = (tmp_out / "report.md").read_text(encoding="utf-8")

            # Check dynamic significant and non-significant text
            self.assertIn("AdGuard DoH (Global):** Achieves **25.0%** accuracy (vs 2.0% chance, n_test=100), statistically significant (nominal p = 0.0100).", gen_text)
            self.assertIn("Customres DoH (India):** Achieves **3.0%** accuracy (vs 2.0% chance, n_test=100), not statistically distinguishable from chance (nominal p = 0.3500).", gen_text)

            # Check that no unrelated hardcoded Google conclusions exist
            self.assertNotIn("Google DoH remains statistically significant", gen_text)
            self.assertNotIn("AdGuard DoH achieves statistical significance on the India workload", gen_text)

            # Check that N1 findings section has exactly 2 bullets matching the 2 mock rows
            n1_section = re.search(r"## N1: Within-Jio Fingerprinting Performance.*?\n\n(.*?)\n\n---", gen_text, re.DOTALL)
            self.assertIsNotNone(n1_section)
            bullets = [line for line in n1_section.group(1).splitlines() if line.startswith("- **")]
            self.assertEqual(len(bullets), 2)

    def test_n2_and_n3_findings_language(self):
        """Ensure N2 and N3 findings avoid overclaiming and accurately state empirical results."""
        text = self.report_path.read_text(encoding="utf-8")

        # N2: Should not overclaim absolute non-generalization without an equivalence test
        self.assertNotIn("Models trained on fixed broadband do not generalize to cellular traffic without multi-network training.", text)
        self.assertIn("Across the evaluated cross-network slices, transfer accuracy remained close to the 2.0% chance baseline (1.7%–2.4%)", text)
        self.assertIn("indicate substantial cross-network performance degradation", text)

        # N3: Should not claim uniform blanket recovery across networks
        self.assertNotIn("Multi-network training successfully recovers accuracy when evaluating on either network", text)
        self.assertIn("recovery is resolver-dependent", text)
        self.assertIn("Google achieves 13.3%–15.0% accuracy, while AdGuard achieves 3.4%–4.4%", text)


if __name__ == "__main__":
    unittest.main()
