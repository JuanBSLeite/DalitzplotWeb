from __future__ import annotations

import numpy as np

from app.physics.phasespace_generator import PhaseSpaceGenerator
from app.schemas import (
    MonteCarloEvent,
    ParticleInfo,
    PhaseSpaceGenerateRequest,
    PhaseSpaceGenerateResponse,
)
from app.services.particles import ResolvedParticle, resolve_decay


def _to_particle_info(particle: ResolvedParticle) -> ParticleInfo:
    return ParticleInfo(
        name=particle.name,
        pdgid=particle.pdgid,
        mass_gev=particle.mass_gev,
        charge=particle.charge,
        spin=particle.spin,
        width_gev=particle.width_gev,
    )


def generate_weighted_sample(
    payload: PhaseSpaceGenerateRequest,
) -> PhaseSpaceGenerateResponse:
    daughter_names = tuple(item.name for item in payload.daughters)
    mother, daughters = resolve_decay(payload.mother.name, daughter_names)

    sample = PhaseSpaceGenerator().generate(
        mother_mass=mother.mass_gev,
        daughter_masses=tuple(particle.mass_gev for particle in daughters),
        daughter_names=("p1", "p2", "p3"),
        n_events=payload.n_events,
        seed=payload.seed,
    )

    # Placeholder until the amplitude engine is connected. Keeping this
    # separate from the phase-space weight fixes the correct data contract.
    amplitude_squared = np.ones(sample.n_events, dtype=np.float64)
    total_weight = sample.phase_space_weight * amplitude_squared

    p1, p2, p3 = sample.momenta
    events = [
        MonteCarloEvent(
            p1=tuple(float(value) for value in p1[index]),
            p2=tuple(float(value) for value in p2[index]),
            p3=tuple(float(value) for value in p3[index]),
            s12=float(sample.s12[index]),
            s13=float(sample.s13[index]),
            s23=float(sample.s23[index]),
            phase_space_weight=float(sample.phase_space_weight[index]),
            amplitude_squared=float(amplitude_squared[index]),
            total_weight=float(total_weight[index]),
        )
        for index in range(sample.n_events)
    ]

    return PhaseSpaceGenerateResponse(
        mother=_to_particle_info(mother),
        daughters=tuple(_to_particle_info(particle) for particle in daughters),
        events=events,
    )
