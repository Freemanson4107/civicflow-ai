import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from app.core.queue_predictor import best_visit_slot

router = APIRouter(prefix="/api/journey", tags=["journey"])

BENEFITS_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "benefits.json")
OFFICES_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "offices.json")

with open(BENEFITS_PATH, encoding="utf-8") as f:
    BENEFITS_BY_ID = {b["id"]: b for b in json.load(f)}
with open(OFFICES_PATH, encoding="utf-8") as f:
    OFFICES = json.load(f)

CATEGORY_TO_OFFICE_TYPE = {
    "healthcare_support": "healthcare",
    "elderly_care": "healthcare",
    "disability_support": "government_office",
}

# Below this life-event confidence, we don't treat the detected category as
# strong enough signal to flag urgency in the roadmap copy.
URGENCY_CONFIDENCE_THRESHOLD = 0.6


@router.get("/roadmap/{benefit_id}")
def get_roadmap(
    benefit_id: str,
    region: str = "US",
    life_event_category: str | None = Query(
        default=None, description="top_prediction.category from POST /api/life-event/detect"
    ),
    life_event_confidence: float | None = Query(
        default=None, description="top_prediction.confidence from POST /api/life-event/detect"
    ),
):
    benefit = BENEFITS_BY_ID.get(benefit_id)
    if not benefit:
        raise HTTPException(status_code=404, detail="Unknown benefit_id.")

    target_type = CATEGORY_TO_OFFICE_TYPE.get(benefit["category"], "benefit_center")
    nearby = [o for o in OFFICES if o["region"] == region and o["type"] == target_type] or \
              [o for o in OFFICES if o["region"] == region]

    recommended_office = nearby[0] if nearby else None

    # Build the ordered list of (title, detail) entries first; step numbers
    # are assigned exactly once at the end so inserting an urgency banner up
    # front can never desync the numbering from the actual list contents.
    entries = []

    # If the Life Event Detection model's output is passed in and it matches
    # this benefit's category with reasonably high confidence, lead with
    # that — this is the actual "AI-composed" link between features the
    # README claims, made visible in the payload rather than asserted in prose.
    life_event_signal = None
    if life_event_category and life_event_confidence is not None:
        matches_category = life_event_category == benefit["category"]
        life_event_signal = {
            "category": life_event_category,
            "confidence": life_event_confidence,
            "matches_benefit_category": matches_category,
        }
        if matches_category and life_event_confidence >= URGENCY_CONFIDENCE_THRESHOLD:
            entries.append({
                "title": "Flagged as time-sensitive",
                "detail": (
                    f"Life Event Detection identified your situation as "
                    f"'{life_event_category}' with {round(life_event_confidence * 100)}% "
                    f"confidence, matching this benefit's category — consider "
                    f"prioritizing this application."
                ),
            })

    entries.append({"title": "Collect required documents", "detail": benefit["documents_required"]})
    entries.append({
        "title": "Submit application",
        "detail": benefit["application_steps"][0] if benefit["application_steps"] else "Submit via official portal",
    })
    for action in benefit["application_steps"][1:]:
        entries.append({"title": action, "detail": ""})

    queue_forecast = None
    if recommended_office:
        # Calls the actual trained queue model (app/core/queue_predictor.py,
        # same model used by /api/queue/predict) to find the office's lowest
        # predicted-wait slot over the next two weeks. This REPLACES the
        # previous hardcoded "Tue/Wed 9-10am" claim, which was not derived
        # from any data.
        slot = best_visit_slot(recommended_office["office_id"], datetime.now())
        if slot:
            queue_forecast = slot
            detail = (
                f"{recommended_office['city']} — model-recommended visit: "
                f"{slot['weekday']} {slot['date']} at {slot['hour']}:00 "
                f"(predicted wait ~{slot['predicted_wait_minutes']} min, "
                f"crowd level: {slot['crowd_level']})"
            )
        else:
            detail = f"{recommended_office['city']}"
        entries.append({"title": f"Visit {recommended_office['name']}", "detail": detail})

    entries.append({
        "title": "Follow up",
        "detail": "Track application status and respond to any document requests within 7 days.",
    })

    roadmap = [{"step": i, **entry} for i, entry in enumerate(entries, start=1)]

    return {
        "benefit": {"id": benefit["id"], "name": benefit["name"], "category": benefit["category"]},
        "recommended_office": recommended_office,
        "queue_forecast": queue_forecast,
        "life_event_signal": life_event_signal,
        "roadmap": roadmap,
    }
