from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas import (
    DecayRequest,
    DecayValidation,
    PhaseSpaceGenerateRequest,
    PhaseSpaceGenerateResponse,
    TheoreticalPlotRequest,
    TheoreticalPlotResponse,
    ModelDocument,
    ModelImportValidation,
    ParticleRef,
)
from app.services.decays import validate_decay
from app.services.export import export_csv
from app.services.monte_carlo import generate_weighted_sample
from app.services.particles import ParticleLookupError, resolve_particle
from app.services.qrules_service import QRulesValidationError
from app.services.theoretical_plot import calculate_theoretical_plot

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




@router.post("/model/validate-import", response_model=ModelImportValidation)
def validate_imported_model(payload: ModelDocument) -> ModelImportValidation:
    decay = payload.decay
    mother = decay.get("mother")
    daughters = decay.get("daughters")
    if not isinstance(mother, str) or not isinstance(daughters, list) or len(daughters) != 3 or not all(isinstance(item, str) for item in daughters):
        raise HTTPException(status_code=422, detail="The model decay must contain one mother and exactly three daughter names.")

    warnings: list[str] = []
    validation = validate_decay(
        DecayRequest(
            mother=ParticleRef(name=mother),
            daughters=[ParticleRef(name=item) for item in daughters],
        )
    )
    for amplitude in payload.amplitudes:
        if amplitude.component_type == "nonresonant":
            continue
        try:
            particle = resolve_particle(amplitude.name)
        except ParticleLookupError:
            warnings.append(f"Amplitude '{amplitude.name}' is not present in the particle database; imported as a custom state.")
            continue
        if particle.spin is not None and round(particle.spin) != amplitude.spin:
            warnings.append(
                f"Amplitude '{amplitude.name}' has spin {amplitude.spin} in the file but {particle.spin:g} in the particle database."
            )

    return ModelImportValidation(
        valid=True,
        allowed=validation.allowed,
        channel=validation.channel,
        warnings=[*validation.warnings, *warnings],
    )


@router.post("/model/theoretical-plot", response_model=TheoreticalPlotResponse)
def theoretical_plot(payload: TheoreticalPlotRequest) -> TheoreticalPlotResponse:
    try:
        return calculate_theoretical_plot(payload)
    except (ParticleLookupError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/toy/generate", response_model=PhaseSpaceGenerateResponse)
def generate_toy(payload: PhaseSpaceGenerateRequest) -> PhaseSpaceGenerateResponse:
    try:
        return generate_weighted_sample(payload)
    except (ParticleLookupError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# Backward-compatible alias.
@router.post("/phase-space/generate", response_model=PhaseSpaceGenerateResponse)
def generate_phase_space(payload: PhaseSpaceGenerateRequest) -> PhaseSpaceGenerateResponse:
    return generate_toy(payload)


@router.post("/toy/export/csv")
def download_csv(payload: PhaseSpaceGenerateRequest) -> Response:
    try:
        content = export_csv(payload)
    except (ParticleLookupError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="dalitz_toy.csv"'},
    )
