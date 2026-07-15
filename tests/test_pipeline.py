from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from turbofan_rul.data import load_turbofan_rows
from turbofan_rul.features import add_remaining_useful_life, latest_engine_scores, risk_band
from turbofan_rul.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_turbofan.csv"


class FeatureTests(unittest.TestCase):
    def test_rul_is_calculated_per_engine(self) -> None:
        rows = add_remaining_useful_life(load_turbofan_rows(SAMPLE))

        first_engine_rows = [row for row in rows if row["unit"] == 1]

        self.assertEqual(first_engine_rows[0]["rul"], 7)
        self.assertEqual(first_engine_rows[-1]["rul"], 0)
        self.assertEqual(risk_band(1), "critical")
        self.assertEqual(risk_band(4), "warning")

    def test_latest_scores_skip_failure_rows(self) -> None:
        rows = add_remaining_useful_life(load_turbofan_rows(SAMPLE))
        scores = latest_engine_scores(rows)

        self.assertEqual(len(scores), 4)
        self.assertTrue(all(score["remaining_useful_life"] > 0 for score in scores))


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = run_pipeline(SAMPLE, output_dir)

            self.assertEqual(result.engines, 4)
            self.assertTrue((output_dir / "latest_engine_scores.csv").exists())
            self.assertTrue((output_dir / "enriched_cycles.csv").exists())
            self.assertTrue((output_dir / "summary.md").exists())
            self.assertTrue((output_dir / "rul_trend.svg").exists())
            self.assertTrue((output_dir / "engine_risk.svg").exists())

            metrics = json.loads((output_dir / "model_metrics.json").read_text())
            self.assertIn("rmse", metrics)
            self.assertGreaterEqual(metrics["rmse"], 0)


if __name__ == "__main__":
    unittest.main()
