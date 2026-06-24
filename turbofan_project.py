#!/usr/bin/env python3
"""Mini aerospace data project: NASA-style turbofan engine degradation.

This script uses a small built-in dataset shaped like NASA's Turbofan Engine
Degradation Dataset. It calculates Remaining Useful Life (RUL), scores engine
health, and prints which engine should get maintenance attention first.
"""

engines = [
    {"unit": 1, "cycle": 1, "sensor2": 642.10, "sensor3": 1582.1, "sensor4": 1398.5, "sensor7": 554.4, "sensor11": 47.20},
    {"unit": 1, "cycle": 2, "sensor2": 642.17, "sensor3": 1583.0, "sensor4": 1399.2, "sensor7": 554.0, "sensor11": 47.24},
    {"unit": 1, "cycle": 3, "sensor2": 642.26, "sensor3": 1584.2, "sensor4": 1400.1, "sensor7": 553.7, "sensor11": 47.29},
    {"unit": 1, "cycle": 4, "sensor2": 642.35, "sensor3": 1585.5, "sensor4": 1401.0, "sensor7": 553.3, "sensor11": 47.35},
    {"unit": 1, "cycle": 5, "sensor2": 642.46, "sensor3": 1586.8, "sensor4": 1402.0, "sensor7": 552.8, "sensor11": 47.41},
    {"unit": 2, "cycle": 1, "sensor2": 641.98, "sensor3": 1579.9, "sensor4": 1395.9, "sensor7": 555.2, "sensor11": 47.04},
    {"unit": 2, "cycle": 2, "sensor2": 642.03, "sensor3": 1580.4, "sensor4": 1396.5, "sensor7": 555.0, "sensor11": 47.07},
    {"unit": 2, "cycle": 3, "sensor2": 642.08, "sensor3": 1581.0, "sensor4": 1397.0, "sensor7": 554.8, "sensor11": 47.09},
    {"unit": 2, "cycle": 4, "sensor2": 642.15, "sensor3": 1581.8, "sensor4": 1397.8, "sensor7": 554.6, "sensor11": 47.12},
    {"unit": 2, "cycle": 5, "sensor2": 642.23, "sensor3": 1582.7, "sensor4": 1398.6, "sensor7": 554.3, "sensor11": 47.17},
    {"unit": 2, "cycle": 6, "sensor2": 642.32, "sensor3": 1583.8, "sensor4": 1399.7, "sensor7": 554.0, "sensor11": 47.22},
    {"unit": 2, "cycle": 7, "sensor2": 642.43, "sensor3": 1585.0, "sensor4": 1400.9, "sensor7": 553.6, "sensor11": 47.28},
    {"unit": 3, "cycle": 1, "sensor2": 642.22, "sensor3": 1583.2, "sensor4": 1398.8, "sensor7": 554.0, "sensor11": 47.23},
    {"unit": 3, "cycle": 2, "sensor2": 642.36, "sensor3": 1585.1, "sensor4": 1400.3, "sensor7": 553.5, "sensor11": 47.31},
    {"unit": 3, "cycle": 3, "sensor2": 642.52, "sensor3": 1587.0, "sensor4": 1402.1, "sensor7": 553.0, "sensor11": 47.40},
    {"unit": 3, "cycle": 4, "sensor2": 642.70, "sensor3": 1589.5, "sensor4": 1404.3, "sensor7": 552.2, "sensor11": 47.55},
]


def calculate_rul(rows):
    final_cycle_by_engine = {}

    for row in rows:
        unit = row["unit"]
        cycle = row["cycle"]
        final_cycle_by_engine[unit] = max(cycle, final_cycle_by_engine.get(unit, 0))

    for row in rows:
        row["rul"] = final_cycle_by_engine[row["unit"]] - row["cycle"]

    return rows


def health_score(row):
    """Higher score means the engine looks closer to failure."""

    rising_sensors = (
        row["sensor2"] - 642.0
        + (row["sensor3"] - 1580.0) / 10
        + (row["sensor4"] - 1396.0) / 10
        + (row["sensor11"] - 47.0) * 3
    )
    falling_sensors = (555.0 - row["sensor7"]) / 2
    return round(rising_sensors + falling_sensors, 2)


def risk_label(rul):
    if rul <= 1:
        return "critical"
    if rul <= 3:
        return "warning"
    return "monitor"


def latest_pre_failure_rows(rows):
    latest = {}

    for row in rows:
        if row["rul"] == 0:
            continue

        unit = row["unit"]
        if unit not in latest or row["cycle"] > latest[unit]["cycle"]:
            latest[unit] = row

    return list(latest.values())


def main():
    data = calculate_rul(engines)
    latest_rows = latest_pre_failure_rows(data)

    results = []
    for row in latest_rows:
        results.append(
            {
                "engine": row["unit"],
                "cycle": row["cycle"],
                "rul": row["rul"],
                "risk": risk_label(row["rul"]),
                "health_score": health_score(row),
            }
        )

    results.sort(key=lambda item: (item["rul"], -item["health_score"]))

    print("NASA Turbofan Engine Degradation Mini-Project")
    print("=" * 50)
    print("Engine | Cycle | RUL | Risk     | Health Score")
    print("-" * 50)

    for item in results:
        print(
            f"{item['engine']:>6} | "
            f"{item['cycle']:>5} | "
            f"{item['rul']:>3} | "
            f"{item['risk']:<8} | "
            f"{item['health_score']:>12}"
        )

    highest_priority = results[0]
    print()
    print(
        f"Maintenance priority: Engine {highest_priority['engine']} "
        f"because it has {highest_priority['rul']} cycle left and the highest health score."
    )


if __name__ == "__main__":
    main()
