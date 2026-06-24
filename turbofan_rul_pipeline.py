#!/usr/bin/env python3
"""
turbofan_rul_pipeline.py
========================
NASA CMAPSS Turbofan RUL Predictive Maintenance Pipeline
---------------------------------------------------------
Requires: CMAPSSData.zip in the working directory.

Blocks:
  1. turbofan_rul_analysis    — Load data, compute RUL, health index, risk bands
  2. rul_trend_chart          — RUL degradation trend chart (stratified sample)
  3. feature_engineering      — Rolling features, scaling, engine-level train/test split
  4. model_training           — GradientBoostingRegressor, evaluation metrics
  5. model_evaluation_charts  — Actual vs Predicted scatter + Feature importance bar chart

Usage:
  python turbofan_rul_pipeline.py
  # Charts are saved as PNG files if matplotlib is available.
"""

# ==============================================================================
# BLOCK 1 — turbofan_rul_analysis
# ==============================================================================
"""Predictive-maintenance analysis for NASA CMAPSS turbofan data.

Loads train_FD001.txt from CMAPSSData.zip. The file is space-delimited with
no header: unit, cycle, setting1-3, sensor1-21 (26 columns total).

RUL = max_cycle_for_engine - current_cycle  (0 at the failure point).
"""

from __future__ import annotations

import zipfile
import io
from collections import defaultdict
from statistics import mean

import pandas as pd

# Column names for FD001 (no header in the file)
_COLS = (
    ["unit", "cycle"]
    + [f"setting{i}" for i in range(1, 4)]
    + [f"sensor{i}"  for i in range(1, 22)]
)

ZIP_FILE  = "CMAPSSData.zip"
DATA_FILE = "train_FD001.txt"

with zipfile.ZipFile(ZIP_FILE) as _zf:
    _names = _zf.namelist()
    _match = next((n for n in _names if n.endswith("train_FD001.txt")), None)
    if _match is None:
        raise FileNotFoundError(
            f"train_FD001.txt not found in {ZIP_FILE}. "
            f"Available files: {_names}"
        )
    with _zf.open(_match) as _f:
        _raw_df = pd.read_csv(
            io.TextIOWrapper(_f),
            sep=r"\s+",
            header=None,
            names=_COLS,
            engine="python",
        )

_raw_df = _raw_df.dropna(axis=1, how="all")

print(f"Loaded {len(_raw_df):,} rows, {_raw_df['unit'].nunique()} engines from {DATA_FILE}")

# Compute RUL per row
_max_cycle = _raw_df.groupby("unit")["cycle"].max().rename("max_cycle")
_raw_df    = _raw_df.join(_max_cycle, on="unit")
_raw_df["rul"] = _raw_df["max_cycle"] - _raw_df["cycle"]

# Risk thresholds
RISK_BANDS = (
    (30,   "critical"),
    (80,   "warning"),
    (9999, "monitor"),
)

def _risk_band(rul: int) -> str:
    for threshold, label in RISK_BANDS:
        if rul <= threshold:
            return label
    return "monitor"

# Health index
_raw_df["health_index"] = (
    (_raw_df["sensor2"]  - 642.0)
    + (_raw_df["sensor3"]  - 1580.0) / 10
    + (_raw_df["sensor4"]  - 1396.0) / 10
    + (_raw_df["sensor11"] - 47.0)   * 3
    + (_raw_df["sensor15"] - 8.35)   * 20
    + (555.0  - _raw_df["sensor7"])  / 2
    + (523.0  - _raw_df["sensor12"]) / 2
    + (39.3   - _raw_df["sensor20"]) * 2
    + (23.5   - _raw_df["sensor21"]) * 3
).round(3)

# Latest pre-failure snapshot per engine
_pre_failure  = _raw_df[_raw_df["rul"] > 0]
_latest_idx   = _pre_failure.groupby("unit")["cycle"].idxmax()
_latest_df    = _pre_failure.loc[_latest_idx, ["unit", "cycle", "rul", "health_index"]].copy()
_latest_df["risk_band"] = _latest_df["rul"].apply(_risk_band)
_latest_df    = _latest_df.sort_values("rul").reset_index(drop=True)
_latest_df.rename(columns={"cycle": "latest_cycle", "rul": "remaining_useful_life"}, inplace=True)

