"""Experiment routes."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.deps import get_experiment_runner
from backend.database.models import ExperimentResult
from backend.database.session import get_db
from backend.experiments.runner import EXPERIMENTS, ExperimentRunner

router = APIRouter(prefix="/experiments", tags=["experiments"])


class RunExperimentBody(BaseModel):
    experiment_id: str = Field(..., min_length=1, max_length=64)


@router.get("")
def list_experiments():
    return {"experiments": list(EXPERIMENTS.values())}


@router.post("/run")
def run_experiment(
    body: RunExperimentBody,
    runner: ExperimentRunner = Depends(get_experiment_runner),
    db: Session = Depends(get_db),
):
    try:
        record = runner.run(body.experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    row = ExperimentResult(
        experiment_id=record["experiment_id"],
        title=record["title"],
        success=bool(record.get("success")),
        result_json=json.dumps(record, default=str),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    return {"ok": True, "result": record}


@router.get("/results")
def experiment_results(
    runner: ExperimentRunner = Depends(get_experiment_runner),
    db: Session = Depends(get_db),
):
    live = list(runner.results)
    rows = db.query(ExperimentResult).order_by(ExperimentResult.id.desc()).limit(100).all()
    persisted = [
        {
            "id": r.id,
            "experiment_id": r.experiment_id,
            "title": r.title,
            "success": r.success,
            "result": json.loads(r.result_json),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"results": live, "persisted": persisted}
