from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class LineShape(ABC):
    @abstractmethod
    def evaluate(self, s: np.ndarray) -> np.ndarray:
        raise NotImplementedError


def kallen(x: np.ndarray | float, y: float, z: float) -> np.ndarray:
    x_arr = np.asarray(x, dtype=np.float64)
    return x_arr * x_arr + y * y + z * z - 2.0 * (x_arr * y + x_arr * z + y * z)


def breakup_momentum(s: np.ndarray | float, mass_a: float, mass_b: float) -> np.ndarray:
    s_arr = np.asarray(s, dtype=np.float64)
    root_s = np.sqrt(np.clip(s_arr, 0.0, None))
    lam = kallen(s_arr, mass_a * mass_a, mass_b * mass_b)
    momentum = np.zeros_like(root_s)
    valid = (root_s > 0.0) & (lam > 0.0)
    momentum[valid] = np.sqrt(lam[valid]) / (2.0 * root_s[valid])
    return momentum


def blatt_weisskopf(spin: int, z: np.ndarray | float) -> np.ndarray:
    """Unnormalised Blatt-Weisskopf barrier factor B_L(z), z=(qr)^2."""

    z_arr = np.asarray(z, dtype=np.float64)
    if spin == 0:
        return np.ones_like(z_arr)
    if spin == 1:
        return np.sqrt(1.0 / (1.0 + z_arr))
    if spin == 2:
        return np.sqrt(1.0 / (z_arr * z_arr + 3.0 * z_arr + 9.0))
    raise ValueError("Blatt-Weisskopf factors are currently implemented for spin 0, 1, and 2")


def normalised_blatt_weisskopf(
    spin: int,
    momentum: np.ndarray,
    reference_momentum: float,
    radius: float,
) -> np.ndarray:
    z = (momentum * radius) ** 2
    z0 = (reference_momentum * radius) ** 2
    denominator = float(blatt_weisskopf(spin, z0))
    if denominator == 0.0:
        raise ValueError("Invalid Blatt-Weisskopf reference value")
    return blatt_weisskopf(spin, z) / denominator


class DynamicRelativisticBreitWigner(LineShape):
    """Relativistic Breit-Wigner with dynamic width and barrier factors."""

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

        self.q0 = float(
            breakup_momentum(
                pole_mass * pole_mass,
                daughter_masses[0],
                daughter_masses[1],
            )
        )
        self.p0 = float(
            breakup_momentum(
                pole_mass * pole_mass,
                mother_mass,
                bachelor_mass,
            )
        )
        # breakup_momentum(s, M, mb) is symmetric but represents an unphysical
        # two-body system here. Use the algebraically equivalent expression in
        # the resonance rest frame explicitly.
        pole_s = pole_mass * pole_mass
        lam_parent = kallen(mother_mass * mother_mass, pole_s, bachelor_mass * bachelor_mass)
        self.p0 = float(np.sqrt(max(float(lam_parent), 0.0)) / (2.0 * pole_mass))

        if self.q0 <= 0.0:
            raise ValueError("The resonance pole lies at or below the daughter threshold")

    def evaluate(self, s: np.ndarray) -> np.ndarray:
        s_arr = np.asarray(s, dtype=np.float64)
        root_s = np.sqrt(np.clip(s_arr, 1e-15, None))
        q = breakup_momentum(s_arr, *self.daughter_masses)

        lam_parent = kallen(
            self.mother_mass * self.mother_mass,
            s_arr,
            self.bachelor_mass * self.bachelor_mass,
        )
        p = np.zeros_like(root_s)
        valid_parent = lam_parent > 0.0
        p[valid_parent] = np.sqrt(lam_parent[valid_parent]) / (2.0 * root_s[valid_parent])

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
