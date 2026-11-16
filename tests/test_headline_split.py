"""Unit tests asserting exact headline repeat indices, domain coverage, and no leakage."""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path

from src.encdns.analysis.fingerprinting import (
    select_headline_repeats,
    evaluate,
)

ROOT = Path(__file__).resolve().parents[1]


class TestHeadlineSplit(unittest.TestCase):
    def setUp(self):
        # Synthetic frame with 10 domains and repeats 0 through 19 (20 repeats each)
        rows = []
        for d in range(10):
            dom = f"domain{d}.org"
            for rep in range(20):
                rows.append({
                    "domain": dom,
                    "repeat": rep,
                    "bytes_total": 100 + d * 10 + rep,
                    "n_pkts": 20 + rep,
                })
        self.synthetic_df = pd.DataFrame(rows)

    def test_temporal_holdout_exact_repeats(self):
        selected, dropped = select_headline_repeats(
            self.synthetic_df,
            repeat_start=8,
            repeat_end=19,
            split_strategy="temporal_holdout",
        )
        self.assertEqual(len(dropped), 0)
        
        train_reps = set(range(8, 18))  # 8..17
        test_reps = {18, 19}
        
        train = selected[selected["repeat"].isin(train_reps)]
        test = selected[selected["repeat"].isin(test_reps)]
        
        # Verify exact repeat sets
        self.assertEqual(set(train["repeat"]), train_reps)
        self.assertEqual(set(test["repeat"]), test_reps)
        
        # Verify no overlap between train and test repeats
        self.assertEqual(len(set(train["repeat"]).intersection(set(test["repeat"]))), 0)
        
        # Verify domain coverage
        self.assertEqual(set(train["domain"]), set(test["domain"]))
        self.assertEqual(len(set(train["domain"])), 10)

    def test_domain_filtering_when_domain_missing_in_test(self):
        # Remove repeats 18 and 19 for domain0.org
        mod_df = self.synthetic_df[~((self.synthetic_df["domain"] == "domain0.org") & (self.synthetic_df["repeat"].isin([18, 19])))]
        selected, dropped = select_headline_repeats(
            mod_df,
            repeat_start=8,
            repeat_end=19,
            split_strategy="temporal_holdout",
        )
        self.assertIn("domain0.org", dropped)
        self.assertNotIn("domain0.org", selected["domain"].values)
        self.assertEqual(selected["domain"].nunique(), 9)

    def test_evaluate_default_is_temporal_holdout(self):
        res = evaluate(
            self.synthetic_df,
            seeds=[17, 42],
            permutations=10,
            estimators=10,
            features=["bytes_total", "n_pkts"],
        )
        self.assertIsNotNone(res)
        self.assertEqual(res["split_strategy"], "temporal_holdout")
        self.assertEqual(res["train_repeats"], "8-17")
        self.assertEqual(res["test_repeats"], "18-19")
        self.assertEqual(res["n_train"], 100)  # 10 domains * 10 repeats
        self.assertEqual(res["n_test"], 20)    # 10 domains * 2 repeats


if __name__ == "__main__":
    unittest.main()
