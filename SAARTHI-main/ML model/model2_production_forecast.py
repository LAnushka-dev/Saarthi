"""
Model 2: Yearly Production Forecasting
========================================
Predicts crop production (in metric tonnes) for a given state and crop,
up to 2 seasons ahead.

Architecture:
  - LSTM-based time-series regression (PyTorch)
  - Input features: historical production, rainfall, temperature anomaly,
    irrigated area %, MSP (minimum support price), previous season yield
  - Output: predicted production in MT + confidence interval

Training data shape expected:
  (num_samples, sequence_length=5, num_features=7)

In production: train on Ministry of Agriculture data (1990–present),
IMD gridded rainfall, and APEDA export/price data.
"""

from __future__ import annotations
import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Synthetic historical data  (replace with real MoA CSV in production)
# ---------------------------------------------------------------------------

HISTORICAL_DATA: dict[str, dict[str, list]] = {
    # Each entry: list of yearly records for a (crop, state) pair
    # Fields: year, production_mt, rainfall_mm, temp_anomaly_c,
    #         irrigated_pct, msp_per_qt, area_ha
    "wheat_Punjab": {
        "years":          [2018, 2019, 2020, 2021, 2022, 2023],
        "production_mt":  [17200, 17450, 17800, 18100, 17950, 18400],
        "rainfall_mm":    [620,   590,   640,   580,   650,   610],
        "temp_anomaly":   [0.2,   0.4,   0.1,   0.6,   -0.1,  0.3],
        "irrigated_pct":  [98,    98,    99,    99,    99,    99],
        "msp_per_qt":     [1735,  1840,  1925,  1975,  2015,  2125],
        "area_ha":        [3520,  3510,  3530,  3550,  3540,  3560],
    },
    "tomato_AndhraPradesh": {
        "years":          [2018, 2019, 2020, 2021, 2022, 2023],
        "production_mt":  [1820, 2100, 1950, 2300, 2150, 2450],
        "rainfall_mm":    [910,  780,  850,  920,  760,  890],
        "temp_anomaly":   [0.3,  0.8,  0.4,  0.2,  1.1,  0.5],
        "irrigated_pct":  [65,   68,   70,   72,   74,   75],
        "msp_per_qt":     [0,    0,    0,    0,    0,    0],  # Tomato not MSP-regulated
        "area_ha":        [155,  170,  163,  185,  178,  195],
    },
    "rice_WestBengal": {
        "years":          [2018, 2019, 2020, 2021, 2022, 2023],
        "production_mt":  [15800, 15600, 16100, 15900, 16400, 16200],
        "rainfall_mm":    [1480, 1520,  1390,  1600,  1430,  1510],
        "temp_anomaly":   [0.4,  0.2,   0.7,   0.3,   0.9,   0.5],
        "irrigated_pct":  [55,   57,    58,    60,    61,    62],
        "msp_per_qt":     [1550, 1815,  1868,  1940,  2040,  2183],
        "area_ha":        [5800, 5750,  5820,  5790,  5840,  5810],
    },
    "soybean_MadhyaPradesh": {
        "years":          [2018, 2019, 2020, 2021, 2022, 2023],
        "production_mt":  [5200, 4800, 5600, 5100, 5900, 5700],
        "rainfall_mm":    [980,  870,  1020, 950,  1050, 990],
        "temp_anomaly":   [0.5,  1.2,  0.3,  0.8,  0.2,  0.6],
        "irrigated_pct":  [22,   23,   24,   25,   26,   27],
        "msp_per_qt":     [3399, 3710, 3880, 3950, 4300, 4600],
        "area_ha":        [5100, 4950, 5300, 5200, 5450, 5380],
    },
}

FEATURE_COLS = ["production_mt", "rainfall_mm", "temp_anomaly", "irrigated_pct", "msp_per_qt", "area_ha"]
SEQ_LEN = 4  # use last 4 years to predict next


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ForecastResult:
    crop: str
    state: str
    target_year: int
    predicted_production_mt: float
    lower_bound_mt: float          # 80% confidence interval
    upper_bound_mt: float
    yoy_change_pct: float          # vs previous year actual
    input_features: dict
    model_type: str = "LSTM"
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

