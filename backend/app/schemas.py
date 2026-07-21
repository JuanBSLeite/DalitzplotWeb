from typing import Literal

from pydantic import BaseModel, Field


class ParticleRef(BaseModel):
    name: str


class DecayRequest(BaseModel):
    mother: ParticleRef
    daughters: list[ParticleRef] = Field(min_length=3, max_length=3)


class DecayValidation(BaseModel):
    valid: bool
    message: str
    warnings: list[str] = []


class ResonanceConfig(BaseModel):
    name: str
    pair: tuple[int, int]
    spin: int = 0
    mass: float
    width: float
    lineshape: Literal["RBW", "GS", "FLATTE"] = "RBW"
    magnitude: float = 1.0
    phase_deg: float = 0.0
    source: Literal["suggested", "database", "custom"] = "custom"


class MonteCarloGenerateRequest(BaseModel):
    mother_mass: float = Field(gt=0)
    daughter_masses: tuple[float, float, float]
    n_events: int = Field(default=10_000, ge=1, le=1_000_000)
    seed: int | None = None


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


class MonteCarloGenerateResponse(BaseModel):
    events: list[MonteCarloEvent]
