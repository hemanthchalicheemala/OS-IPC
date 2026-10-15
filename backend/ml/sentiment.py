"""Sentiment analysis: Positive / Neutral / Negative."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from backend import MODELS_DIR

_POSITIVE = {
    "love",
    "great",
    "excellent",
    "happy",
    "fantastic",
    "thanks",
    "good",
    "awesome",
    "brilliant",
    "helpful",
}
_NEGATIVE = {
    "hate",
    "terrible",
    "awful",
    "horrible",
    "frustrated",
    "disappointed",
    "broken",
    "fail",
    "bad",
    "slow",
}


class SentimentAnalyzer:
    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else MODELS_DIR / "sentiment_clf.joblib"
        self._model = None

    def load(self) -> None:
        if not self.model_path.exists():
            from backend.ml.train import train_sentiment_model

            train_sentiment_model(self.model_path)
        try:
            self._model = joblib.load(self.model_path)
        except Exception:
            self._model = None

    def analyze(self, text: str) -> dict[str, Any]:
        if self._model is None:
            try:
                self.load()
            except Exception:
                self._model = None

        if self._model is not None:
            label = str(self._model.predict([text])[0])
            confidence = 0.0
            if hasattr(self._model, "predict_proba"):
                proba = self._model.predict_proba([text])[0]
                confidence = float(max(proba))
                label = str(self._model.classes_[int(proba.argmax())])
            return {
                "label": label.capitalize() if label.islower() else label,
                "confidence": confidence,
                "method": "sklearn",
            }

        tokens = {t.strip(".,!?\"'").lower() for t in text.split()}
        pos = len(tokens & _POSITIVE)
        neg = len(tokens & _NEGATIVE)
        if pos > neg:
            label, conf = "Positive", min(0.9, 0.55 + 0.1 * pos)
        elif neg > pos:
            label, conf = "Negative", min(0.9, 0.55 + 0.1 * neg)
        else:
            label, conf = "Neutral", 0.5
        return {"label": label, "confidence": conf, "method": "lexicon"}
