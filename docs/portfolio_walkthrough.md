# Portfolio Walkthrough

Use this project to explain a predictive-maintenance workflow for turbofan engines.

## 1. Problem

Aircraft turbofan engines degrade over operating cycles. Maintenance teams need to know which engine is closest to failure so inspections can be prioritized before unscheduled downtime.

## 2. Dataset

The included sample data follows the NASA CMAPSS format:

- `unit`: engine identifier
- `cycle`: operating cycle
- `setting1` through `setting3`: operating conditions
- selected sensor columns such as `sensor2`, `sensor4`, `sensor11`, and `sensor15`

For NASA training data, each engine's final cycle is treated as the failure point. Remaining Useful Life is calculated as:

```text
RUL = max_cycle_for_engine - current_cycle
```

## 3. Pipeline

```text
CMAPSS-style CSV or TXT
  -> load and coerce numeric rows
  -> calculate RUL
  -> create health index
  -> fit baseline RUL model
  -> score latest pre-failure engine snapshot
  -> export CSV, JSON, Markdown, and SVG reports
```

## 4. Demo

```bash
python3 -m pip install -e .
turbofan-rul
```

Open `results/summary.md`, `results/rul_trend.svg`, and `results/engine_risk.svg`.

## 5. Talking Points

- The project separates data loading, feature engineering, modeling, reporting, and CLI layers.
- It includes a small dataset so reviewers can run it immediately.
- It supports NASA CMAPSS-style whitespace-delimited files through `--source`.
- The model is intentionally lightweight and explainable for a portfolio demo.
- A full production version would validate on the full FD001/FD002/FD003/FD004 datasets and compare stronger models.
