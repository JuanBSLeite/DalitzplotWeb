import numpy as np

from app.physics.normalization import component_normalizations
from app.schemas import ResonanceConfig


def _rho(magnitude: float = 1.0, phase_deg: float = 0.0) -> ResonanceConfig:
    return ResonanceConfig(
        name="rho(770)0",
        pair=(1, 2),
        spin=1,
        mass=0.77526,
        width=0.1491,
        magnitude=magnitude,
        phase_deg=phase_deg,
    )


def test_component_normalization_is_independent_of_coefficient():
    kwargs = dict(
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957, 0.13498),
        daughter_ids=(211, -211, 111),
        symmetrize=True,
    )
    first = component_normalizations([_rho(1.0, 0.0)], **kwargs)
    second = component_normalizations([_rho(3.4, 137.0)], **kwargs)

    assert first.keys() == second.keys()
    for key in first:
        assert np.isclose(first[key], second[key], rtol=0.0, atol=0.0)


def test_component_normalization_is_deterministic():
    kwargs = dict(
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957, 0.13498),
        daughter_ids=(211, -211, 111),
        symmetrize=True,
    )
    first = component_normalizations([_rho()], **kwargs)
    second = component_normalizations([_rho()], **kwargs)
    assert first == second
