import numpy as np

from app.physics.dalitz_grid import build_dalitz_grid


def test_grid_reconstructs_energy_momentum_and_invariants():
    grid = build_dalitz_grid(1.86483, (0.13957, 0.13957, 0.13498), resolution=60)
    p1, p2, p3 = grid.momenta
    total = p1 + p2 + p3
    assert np.allclose(total[:, :3], 0.0, atol=1e-9)
    assert np.allclose(total[:, 3], 1.86483, atol=1e-9)
    identity = grid.s12 + grid.s13 + grid.s23
    expected = 1.86483**2 + 0.13957**2 + 0.13957**2 + 0.13498**2
    assert np.allclose(identity, expected, atol=1e-9)
