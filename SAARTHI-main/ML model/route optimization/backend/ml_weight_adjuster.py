from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .graph_data import Edge


@dataclass
class AdjustedEdgeValues:
    distance_km: float
    time_hours: float
    cost_inr: float


class WeightAdjuster:
    """
    Demo ML component: learns synthetic multipliers for time/cost based on cargo + month + edge type.

    This is intentionally "data plug-in ready":
    - Replace `train_synthetic()` with training on your real historical dataset.
    - Keep `predict_multiplier()` interface stable.
    """

    def __init__(self, artifact_path: str):
        self.artifact_path = artifact_path
        self._loaded = False
        self.cargo_types: list[str] = []
        self.time_model: RandomForestRegressor | None = None
        self.cost_model: RandomForestRegressor | None = None

    def _load_or_train(self) -> None:
        if self._loaded:
            return
        if os.path.exists(self.artifact_path):
            data: dict[str, Any] = joblib.load(self.artifact_path)
            self.cargo_types = data["cargo_types"]
            self.time_model = data["time_model"]
            self.cost_model = data["cost_model"]
            expected_features = len(self.cargo_types) + 5  # one-hot cargo + month + edge + base_time + base_cost + base_dist
            time_n = getattr(self.time_model, "n_features_in_", None)
            cost_n = getattr(self.cost_model, "n_features_in_", None)
            if time_n != expected_features or cost_n != expected_features:
                # Artifact was trained with a different feature schema; retrain.
                self.train_synthetic()
            self._loaded = True
            return

        self.train_synthetic()
        self._loaded = True

    def train_synthetic(self, n_samples: int = 2500, random_seed: int = 42) -> None:
        rng = np.random.default_rng(random_seed)
        # Categories aligned with the UI (Category part of "Category|Item").
        cargo_types = [
            "Perishable Goods",
            "Non-Perishable Goods",
            "Fragile Goods",
            "Hazardous Materials (Hazmat)",
            "Livestock",
            "Heavy / Bulk Cargo",
            "High-Value Goods",
            "General Cargo",
            "Oversized Cargo",
            "Liquid Cargo",
        ]

        # Important: make sure `_encode_features()` uses the correct cargo one-hot dimensions.
        self.cargo_types = cargo_types

        X: list[list[float]] = []
        y_time: list[float] = []
        y_cost: list[float] = []

        for _ in range(n_samples):
            cargo = rng.choice(cargo_types)
            month = int(rng.integers(1, 13))
            edge_type = rng.choice(["road", "rail"])

            # Base-like features (synthetic sampling from plausible ranges).
            base_time = float(rng.uniform(0.6, 20.0))
            base_cost = float(rng.uniform(60, 3500))
            base_dist = float(rng.uniform(40, 1600))

            # Cargo sensitivity factors (synthetic but consistent).
            # Higher means "time matters more", thus increases effective time for routing weight.
            cargo_time_bias_map = {
                "Perishable Goods": 0.12,
                "Livestock": 0.10,
                "Hazardous Materials (Hazmat)": 0.08,
                "Fragile Goods": 0.07,
                "High-Value Goods": 0.06,
                "Liquid Cargo": 0.06,
                "Oversized Cargo": 0.05,
                "Heavy / Bulk Cargo": 0.04,
                "Non-Perishable Goods": 0.03,
                "General Cargo": 0.03,
            }
            cargo_time_bias = float(cargo_time_bias_map.get(str(cargo), 0.03))

            cargo_cost_bias = cargo_time_bias * 0.6

            # Road vs rail stability
            road_penalty = 0.06 if edge_type == "road" else 0.02

            # Seasonal factor: monsoon window (rough)
            monsoon = 1.0 if month in (6, 7, 8) else 0.0
            seasonal_time = 0.08 * monsoon * (1.0 if edge_type == "road" else 0.6)
            seasonal_cost = 0.04 * monsoon * (1.0 if edge_type == "road" else 0.7)

            noise_t = float(rng.normal(0.0, 0.03))
            noise_c = float(rng.normal(0.0, 0.04))

            time_mult = 1.0 + road_penalty + cargo_time_bias + seasonal_time + noise_t
            cost_mult = 1.0 + cargo_cost_bias + seasonal_cost + noise_c

            # Clip to keep routing stable.
            time_mult = float(np.clip(time_mult, 0.7, 1.5))
            cost_mult = float(np.clip(cost_mult, 0.7, 1.6))

            X.append(self._encode_features(cargo, month, edge_type, base_time, base_cost, base_dist))
            y_time.append(time_mult)
            y_cost.append(cost_mult)

        time_model = RandomForestRegressor(n_estimators=120, random_state=random_seed)
        cost_model = RandomForestRegressor(n_estimators=120, random_state=random_seed + 1)
        time_model.fit(np.asarray(X), np.asarray(y_time))
        cost_model.fit(np.asarray(X), np.asarray(y_cost))

        os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
        joblib.dump(
            {"cargo_types": self.cargo_types, "time_model": time_model, "cost_model": cost_model},
            self.artifact_path,
        )

        self.time_model = time_model
        self.cost_model = cost_model

    def _encode_features(
        self,
        cargo_type: str,
        month: int,
        edge_type: str,
        base_time: float,
        base_cost: float,
        base_dist: float,
    ) -> list[float]:
        # One-hot cargo, then numeric features.
        cargo_one_hot = [1.0 if cargo_type == c else 0.0 for c in self.cargo_types]
        edge_is_road = 1.0 if edge_type == "road" else 0.0
        return cargo_one_hot + [
            float(month),
            edge_is_road,
            float(base_time),
            float(base_cost),
            float(base_dist),
        ]

    def predict_multiplier(self, cargo_type: str, month: int, edge: Edge, metric: str) -> float:
        self._load_or_train()
        assert self.time_model is not None and self.cost_model is not None
        raw = (cargo_type or "").strip()
        category = raw.split("|", 1)[0].strip() if "|" in raw else raw
        cargo_key = category if category in self.cargo_types else self.cargo_types[0]

        X = [self._encode_features(cargo_key, month, edge.edge_type, edge.time_hours, edge.toll_or_fare_inr, edge.distance_km)]
        if metric == "time":
            pred = float(self.time_model.predict(np.asarray(X))[0])
        elif metric == "cost":
            pred = float(self.cost_model.predict(np.asarray(X))[0])
        else:
            pred = 1.0
        return float(np.clip(pred, 0.7, 1.6))

    def adjusted_values(
        self,
        cargo_type: str,
        month: int,
        edge: Edge,
    ) -> AdjustedEdgeValues:
        time_mult = self.predict_multiplier(cargo_type=cargo_type, month=month, edge=edge, metric="time")
        cost_mult = self.predict_multiplier(cargo_type=cargo_type, month=month, edge=edge, metric="cost")
        return AdjustedEdgeValues(
            distance_km=float(edge.distance_km),
            time_hours=float(edge.time_hours * time_mult),
            cost_inr=float(edge.toll_or_fare_inr * cost_mult),
        )

