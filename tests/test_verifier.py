"""Unit tests for research result verifier."""

import unittest
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
