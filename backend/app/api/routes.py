from fastapi import APIRouter

from app.schemas import (
    DecayRequest,
    DecayValidation,
    MonteCarloGenerateRequest,
    MonteCarloGenerateResponse,
)
from app.services.decays import validate_decay
from app.services.monte_carlo import generate_weighted_sample

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/decays/validate", response_model=DecayValidation)
def validate(payload: DecayRequest) -> DecayValidation:
    return validate_decay(payload)


@router.post("/mc/generate", response_model=MonteCarloGenerateResponse)
def generate_mc(payload: MonteCarloGenerateRequest) -> MonteCarloGenerateResponse:
    return generate_weighted_sample(payload)
