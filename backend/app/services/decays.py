from app.schemas import DecayRequest, DecayValidation
from app.services.particles import (
    ParticleLookupError,
    resolve_decay,
    validate_spinless_dalitz_scope,
)
from app.services.qrules_service import validate_decay_with_qrules


def validate_decay(req: DecayRequest) -> DecayValidation:
    """Validate the physical decay and report amplitude-engine scope warnings."""

    validation = validate_decay_with_qrules(req)
    if not validation.allowed:
        return validation

    try:
        mother, daughters = resolve_decay(
            req.mother.name,
            tuple(item.name for item in req.daughters),
        )
        validate_spinless_dalitz_scope(mother, daughters)
    except ParticleLookupError as exc:
        # qrules answers whether the decay is physically allowed. Keep that
        # information, but make the narrower amplitude-engine scope explicit.
        validation.warnings.append(f"Amplitude-model scope: {exc}")

    return validation
