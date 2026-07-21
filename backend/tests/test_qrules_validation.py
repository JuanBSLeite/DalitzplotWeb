from app.schemas import DecayRequest, ParticleRef
from app.services.qrules_service import validate_decay_with_qrules


def test_d0_three_pion_is_allowed_and_grouped():
    result = validate_decay_with_qrules(
        DecayRequest(
            mother=ParticleRef(name="D0"),
            daughters=[
                ParticleRef(name="pi+"),
                ParticleRef(name="pi-"),
                ParticleRef(name="pi0"),
            ],
        )
    )

    assert result.allowed
    assert result.transition_count > 0
    assert "rho(770)0" in {item.name for item in result.suggested_resonances["12"]}
    assert "rho(770)+" in {item.name for item in result.suggested_resonances["13"]}
    assert "rho(770)-" in {item.name for item in result.suggested_resonances["23"]}
