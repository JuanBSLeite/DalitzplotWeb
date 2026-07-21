from __future__ import annotations

from dataclasses import dataclass

from particle import Particle

MEV_TO_GEV = 1.0e-3


class ParticleLookupError(ValueError):
    """Raised when a particle cannot be resolved or has no usable mass."""


@dataclass(frozen=True, slots=True)
class ResolvedParticle:
    name: str
    pdgid: int
    mass_gev: float
    charge: float | None
    spin: float | None
    width_gev: float | None


def resolve_particle(name: str) -> ResolvedParticle:
    """Resolve a particle name using the PDG table exposed by ``particle``.

    The public physics layer uses GeV. Values returned by ``particle`` are in
    MeV and are converted here, at the boundary of the application.
    """

    clean_name = name.strip()
    if not clean_name:
        raise ParticleLookupError("Particle name cannot be empty")

    try:
        particle = Particle.from_name(clean_name)
    except Exception as exc:  # particle raises different lookup exceptions
        raise ParticleLookupError(f"Unknown particle {clean_name!r}") from exc

    if particle.mass is None:
        raise ParticleLookupError(f"Particle {particle.name!r} has no tabulated mass")

    width_gev = None if particle.width is None else float(particle.width) * MEV_TO_GEV
    spin = None if particle.J is None else float(particle.J)
    charge = None if particle.charge is None else float(particle.charge)

    return ResolvedParticle(
        name=particle.name,
        pdgid=int(particle.pdgid),
        mass_gev=float(particle.mass) * MEV_TO_GEV,
        charge=charge,
        spin=spin,
        width_gev=width_gev,
    )


def resolve_decay(
    mother_name: str,
    daughter_names: tuple[str, str, str],
) -> tuple[ResolvedParticle, tuple[ResolvedParticle, ResolvedParticle, ResolvedParticle]]:
    mother = resolve_particle(mother_name)
    daughters = tuple(resolve_particle(name) for name in daughter_names)

    daughter_mass_sum = sum(particle.mass_gev for particle in daughters)
    if mother.mass_gev <= daughter_mass_sum:
        raise ParticleLookupError(
            "Decay is kinematically forbidden: mother mass must exceed the "
            "sum of daughter masses"
        )

    return mother, daughters  # type: ignore[return-value]
