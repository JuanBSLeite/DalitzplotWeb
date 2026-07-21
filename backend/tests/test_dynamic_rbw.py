import numpy as np

from app.physics.lineshapes import (
    DynamicRelativisticBreitWigner,
    breakup_momentum,
    normalised_blatt_weisskopf,
)


def test_breakup_momentum_vanishes_below_threshold():
    q = breakup_momentum(np.array([0.01]), 0.13957, 0.13957)
    assert q[0] == 0.0


def test_barrier_factor_is_normalised_at_reference_momentum():
    result = normalised_blatt_weisskopf(
        1,
        np.array([0.3]),
        reference_momentum=0.3,
        radius=1.5,
    )
    assert np.allclose(result, 1.0)


def test_dynamic_rbw_is_finite_near_pole():
    rbw = DynamicRelativisticBreitWigner(
        pole_mass=0.77526,
        pole_width=0.1491,
        orbital_l=1,
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957),
        bachelor_mass=0.13498,
    )
    value = rbw.evaluate(np.array([0.77526**2]))
    assert np.isfinite(value.real).all()
    assert np.isfinite(value.imag).all()
    assert np.abs(value[0]) > 0.0
