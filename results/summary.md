# Turbofan Engine Degradation Mini-Analysis

## What this dataset tells us

Each row is one engine at one operating cycle. The final cycle for each engine is treated as the failure point, which lets us calculate Remaining Useful Life (RUL).

## Dataset Snapshot

- Engines: 4
- Rows/cycles observed: 34
- Longest engine run: 11 cycles
- Average row-level RUL: 4.1 cycles

## Latest Pre-Failure Engine Risk Scores

| Engine | Latest Cycle | RUL | Risk | Health Index |
|---:|---:|---:|---|---:|
| 1 | 7 | 1 | critical | 12.3 |
| 2 | 9 | 1 | critical | 10.925 |
| 3 | 4 | 1 | critical | 11.434 |
| 4 | 10 | 1 | critical | 13.255 |

## Main Finding

Engine 4 is the highest-priority maintenance candidate because it has the lowest RUL among the current snapshots and the strongest degradation score in that group.

## How to use this with the real NASA data

Replace `data/sample_turbofan.csv` with a parsed CMAPSS file such as `train_FD001.txt`. Keep the same idea: group by engine, find each engine's max cycle, compute `RUL = max_cycle - cycle`, then train or score from the sensor columns.

## Caveat

This is a tiny teaching dataset with an average latest-engine health index of 11.98. It demonstrates the workflow, but it is not large enough for a real model.
