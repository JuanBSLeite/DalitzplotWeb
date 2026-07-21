from fastapi import APIRouter, HTTPException

from app.schemas import (
    DecayRequest,
    DecayValidation,
    PhaseSpaceGenerateRequest,
    PhaseSpaceGenerateResponse,
)
from app.services.decays import validate_decay
from app.services.qrules_service import QRulesValidationError
from app.services.monte_carlo import generate_weighted_sample
from app.services.particles import ParticleLookupError, resolve_particle

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/particles/{particle_name}")
def particle_info(particle_name: str) -> dict[str, object]:
    try:
        particle = resolve_particle(particle_name)
    except ParticleLookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "name": particle.name,
        "pdgid": particle.pdgid,
        "mass_gev": particle.mass_gev,
        "charge": particle.charge,
        "spin": particle.spin,
        "width_gev": particle.width_gev,
    }


@router.post("/decays/validate", response_model=DecayValidation)
def validate(payload: DecayRequest) -> DecayValidation:
    try:
        return validate_decay(payload)
    except QRulesValidationError as exc:
        raise HTTPException(status_code=500, detail=f"QRules failed: {exc}") from exc


@router.post("/phase-space/generate", response_model=PhaseSpaceGenerateResponse)
def generate_phase_space(
    payload: PhaseSpaceGenerateRequest,
) -> PhaseSpaceGenerateResponse:
    try:
        return generate_weighted_sample(payload)
    except ParticleLookupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
