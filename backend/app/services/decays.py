from app.schemas import DecayRequest, DecayValidation
from app.services.qrules_service import validate_decay_with_qrules


def validate_decay(req: DecayRequest) -> DecayValidation:
    return validate_decay_with_qrules(req)