engine_scores = _latest_df.to_dict(orient="records")

# Summary stats
_most_at_risk = engine_scores[0]
rul_summary = {
    "n_engines":               int(_raw_df["unit"].nunique()),
    "n_rows":                  len(_raw_df),
    "longest_run_cycles":      int(_raw_df["cycle"].max()),
    "avg_rul_all_rows":        round(float(_raw_df["rul"].mean()), 1),
    "avg_health_index":        round(float(_latest_df["health_index"].mean()), 2),
    "highest_priority_engine": int(_most_at_risk["unit"]),
}

enriched_df = _raw_df[["unit", "cycle", "rul", "health_index"]].copy()

print(f"{'='*60}")
print(f"  Turbofan RUL Analysis — {rul_summary['n_engines']} engines, {rul_summary['n_rows']:,} rows")
print(f"{'='*60}")
print(f"  Longest engine run : {rul_summary['longest_run_cycles']} cycles")
print(f"  Avg row-level RUL  : {rul_summary['avg_rul_all_rows']} cycles")
print(f"  Avg health index   : {rul_summary['avg_health_index']:.2f}")
print()
print(f"  {'Engine':>7}  {'Last Cycle':>11}  {'RUL':>6}  {'Risk':<10}  {'Health Idx':>10}")
print(f"  {'-'*7}  {'-'*11}  {'-'*6}  {'-'*10}  {'-'*10}")
for s in engine_scores[:15]:
    print(f"  {int(s['unit']):>7}  {int(s['latest_cycle']):>11}  {int(s['remaining_useful_life']):>6}  {s['risk_band']:<10}  {float(s['health_index']):>10.3f}")
if len(engine_scores) > 15:
    print(f"  ... ({len(engine_scores) - 15} more engines)")
print()
print(f"  ⚠  Highest-priority: Engine {_most_at_risk['unit']} "
      f"(RUL={int(_most_at_risk['remaining_useful_life'])}, risk={_most_at_risk['risk_band']})")


