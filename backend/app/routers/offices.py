import os
import json
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/offices", tags=["offices"])

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "offices.json")
with open(DATA_PATH, encoding="utf-8") as f:
    OFFICES = json.load(f)


@router.get("")
def list_offices(region: str = Query(default="US", pattern="^(IN|US|BR)$")):
    return [o for o in OFFICES if o["region"] == region]
