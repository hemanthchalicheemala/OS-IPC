"""Message category classifier (normal / spam / toxic / urgent)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from backend import MODELS_DIR


class MessageClassifier:
    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else MODELS_DIR / "message_clf.joblib"
        self._model = None

    def load(self) -> None:
        if not self.model_path.exists():
            from backend.ml.train import train_message_classifier

            train_message_classifier(self.model_path)
        self._model = joblib.load(self.model_path)

    def predict(self, text: str) -> dict[str, Any]:
        if self._model is None:
            self.load()
        assert self._model is not None
        label = self._model.predict([text])[0]
        confidence = 0.0
        if hasattr(self._model, "predict_proba"):
            proba = self._model.predict_proba([text])[0]
            classes = list(self._model.classes_)
            confidence = float(max(proba))
            label = classes[int(proba.argmax())]
            distribution = {classes[i]: float(proba[i]) for i in range(len(classes))}
        else:
            distribution = {str(label): 1.0}
        return {
            "label": str(label),
            "confidence": confidence,
            "distribution": distribution,
        }
