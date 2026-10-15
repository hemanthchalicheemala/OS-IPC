"""Train TF-IDF + LogisticRegression classifiers and persist with joblib."""

from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from backend import MODELS_DIR
from backend.ml.dataset import get_sentiment_samples, get_training_samples


def ensure_models_dir() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def train_message_classifier(model_path: Path | None = None) -> Path:
    ensure_models_dir()
    path = model_path or (MODELS_DIR / "message_clf.joblib")
    texts, labels = get_training_samples()
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            (
                "clf",
                LogisticRegression(max_iter=2000),
            ),
        ]
    )
    pipe.fit(texts, labels)
    joblib.dump(pipe, path)
    return path


def train_sentiment_model(model_path: Path | None = None) -> Path:
    ensure_models_dir()
    path = model_path or (MODELS_DIR / "sentiment_clf.joblib")
    texts, labels = get_sentiment_samples()
    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=2000)),
        ]
    )
    pipe.fit(texts, labels)
    joblib.dump(pipe, path)
    return path


def ensure_trained() -> dict[str, str]:
    ensure_models_dir()
    msg_path = MODELS_DIR / "message_clf.joblib"
    sent_path = MODELS_DIR / "sentiment_clf.joblib"
    if not msg_path.exists():
        train_message_classifier(msg_path)
    if not sent_path.exists():
        train_sentiment_model(sent_path)
    return {"message_clf": str(msg_path), "sentiment_clf": str(sent_path)}
