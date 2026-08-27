import numpy as np

from app.physics.lineshapes import (
    DynamicRelativisticBreitWigner,
    bachelor_momentum_in_resonance_rest,
    blatt_weisskopf,
    breakup_momentum,
    normalised_blatt_weisskopf,
    virtual_reference_mass,
)


def test_breakup_momentum_vanishes_below_threshold():
    q = breakup_momentum(np.array([0.01]), 0.13957, 0.13957)
    assert q[0] == 0.0


def test_breakup_momentum_vanishes_below_unequal_mass_threshold():
    q = breakup_momentum(np.array([0.01]), 0.493677, 0.139570)
    assert q[0] == 0.0


def test_virtual_reference_mass_maps_subthreshold_pole_into_physical_region():
    minimum = 2.0 * 0.13957
    maximum = 1.86484 - 0.13498
    effective = virtual_reference_mass(0.25, minimum, maximum)
    assert minimum < effective < maximum


def test_virtual_reference_mass_leaves_physical_pole_unchanged():
    assert np.isclose(virtual_reference_mass(0.77526, 0.27914, 1.72986), 0.77526)


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


def test_dynamic_rbw_at_physical_pole_has_pole_width_and_unit_barriers():
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
    assert not rbw.virtual_pole
    assert np.isclose(rbw.reference_mass, pole_mass)
    value = rbw.evaluate(np.array([pole_mass**2]))[0]
    expected = 1j / (pole_mass * pole_width)
    assert np.allclose(value, expected)


def test_dynamic_rbw_accepts_subthreshold_virtual_pole():
    rbw = DynamicRelativisticBreitWigner(
        pole_mass=0.25,
        pole_width=0.10,
        orbital_l=1,
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957),
        bachelor_mass=0.13498,
    )
    assert rbw.virtual_pole
    assert rbw.reference_mass > 2.0 * 0.13957
    assert rbw.q0 > 0.0
    assert rbw.p0 > 0.0

    value = rbw.evaluate(np.array([0.40**2]))
    assert np.isfinite(value.real).all()
    assert np.isfinite(value.imag).all()


def test_dynamic_rbw_accepts_pole_above_accessible_pair_region():
    rbw = DynamicRelativisticBreitWigner(
        pole_mass=2.10,
        pole_width=0.20,
        orbital_l=0,
        mother_mass=1.86484,
        daughter_masses=(0.13957, 0.13957),
        bachelor_mass=0.13498,
    )
    assert rbw.virtual_pole
    assert rbw.reference_mass < 1.86484 - 0.13498
    value = rbw.evaluate(np.array([1.20**2]))
    assert np.isfinite(value.real).all()
    assert np.isfinite(value.imag).all()
