from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class LineShape(ABC):
    @abstractmethod
    def evaluate(self, s: np.ndarray) -> np.ndarray:
        raise NotImplementedError


def kallen(x: np.ndarray | float, y: float, z: float) -> np.ndarray:
    """Return the Källén function lambda(x,y,z)."""

    x_arr = np.asarray(x, dtype=np.float64)
    return x_arr * x_arr + y * y + z * z - 2.0 * (x_arr * y + x_arr * z + y * z)


def breakup_momentum(s: np.ndarray | float, mass_a: float, mass_b: float) -> np.ndarray:
    """Physical two-body breakup momentum in the ab rest frame.

    q(s) = sqrt(lambda(s, m_a^2, m_b^2)) / (2 sqrt(s)).

    The physical momentum is set to zero below threshold. This avoids the
    pseudo-threshold branch that appears for unequal daughter masses.
    """

    s_arr = np.asarray(s, dtype=np.float64)
    root_s = np.sqrt(np.clip(s_arr, 0.0, None))
    lam = kallen(s_arr, mass_a * mass_a, mass_b * mass_b)
    threshold = mass_a + mass_b
    momentum = np.zeros_like(root_s)
    valid = (root_s >= threshold) & (root_s > 0.0) & (lam >= 0.0)
    momentum[valid] = np.sqrt(np.clip(lam[valid], 0.0, None)) / (2.0 * root_s[valid])
    return momentum


def virtual_reference_mass(
    pole_mass: float,
    minimum_mass: float,
    maximum_mass: float,
) -> float:
    """Return the effective mass used for a virtual resonance reference point.

    If ``pole_mass`` lies inside the kinematically accessible two-body mass
    interval, it is returned unchanged. Otherwise the pole is smoothly mapped
    inside the interval with the commonly used Dalitz-fit prescription

        m_eff = m_min + (m_max-m_min)/2 *
                [1 + tanh((m0 - (m_min+m_max)/2)/(m_max-m_min))].

    The true pole mass remains in the Breit-Wigner denominator. ``m_eff`` is
    used only to define the reference momenta of barrier factors and the
    mass-dependent width for a virtual contribution.
    """

    if maximum_mass <= minimum_mass:
        raise ValueError("Virtual-resonance mass interval must have positive width")
    if minimum_mass <= pole_mass <= maximum_mass:
        return pole_mass

    span = maximum_mass - minimum_mass
    midpoint = 0.5 * (minimum_mass + maximum_mass)
    effective = minimum_mass + 0.5 * span * (
        1.0 + np.tanh((pole_mass - midpoint) / span)
    )

    # Keep the reference point strictly inside the open physical interval so
    # q0 and p0 remain finite even for very distant virtual poles.
    epsilon = max(1e-12 * span, np.finfo(np.float64).eps * max(1.0, maximum_mass))
    return float(np.clip(effective, minimum_mass + epsilon, maximum_mass - epsilon))


def bachelor_momentum_in_resonance_rest(
    s: np.ndarray | float,
    mother_mass: float,
    bachelor_mass: float,
) -> np.ndarray:
    """Bachelor momentum in the rest frame of the resonance pair.

    For a spin-0 three-body decay M -> R(s) + b, the Dalitz/Zemach
    convention used in this project evaluates the bachelor momentum p in
    the R rest frame:

        p(s) = sqrt(lambda(M^2, s, m_b^2)) / (2 sqrt(s)).
    """

    s_arr = np.asarray(s, dtype=np.float64)
    root_s = np.sqrt(np.clip(s_arr, 0.0, None))
    lam = kallen(mother_mass * mother_mass, s_arr, bachelor_mass * bachelor_mass)
    momentum = np.zeros_like(root_s)
    upper_limit = mother_mass - bachelor_mass
    valid = (root_s > 0.0) & (root_s <= upper_limit) & (lam >= 0.0)
    momentum[valid] = np.sqrt(np.clip(lam[valid], 0.0, None)) / (2.0 * root_s[valid])
    return momentum


