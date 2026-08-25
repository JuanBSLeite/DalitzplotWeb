import numpy as np

from app.physics.lineshapes import (
    DynamicRelativisticBreitWigner,
    bachelor_momentum_in_resonance_rest,
    blatt_weisskopf,
    breakup_momentum,
    breakup_momentum_reference,
    normalised_blatt_weisskopf,
)


def test_breakup_momentum_vanishes_below_threshold():
    q = breakup_momentum(np.array([0.01]), 0.13957, 0.13957)
    assert q[0] == 0.0


def test_breakup_momentum_vanishes_below_unequal_mass_threshold():
    # lambda is positive again below the pseudo-threshold |m1-m2|, but the
    # physical two-body momentum must still be zero below m1+m2.
    q = breakup_momentum(np.array([0.01]), 0.493677, 0.139570)
    assert q[0] == 0.0


def test_subthreshold_reference_momentum_is_positive():
    pole_mass = 0.25
    mass = 0.13957
    q_physical = breakup_momentum(np.array([pole_mass**2]), mass, mass)[0]
    q_reference = breakup_momentum_reference(np.array([pole_mass**2]), mass, mass)[0]
    assert q_physical == 0.0
    assert q_reference > 0.0


def test_barrier_factor_is_normalised_at_reference_momentum():
    for orbital_l in (0, 1, 2):
        result = normalised_blatt_weisskopf(
            orbital_l,
            np.array([0.3]),
            reference_momentum=0.3,
            radius=1.5,
        )
        assert np.allclose(result, 1.0)


def test_blatt_weisskopf_values_at_zero():
    assert np.allclose(blatt_weisskopf(0, np.array([0.0])), 1.0)
    assert np.allclose(blatt_weisskopf(1, np.array([0.0])), 1.0)
    assert np.allclose(blatt_weisskopf(2, np.array([0.0])), 1.0 / 3.0)


def test_bachelor_momentum_in_resonance_rest_matches_formula():
    mother_mass = 1.86484
    resonance_mass = 0.77526
    bachelor_mass = 0.13498
    s = resonance_mass**2

    p = bachelor_momentum_in_resonance_rest(
        np.array([s]), mother_mass, bachelor_mass
    )[0]
    lam = (
        mother_mass**4
        + s**2
        + bachelor_mass**4
        - 2.0
        * (
            mother_mass**2 * s
            + mother_mass**2 * bachelor_mass**2
            + s * bachelor_mass**2
        )
    )
    expected = np.sqrt(lam) / (2.0 * np.sqrt(s))
    assert np.allclose(p, expected)


def test_dynamic_rbw_at_pole_has_pole_width_and_unit_barriers():
    pole_mass = 0.77526
    pole_width = 0.1491
    rbw = DynamicRelativisticBreitWigner(
        pole_mass=pole_mass,
        pole_width=pole_width,
        orbital_l=1,
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957),
        bachelor_mass=0.13498,
    )
    value = rbw.evaluate(np.array([pole_mass**2]))[0]

    # At s=m0^2 both normalized barrier factors are one and Gamma(s)=Gamma0,
    # so BW(m0^2)=i/(m0 Gamma0) for the denominator convention used here.
    expected = 1j / (pole_mass * pole_width)
    assert np.allclose(value, expected)


def test_dynamic_rbw_accepts_subthreshold_pole():
    rbw = DynamicRelativisticBreitWigner(
        pole_mass=0.25,
        pole_width=0.10,
        orbital_l=1,
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957),
        bachelor_mass=0.13498,
    )
    assert rbw.subthreshold_pole
    assert rbw.q0 > 0.0

    # Evaluate in the physical pi-pi region. The result must remain finite.
    value = rbw.evaluate(np.array([0.40**2]))
    assert np.isfinite(value.real).all()
    assert np.isfinite(value.imag).all()


def test_dynamic_rbw_accepts_pole_exactly_at_threshold():
    mass = 0.13957
    rbw = DynamicRelativisticBreitWigner(
        pole_mass=2.0 * mass,
        pole_width=0.10,
        orbital_l=0,
        mother_mass=1.86484,
        daughter_masses=(mass, mass),
        bachelor_mass=0.13498,
    )
    assert rbw.constant_width_fallback
    value = rbw.evaluate(np.array([0.40**2]))
    assert np.isfinite(value.real).all()
    assert np.isfinite(value.imag).all()


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
