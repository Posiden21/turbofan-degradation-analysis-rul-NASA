#!/usr/bin/env python3
"""Small predictive-maintenance analysis for NASA CMAPSS-style turbofan data.

The real NASA CMAPSS training files use one row per engine cycle. For each
engine, the last row represents failure, so Remaining Useful Life (RUL) can be
computed as: max_cycle_for_engine - current_cycle.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sample_turbofan.csv"
RESULTS_DIR = ROOT / "results"
SUMMARY_PATH = RESULTS_DIR / "summary.md"
PREDICTIONS_PATH = RESULTS_DIR / "latest_engine_scores.csv"


RISK_BANDS = (
    (2, "critical"),
    (5, "warning"),
    (9999, "monitor"),
)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def add_remaining_useful_life(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    max_cycle_by_unit: dict[int, int] = defaultdict(int)
    for row in rows:
        unit = int(row["unit"])
        cycle = int(row["cycle"])
        max_cycle_by_unit[unit] = max(max_cycle_by_unit[unit], cycle)

    enriched: list[dict[str, object]] = []
    for row in rows:
        unit = int(row["unit"])
        cycle = int(row["cycle"])
        numeric_row: dict[str, object] = {
            key: float(value) if key not in {"unit", "cycle"} else int(value)
            for key, value in row.items()
        }
        numeric_row["rul"] = max_cycle_by_unit[unit] - cycle
        enriched.append(numeric_row)

    return enriched


def health_index(row: dict[str, object]) -> float:
    """Higher score means the engine looks closer to failure.

    The sample combines sensors that usually rise during degradation with
    sensors that usually fall. This is a simple teaching metric, not a certified
    aircraft-health model.
    """

    rising_pressure_temp = (
        float(row["sensor2"]) - 642.0
        + (float(row["sensor3"]) - 1580.0) / 10
        + (float(row["sensor4"]) - 1396.0) / 10
        + (float(row["sensor11"]) - 47.0) * 3
        + (float(row["sensor15"]) - 8.35) * 20
    )
    falling_efficiency = (
        (555.0 - float(row["sensor7"])) / 2
        + (523.0 - float(row["sensor12"])) / 2
        + (39.3 - float(row["sensor20"])) * 2
        + (23.5 - float(row["sensor21"])) * 3
    )
    return round(rising_pressure_temp + falling_efficiency, 3)


def risk_band(rul: int) -> str:
    for threshold, label in RISK_BANDS:
        if rul <= threshold:
            return label
    raise AssertionError("unreachable")


def latest_engine_scores(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Score the latest pre-failure row for each engine.

    CMAPSS training data includes each engine's failure row. For a maintenance
    decision, the more useful snapshot is the last observed cycle before that
    failure point.
    """

    latest_by_unit: dict[int, dict[str, object]] = {}
    for row in rows:
        if int(row["rul"]) == 0:
            continue
        unit = int(row["unit"])
        if unit not in latest_by_unit or int(row["cycle"]) > int(latest_by_unit[unit]["cycle"]):
            latest_by_unit[unit] = row

    scored = []
    for row in latest_by_unit.values():
        rul = int(row["rul"])
        scored.append(
            {
                "unit": row["unit"],
                "latest_cycle": row["cycle"],
                "remaining_useful_life": rul,
                "risk_band": risk_band(rul),
                "health_index": health_index(row),
            }
        )
    return sorted(scored, key=lambda item: (int(item["remaining_useful_life"]), int(item["unit"])))


def write_predictions(scores: list[dict[str, object]], path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["unit", "latest_cycle", "remaining_useful_life", "risk_band", "health_index"],
        )
        writer.writeheader()
        writer.writerows(scores)


def write_summary(rows: list[dict[str, object]], scores: list[dict[str, object]], path: Path) -> None:
    cycles = [int(row["cycle"]) for row in rows]
    ruls = [int(row["rul"]) for row in rows]
    most_at_risk = sorted(
        scores,
        key=lambda score: (int(score["remaining_useful_life"]), -float(score["health_index"])),
    )[0]
    average_health = mean(float(score["health_index"]) for score in scores)

    lines = [
        "# Turbofan Engine Degradation Mini-Analysis",
        "",
        "## What this dataset tells us",
        "",
        "Each row is one engine at one operating cycle. The final cycle for each engine is treated as the failure point, which lets us calculate Remaining Useful Life (RUL).",
        "",
        "## Dataset Snapshot",
        "",
        f"- Engines: {len(scores)}",
        f"- Rows/cycles observed: {len(rows)}",
        f"- Longest engine run: {max(cycles)} cycles",
        f"- Average row-level RUL: {mean(ruls):.1f} cycles",
        "",
            "## Latest Pre-Failure Engine Risk Scores",
        "",
        "| Engine | Latest Cycle | RUL | Risk | Health Index |",
        "|---:|---:|---:|---|---:|",
    ]

    for score in scores:
        lines.append(
            f"| {score['unit']} | {score['latest_cycle']} | {score['remaining_useful_life']} | "
            f"{score['risk_band']} | {score['health_index']} |"
        )

    lines.extend(
        [
            "",
            "## Main Finding",
            "",
            f"Engine {most_at_risk['unit']} is the highest-priority maintenance candidate because it has the lowest RUL among the current snapshots and the strongest degradation score in that group.",
            "",
            "## How to use this with the real NASA data",
            "",
            "Replace `data/sample_turbofan.csv` with a parsed CMAPSS file such as `train_FD001.txt`. Keep the same idea: group by engine, find each engine's max cycle, compute `RUL = max_cycle - cycle`, then train or score from the sensor columns.",
            "",
            "## Caveat",
            "",
            f"This is a tiny teaching dataset with an average latest-engine health index of {average_health:.2f}. It demonstrates the workflow, but it is not large enough for a real model.",
            "",
        ]
    )

    path.write_text("\n".join(lines))


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = add_remaining_useful_life(load_rows(DATA_PATH))
    scores = latest_engine_scores(rows)
    write_predictions(scores, PREDICTIONS_PATH)
    write_summary(rows, scores, SUMMARY_PATH)
    print(f"Wrote {PREDICTIONS_PATH}")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
