"""Small standard-library RUL regression baseline."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class LinearRulModel:
    coefficients: list[float]

    def predict_one(self, features: list[float]) -> float:
        return max(0.0, sum(coef * value for coef, value in zip(self.coefficients, features)))

    def predict(self, rows: list[list[float]]) -> list[float]:
        return [self.predict_one(row) for row in rows]


def train_linear_model(features: list[list[float]], target: list[float], ridge: float = 0.1) -> LinearRulModel:
    """Fit a ridge-regularized linear model using normal equations."""
    if not features:
        raise ValueError("features cannot be empty")
    n_features = len(features[0])
    xtx = [[0.0 for _ in range(n_features)] for _ in range(n_features)]
    xty = [0.0 for _ in range(n_features)]

    for x_row, y_value in zip(features, target):
        for i in range(n_features):
            xty[i] += x_row[i] * y_value
            for j in range(n_features):
                xtx[i][j] += x_row[i] * x_row[j]

    for i in range(1, n_features):
        xtx[i][i] += ridge

    return LinearRulModel(coefficients=_solve_linear_system(xtx, xty))


def regression_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    errors = [prediction - truth for truth, prediction in zip(actual, predicted)]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = sqrt(sum(error * error for error in errors) / len(errors))
    mean_actual = sum(actual) / len(actual)
    ss_tot = sum((value - mean_actual) ** 2 for value in actual)
    ss_res = sum(error * error for error in errors)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 3)}


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) < 1e-12:
            continue
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        pivot_value = augmented[col][col]
        augmented[col] = [value / pivot_value for value in augmented[col]]

        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [value - factor * pivot_value for value, pivot_value in zip(augmented[row], augmented[col])]

    return [augmented[row][-1] for row in range(n)]
