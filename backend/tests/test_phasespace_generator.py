import numpy as np

from app.physics.phasespace_generator import invariant_mass_squared


def test_invariant_mass_squared_for_particle_at_rest() -> None:
    vector = np.array([[0.0, 0.0, 0.0, 2.0]])
    result = invariant_mass_squared(vector)
    np.testing.assert_allclose(result, [4.0])


def test_invariant_mass_squared_for_lightlike_vector() -> None:
    vector = np.array([[0.0, 0.0, 3.0, 3.0]])
    result = invariant_mass_squared(vector)
    np.testing.assert_allclose(result, [0.0])
