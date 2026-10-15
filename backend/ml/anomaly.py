"""IsolationForest anomaly detection on process resource features."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """Fits on rolling feature vectors: CPU%, memory MB, threads, msg_rate."""

    def __init__(self, contamination: float = 0.1) -> None:
        self.contamination = contamination
        self._model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
        )
        self._fitted = False
        self._history: list[list[float]] = []

    def update_and_score(
        self,
        cpu_percent: float,
        memory_mb: float,
        num_threads: float,
        msg_rate: float,
    ) -> dict[str, Any]:
        features = [float(cpu_percent), float(memory_mb), float(num_threads), float(msg_rate)]
        self._history.append(features)
        if len(self._history) > 200:
            self._history = self._history[-200:]

        result: dict[str, Any] = {
            "features": {
                "cpu_percent": features[0],
                "memory_mb": features[1],
                "num_threads": features[2],
                "msg_rate": features[3],
            },
            "anomaly": False,
            "score": 0.0,
            "fitted": self._fitted,
        }

        if len(self._history) < 10:
            return result

        X = np.array(self._history, dtype=float)
        self._model.fit(X)
        self._fitted = True
        pred = int(self._model.predict([features])[0])  # 1 normal, -1 anomaly
        score = float(self._model.decision_function([features])[0])
        result["anomaly"] = pred == -1
        result["score"] = score
        result["fitted"] = True
        return result
