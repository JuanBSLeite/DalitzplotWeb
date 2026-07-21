from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class DalitzGrid:
    momenta: tuple[np.ndarray, np.ndarray, np.ndarray]
    s12: np.ndarray
    s13: np.ndarray
    s23: np.ndarray
    x_axis: np.ndarray
    y_axis: np.ndarray
    valid_flat_indices: np.ndarray
    resolution: int


def build_dalitz_grid(
    mother_mass: float,
    daughter_masses: tuple[float, float, float],
    resolution: int = 140,
) -> DalitzGrid:
    """Build a regular grid in (s12, s13) and reconstruct valid four-vectors.

    The reconstruction is performed in the parent rest frame. Global orientation
    is arbitrary; p1 is placed along +z and p2 in the x-z plane. This preserves
    all Lorentz invariants and helicity/Zemach angular information.
    """

    if not 40 <= resolution <= 350:
        raise ValueError("resolution must be between 40 and 350")
    m1, m2, m3 = daughter_masses
    if mother_mass <= m1 + m2 + m3:
        raise ValueError("Mother mass must exceed the daughter-mass sum")

    s12_axis = np.linspace((m1 + m2) ** 2, (mother_mass - m3) ** 2, resolution)
    s13_axis = np.linspace((m1 + m3) ** 2, (mother_mass - m2) ** 2, resolution)
    s12_mesh, s13_mesh = np.meshgrid(s12_axis, s13_axis, indexing="xy")
    s12 = s12_mesh.ravel()
    s13 = s13_mesh.ravel()
    s23 = mother_mass**2 + m1**2 + m2**2 + m3**2 - s12 - s13

    e1 = (mother_mass**2 + m1**2 - s23) / (2.0 * mother_mass)
    e2 = (mother_mass**2 + m2**2 - s13) / (2.0 * mother_mass)
    e3 = (mother_mass**2 + m3**2 - s12) / (2.0 * mother_mass)
    p1_mag2 = e1**2 - m1**2
    p2_mag2 = e2**2 - m2**2
    p3_mag2 = e3**2 - m3**2

    p1_mag = np.sqrt(np.clip(p1_mag2, 0.0, None))
    p2_mag = np.sqrt(np.clip(p2_mag2, 0.0, None))
    denominator = 2.0 * p1_mag * p2_mag
    numerator = 2.0 * e1 * e2 - (s12 - m1**2 - m2**2)
    cos12 = np.divide(numerator, denominator, out=np.full_like(numerator, 2.0), where=denominator > 1e-14)

    valid = (
        (s23 >= (m2 + m3) ** 2)
        & (s23 <= (mother_mass - m1) ** 2)
        & (p1_mag2 >= -1e-10)
        & (p2_mag2 >= -1e-10)
        & (p3_mag2 >= -1e-10)
        & (cos12 >= -1.0 - 1e-9)
        & (cos12 <= 1.0 + 1e-9)
    )
    valid_indices = np.flatnonzero(valid)
    c = np.clip(cos12[valid], -1.0, 1.0)
    sin12 = np.sqrt(np.clip(1.0 - c**2, 0.0, None))

    p1v = np.column_stack((
        np.zeros(valid_indices.size),
        np.zeros(valid_indices.size),
        p1_mag[valid],
        e1[valid],
    ))
    p2v = np.column_stack((
        p2_mag[valid] * sin12,
        np.zeros(valid_indices.size),
        p2_mag[valid] * c,
        e2[valid],
    ))
    p3_spatial = -(p1v[:, :3] + p2v[:, :3])
    p3v = np.column_stack((p3_spatial, e3[valid]))

    return DalitzGrid(
        momenta=(p1v, p2v, p3v),
        s12=s12[valid],
        s13=s13[valid],
        s23=s23[valid],
        x_axis=s12_axis,
        y_axis=s13_axis,
        valid_flat_indices=valid_indices,
        resolution=resolution,
    )