class FeatureBuilder:
    """Normalise and build sequences from raw historical dict."""

    def __init__(self):
        self._stats: dict[str, tuple[float, float]] = {}  # col -> (mean, std)

    def fit(self, data: dict) -> "FeatureBuilder":
        arrays = {col: np.array(data[col], dtype=np.float32) for col in FEATURE_COLS}
        for col, arr in arrays.items():
            self._stats[col] = (float(arr.mean()), float(arr.std()) + 1e-8)
        return self

    def transform(self, data: dict) -> np.ndarray:
        """Returns shape (T, num_features)."""
        cols = []
        for col in FEATURE_COLS:
            arr = np.array(data[col], dtype=np.float32)
            mean, std = self._stats[col]
            cols.append((arr - mean) / std)
        return np.stack(cols, axis=1)  # (T, F)

    def inverse_production(self, val: float) -> float:
        mean, std = self._stats["production_mt"]
        return val * std + mean

    def fit_transform(self, data: dict) -> np.ndarray:
        return self.fit(data).transform(data)


# ---------------------------------------------------------------------------
# LSTM Model (PyTorch)
# ---------------------------------------------------------------------------

def _build_pytorch_model(seq_len: int, num_features: int, hidden_size: int = 64):
    """Build a small LSTM regressor. Returns (model, optimizer)."""
    try:
        import torch
        import torch.nn as nn

        class LSTMForecaster(nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = nn.LSTM(
                    input_size=num_features,
                    hidden_size=hidden_size,
                    num_layers=2,
                    batch_first=True,
                    dropout=0.2,
                )
                self.fc = nn.Sequential(
                    nn.Linear(hidden_size, 32),
                    nn.ReLU(),
                    nn.Linear(32, 1),
                )

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :]).squeeze(-1)

        model = LSTMForecaster()
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        return model, optimizer, torch

    except ImportError:
        return None, None, None


