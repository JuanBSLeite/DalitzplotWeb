from __future__ import annotations

from functools import lru_cache

import numpy as np

from app.physics.amplitudes import AmplitudeModel
from app.physics.dalitz_grid import DalitzGrid, build_dalitz_grid
from app.schemas import ResonanceConfig

# Fixed deterministic grid used only for physics integrals.  It is deliberately
# independent of the display resolution and of any toy-MC sample.
INTEGRATION_RESOLUTION = 260


def _resonance_descriptor(config: ResonanceConfig) -> tuple[object, ...]:
    """Return the dynamics-only cache key for one amplitude component.

    Magnitude and phase are intentionally excluded because they do not affect
    the normalization of the basis function.
    """

    return (
        config.component_type,
        config.name,
        tuple(config.pair),
        int(config.spin),
        float(config.mass),
        float(config.width),
        float(config.resonance_radius),
        float(config.mother_radius),
        config.source,
    )


def _config_from_descriptor(item: tuple[object, ...]) -> ResonanceConfig:
    component_type, name, pair, spin, mass, width, resonance_radius, mother_radius, source = item
    return ResonanceConfig(
        component_type=str(component_type),
        name=str(name),
        pair=tuple(pair),  # type: ignore[arg-type]
        spin=int(spin),
        mass=float(mass),
        width=float(width),
        magnitude=1.0,
        phase_deg=0.0,
        resonance_radius=float(resonance_radius),
        mother_radius=float(mother_radius),
        source=str(source),
    )


@lru_cache(maxsize=32)
def _integration_grid_cached(
    mother_mass: float,
    daughter_masses: tuple[float, float, float],
) -> DalitzGrid:
    return build_dalitz_grid(
        mother_mass,
        daughter_masses,
        resolution=INTEGRATION_RESOLUTION,
    )


@lru_cache(maxsize=256)
def _component_normalizations_cached(
    mother_mass: float,
    daughter_masses: tuple[float, float, float],
    daughter_ids: tuple[int, int, int],
    symmetrize: bool,
    descriptors: tuple[tuple[object, ...], ...],
) -> tuple[tuple[str, float], ...]:
    grid = _integration_grid_cached(mother_mass, daughter_masses)
    resonances = [_config_from_descriptor(item) for item in descriptors]
    evaluation = AmplitudeModel(
        resonances,
        mother_mass=mother_mass,
        daughter_masses=daughter_masses,
        daughter_ids=daughter_ids,
        symmetrize=symmetrize,
    ).evaluate(
        momenta=grid.momenta,
        s12=grid.s12,
        s13=grid.s13,
        s23=grid.s23,
        normalize_components=False,
    )

    ds12 = float(grid.x_axis[1] - grid.x_axis[0])
    ds13 = float(grid.y_axis[1] - grid.y_axis[0])
    cell_area = ds12 * ds13

    integrals: list[tuple[str, float]] = []
    for key, component in evaluation.component_amplitudes.items():
        integral = float(np.sum(np.abs(component) ** 2) * cell_area)
        if not np.isfinite(integral) or integral <= 0.0:
            raise ValueError(f"Invalid normalization integral for {key}: {integral}")
        integrals.append((key, integral))
    return tuple(integrals)


def component_normalizations(
    resonances: list[ResonanceConfig],
    *,
    mother_mass: float,
    daughter_masses: tuple[float, float, float],
    daughter_ids: tuple[int, int, int],
    symmetrize: bool,
) -> dict[str, float]:
    """Return deterministic, cached component integrals over the Dalitz plot."""

    if not resonances:
        return {}
    descriptors = tuple(_resonance_descriptor(config) for config in resonances)
    return dict(
        _component_normalizations_cached(
            float(mother_mass),
            tuple(float(value) for value in daughter_masses),
            tuple(int(value) for value in daughter_ids),
            bool(symmetrize),
            descriptors,
        )
    )


def integration_evaluation(
    resonances: list[ResonanceConfig],
    *,
    mother_mass: float,
    daughter_masses: tuple[float, float, float],
    daughter_ids: tuple[int, int, int],
    symmetrize: bool,
):
    """Evaluate the normalized model on the fixed deterministic integration grid.

    This is used for fit fractions and other integrated quantities so they do
    not depend on the user's display resolution or toy-MC seed/sample size.
    """

    grid = _integration_grid_cached(
        float(mother_mass),
        tuple(float(value) for value in daughter_masses),
    )
    normalizations = component_normalizations(
        resonances,
        mother_mass=mother_mass,
        daughter_masses=daughter_masses,
        daughter_ids=daughter_ids,
        symmetrize=symmetrize,
    )
    evaluation = AmplitudeModel(
        resonances,
        mother_mass=mother_mass,
        daughter_masses=daughter_masses,
        daughter_ids=daughter_ids,
        symmetrize=symmetrize,
    ).evaluate(
        momenta=grid.momenta,
        s12=grid.s12,
        s13=grid.s13,
        s23=grid.s23,
        normalize_components=True,
        normalization_integrals=normalizations,
    )
    return grid, evaluation