# ==============================================================================
# BLOCK 2 — rul_trend_chart
# ==============================================================================
"""RUL trend chart — one line per engine over operating cycles.

Uses `enriched_df` from the upstream analysis block (unit, cycle, rul, health_index).
Shows a stratified sample of 15 engines.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_max_cycles  = enriched_df.groupby("unit")["cycle"].max().sort_values()
_n_total     = len(_max_cycles)
_n_sample    = 15

_indices      = np.linspace(0, _n_total - 1, _n_sample, dtype=int)
_sample_units = set(_max_cycles.iloc[_indices].index.tolist())

_plot_df = enriched_df[enriched_df["unit"].isin(_sample_units)].copy()
_units   = sorted(_sample_units)

_CRIT_MAX = 30
_WARN_MAX = 80

_all_ruls = enriched_df["rul"].values
_max_rul  = int(_all_ruls.max())
_y_top    = _max_rul + max(10, round(_max_rul * 0.08))

_COLORS = [
    "#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
    "#1F77B4", "#9467BD", "#8C564B", "#C49C94", "#E377C2",
    "#F7B6D2", "#ffd400", "#17b26a", "#f04438", "#00BFFF",
]

rul_trend_fig, ax = plt.subplots(figsize=(12, 6))
rul_trend_fig.patch.set_facecolor("#1D1D20")
ax.set_facecolor("#1D1D20")

ax.axhspan(0,          _CRIT_MAX, alpha=0.10, color="#f04438", zorder=0)
ax.axhspan(_CRIT_MAX,  _WARN_MAX, alpha=0.07, color="#ffd400", zorder=0)
ax.axhspan(_WARN_MAX,  _y_top,    alpha=0.04, color="#17b26a", zorder=0)

ax.axhline(_CRIT_MAX, color="#f04438", linewidth=0.9, linestyle="--", alpha=0.7)
ax.axhline(_WARN_MAX, color="#ffd400", linewidth=0.9, linestyle="--", alpha=0.7)

ax.text(1.002, _CRIT_MAX, f"Critical ≤{_CRIT_MAX}",
        transform=ax.get_yaxis_transform(), color="#f04438",
        fontsize=7.5, va="center", clip_on=False)
ax.text(1.002, _WARN_MAX, f"Warning ≤{_WARN_MAX}",
        transform=ax.get_yaxis_transform(), color="#ffd400",
        fontsize=7.5, va="center", clip_on=False)

for _i, _unit in enumerate(_units):
    _ts     = _plot_df[_plot_df["unit"] == _unit].sort_values("cycle")
    _cycles = _ts["cycle"].values
    _ruls   = _ts["rul"].values
    _color  = _COLORS[_i % len(_COLORS)]
    ax.plot(_cycles, _ruls,
            color=_color, linewidth=1.8, alpha=0.85,
            label=f"Eng {_unit}  ({_cycles.max()}cy)", zorder=3)

ax.set_xlim(left=0, right=enriched_df["cycle"].max() + 5)
ax.set_ylim(bottom=0, top=_y_top)
ax.set_xlabel("Operating Cycle", color="#909094", fontsize=10)
ax.set_ylabel("Remaining Useful Life (cycles)", color="#909094", fontsize=10)
ax.set_title(
    "Turbofan Engine RUL Degradation — FD001 (15-engine stratified sample)",
    color="#fbfbff", fontsize=12, pad=14,
)
ax.tick_params(colors="#909094", labelsize=8)
for _spine in ax.spines.values():
    _spine.set_edgecolor("#3a3a3e")

_x_max   = int(enriched_df["cycle"].max())
_x_ticks = list(range(0, _x_max + 1, 50))
ax.set_xticks(_x_ticks)
ax.set_xticklabels([str(v) for v in _x_ticks], fontsize=8)

_y_step  = 50
_y_ticks = list(range(0, _y_top + 1, _y_step))
ax.set_yticks(_y_ticks)
ax.set_yticklabels([str(v) for v in _y_ticks], fontsize=8)

_eng_handles, _eng_labels = ax.get_legend_handles_labels()
_band_handles = [
    mpatches.Patch(color="#f04438", alpha=0.5, label=f"Critical  (RUL ≤ {_CRIT_MAX})"),
    mpatches.Patch(color="#ffd400", alpha=0.4, label=f"Warning   (RUL ≤ {_WARN_MAX})"),
    mpatches.Patch(color="#17b26a", alpha=0.3, label=f"Monitor   (RUL > {_WARN_MAX})"),
]
ax.legend(
    handles=_eng_handles + _band_handles,
    labels=_eng_labels + [p.get_label() for p in _band_handles],
    loc="upper right", fontsize=7.5, ncol=2,
    facecolor="#2a2a2e", edgecolor="#3a3a3e", labelcolor="#fbfbff",
)
ax.grid(axis="y", color="#3a3a3e", linewidth=0.5, alpha=0.6)
rul_trend_fig.tight_layout()
rul_trend_fig.savefig("rul_trend_chart.png", dpi=150, bbox_inches="tight")
print("Saved: rul_trend_chart.png")


# ==============================================================================
# BLOCK 3 — feature_engineering
# ==============================================================================
"""Feature engineering for CMAPSS FD001 RUL prediction.

