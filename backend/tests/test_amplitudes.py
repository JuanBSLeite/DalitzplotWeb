import numpy as np

from app.physics.amplitudes import AmplitudeModel, _zemach_angular_term
from app.schemas import ResonanceConfig


def _momenta() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p1 = np.array([[0.15, 0.00, 0.00, 0.25], [0.10, 0.02, 0.00, 0.22]])
    p2 = np.array([[-0.05, 0.04, 0.00, 0.22], [-0.02, 0.01, 0.05, 0.20]])
    p3 = np.array([[-0.10, -0.04, 0.00, 0.30], [-0.08, -0.03, -0.05, 0.27]])
    return p1, p2, p3


def _m2(p: np.ndarray) -> np.ndarray:
    return p[:, 3] ** 2 - np.sum(p[:, :3] ** 2, axis=1)


def test_empty_model_is_pure_phase_space() -> None:
    momenta = _momenta()
    s12, s13, s23 = (_m2(momenta[0] + momenta[1]), _m2(momenta[0] + momenta[2]), _m2(momenta[1] + momenta[2]))
    result = AmplitudeModel(
        [], mother_mass=1.865, daughter_masses=(0.139, 0.139, 0.135), daughter_ids=(211, -211, 111)
    ).evaluate(momenta=momenta, s12=s12, s13=s13, s23=s23, normalize_components=False)
    assert np.allclose(result.amplitude_squared, 1.0)


def test_zemach_spin_zero_is_constant():
    daughter = np.array([[0.2, 0.0, 0.0, 0.3]])
    bachelor = np.array([[0.1, 0.0, 0.0, 0.2]])
    resonance = np.array([[0.0, 0.0, 0.0, 0.8]])
    assert np.allclose(_zemach_angular_term(0, daughter, bachelor, resonance), 1.0)


def test_zemach_spin_one_sign_flips_when_q_flips():
    resonance = np.array([[0.0, 0.0, 0.0, 1.0]])
    bachelor = np.array([[0.20, 0.0, 0.0, 0.30]])
    daughter_a = np.array([[0.10, 0.0, 0.0, 0.20]])
    daughter_b = np.array([[-0.10, 0.0, 0.0, 0.20]])

    z_a = _zemach_angular_term(1, daughter_a, bachelor, resonance)
    z_b = _zemach_angular_term(1, daughter_b, bachelor, resonance)
    assert np.allclose(z_a, -z_b)


def test_zemach_spin_two_matches_definition_in_resonance_rest_frame():
    resonance = np.array([[0.0, 0.0, 0.0, 1.0]])
    bachelor = np.array([[0.20, 0.0, 0.0, 0.30]])
    daughter = np.array([[0.10, 0.0, 0.0, 0.20]])

    result = _zemach_angular_term(2, daughter, bachelor, resonance)[0]
    dot = 0.20 * 0.10
    p2 = 0.20**2
    q2 = 0.10**2
    expected = (4.0 / 3.0) * (3.0 * dot**2 - p2 * q2)
    assert np.allclose(result, expected)
