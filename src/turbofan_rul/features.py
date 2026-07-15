"""Feature engineering and scoring rules for turbofan RUL analysis."""

from __future__ import annotations

from collections import defaultdict


RISK_BANDS = (
    (2, "critical"),
    (5, "warning"),
    (10_000, "monitor"),
)


def add_remaining_useful_life(rows: list[dict[str, float | int]]) -> list[dict[str, float | int | str]]:
    """Add row-level RUL using each engine's final observed cycle as the failure point."""
    max_cycle_by_unit: dict[int, int] = defaultdict(int)
    for row in rows:
        unit = int(row["unit"])
        cycle = int(row["cycle"])
        max_cycle_by_unit[unit] = max(max_cycle_by_unit[unit], cycle)

    enriched = []
    for row in rows:
        unit = int(row["unit"])
        cycle = int(row["cycle"])
        record = dict(row)
        record["rul"] = max_cycle_by_unit[unit] - cycle
        record["health_index"] = health_index(record)
        record["risk_band"] = risk_band(int(record["rul"]))
        enriched.append(record)
    return enriched


def health_index(row: dict[str, float | int | str]) -> float:
    """Calculate a simple degradation score from common CMAPSS sensor trends."""
    score = 0.0
    score += _sensor(row, "sensor2", 642.0, scale=1.0, direction=1)
    score += _sensor(row, "sensor3", 1580.0, scale=10.0, direction=1)
    score += _sensor(row, "sensor4", 1396.0, scale=10.0, direction=1)
    score += _sensor(row, "sensor11", 47.0, scale=1 / 3, direction=1)
    score += _sensor(row, "sensor15", 8.35, scale=1 / 20, direction=1)
    score += _sensor(row, "sensor7", 555.0, scale=2.0, direction=-1)
    score += _sensor(row, "sensor12", 523.0, scale=2.0, direction=-1)
    score += _sensor(row, "sensor20", 39.3, scale=0.5, direction=-1)
    score += _sensor(row, "sensor21", 23.5, scale=1 / 3, direction=-1)
    return round(score, 3)


def risk_band(rul: int) -> str:
    for threshold, label in RISK_BANDS:
        if rul <= threshold:
            return label
    raise AssertionError("unreachable")


def latest_engine_scores(rows: list[dict[str, float | int | str]]) -> list[dict[str, float | int | str]]:
    """Return the latest pre-failure observation for each engine."""
    latest_by_unit: dict[int, dict[str, float | int | str]] = {}
    for row in rows:
        if int(row["rul"]) == 0:
            continue
        unit = int(row["unit"])
        if unit not in latest_by_unit or int(row["cycle"]) > int(latest_by_unit[unit]["cycle"]):
            latest_by_unit[unit] = row

    scores = []
    for row in latest_by_unit.values():
        scores.append(
            {
                "unit": int(row["unit"]),
                "latest_cycle": int(row["cycle"]),
                "remaining_useful_life": int(row["rul"]),
                "risk_band": str(row["risk_band"]),
                "health_index": float(row["health_index"]),
            }
        )
    return sorted(scores, key=lambda score: (int(score["remaining_useful_life"]), -float(score["health_index"])))


def feature_matrix(rows: list[dict[str, float | int | str]]) -> tuple[list[list[float]], list[float]]:
    """Build simple model features: cycle, health index, and selected sensor readings."""
    sensor_names = ["sensor2", "sensor3", "sensor4", "sensor7", "sensor11", "sensor12", "sensor15", "sensor20", "sensor21"]
    x_rows: list[list[float]] = []
    y_values: list[float] = []
    for row in rows:
        x_rows.append([1.0, float(row["cycle"]), float(row["health_index"])] + [float(row.get(name, 0.0)) for name in sensor_names])
        y_values.append(float(row["rul"]))
    return x_rows, y_values


def _sensor(row: dict[str, float | int | str], name: str, baseline: float, *, scale: float, direction: int) -> float:
    if name not in row:
        return 0.0
    value = float(row[name])
    return direction * (value - baseline) / scale