Loads the full 26-column dataset, adds rolling-window stats per engine,
scales features, and splits by engine (80/20) to avoid data leakage.
"""

import zipfile
import io

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import GroupShuffleSplit

_COLS = (
    ["unit", "cycle"]
    + [f"setting{i}" for i in range(1, 4)]
    + [f"sensor{i}"  for i in range(1, 22)]
)

_ZIP  = "CMAPSSData.zip"
_FILE = "train_FD001.txt"

with zipfile.ZipFile(_ZIP) as _zf:
    _match = next(n for n in _zf.namelist() if n.endswith(_FILE))
    with _zf.open(_match) as _f:
        _df = pd.read_csv(
            io.TextIOWrapper(_f),
            sep=r"\s+", header=None, names=_COLS, engine="python",
        )

_df = _df.dropna(axis=1, how="all")

_max_cycle = _df.groupby("unit")["cycle"].max()
_df["rul"]  = _df["unit"].map(_max_cycle) - _df["cycle"]

_DROP_SENSORS = {"sensor1", "sensor5", "sensor6", "sensor10",
                 "sensor16", "sensor18", "sensor19"}

_BASE_FEATURES = [c for c in _COLS[2:] if c not in _DROP_SENSORS]

_WINDOW = 5
_roll_dfs = []

for _unit, _grp in _df.groupby("unit"):
    _grp = _grp.sort_values("cycle").copy()
    for _col in _BASE_FEATURES:
        _rolled = _grp[_col].rolling(_WINDOW, min_periods=1)
        _grp[f"{_col}_rmean"] = _rolled.mean()
        _grp[f"{_col}_rstd"]  = _rolled.std().fillna(0)
    _roll_dfs.append(_grp)

_feat_df = pd.concat(_roll_dfs, ignore_index=True)

feature_names = (
    _BASE_FEATURES
    + [f"{c}_rmean" for c in _BASE_FEATURES]
    + [f"{c}_rstd"  for c in _BASE_FEATURES]
)

_engines  = _feat_df["unit"].values
_gss      = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
_tr_idx, _te_idx = next(_gss.split(_feat_df, groups=_engines))

_train_df = _feat_df.iloc[_tr_idx]
_test_df  = _feat_df.iloc[_te_idx]

_scaler = MinMaxScaler()
X_train = _scaler.fit_transform(_train_df[feature_names])
X_test  = _scaler.transform(_test_df[feature_names])
y_train = _train_df["rul"].values
y_test  = _test_df["rul"].values

test_meta = _test_df[["unit", "cycle", "rul"]].reset_index(drop=True)

print(f"Feature engineering complete")
print(f"  Base sensors used  : {len(_BASE_FEATURES)}")
print(f"  Total features     : {len(feature_names)}  (original + rolling mean/std)")
print(f"  Train rows         : {X_train.shape[0]:,}  ({_train_df['unit'].nunique()} engines)")
print(f"  Test rows          : {X_test.shape[0]:,}  ({_test_df['unit'].nunique()} engines)")
print(f"  RUL range (train)  : {y_train.min():.0f} – {y_train.max():.0f}")
print(f"  RUL range (test)   : {y_test.min():.0f} – {y_test.max():.0f}")


# ==============================================================================
# BLOCK 4 — model_training
# ==============================================================================
"""Train a GradientBoostingRegressor to predict RUL from sensor features."""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

rul_model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=10,
    random_state=42,
)

rul_model.fit(X_train, y_train)

_y_pred = rul_model.predict(X_test)
_y_pred = np.clip(_y_pred, 0, None)

_rmse = np.sqrt(mean_squared_error(y_test, _y_pred))
_mae  = mean_absolute_error(y_test, _y_pred)
_r2   = rul_model.score(X_test, y_test)

print("=" * 50)
print("  GradientBoosting RUL Model — Test Results")
print("=" * 50)
print(f"  RMSE : {_rmse:.2f} cycles")
print(f"  MAE  : {_mae:.2f} cycles")
print(f"  R²   : {_r2:.4f}")
print()

predicted_rul_df = test_meta.copy()
predicted_rul_df["predicted_rul"] = _y_pred.round(1)
predicted_rul_df.rename(columns={"rul": "actual_rul"}, inplace=True)

feat_imp = pd.DataFrame({
    "feature":    feature_names,
    "importance": rul_model.feature_importances_,
}).sort_values("importance", ascending=False).reset_index(drop=True)

print(f"  Top 10 features by importance:")
print(feat_imp.head(10).to_string(index=False))


# ==============================================================================
# BLOCK 5 — model_evaluation_charts
# ==============================================================================
"""Model evaluation charts: actual vs predicted RUL + feature importance."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_BG      = "#1D1D20"
_TEXT    = "#fbfbff"
_SUBTLE  = "#909094"
_BLUE    = "#A1C9F4"
_ORANGE  = "#FFB482"
_GREEN   = "#8DE5A1"
_CORAL   = "#FF9F9B"

