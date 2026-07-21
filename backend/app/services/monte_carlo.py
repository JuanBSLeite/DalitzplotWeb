from __future__ import annotations

import numpy as np

from app.physics.phasespace_generator import PhaseSpaceGenerator
from app.schemas import MonteCarloGenerateRequest, MonteCarloGenerateResponse


def generate_weighted_sample(
    payload: MonteCarloGenerateRequest,
) -> MonteCarloGenerateResponse:
    sample = PhaseSpaceGenerator().generate(
        mother_mass=payload.mother_mass,
        daughter_masses=payload.daughter_masses,
        n_events=payload.n_events,
        seed=payload.seed,
    )

    # The amplitude engine will replace this unity placeholder. Keeping the
    # columns separate already fixes the public contract for later models.
    amplitude_squared = np.ones(sample.n_events, dtype=np.float64)
    total_weight = sample.phase_space_weight * amplitude_squared

    p1, p2, p3 = sample.momenta
    events = []
    for index in range(sample.n_events):
        events.append(
            {
                "p1": p1[index].tolist(),
                "p2": p2[index].tolist(),
                "p3": p3[index].tolist(),
                "s12": float(sample.s12[index]),
                "s13": float(sample.s13[index]),
                "s23": float(sample.s23[index]),
                "phase_space_weight": float(sample.phase_space_weight[index]),
                "amplitude_squared": float(amplitude_squared[index]),
                "total_weight": float(total_weight[index]),
            }
        )

    return MonteCarloGenerateResponse(events=events)
