import os
import json
import joblib
import pandas as pd
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.models.orm_models import User
from app.models.schemas import BenefitMatch

router = APIRouter(prefix="/api/benefits", tags=["benefits"])

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "benefits.json")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "benefit_priority_model.joblib")

with open(DATA_PATH, encoding="utf-8") as f:
    BENEFITS = json.load(f)

_bundle = joblib.load(MODEL_PATH)
_PRIORITY_PIPELINE = _bundle["pipeline"]
_PRIORITY_FEATURES = _bundle["features"]

_REGION_DENSITY = {}
for _b in BENEFITS:
    _REGION_DENSITY[_b["region"]] = _REGION_DENSITY.get(_b["region"], 0) + 1


def _is_eligible(benefit: dict, age: int, family_size: int, income: float,
                  employment_status: str) -> bool:
    """Deterministic eligibility gate. This is the ONLY thing that decides
    pass/fail. It is intentionally rule-based — exact age/income/employment/
    family-size cutoffs from the benefit's own published criteria, no model,
    no probabilities. A benefit a citizen does not actually qualify for must
    never appear in their results, regardless of how "close" they are."""
    if not (benefit["min_age"] <= age <= benefit["max_age"]):
        return False
    if income > benefit["max_income_monthly"]:
        return False
    if family_size < benefit["family_size_min"]:
        return False
    allowed_emp = benefit["employment_status"]
    if "any" not in allowed_emp and employment_status not in allowed_emp:
        return False
    return True


def _score_priority(benefit: dict, age: int, family_size: int, income: float,
                     category_hint: str | None) -> float:
    """ML ranking ONLY among benefits that already passed _is_eligible. This
    model never determines whether someone qualifies — only how to order
    the benefits they already qualify for, using richer multi-factor signal
    than a flat constant. See data/train_benefit_priority_model.py."""
    max_income = benefit["max_income_monthly"]
    income_ratio = min(1.0, income / max_income) if max_income < 999999 else 0.0

    span = max(1, benefit["max_age"] - benefit["min_age"])
    age_centrality = 1.0 - abs((age - benefit["min_age"]) / span - 0.5) * 2

    family_margin = family_size - benefit["family_size_min"]
    category_match = 1 if (category_hint and category_hint == benefit["category"]) else 0
    employment_match_any = 1 if "any" in benefit["employment_status"] else 0
    region_density = _REGION_DENSITY.get(benefit["region"], 1)

    row = pd.DataFrame([{
        "income_ratio": income_ratio,
        "age_centrality": age_centrality,
        "family_margin": family_margin,
        "category_match": category_match,
        "employment_match_any": employment_match_any,
        "region_density": region_density,
    }])[_PRIORITY_FEATURES]

    priority = float(_PRIORITY_PIPELINE.predict(row)[0])
    return max(0.0, min(1.0, round(priority, 3)))


@router.get("/match", response_model=list[BenefitMatch])
def match_benefits(
    category_hint: str | None = Query(default=None, description="From Life Event Detection output"),
    user: User = Depends(get_current_user),
):
    age = user.age if user.age is not None else 30
    family_size = user.family_size if user.family_size is not None else 1
    income = user.monthly_income if user.monthly_income is not None else 0
    employment_status = user.employment_status or "unemployed"

    region_benefits = [b for b in BENEFITS if b["region"] == user.region]

    # Step 1: deterministic gate. Anyone who fails this is excluded — full stop,
    # no soft penalty, no near-miss inclusion.
    eligible = [
        b for b in region_benefits
        if _is_eligible(b, age, family_size, income, employment_status)
    ]

    # Step 2: ML ranks ONLY the already-eligible set.
    results = []
    for b in eligible:
        priority = _score_priority(b, age, family_size, income, category_hint)
        results.append(BenefitMatch(
            id=b["id"], name=b["name"], category=b["category"],
            description=b["description"], priority_score=priority,
            documents_required=b["documents_required"],
            application_steps=b["application_steps"],
            priority_rank=0,
        ))

    results.sort(key=lambda r: r.priority_score, reverse=True)
    for i, r in enumerate(results, start=1):
        r.priority_rank = i

    return results


@router.get("/all")
def list_all_benefits(region: str = Query(default="US", pattern="^(IN|US|BR)$")):
    return [b for b in BENEFITS if b["region"] == region]
