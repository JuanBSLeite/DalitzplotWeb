import numpy as np

from app.physics.amplitudes import AmplitudeModel
from app.schemas import ResonanceConfig


def test_nonresonant_component_is_constant_and_normalized():
    n = 8
    zeros = np.zeros((n, 4), dtype=float)
    config = ResonanceConfig(
        component_type="nonresonant",
        name="Non-resonant",
        pair=(1, 2),
        spin=0,
        mass=1.0,
        width=1.0,
        magnitude=2.0,
        phase_deg=30.0,
    )
    result = AmplitudeModel(
        [config],
        mother_mass=2.0,
        daughter_masses=(0.1, 0.1, 0.1),
        daughter_ids=(1, 2, 3),
    ).evaluate(
        momenta=(zeros, zeros, zeros),
        s12=np.ones(n),
        s13=np.ones(n),
        s23=np.ones(n),
        phase_space_weight=np.ones(n),
        normalize_components=True,
    )
    expected = 2.0 * np.exp(1j * np.deg2rad(30.0))
    assert np.allclose(result.amplitude, expected)
    assert np.allclose(result.amplitude_squared, 4.0)
    assert list(result.component_normalization_integrals.values()) == [1.0]
