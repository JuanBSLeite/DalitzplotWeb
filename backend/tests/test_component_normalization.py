import numpy as np

from app.physics.amplitudes import AmplitudeModel
from app.schemas import ResonanceConfig


def _m2(p: np.ndarray) -> np.ndarray:
    return p[:, 3] ** 2 - np.sum(p[:, :3] ** 2, axis=1)


def test_complete_component_is_normalized_with_phase_space_weights() -> None:
    rng = np.random.default_rng(13)
    n = 256
    # Synthetic, non-singular four-vectors sufficient for testing the normalization algebra.
    spatial1 = rng.normal(0.0, 0.08, size=(n, 3))
    spatial2 = rng.normal(0.0, 0.08, size=(n, 3))
    spatial3 = -(spatial1 + spatial2)
    mass = 0.13957
    p1 = np.column_stack((spatial1, np.sqrt(np.sum(spatial1**2, axis=1) + mass**2)))
    p2 = np.column_stack((spatial2, np.sqrt(np.sum(spatial2**2, axis=1) + mass**2)))
    p3 = np.column_stack((spatial3, np.sqrt(np.sum(spatial3**2, axis=1) + mass**2)))
    s12, s13, s23 = _m2(p1+p2), _m2(p1+p3), _m2(p2+p3)
    weights = rng.uniform(0.2, 1.2, size=n)
    resonance = ResonanceConfig(name="rho", pair=(1, 2), spin=1, mass=0.775, width=0.149)
    result = AmplitudeModel(
        [resonance], mother_mass=1.865, daughter_masses=(mass, mass, mass),
        daughter_ids=(211, -211, 111), symmetrize=True,
    ).evaluate(
        momenta=(p1,p2,p3), s12=s12, s13=s13, s23=s23,
        phase_space_weight=weights, normalize_components=True,
    )
    component = next(iter(result.component_amplitudes.values()))
    assert np.isclose(np.mean(weights * np.abs(component)**2), 1.0, rtol=1e-12, atol=1e-12)
    assert next(iter(result.component_normalization_integrals.values())) > 0.0


def test_magnitude_is_applied_after_basis_normalization() -> None:
    rng = np.random.default_rng(4)
    n = 128
    x = rng.normal(0, 0.05, (n,3)); y = rng.normal(0,0.05,(n,3)); z=-(x+y); m=.13957
    mk=lambda v: np.column_stack((v, np.sqrt(np.sum(v*v,axis=1)+m*m)))
    p1,p2,p3=mk(x),mk(y),mk(z)
    s12,s13,s23=_m2(p1+p2),_m2(p1+p3),_m2(p2+p3)
    weights=np.ones(n)
    cfg=ResonanceConfig(name="scalar", pair=(1,2), spin=0, mass=.7, width=.1, magnitude=3.0)
    result=AmplitudeModel([cfg], mother_mass=1.865, daughter_masses=(m,m,m), daughter_ids=(211,-211,111)).evaluate(
        momenta=(p1,p2,p3), s12=s12,s13=s13,s23=s23, phase_space_weight=weights
    )
    assert np.isclose(np.mean(weights*result.amplitude_squared), 9.0, rtol=1e-12, atol=1e-12)
