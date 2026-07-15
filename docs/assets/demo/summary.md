# Turbofan Engine Degradation Analysis

## Dataset Snapshot

- Engines: 4
- Rows/cycles observed: 34
- Longest engine run: 11 cycles
- Average row-level RUL: 4.1 cycles

## Baseline RUL Model

- RMSE: 0.715 cycles
- MAE: 0.534 cycles
- R2: 0.938

## Latest Pre-Failure Engine Risk Scores

| Engine | Latest Cycle | RUL | Risk | Health Index | Predicted RUL |
|---:|---:|---:|---|---:|---:|
| 4 | 10 | 1 | critical | 13.255 | 0.3 |
| 1 | 7 | 1 | critical | 12.3 | 0.9 |
| 3 | 4 | 1 | critical | 11.434 | 0.9 |
| 2 | 9 | 1 | critical | 10.925 | 1.7 |

## Main Finding

Engine 4 is the highest-priority maintenance candidate because it has the lowest RUL and the strongest degradation score among the latest snapshots.

## Notes

This repository includes a small CMAPSS-style sample dataset for fast portfolio demos. For full NASA FD001 analysis, pass a parsed `train_FD001.txt` file with `--source`.
