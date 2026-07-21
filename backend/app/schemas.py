from typing import Literal

from pydantic import BaseModel, Field


class ParticleRef(BaseModel):
    name: str = Field(min_length=1)


class ParticleInfo(BaseModel):
    name: str
    pdgid: int
    mass_gev: float
    charge: float | None = None
    spin: float | None = None
    width_gev: float | None = None


class DecayRequest(BaseModel):
    mother: ParticleRef
    daughters: list[ParticleRef] = Field(min_length=3, max_length=3)


class SuggestedResonance(BaseModel):
    name: str
    pdgid: int
    pair: Literal["12", "13", "23"]
    mass_gev: float | None = None
    width_gev: float | None = None
    spin: float | None = None


class DecayValidation(BaseModel):
    allowed: bool
    channel: str
    message: str
    warnings: list[str] = Field(default_factory=list)
    transition_count: int = 0
    suggested_resonances: dict[str, list[SuggestedResonance]] = Field(
        default_factory=lambda: {"12": [], "13": [], "23": []}
    )


class ResonanceConfig(BaseModel):
    name: str
    pair: tuple[int, int]
    spin: int = 0
    mass: float
    width: float
    lineshape: Literal["RBW", "GS", "FLATTE"] = "RBW"
    magnitude: float = 1.0
    phase_deg: float = 0.0
    resonance_radius: float = Field(default=1.5, gt=0.0)
    mother_radius: float = Field(default=5.0, gt=0.0)
    source: Literal["suggested", "database", "custom"] = "custom"


class PhaseSpaceGenerateRequest(BaseModel):
    mother: ParticleRef
    daughters: tuple[ParticleRef, ParticleRef, ParticleRef]
    n_events: int = Field(default=10_000, ge=1, le=1_000_000)
    seed: int | None = None
    resonances: list[ResonanceConfig] = Field(default_factory=list)
    symmetrize: bool = True
    normalize_components: bool = True


class MonteCarloEvent(BaseModel):
    p1: tuple[float, float, float, float]
    p2: tuple[float, float, float, float]
    p3: tuple[float, float, float, float]
    s12: float
    s13: float
    s23: float
    phase_space_weight: float
    amplitude_squared: float
    total_weight: float


class ComponentNormalization(BaseModel):
    key: str
    integral: float
    amplitude_scale: float


class PhaseSpaceGenerateResponse(BaseModel):
    mother: ParticleInfo
    daughters: tuple[ParticleInfo, ParticleInfo, ParticleInfo]
    unit: Literal["GeV"] = "GeV"
    symmetrized: bool = False
    symmetry_term_count: int = 1
    components_normalized: bool = True
    component_normalizations: list[ComponentNormalization] = Field(default_factory=list)
    events: list[MonteCarloEvent]
