import os
import joblib
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.models.orm_models import User, LifeEventQuery
from app.models.schemas import LifeEventRequest, LifeEventResponse, LifeEventResult

router = APIRouter(prefix="/api/life-event", tags=["life-event"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "life_event_model.joblib")
_pipeline = joblib.load(MODEL_PATH)


@router.post("/detect", response_model=LifeEventResponse)
def detect_life_event(
    payload: LifeEventRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    probs = _pipeline.predict_proba([payload.text])[0]
    classes = _pipeline.classes_
    scored = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)

    top_category, top_conf = scored[0]
    all_scores = [LifeEventResult(category=c, confidence=round(float(p), 4)) for c, p in scored]

    db.add(LifeEventQuery(
        user_id=user.id if user else None,
        input_text=payload.text,
        predicted_category=top_category,
        confidence=float(top_conf),
    ))
    db.commit()

    return LifeEventResponse(
        top_prediction=LifeEventResult(category=top_category, confidence=round(float(top_conf), 4)),
        all_scores=all_scores,
    )
