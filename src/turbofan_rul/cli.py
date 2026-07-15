"""Command-line interface for the turbofan RUL pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "sample_turbofan.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "results"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the turbofan degradation RUL analysis pipeline.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="CSV or CMAPSS train_FD001.txt input path.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Directory for generated outputs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_pipeline(source_path=args.source, output_dir=args.output_dir)
    print("Turbofan RUL analysis complete")
    print(f"Rows analyzed: {result.rows}")
    print(f"Engines analyzed: {result.engines}")
    print(f"RMSE: {result.metrics['rmse']} cycles")
    print(f"MAE: {result.metrics['mae']} cycles")
    print(f"Output directory: {result.output_dir}")


if __name__ == "__main__":
    main()
