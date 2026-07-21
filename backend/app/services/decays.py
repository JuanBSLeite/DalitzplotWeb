from particle import Particle
from app.schemas import DecayRequest,DecayValidation
def validate_decay(req:DecayRequest)->DecayValidation:
    try:
        mother=Particle.from_name(req.mother.name)
        daughters=[Particle.from_name(x.name) for x in req.daughters]
    except Exception as exc:
        return DecayValidation(valid=False,message=f"Unknown particle: {exc}")
    q0=mother.charge or 0; qf=sum((p.charge or 0) for p in daughters)
    if abs(q0-qf)>1e-9:
        return DecayValidation(valid=False,message="Electric charge is not conserved.")
    # qrules integration belongs in this adapter; charge is the first fast validation.
    return DecayValidation(valid=True,message="Basic quantum-number checks passed; qrules topology generation is the next implementation step.",warnings=["Full qrules validation not wired yet."])
