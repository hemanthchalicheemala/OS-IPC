"""ML analysis routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.models import MlPrediction
from backend.database.session import get_db
from backend.ml.anomaly import AnomalyDetector
from backend.ml.classifier import MessageClassifier
from backend.ml.sentiment import SentimentAnalyzer

router = APIRouter(prefix="/ml", tags=["ml"])

_classifier: MessageClassifier | None = None
_sentiment: SentimentAnalyzer | None = None
_anomaly = AnomalyDetector()


def _get_clf() -> MessageClassifier:
    global _classifier
    if _classifier is None:
        _classifier = MessageClassifier()
        _classifier.load()
    return _classifier


def _get_sent() -> SentimentAnalyzer:
    global _sentiment
    if _sentiment is None:
        _sentiment = SentimentAnalyzer()
    return _sentiment


class AnalyzeBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


@router.post("/analyze")
def analyze_text(body: AnalyzeBody, db: Session = Depends(get_db)):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must be non-empty")
    try:
        classification = _get_clf().predict(text)
        sentiment = _get_sent().analyze(text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    row = MlPrediction(
        message_uid=None,
        text=text,
        label=str(classification.get("label")),
        confidence=float(classification.get("confidence") or 0.0),
        sentiment=str((sentiment or {}).get("label")),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return {
        "ok": True,
        "text": text,
        "classification": classification,
        "sentiment": sentiment,
    }


@router.post("/anomaly")
def anomaly_check(
    cpu_percent: float = 0.0,
    memory_mb: float = 0.0,
    num_threads: float = 1.0,
    msg_rate: float = 0.0,
):
    return _anomaly.update_and_score(cpu_percent, memory_mb, num_threads, msg_rate)
