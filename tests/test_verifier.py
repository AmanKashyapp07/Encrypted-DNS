"""Unit tests for research result verifier, including comprehensive positive and negative failure-mode tests."""

import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

from scripts.verify_research_results import (
    verify_datasets,
    verify_feature_space,
    verify_baselines,
    verify_jio_quic_blocking,
    verify_model_comparisons,
    verify_claims_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
_ORIG_READ_CSV = pd.read_csv


class TestResearchVerifier(unittest.TestCase):
    def test_verify_datasets(self):
        self.assertTrue(verify_datasets())

    def test_verify_feature_space(self):
        self.assertTrue(verify_feature_space())

    def test_verify_baselines(self):
        self.assertTrue(verify_baselines())

    def test_verify_jio_quic_blocking(self):
        self.assertTrue(verify_jio_quic_blocking())

    def test_verify_model_comparisons(self):
        self.assertTrue(verify_model_comparisons())

    def test_verify_claims_ledger(self):
        self.assertTrue(verify_claims_ledger())

    def test_negative_corrupted_accuracy_rejected(self):
        """Verifier must catch and reject any corrupted accuracy value in claims ledger."""
        real_df = _ORIG_READ_CSV(ROOT / "docs/claims_ledger.csv")
        corrupted = real_df.copy()
        corrupted.loc[0, "value"] = 0.9999  # Corrupt first claim value

        def mock_read_csv(path, *args, **kwargs):
            if "claims_ledger.csv" in str(path):
                return corrupted.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_claims_ledger())

    def test_negative_invalid_commit_rejected(self):
        """Verifier must catch and reject invalid or non-existent commit hashes."""
        real_df = _ORIG_READ_CSV(ROOT / "docs/claims_ledger.csv")
        corrupted = real_df.copy()
        corrupted.loc[0, "commit"] = "0000000000000000000000000000000000000000"

        def mock_read_csv(path, *args, **kwargs):
            if "claims_ledger.csv" in str(path):
                return corrupted.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_claims_ledger())

    def test_negative_malformed_commit_sha_rejected(self):
        """Verifier must catch and reject non-40-hex commit hashes (e.g. malformed or short)."""
        real_df = _ORIG_READ_CSV(ROOT / "docs/claims_ledger.csv")
        corrupted = real_df.copy()
        corrupted.loc[0, "commit"] = "not_a_valid_git_sha"

        def mock_read_csv(path, *args, **kwargs):
            if "claims_ledger.csv" in str(path):
                return corrupted.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_claims_ledger())

    def test_negative_missing_column_rejected(self):
        """Verifier must fail if required schema columns are missing."""
        real_df = _ORIG_READ_CSV(ROOT / "docs/claims_ledger.csv")
        corrupted = real_df.drop(columns=["confidence_interval"])

        def mock_read_csv(path, *args, **kwargs):
            if "claims_ledger.csv" in str(path):
                return corrupted.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_claims_ledger())

    def test_negative_ambiguous_slice_rejected(self):
        """Verifier must reject ambiguous slices if multiple rows match a single claim."""
        real_df = _ORIG_READ_CSV(ROOT / "docs/claims_ledger.csv")
        corrupted = real_df.copy()
        # Remove resolver constraint so it matches multiple rows in source CSV
        corrupted.loc[0, "resolver"] = None

        def mock_read_csv(path, *args, **kwargs):
            if "claims_ledger.csv" in str(path):
                return corrupted.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_claims_ledger())

    def test_negative_corrupted_ci_bounds_rejected(self):
        """Verifier must reject confidence intervals in claims ledger that diverge from source CSV."""
        real_df = _ORIG_READ_CSV(ROOT / "docs/claims_ledger.csv")
        corrupted = real_df.copy()
        corrupted.loc[0, "confidence_interval"] = "[0.8000, 0.9500]"  # Corrupted CI bounds

        def mock_read_csv(path, *args, **kwargs):
            if "claims_ledger.csv" in str(path):
                return corrupted.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_claims_ledger())

    def test_negative_duplicate_model_rows_rejected(self):
        """Verifier must reject model comparison file if duplicate rows for a model exist."""
        real_mc = _ORIG_READ_CSV(ROOT / "results/airtel_advanced_20261113/model_comparison.csv")
        corrupted_mc = pd.concat([real_mc, real_mc.iloc[[0]]], ignore_index=True)  # Duplicate first row

        def mock_read_csv(path, *args, **kwargs):
            if "model_comparison.csv" in str(path):
                return corrupted_mc.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_model_comparisons())

    def test_negative_duplicate_rf_headline_rejected(self):
        """Verifier must reject model comparison if headline fingerprinting output has duplicate rows."""
        real_fp = _ORIG_READ_CSV(ROOT / "results/airtel_topup_20261113/rq1_rq2_fingerprinting.csv")
        corrupted_fp = pd.concat([real_fp, real_fp.iloc[[0]]], ignore_index=True)

        def mock_read_csv(path, *args, **kwargs):
            if "rq1_rq2_fingerprinting.csv" in str(path):
                return corrupted_fp.copy()
            return _ORIG_READ_CSV(path, *args, **kwargs)

        with patch("scripts.verify_research_results.pd.read_csv", side_effect=mock_read_csv):
            self.assertFalse(verify_model_comparisons())


if __name__ == "__main__":
    unittest.main()
