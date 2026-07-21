from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import phasespace


@dataclass(slots=True)
class PhaseSpaceSample:
    """Three-body phase-space sample in the parent rest frame.

    Four-vectors use the ``(px, py, pz, E)`` convention after conversion from
    the TensorFlow PhaseSpace output.
    """

    momenta: tuple[np.ndarray, np.ndarray, np.ndarray]
    phase_space_weight: np.ndarray
    s12: np.ndarray
    s13: np.ndarray
    s23: np.ndarray

    @property
    def n_events(self) -> int:
        return int(self.phase_space_weight.shape[0])


def invariant_mass_squared(four_vector: np.ndarray) -> np.ndarray:
    """Return p² = E² - |p⃗|² for vectors stored as (px, py, pz, E)."""

    vector = np.asarray(four_vector, dtype=np.float64)
    if vector.ndim != 2 or vector.shape[1] != 4:
        raise ValueError("four_vector must have shape (n_events, 4)")
    spatial_squared = np.sum(vector[:, :3] ** 2, axis=1)
    return vector[:, 3] ** 2 - spatial_squared


def _as_numpy(value: object) -> np.ndarray:
    """Convert a TensorFlow tensor or array-like value to NumPy."""

    numpy_method = getattr(value, "numpy", None)
    array = numpy_method() if callable(numpy_method) else value
    return np.asarray(array, dtype=np.float64)


def _ordered_momenta(
    particles: Mapping[str, object], daughter_names: Sequence[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    try:
        vectors = tuple(_as_numpy(particles[name]) for name in daughter_names)
    except KeyError as exc:
        available = ", ".join(sorted(particles))
        raise RuntimeError(
            f"PhaseSpace did not return daughter {exc.args[0]!r}; available: {available}"
        ) from exc

    if len(vectors) != 3:
        raise ValueError("Exactly three daughter momenta are required")
    if any(vector.ndim != 2 or vector.shape[1] != 4 for vector in vectors):
        raise RuntimeError("PhaseSpace returned an unexpected four-vector shape")
    return vectors  # type: ignore[return-value]


class PhaseSpaceGenerator:
    """Adapter around ``phasespace.nbody_decay`` for three-body decays."""

    def generate(
        self,
        mother_mass: float,
        daughter_masses: Sequence[float],
        n_events: int,
        *,
        daughter_names: Sequence[str] = ("p1", "p2", "p3"),
        seed: int | None = None,
    ) -> PhaseSpaceSample:
        if len(daughter_masses) != 3:
            raise ValueError("Exactly three daughter masses are required")
        if len(daughter_names) != 3 or len(set(daughter_names)) != 3:
            raise ValueError("Exactly three unique daughter names are required")
        if not 1 <= n_events <= 1_000_000:
            raise ValueError("n_events must be between 1 and 1,000,000")
        if mother_mass <= sum(daughter_masses):
            raise ValueError("Mother mass must exceed the daughter-mass sum")

        if seed is not None:
            # PhaseSpace uses TensorFlow's RNG. Import locally to keep the
            # adapter's public surface independent from TensorFlow.
            import tensorflow as tf

            tf.random.set_seed(seed)

        decay = phasespace.nbody_decay(
            mother_mass,
            list(daughter_masses),
            names=list(daughter_names),
        )
        weights, particles = decay.generate(n_events=n_events)

        p1, p2, p3 = _ordered_momenta(particles, daughter_names)
        phase_space_weight = _as_numpy(weights).reshape(-1)

        return PhaseSpaceSample(
            momenta=(p1, p2, p3),
            phase_space_weight=phase_space_weight,
            s12=invariant_mass_squared(p1 + p2),
            s13=invariant_mass_squared(p1 + p3),
            s23=invariant_mass_squared(p2 + p3),
        )
