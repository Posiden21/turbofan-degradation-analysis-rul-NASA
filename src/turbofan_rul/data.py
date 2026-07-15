"""Data loading helpers for CMAPSS-style turbofan engine cycle data."""

from __future__ import annotations

import csv
from pathlib import Path


CMAPSS_COLUMNS = (
    ["unit", "cycle"]
    + [f"setting{i}" for i in range(1, 4)]
    + [f"sensor{i}" for i in range(1, 22)]
)


def load_turbofan_rows(path: Path) -> list[dict[str, float | int]]:
    """Load either a headered CSV sample or a NASA CMAPSS whitespace-delimited text file."""
    if path.suffix.lower() == ".csv":
        return _load_csv(path)
    return _load_cmapss_text(path)


def _load_csv(path: Path) -> list[dict[str, float | int]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [_coerce_row(row) for row in reader]


def _load_cmapss_text(path: Path) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            values = line.strip().split()
            if not values:
                continue
            if len(values) != len(CMAPSS_COLUMNS):
                raise ValueError(f"line {line_number} has {len(values)} columns; expected {len(CMAPSS_COLUMNS)}")
            rows.append(_coerce_row(dict(zip(CMAPSS_COLUMNS, values))))
    return rows


def _coerce_row(row: dict[str, str]) -> dict[str, float | int]:
    coerced: dict[str, float | int] = {}
    for key, value in row.items():
        if key in {"unit", "cycle"}:
            coerced[key] = int(float(value))
        else:
            coerced[key] = float(value)
    return coerced
