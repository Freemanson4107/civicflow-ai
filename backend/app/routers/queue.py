from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.core.queue_predictor import predict_wait, OFFICES_BY_ID
from app.models.schemas import QueuePredictionRequest, QueuePredictionResponse

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.post("/predict", response_model=QueuePredictionResponse)
def predict_queue(payload: QueuePredictionRequest):
    if payload.office_id not in OFFICES_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown office_id.")

    try:
        dt = datetime.strptime(payload.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    result = predict_wait(payload.office_id, dt, payload.hour, payload.weather)

    return QueuePredictionResponse(
        office_id=payload.office_id,
        predicted_wait_minutes=result["predicted_wait_minutes"],
        crowd_level=result["crowd_level"],
        service_efficiency_score=result["service_efficiency_score"],
    )