class ProductionForecaster:
    """
    Trains a per-(crop, state) LSTM on available historical data.
    Falls back to weighted linear trend when PyTorch is not installed.
    """

    def __init__(self, hidden_size: int = 64, epochs: int = 200):
        self.hidden_size = hidden_size
        self.epochs = epochs
        self._fitted: dict[str, tuple] = {}  # key -> (feature_builder, model/coeffs, has_torch)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(self, key: str, data: dict) -> "ProductionForecaster":
        fb = FeatureBuilder()
        X = fb.fit_transform(data)  # (T, F)

        torch_model, optimizer, torch = _build_pytorch_model(SEQ_LEN, X.shape[1], self.hidden_size)

        if torch_model is not None:
            self._fit_torch(key, X, fb, torch_model, optimizer, torch)
        else:
            self._fit_linear(key, X, fb)

        return self

    def _fit_torch(self, key, X, fb, model, optimizer, torch):
        import torch as t
        import torch.nn as nn

        # Build (seq, target) pairs from the time series
        seqs, targets = [], []
        for i in range(len(X) - SEQ_LEN):
            seqs.append(X[i: i + SEQ_LEN])
            targets.append(X[i + SEQ_LEN, 0])  # index 0 = normalised production

        X_t = t.tensor(np.array(seqs), dtype=t.float32)
        y_t = t.tensor(np.array(targets), dtype=t.float32)
        loss_fn = nn.HuberLoss()

        model.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            pred = model(X_t)
            loss = loss_fn(pred, y_t)
            loss.backward()
            optimizer.step()

        self._fitted[key] = (fb, model, True, torch)
        print(f"[Forecaster] LSTM trained for {key} (PyTorch). Final loss: {loss.item():.4f}")

    def _fit_linear(self, key, X, fb):
        """Weighted linear regression on normalised production (index 0)."""
        y = X[:, 0]
        T = len(y)
        t_idx = np.arange(T, dtype=np.float32)
        weights = np.exp(0.3 * t_idx)  # exponentially up-weight recent years
        weights /= weights.sum()

        w_mean_t = (weights * t_idx).sum()
        w_mean_y = (weights * y).sum()
        slope = (weights * (t_idx - w_mean_t) * (y - w_mean_y)).sum() / \
                (weights * (t_idx - w_mean_t) ** 2).sum()
        intercept = w_mean_y - slope * w_mean_t

        self._fitted[key] = (fb, (slope, intercept, T), False, None)
        print(f"[Forecaster] Linear trend fitted for {key}. Slope={slope:.4f}")

    def fit_all(self) -> "ProductionForecaster":
        for key, data in HISTORICAL_DATA.items():
            self.fit(key, data)
        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        crop: str,
        state: str,
        target_year: int,
        rainfall_mm: Optional[float] = None,
        temp_anomaly: Optional[float] = None,
    ) -> ForecastResult:
        key = f"{crop.lower().replace(' ', '_')}_{state.replace(' ', '')}"
        data = HISTORICAL_DATA.get(key)

        if data is None:
            return self._fallback_result(crop, state, target_year)

        if key not in self._fitted:
            self.fit(key, data)

        fb, fitted, has_torch, torch = self._fitted[key]

        # Build extended feature array for prediction step
        X = fb.transform(data)

        if has_torch:
            pred_norm, ci_half = self._predict_torch(X, fitted, torch)
        else:
            pred_norm, ci_half = self._predict_linear(X, fitted)

        pred_mt = fb.inverse_production(pred_norm)
        lower_mt = fb.inverse_production(pred_norm - ci_half)
        upper_mt = fb.inverse_production(pred_norm + ci_half)

        last_actual = data["production_mt"][-1]
        yoy_pct = (pred_mt - last_actual) / last_actual * 100

        input_feats = {
            "last_year_production_mt": last_actual,
            "last_year_rainfall_mm": data["rainfall_mm"][-1],
            "last_year_temp_anomaly": data["temp_anomaly"][-1],
            "override_rainfall_mm": rainfall_mm,
            "override_temp_anomaly": temp_anomaly,
        }

        # Qualitative note
        note = self._qualitative_note(yoy_pct, rainfall_mm, temp_anomaly)

        return ForecastResult(
            crop=crop,
            state=state,
            target_year=target_year,
            predicted_production_mt=round(pred_mt, 0),
            lower_bound_mt=round(lower_mt, 0),
            upper_bound_mt=round(upper_mt, 0),
            yoy_change_pct=round(yoy_pct, 1),
            input_features=input_feats,
            note=note,
        )

    def _predict_torch(self, X, model, torch):
        import torch as t
        model.eval()
        with t.no_grad():
            seq = t.tensor(X[-SEQ_LEN:][np.newaxis], dtype=t.float32)
            pred = model(seq).item()

        # Bootstrap CI: small perturbation ensemble
        preds = []
        for _ in range(30):
            noise = t.tensor(X[-SEQ_LEN:][np.newaxis], dtype=t.float32) + \
                    t.randn_like(seq) * 0.05
            preds.append(model(noise).item())
        ci_half = 1.28 * np.std(preds)  # ~80% CI
        return pred, ci_half

    def _predict_linear(self, X, fitted):
        slope, intercept, T = fitted
        pred = slope * T + intercept
        residuals = [X[i, 0] - (slope * i + intercept) for i in range(T)]
        ci_half = 1.28 * np.std(residuals)
        return pred, ci_half

    def _fallback_result(self, crop, state, year) -> ForecastResult:
        return ForecastResult(
            crop=crop, state=state, target_year=year,
            predicted_production_mt=0, lower_bound_mt=0, upper_bound_mt=0,
            yoy_change_pct=0, input_features={},
            note=f"No historical data available for {crop} in {state}. Add training data.",
        )

    @staticmethod
    def _qualitative_note(yoy_pct, rainfall, temp) -> str:
        parts = []
        if yoy_pct > 10:
            parts.append(f"Strong production growth expected ({yoy_pct:+.1f}% YoY).")
        elif yoy_pct < -10:
            parts.append(f"Production decline expected ({yoy_pct:+.1f}% YoY) — consider early procurement.")
        else:
            parts.append(f"Stable production expected ({yoy_pct:+.1f}% YoY).")
        if rainfall is not None:
            if rainfall > 1200:
                parts.append("High rainfall forecast — watch for waterlogging risk.")
            elif rainfall < 600:
                parts.append("Below-normal rainfall forecast — irrigation dependency rises.")
        if temp is not None and temp > 1.0:
            parts.append("Above-normal temperature anomaly — heat stress risk during flowering.")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    forecaster = ProductionForecaster(epochs=150).fit_all()

    tests = [
        ("wheat", "Punjab", 2024, 620, 0.4),
        ("tomato", "Andhra Pradesh", 2024, 920, 0.3),
        ("rice", "West Bengal", 2024, None, None),
        ("soybean", "Madhya Pradesh", 2024, 1050, 0.2),
    ]

    print("\n=== Production Forecasts ===")
    for crop, state, year, rain, temp in tests:
        r = forecaster.predict(crop, state, year, rain, temp)
        print(f"\n{crop.title()} | {state} | {year}")
        print(f"  Predicted: {r.predicted_production_mt:,.0f} MT")
        print(f"  80% CI:    [{r.lower_bound_mt:,.0f}, {r.upper_bound_mt:,.0f}] MT")
        print(f"  YoY:       {r.yoy_change_pct:+.1f}%")
        print(f"  Note:      {r.note}")