def blatt_weisskopf(orbital_l: int, z: np.ndarray | float) -> np.ndarray:
    """Unnormalised Blatt-Weisskopf barrier factor B_L(z), z=(q r)^2."""

    z_arr = np.asarray(z, dtype=np.float64)
    if orbital_l == 0:
        return np.ones_like(z_arr)
    if orbital_l == 1:
        return np.sqrt(1.0 / (1.0 + z_arr))
    if orbital_l == 2:
        return np.sqrt(1.0 / (z_arr * z_arr + 3.0 * z_arr + 9.0))
    raise ValueError("Blatt-Weisskopf factors are currently implemented for L=0, 1, and 2")


def normalised_blatt_weisskopf(
    orbital_l: int,
    momentum: np.ndarray,
    reference_momentum: float,
    radius: float,
) -> np.ndarray:
    """Blatt-Weisskopf factor normalized to unity at the reference momentum."""

    z = (momentum * radius) ** 2
    z0 = (reference_momentum * radius) ** 2
    denominator = float(blatt_weisskopf(orbital_l, z0))
    if denominator == 0.0:
        raise ValueError("Invalid Blatt-Weisskopf reference value")
    return blatt_weisskopf(orbital_l, z) / denominator


class DynamicRelativisticBreitWigner(LineShape):
    """Relativistic Breit-Wigner with running width and barrier factors.

    BW(s) = F_M(p,p0) F_R(q,q0)
            / [m0^2 - s - i m0 Gamma(s)]

    Gamma(s) = Gamma0 (q/q0)^(2L+1) (m0/sqrt(s)) F_R(q,q0)^2.

    For a virtual pole outside the accessible daughter-pair mass interval, the
    true ``m0`` remains in the Breit-Wigner denominator while the reference
    momenta q0 and p0 are calculated at ``m_eff`` from
    :func:`virtual_reference_mass`.
    """

    def __init__(
        self,
        *,
        pole_mass: float,
        pole_width: float,
        orbital_l: int,
        mother_mass: float,
        daughter_masses: tuple[float, float],
        bachelor_mass: float,
        resonance_radius: float = 1.5,
        mother_radius: float = 5.0,
    ):
        self.pole_mass = pole_mass
        self.pole_width = pole_width
        self.orbital_l = orbital_l
        self.mother_mass = mother_mass
        self.daughter_masses = daughter_masses
        self.bachelor_mass = bachelor_mass
        self.resonance_radius = resonance_radius
        self.mother_radius = mother_radius

        minimum_mass = daughter_masses[0] + daughter_masses[1]
        maximum_mass = mother_mass - bachelor_mass
        self.reference_mass = virtual_reference_mass(
            pole_mass,
            minimum_mass,
            maximum_mass,
        )
        self.virtual_pole = not (minimum_mass <= pole_mass <= maximum_mass)

        reference_s = self.reference_mass * self.reference_mass
        self.q0 = float(
            breakup_momentum(
                reference_s,
                daughter_masses[0],
                daughter_masses[1],
            )
        )
        self.p0 = float(
            bachelor_momentum_in_resonance_rest(
                reference_s,
                mother_mass,
                bachelor_mass,
            )
        )
        if self.q0 <= 0.0:
            raise ValueError("Could not define a finite resonance reference momentum q0")
        if self.p0 <= 0.0:
            raise ValueError("Could not define a finite mother-vertex reference momentum p0")

    def evaluate(self, s: np.ndarray) -> np.ndarray:
        s_arr = np.asarray(s, dtype=np.float64)
        root_s = np.sqrt(np.clip(s_arr, 1e-15, None))
        q = breakup_momentum(s_arr, *self.daughter_masses)
        p = bachelor_momentum_in_resonance_rest(
            s_arr,
            self.mother_mass,
            self.bachelor_mass,
        )

        resonance_barrier = normalised_blatt_weisskopf(
            self.orbital_l,
            q,
            self.q0,
            self.resonance_radius,
        )
        mother_barrier = normalised_blatt_weisskopf(
            self.orbital_l,
            p,
            self.p0,
            self.mother_radius,
        )

        width = np.zeros_like(root_s)
        open_channel = q > 0.0
        width[open_channel] = (
            self.pole_width
            * (q[open_channel] / self.q0) ** (2 * self.orbital_l + 1)
            * (self.pole_mass / root_s[open_channel])
            * resonance_barrier[open_channel] ** 2
        )

        denominator = (
            self.pole_mass * self.pole_mass
            - s_arr
            - 1j * self.pole_mass * width
        )
        return mother_barrier * resonance_barrier / denominator