# 1. Actual vs Predicted scatter
_sample = predicted_rul_df.sample(min(2000, len(predicted_rul_df)), random_state=42)
_actual = _sample["actual_rul"].values
_pred   = _sample["predicted_rul"].values
_err    = np.abs(_actual - _pred)

_vmax = max(_actual.max(), _pred.max())

actual_vs_predicted_fig, ax1 = plt.subplots(figsize=(7, 6))
actual_vs_predicted_fig.patch.set_facecolor(_BG)
ax1.set_facecolor(_BG)

_sc = ax1.scatter(_actual, _pred, c=_err, cmap="YlOrRd",
                  alpha=0.55, s=14, linewidths=0)
_cb = actual_vs_predicted_fig.colorbar(_sc, ax=ax1)
_cb.set_label("Absolute error (cycles)", color=_TEXT, fontsize=10)
_cb.ax.yaxis.set_tick_params(color=_TEXT)
plt.setp(_cb.ax.yaxis.get_ticklabels(), color=_TEXT)

ax1.plot([0, _vmax], [0, _vmax], color=_GREEN, lw=1.4,
         linestyle="--", label="Perfect prediction")
ax1.set_xlim(0, _vmax * 1.05)
ax1.set_ylim(0, _vmax * 1.05)

_tick_vals = list(range(0, int(_vmax * 1.05) + 1, 50))
ax1.set_xticks(_tick_vals)
ax1.set_xticklabels([str(v) for v in _tick_vals], color=_TEXT, fontsize=9)
ax1.set_yticks(_tick_vals)
ax1.set_yticklabels([str(v) for v in _tick_vals], color=_TEXT, fontsize=9)

ax1.set_xlabel("Actual RUL (cycles)", color=_TEXT, fontsize=11)
ax1.set_ylabel("Predicted RUL (cycles)", color=_TEXT, fontsize=11)
ax1.set_title("Actual vs Predicted RUL", color=_TEXT, fontsize=13, fontweight="bold")
ax1.legend(facecolor=_BG, edgecolor=_SUBTLE, labelcolor=_TEXT, fontsize=9)
for _sp in ax1.spines.values():
    _sp.set_edgecolor(_SUBTLE)
ax1.tick_params(colors=_TEXT)
actual_vs_predicted_fig.tight_layout()
actual_vs_predicted_fig.savefig("actual_vs_predicted.png", dpi=150, bbox_inches="tight")
print("Saved: actual_vs_predicted.png")

# 2. Feature importance (top 15)
_top15  = feat_imp.head(15).iloc[::-1]
_labels = _top15["feature"].tolist()
_vals   = _top15["importance"].tolist()

feature_importance_fig, ax2 = plt.subplots(figsize=(8, 6))
feature_importance_fig.patch.set_facecolor(_BG)
ax2.set_facecolor(_BG)

ax2.barh(range(len(_labels)), _vals, color=_BLUE, edgecolor="none")
ax2.set_yticks(range(len(_labels)))
ax2.set_yticklabels(_labels, color=_TEXT, fontsize=9)

_x_max   = max(_vals) * 1.15
_x_steps = np.linspace(0, _x_max, 5)
ax2.set_xticks(_x_steps)
ax2.set_xticklabels([f"{v:.3f}" for v in _x_steps], color=_TEXT, fontsize=9)
ax2.set_xlim(0, _x_max)

ax2.set_xlabel("Importance score", color=_TEXT, fontsize=11)
ax2.set_title("Top 15 Feature Importances", color=_TEXT, fontsize=13, fontweight="bold")
ax2.axvline(0, color=_SUBTLE, lw=0.5)
for _sp in ax2.spines.values():
    _sp.set_edgecolor(_SUBTLE)
ax2.tick_params(colors=_TEXT)
feature_importance_fig.tight_layout()
feature_importance_fig.savefig("feature_importance.png", dpi=150, bbox_inches="tight")
print("Saved: feature_importance.png")

print("\nAll done. Output files: rul_trend_chart.png, actual_vs_predicted.png, feature_importance.png")
