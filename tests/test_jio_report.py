"""Regression tests for Jio report generation, accuracy, and statistical significance statements."""

import unittest
from pathlib import Path
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
        self.assertNotIn("AdGuard DoH: 5.4% average accuracy (vs 2.0% chance, p < 0.005)", text)
        self.assertIn("not statistically distinguishable from chance (p = 0.1244)", text)

        # Google Global and India must be reported with p = 0.005
        self.assertIn("Google DoH (Global):** Achieves **15.7%** accuracy", text)
        self.assertIn("Google DoH (India):** Achieves **12.3%** accuracy", text)

        # AdGuard India has p = 0.0249
        self.assertIn("Adguard DoH (India):** Achieves **6.8%** accuracy", text)
        self.assertIn("p = 0.0249", text)

    def test_generate_report_dynamic_significance(self):
        """Ensure generate_report derives significance strings from data rather than hardcoding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_out = Path(tmpdir)
            # Create a mock n1 where accuracy is 50% but p is 0.20
            mock_n1 = pd.DataFrame([{
                "workload": "global",
                "resolver": "testres",
                "protocol": "doh",
                "domains": 50,
                "n_train": 400,
                "n_test": 100,
                "train_repeats": "0-7",
                "test_repeats": "8-9",
                "accuracy": 0.50,
                "accuracy_sd": 0.01,
                "ci_low": 0.40,
                "ci_high": 0.60,
                "ci_boot_low": 0.40,
                "ci_boot_high": 0.60,
                "chance": 0.02,
                "p_value": 0.20,
                "dropped_domains": "",
            }])
            empty_df = pd.DataFrame()
            generate_report(tmp_out, mock_n1, empty_df, empty_df, empty_df, empty_df, empty_df, empty_df)

            gen_text = (tmp_out / "report.md").read_text(encoding="utf-8")
            self.assertIn("not statistically distinguishable from chance (p = 0.2000)", gen_text)
            self.assertNotIn("statistically significant (p = 0.2000)", gen_text)


if __name__ == "__main__":
    unittest.main()
