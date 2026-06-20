"""
Shared queue-wait prediction logic, used by both app/routers/queue.py (direct
API) and app/routers/journey.py (to pick a genuinely model-recommended visit
slot instead of a hardcoded guess). Keeping this in one place means both
callers run the exact same trained model the exact same way.
"""
import os
import json
import joblib
import pandas as pd
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_HERE, "..", "ml", "queue_model.joblib")
OFFICES_PATH = os.path.join(_HERE, "..", "ml", "offices.json")

_bundle = joblib.load(MODEL_PATH)
with open(OFFICES_PATH, encoding="utf-8") as f:
    OFFICES_BY_ID = {o["office_id"]: o for o in json.load(f)}

# Approximate seasonal-spike months baked into training data generator
SEASONAL_MONTHS = {1, 4, 7, 12}

# Public holiday set (sample) — mirrors the generator; for a production system
# this should come from a holidays API/library per region.
HOLIDAYS = {"01-01", "01-26", "08-15", "10-02", "12-25", "07-04", "09-07", "11-15"}

OFFICE_HOURS = range(9, 17)  # 9am-5pm, matches generate_queue_and_offices.py


def _safe_label(le, value, fallback):
    return le.transform([value])[0] if value in le.classes_ else le.transform([fallback])[0]


def predict_wait(office_id: str, dt: datetime, hour: int, weather: str = "normal") -> dict:
    """Returns predicted_wait_minutes, crowd_level, service_efficiency_score
    for one office/date/hour/weather combination, using the trained queue
    model. Raises KeyError if office_id is unknown."""
    office = OFFICES_BY_ID[office_id]
    le_office, le_type, le_weather, le_region = (
        _bundle["le_office"], _bundle["le_type"], _bundle["le_weather"], _bundle["le_region"]
    )

    row = pd.DataFrame([{
        "region_enc": _safe_label(le_region, office["region"], le_region.classes_[0]),
        "office_id_enc": _safe_label(le_office, office_id, le_office.classes_[0]),
        "office_type_enc": _safe_label(le_type, office["type"], le_type.classes_[0]),
        "day_of_week": dt.weekday(),
        "hour": hour,
        "is_holiday": int(dt.strftime("%m-%d") in HOLIDAYS),
        "weather_enc": _safe_label(le_weather, weather, "normal"),
        "seasonal_factor": 1.15 if dt.month in SEASONAL_MONTHS else 1.0,
    }])[_bundle["features"]]

    wait_pred = float(_bundle["regressor"].predict(row)[0])
    crowd_pred = str(_bundle["classifier"].predict(row)[0])
    efficiency = max(0.0, min(100.0, 100 - (wait_pred / 90 * 100)))

    return {
        "predicted_wait_minutes": round(wait_pred, 1),
        "crowd_level": crowd_pred,
        "service_efficiency_score": round(efficiency, 1),
    }


def best_visit_slot(office_id: str, start_date: datetime, days_ahead: int = 14) -> dict | None:
    """Scans the next `days_ahead` days x office hours for the office and
    returns the day/hour combo with the lowest model-predicted wait time.
    Returns None if the office is unknown. This REPLACES the previous
    hardcoded "Tue/Wed 9-10am" claim with an actual model-derived
    recommendation specific to this office."""
    if office_id not in OFFICES_BY_ID:
        return None

    best = None
    for day_offset in range(days_ahead):
        dt = start_date + pd.Timedelta(days=day_offset)
        if dt.weekday() >= 5:
            continue  # offices observed only on weekdays in training data
        for hour in OFFICE_HOURS:
            pred = predict_wait(office_id, dt, hour)
            if best is None or pred["predicted_wait_minutes"] < best["predicted_wait_minutes"]:
                best = {**pred, "date": dt.strftime("%Y-%m-%d"), "weekday": dt.strftime("%A"), "hour": hour}
    return best
