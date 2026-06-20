from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=128)
    full_name: str | None = None
    region: str = Field(default="US", pattern="^(IN|US|BR)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfileOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    region: str
    age: int | None
    family_size: int | None
    monthly_income: float | None
    employment_status: str | None
    health_status: str | None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    family_size: int | None = Field(default=None, ge=1, le=20)
    monthly_income: float | None = Field(default=None, ge=0)
    employment_status: str | None = None
    health_status: str | None = None


# ---------- Life Event Detection ----------
class LifeEventRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=1000)


class LifeEventResult(BaseModel):
    category: str
    confidence: float


class LifeEventResponse(BaseModel):
    top_prediction: LifeEventResult
    all_scores: list[LifeEventResult]


# ---------- Benefit Matching ----------
class BenefitMatch(BaseModel):
    id: str
    name: str
    category: str
    description: str
    # Priority/strength-of-match score among benefits the citizen has ALREADY
    # been deterministically confirmed eligible for (see
    # app/routers/benefits.py::_is_eligible). Not named "eligibility_likelihood"
    # because eligibility itself is never probabilistic in this system.
    priority_score: float
    documents_required: list[str]
    application_steps: list[str]
    priority_rank: int


# ---------- Queue Forecasting ----------
class QueuePredictionRequest(BaseModel):
    office_id: str
    date: str  # YYYY-MM-DD
    hour: int = Field(..., ge=0, le=23)
    weather: str = Field(default="normal")


class QueuePredictionResponse(BaseModel):
    office_id: str
    predicted_wait_minutes: float
    crowd_level: str
    service_efficiency_score: float


# ---------- Document Readiness ----------
class DocumentCheckResult(BaseModel):
    document_type: str
    detected: bool
    confidence: float
    missing_fields: list[str]


class ReadinessChecklist(BaseModel):
    benefit_id: str
    required_documents: list[str]
    submitted_documents: list[str]
    missing_documents: list[str]
    readiness_percent: float
