from app.schemas import DecayRequest, DecayValidation


def validate_decay(payload: DecayRequest) -> DecayValidation:
    if not payload.mother.name:
        return DecayValidation(
            valid=False,
            message="The mother particle must have a name.",
            warnings=[],
        )

    if len(payload.daughters) != 3:
        return DecayValidation(
            valid=False,
            message="A three-body decay requires exactly three daughters.",
            warnings=[],
        )

    return DecayValidation(
        valid=True,
        message="Decay request accepted.",
        warnings=[],
    )
