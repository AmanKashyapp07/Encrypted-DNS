"""Unit tests for statistical primitives and uncertainty estimation."""

import unittest
import numpy as np
from src.encdns.analysis.stats import (
    wilson_interval,
    domain_clustered_bootstrap,
    fdr_correction,
)


class TestStatisticalPrimitives(unittest.TestCase):
    def test_wilson_interval_bounds(self):
        low, high = wilson_interval(50, 100)
        self.assertGreater(low, 0.35)
        self.assertLess(high, 0.65)
        self.assertLess(low, high)

    def test_wilson_interval_zero_and_full(self):
        low_zero, high_zero = wilson_interval(0, 100)
        self.assertAlmostEqual(low_zero, 0.0)
        self.assertGreater(high_zero, 0.0)

        low_full, high_full = wilson_interval(100, 100)
        self.assertLess(low_full, 1.0)
        self.assertAlmostEqual(high_full, 1.0)

    def test_domain_clustered_bootstrap(self):
        # 10 domains, 5 queries each = 50 items
        rng = np.random.default_rng(42)
        domains = np.repeat([f"dom{i}" for i in range(10)], 5)
        # Half domains always correct, half always incorrect
        y_true = np.repeat([0, 1] * 5, 5)
        y_pred = y_true.copy()
        y_pred[domains == "dom0"] = 1 - y_pred[domains == "dom0"]

        low, high = domain_clustered_bootstrap(
            actual=y_true,
            predicted=y_pred,
            domains=domains,
            n_bootstraps=200,
            alpha=0.05,
            seed=42,
        )
        self.assertGreater(low, 0.5)
        self.assertLessEqual(high, 1.0)
        self.assertLess(low, high)

    def test_fdr_correction(self):
        p_values = [0.001, 0.004, 0.012, 0.045, 0.15, 0.80]
        p_adj = fdr_correction(p_values, alpha=0.05)
        self.assertEqual(len(p_adj), len(p_values))
        self.assertLess(p_adj[0], 0.05)
        self.assertGreater(p_adj[-1], 0.5)


if __name__ == "__main__":
    unittest.main()
