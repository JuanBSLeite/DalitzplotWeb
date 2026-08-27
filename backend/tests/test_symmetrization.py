import numpy as np
import pytest

from app.physics.amplitudes import AmplitudeModel, _mapped_decay_chains
from app.schemas import ResonanceConfig


def _toy_momenta() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p1 = np.array([[0.20, 0.00, 0.10, 0.30], [0.10, 0.04, 0.00, 0.22]])
    p2 = np.array([[-0.08, 0.05, -0.02, 0.24], [-0.03, 0.02, 0.08, 0.21]])
    p3 = np.array([[-0.12, -0.05, -0.08, 0.32], [-0.07, -0.06, -0.08, 0.25]])
    return p1, p2, p3


def _mass_squared(p: np.ndarray) -> np.ndarray:
    return p[:, 3] ** 2 - np.sum(p[:, :3] ** 2, axis=1)


def test_two_identical_bachelors_generate_two_distinct_chains() -> None:
    chains = _mapped_decay_chains((1, 2), (211, -211, 211))
    assert len(chains) == 2
    assert {tuple(sorted(chain[:2])) for chain in chains} == {(0, 1), (1, 2)}


def test_three_identical_particles_generate_three_pairings_not_six() -> None:
    chains = _mapped_decay_chains((1, 2), (111, 111, 111))
    assert len(chains) == 3


def test_symmetrized_amplitude_is_invariant_under_identical_exchange() -> None:
    momenta = _toy_momenta()
    resonance = ResonanceConfig(
        name="rho(770)0",
        pair=(1, 2),
        spin=1,
        mass=0.775,
        width=0.149,
    )

    def evaluate(ps: tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
        p1, p2, p3 = ps
        s12 = _mass_squared(p1 + p2)
        s13 = _mass_squared(p1 + p3)
        s23 = _mass_squared(p2 + p3)
        return AmplitudeModel(
            [resonance],
            mother_mass=1.865,
            daughter_masses=(0.13957, 0.13957, 0.13957),
            daughter_ids=(211, -211, 211),
        ).evaluate(
            momenta=ps,
            s12=s12,
            s13=s13,
            s23=s23,
            normalize_components=False,
        ).amplitude_squared

    original = evaluate(momenta)
    swapped = evaluate((momenta[2], momenta[1], momenta[0]))
    assert np.allclose(original, swapped, rtol=1e-10, atol=1e-10)


def test_odd_L_is_rejected_for_identical_spin_zero_resonance_daughters() -> None:
    momenta = _toy_momenta()
    p1, p2, p3 = momenta
    s12 = _mass_squared(p1 + p2)
    s13 = _mass_squared(p1 + p3)
    s23 = _mass_squared(p2 + p3)
    resonance = ResonanceConfig(
        name="unphysical-vector-identical-pair",
        pair=(1, 2),
        spin=1,
        mass=0.775,
        width=0.149,
    )

    with pytest.raises(ValueError, match="Odd orbital angular momentum"):
        AmplitudeModel(
            [resonance],
            mother_mass=1.865,
            daughter_masses=(0.13957, 0.13957, 0.13498),
            daughter_ids=(111, 111, 221),
            symmetrize=False,
        ).evaluate(
            momenta=momenta,
            s12=s12,
            s13=s13,
            s23=s23,
            normalize_components=False,
        )
