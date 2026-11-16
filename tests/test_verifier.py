"""Unit tests for research result verifier, including positive and negative cases."""

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


if __name__ == "__main__":
    unittest.main()
