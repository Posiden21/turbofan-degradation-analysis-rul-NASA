"""End-to-end turbofan degradation and RUL analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .data import load_turbofan_rows
from .features import add_remaining_useful_life, feature_matrix, latest_engine_scores
from .model import regression_metrics, train_linear_model
from .reporting import write_csv, write_metrics, write_summary
from .visualization import write_risk_bar_svg, write_rul_trend_svg


LATEST_FIELDS = ["unit", "latest_cycle", "remaining_useful_life", "risk_band", "health_index", "predicted_rul"]
ENRICHED_FIELDS = ["unit", "cycle", "rul", "risk_band", "health_index"]


@dataclass(frozen=True)
class PipelineResult:
    rows: int
    engines: int
    output_dir: Path
    metrics: dict[str, float]


def run_pipeline(source_path: Path, output_dir: Path) -> PipelineResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = add_remaining_useful_life(load_turbofan_rows(source_path))
    features, target = feature_matrix(rows)
    model = train_linear_model(features, target)
    predictions = model.predict(features)
    metrics = regression_metrics(target, predictions)

    latest_scores = latest_engine_scores(rows)
    feature_by_unit_cycle = {
        (int(row["unit"]), int(row["cycle"])): feature for row, feature in zip(rows, features)
    }
    latest_scores = [
        {
            **score,
            "predicted_rul": round(model.predict_one(feature_by_unit_cycle[(int(score["unit"]), int(score["latest_cycle"]))]), 1),
        }
        for score in latest_scores
    ]

    enriched_rows = [
        {
            "unit": int(row["unit"]),
            "cycle": int(row["cycle"]),
            "rul": int(row["rul"]),
            "risk_band": str(row["risk_band"]),
            "health_index": float(row["health_index"]),
        }
        for row in rows
    ]

    write_csv(output_dir / "latest_engine_scores.csv", latest_scores, LATEST_FIELDS)
    write_csv(output_dir / "enriched_cycles.csv", enriched_rows, ENRICHED_FIELDS)
    write_metrics(output_dir / "model_metrics.json", metrics)
    write_summary(output_dir / "summary.md", rows, latest_scores, metrics)
    write_rul_trend_svg(output_dir / "rul_trend.svg", enriched_rows)
    write_risk_bar_svg(output_dir / "engine_risk.svg", latest_scores)

    return PipelineResult(
        rows=len(rows),
        engines=len({int(row["unit"]) for row in rows}),
        output_dir=output_dir,
        metrics=metrics,
    )
