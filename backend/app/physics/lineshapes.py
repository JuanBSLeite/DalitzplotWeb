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


def breakup_momentum_reference(
    s: np.ndarray | float,
    mass_a: float,
    mass_b: float,
) -> np.ndarray:
    """Positive momentum scale used to normalize subthreshold poles.

    For a pole mass outside the physical two-body region the physical q0 is
    not real. To keep the real Blatt-Weisskopf/running-width convention used
    by this project, the reference scale is defined from the magnitude of the
    analytically continued Källén function:

        |q_ref| = sqrt(|lambda(s,m_a^2,m_b^2)|) / (2 sqrt(s)).

    This quantity is used only as the normalization scale q0. Event-by-event
    q(s) remains the physical breakup momentum and is zero below threshold.
    """

    s_arr = np.asarray(s, dtype=np.float64)
    root_s = np.sqrt(np.clip(s_arr, 0.0, None))
    lam = kallen(s_arr, mass_a * mass_a, mass_b * mass_b)
    momentum = np.zeros_like(root_s)
    valid = root_s > 0.0
    momentum[valid] = np.sqrt(np.abs(lam[valid])) / (2.0 * root_s[valid])
    return momentum


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

    This is the same p used by the Zemach angular term and by the mother
    Blatt-Weisskopf factor in the convention adopted here.
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
    """Unnormalised Blatt-Weisskopf barrier factor B_L(z).

    The variable used here is z=(q r)^2, with q in GeV and r in GeV^-1,
    so z is dimensionless. The normalized factor is formed by taking the
    ratio B_L(z)/B_L(z0).
    """

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

    The convention implemented is

        BW(s) = F_M(p,p0) F_R(q,q0)
                / [m0^2 - s - i m0 Gamma(s)]

        Gamma(s) = Gamma0 (q/q0)^(2L+1) (m0/sqrt(s)) F_R(q,q0)^2.

    q is the physical momentum of a resonance daughter in the resonance rest
    frame. p is the bachelor momentum in that same resonance rest frame.

    Pole masses below the daughter threshold are allowed. In that case q0 is
    defined by breakup_momentum_reference(), i.e. by the magnitude of the
    analytically continued Källén function. The physical event momentum q(s)
    is still zero whenever the daughter channel is closed.
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

        pole_s = pole_mass * pole_mass
        physical_q0 = float(
            breakup_momentum(
                pole_s,
                daughter_masses[0],
                daughter_masses[1],
            )
        )
        reference_q0 = float(
            breakup_momentum_reference(
                pole_s,
                daughter_masses[0],
                daughter_masses[1],
            )
        )
        self.subthreshold_pole = physical_q0 <= 0.0
        self.q0 = physical_q0 if physical_q0 > 0.0 else reference_q0
        self.p0 = float(
            bachelor_momentum_in_resonance_rest(
                pole_s,
                mother_mass,
                bachelor_mass,
            )
        )

        # Exactly at threshold lambda=0 and no finite q0 normalization exists.
        # The pole is still accepted, using a constant-width fallback.
        self.constant_width_fallback = self.q0 <= 1e-15

    def evaluate(self, s: np.ndarray) -> np.ndarray:
        s_arr = np.asarray(s, dtype=np.float64)
        root_s = np.sqrt(np.clip(s_arr, 1e-15, None))
        q = breakup_momentum(s_arr, *self.daughter_masses)
        p = bachelor_momentum_in_resonance_rest(
            s_arr,
            self.mother_mass,
            self.bachelor_mass,
        )

        q0_for_barrier = 0.0 if self.constant_width_fallback else self.q0
        resonance_barrier = normalised_blatt_weisskopf(
            self.orbital_l,
            q,
            q0_for_barrier,
            self.resonance_radius,
        )
        mother_barrier = normalised_blatt_weisskopf(
            self.orbital_l,
            p,
            self.p0,
            self.mother_radius,
        )

        if self.constant_width_fallback:
            width = np.full_like(root_s, self.pole_width)
        else:
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
