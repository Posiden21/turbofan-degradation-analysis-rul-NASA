"""Output writers for turbofan RUL analysis."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metrics(path: Path, metrics: dict[str, float]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2, sort_keys=True)
        file.write("\n")


def write_summary(
    path: Path,
    rows: list[dict[str, object]],
    scores: list[dict[str, object]],
    metrics: dict[str, float],
) -> None:
    most_at_risk = scores[0]
    lines = [
        "# Turbofan Engine Degradation Analysis",
        "",
        "## Dataset Snapshot",
        "",
        f"- Engines: {len(scores)}",
        f"- Rows/cycles observed: {len(rows)}",
        f"- Longest engine run: {max(int(row['cycle']) for row in rows)} cycles",
        f"- Average row-level RUL: {mean(int(row['rul']) for row in rows):.1f} cycles",
        "",
        "## Baseline RUL Model",
        "",
        f"- RMSE: {metrics['rmse']} cycles",
        f"- MAE: {metrics['mae']} cycles",
        f"- R2: {metrics['r2']}",
        "",
        "## Latest Pre-Failure Engine Risk Scores",
        "",
        "| Engine | Latest Cycle | RUL | Risk | Health Index | Predicted RUL |",
        "|---:|---:|---:|---|---:|---:|",
    ]
    for score in scores:
        lines.append(
            f"| {score['unit']} | {score['latest_cycle']} | {score['remaining_useful_life']} | "
            f"{score['risk_band']} | {score['health_index']} | {score['predicted_rul']} |"
        )

    lines.extend(
        [
            "",
            "## Main Finding",
            "",
            f"Engine {most_at_risk['unit']} is the highest-priority maintenance candidate because it has the lowest RUL and the strongest degradation score among the latest snapshots.",
            "",
            "## Notes",
            "",
            "This repository includes a small CMAPSS-style sample dataset for fast portfolio demos. For full NASA FD001 analysis, pass a parsed `train_FD001.txt` file with `--source`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
