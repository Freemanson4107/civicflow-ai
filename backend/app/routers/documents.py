import os
import json
import joblib
from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import pytesseract
import io

from app.models.schemas import DocumentCheckResult, ReadinessChecklist

router = APIRouter(prefix="/api/documents", tags=["documents"])

BENEFITS_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "benefits.json")
with open(BENEFITS_PATH, encoding="utf-8") as f:
    BENEFITS_BY_ID = {b["id"]: b for b in json.load(f)}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "document_type_model.joblib")
_pipeline = joblib.load(MODEL_PATH)

# Below this confidence, report "unknown" rather than guessing — a wrong
# high-confidence label is worse than an honest "couldn't tell."
MIN_CONFIDENCE = 0.30


@router.post("/scan", response_model=DocumentCheckResult)
async def scan_document(file: UploadFile = File(...)):
    if file.content_type not in ("image/png", "image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Only PNG/JPEG images are supported.")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
        extracted_text = pytesseract.image_to_string(image).lower()
    except Exception:
        # Tesseract binary may not be installed in this environment — degrade gracefully
        extracted_text = ""

    if not extracted_text.strip():
        return DocumentCheckResult(
            document_type="unknown",
            detected=False,
            confidence=0.0,
            missing_fields=["No readable text could be extracted from the image"],
        )

    proba = _pipeline.predict_proba([extracted_text])[0]
    classes = _pipeline.classes_
    best_idx = proba.argmax()
    best_label = str(classes[best_idx])
    best_conf = float(proba[best_idx])

    detected = best_conf >= MIN_CONFIDENCE

    return DocumentCheckResult(
        document_type=best_label if detected else "unknown",
        detected=detected,
        confidence=round(best_conf, 2),
        missing_fields=[] if detected else ["Could not confidently identify document type"],
    )


@router.get("/checklist/{benefit_id}", response_model=ReadinessChecklist)
def get_checklist(benefit_id: str, submitted: str = ""):
    benefit = BENEFITS_BY_ID.get(benefit_id)
    if not benefit:
        raise HTTPException(status_code=404, detail="Unknown benefit_id.")

    submitted_docs = [s.strip() for s in submitted.split(",") if s.strip()]
    required = benefit["documents_required"]
    missing = [d for d in required if d not in submitted_docs]
    readiness = round(100 * (len(required) - len(missing)) / max(len(required), 1), 1)

    return ReadinessChecklist(
        benefit_id=benefit_id,
        required_documents=required,
        submitted_documents=submitted_docs,
        missing_documents=missing,
        readiness_percent=readiness,
    )
