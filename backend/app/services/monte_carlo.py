from __future__ import annotations

import numpy as np

from app.physics.amplitudes import AmplitudeModel
from app.physics.phasespace_generator import PhaseSpaceGenerator
from app.schemas import (
    ComponentNormalization,
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
    *,
    include_complex_amplitude: bool = True,
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

    evaluation = AmplitudeModel(
        payload.resonances,
        mother_mass=mother.mass_gev,
        daughter_masses=tuple(particle.mass_gev for particle in daughters),
        daughter_ids=tuple(particle.pdgid for particle in daughters),
        symmetrize=payload.symmetrize,
    ).evaluate(
        momenta=sample.momenta,
        s12=sample.s12,
        s13=sample.s13,
        s23=sample.s23,
        phase_space_weight=sample.phase_space_weight,
        normalize_components=payload.normalize_components,
    )
    amplitude_squared = evaluation.amplitude_squared.astype(np.float64)
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
            amplitude_real=float(evaluation.amplitude[index].real) if include_complex_amplitude else 0.0,
            amplitude_imag=float(evaluation.amplitude[index].imag) if include_complex_amplitude else 0.0,
            amplitude_squared=float(amplitude_squared[index]),
            total_weight=float(total_weight[index]),
        )
        for index in range(sample.n_events)
    ]

    return PhaseSpaceGenerateResponse(
        mother=_to_particle_info(mother),
        daughters=tuple(_to_particle_info(particle) for particle in daughters),
        symmetrized=evaluation.symmetrized,
        symmetry_term_count=evaluation.symmetry_term_count,
        components_normalized=payload.normalize_components,
        component_normalizations=[
            ComponentNormalization(
                key=key,
                integral=integral,
                amplitude_scale=1.0 / float(np.sqrt(integral)),
            )
            for key, integral in evaluation.component_normalization_integrals.items()
        ],
        events=events,
    )
