from __future__ import annotations

import numpy as np

from app.physics.amplitudes import AmplitudeModel
from app.physics.dalitz_grid import build_dalitz_grid
from app.physics.normalization import component_normalizations, integration_evaluation
from app.schemas import (
    ComponentNormalization,
    FitFraction,
    TheoreticalPlotRequest,
    TheoreticalPlotResponse,
)
from app.services.particles import resolve_decay, validate_spinless_dalitz_scope


def calculate_theoretical_plot(payload: TheoreticalPlotRequest) -> TheoreticalPlotResponse:
    mother, daughters = resolve_decay(
        payload.mother.name, tuple(item.name for item in payload.daughters)
    )
    validate_spinless_dalitz_scope(mother, daughters)

    daughter_masses = tuple(item.mass_gev for item in daughters)
    daughter_ids = tuple(item.pdgid for item in daughters)
    normalizations = component_normalizations(
        payload.resonances,
        mother_mass=mother.mass_gev,
        daughter_masses=daughter_masses,
        daughter_ids=daughter_ids,
        symmetrize=payload.symmetrize,
    ) if payload.normalize_components else None

    # Display grid: changing its resolution must not change the amplitude basis.
    grid = build_dalitz_grid(
        mother.mass_gev,
        daughter_masses,
        payload.resolution,
    )
    evaluation = AmplitudeModel(
        payload.resonances,
        mother_mass=mother.mass_gev,
        daughter_masses=daughter_masses,
        daughter_ids=daughter_ids,
        symmetrize=payload.symmetrize,
    ).evaluate(
        momenta=grid.momenta,
        s12=grid.s12,
        s13=grid.s13,
        s23=grid.s23,
        normalize_components=payload.normalize_components,
        normalization_integrals=normalizations,
    )

    intensity_flat = np.full(grid.resolution * grid.resolution, np.nan)
    intensity_flat[grid.valid_flat_indices] = evaluation.amplitude_squared
    intensity = intensity_flat.reshape((grid.resolution, grid.resolution))

    # dPhi_3 is uniform in ds12 ds13 up to a channel-wide constant. Numerical
    # projections therefore integrate |A|^2 over the complementary invariant.
    ds12 = float(grid.x_axis[1] - grid.x_axis[0])
    ds13 = float(grid.y_axis[1] - grid.y_axis[0])
    projection_s12 = np.nansum(intensity, axis=0) * ds13
    projection_s13 = np.nansum(intensity, axis=1) * ds12

    s23_min = (daughters[1].mass_gev + daughters[2].mass_gev) ** 2
    s23_max = (mother.mass_gev - daughters[0].mass_gev) ** 2
    s23_edges = np.linspace(s23_min, s23_max, payload.resolution + 1)
    projection_s23, _ = np.histogram(
        grid.s23,
        bins=s23_edges,
        weights=evaluation.amplitude_squared * ds12 * ds13,
    )
    s23_centres = 0.5 * (s23_edges[:-1] + s23_edges[1:])

    # Fit fractions are evaluated on the fixed deterministic integration grid,
    # not on the display grid. They therefore do not depend on plot resolution.
    fit_fractions: list[FitFraction] = []
    if payload.resonances:
        int_grid, int_eval = integration_evaluation(
            payload.resonances,
            mother_mass=mother.mass_gev,
            daughter_masses=daughter_masses,
            daughter_ids=daughter_ids,
            symmetrize=payload.symmetrize,
        ) if payload.normalize_components else (
            None,
            None,
        )

        if int_grid is not None and int_eval is not None:
            int_ds12 = float(int_grid.x_axis[1] - int_grid.x_axis[0])
            int_ds13 = float(int_grid.y_axis[1] - int_grid.y_axis[0])
            cell_area = int_ds12 * int_ds13
            total_integral = float(np.sum(int_eval.amplitude_squared) * cell_area)
            if total_integral > 0.0:
                for key, component in int_eval.component_amplitudes.items():
                    numerator = float(np.sum(np.abs(component) ** 2) * cell_area)
                    fraction = numerator / total_integral
                    fit_fractions.append(
                        FitFraction(key=key, fraction=fraction, percent=100.0 * fraction)
                    )
        else:
            # Unnormalized mode is primarily diagnostic. Use the display grid
            # consistently when explicit basis normalization was disabled.
            total_integral = float(np.sum(evaluation.amplitude_squared) * ds12 * ds13)
            if total_integral > 0.0:
                for key, component in evaluation.component_amplitudes.items():
                    numerator = float(np.sum(np.abs(component) ** 2) * ds12 * ds13)
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
