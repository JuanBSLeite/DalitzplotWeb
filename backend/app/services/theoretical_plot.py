from __future__ import annotations

import numpy as np

from app.physics.amplitudes import AmplitudeModel
from app.physics.dalitz_grid import build_dalitz_grid
from app.schemas import (
    ComponentNormalization,
    FitFraction,
    TheoreticalPlotRequest,
    TheoreticalPlotResponse,
)
from app.services.particles import resolve_decay


def calculate_theoretical_plot(payload: TheoreticalPlotRequest) -> TheoreticalPlotResponse:
    mother, daughters = resolve_decay(
        payload.mother.name, tuple(item.name for item in payload.daughters)
    )
    grid = build_dalitz_grid(
        mother.mass_gev,
        tuple(item.mass_gev for item in daughters),
        payload.resolution,
    )

    # Three-body phase space is uniform in ds12 ds13 up to a global constant.
    # Equal weights therefore provide a consistent component normalization on
    # this regular physical grid.
    integration_weights = np.ones_like(grid.s12, dtype=np.float64)
    evaluation = AmplitudeModel(
        payload.resonances,
        mother_mass=mother.mass_gev,
        daughter_masses=tuple(item.mass_gev for item in daughters),
        daughter_ids=tuple(item.pdgid for item in daughters),
        symmetrize=payload.symmetrize,
    ).evaluate(
        momenta=grid.momenta,
        s12=grid.s12,
        s13=grid.s13,
        s23=grid.s23,
        phase_space_weight=integration_weights,
        normalize_components=payload.normalize_components,
    )

    intensity_flat = np.full(grid.resolution * grid.resolution, np.nan)
    intensity_flat[grid.valid_flat_indices] = evaluation.amplitude_squared
    intensity = intensity_flat.reshape((grid.resolution, grid.resolution))

    # Numerical projections are integrals over the complementary invariant.
    projection_s12 = np.nansum(intensity, axis=0)
    projection_s13 = np.nansum(intensity, axis=1)
    bins = grid.x_axis
    s23_min = (daughters[1].mass_gev + daughters[2].mass_gev) ** 2
    s23_max = (mother.mass_gev - daughters[0].mass_gev) ** 2
    s23_edges = np.linspace(s23_min, s23_max, payload.resolution + 1)
    projection_s23, _ = np.histogram(
        grid.s23, bins=s23_edges, weights=evaluation.amplitude_squared
    )
    s23_centres = 0.5 * (s23_edges[:-1] + s23_edges[1:])

    total_integral = float(np.mean(evaluation.amplitude_squared))
    fit_fractions: list[FitFraction] = []
    if total_integral > 0.0:
        for key, component in evaluation.component_amplitudes.items():
            numerator = float(np.mean(np.abs(component) ** 2))
            fraction = numerator / total_integral
            fit_fractions.append(
                FitFraction(key=key, fraction=fraction, percent=100.0 * fraction)
            )
    fit_fraction_sum = float(sum(item.fraction for item in fit_fractions))

    return TheoreticalPlotResponse(
        s12_axis=grid.x_axis.tolist(),
        s13_axis=grid.y_axis.tolist(),
        intensity=[[None if not np.isfinite(value) else float(value) for value in row] for row in intensity],
        projection_s12=projection_s12.tolist(),
        projection_s13=projection_s13.tolist(),
        s23_axis=s23_centres.tolist(),
        projection_s23=projection_s23.tolist(),
        symmetrized=evaluation.symmetrized,
        symmetry_term_count=evaluation.symmetry_term_count,
        component_normalizations=[
            ComponentNormalization(
                key=key,
                integral=integral,
                amplitude_scale=1.0 / float(np.sqrt(integral)),
            )
            for key, integral in evaluation.component_normalization_integrals.items()
        ],
        fit_fractions=fit_fractions,
        fit_fraction_sum=fit_fraction_sum,
    )
