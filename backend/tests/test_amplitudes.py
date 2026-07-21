import numpy as np

from app.physics.amplitudes import AmplitudeModel
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
