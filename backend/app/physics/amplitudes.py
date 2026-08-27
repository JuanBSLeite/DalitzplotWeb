from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product

import numpy as np

from app.physics.lineshapes import DynamicRelativisticBreitWigner
from app.schemas import ResonanceConfig


@dataclass(slots=True)
class AmplitudeEvaluation:
    amplitude: np.ndarray
    amplitude_squared: np.ndarray
    component_amplitudes: dict[str, np.ndarray]
    component_normalization_integrals: dict[str, float]
    symmetrized: bool
    symmetry_term_count: int


def _lorentz_boost_to_rest(vectors: np.ndarray, frame: np.ndarray) -> np.ndarray:
    """Boost four-vectors into the rest frame of ``frame``.

    Input and output convention is ``(px, py, pz, E)``.
    """

    beta = frame[:, :3] / frame[:, 3, None]
    beta2 = np.sum(beta * beta, axis=1)
    gamma = 1.0 / np.sqrt(np.clip(1.0 - beta2, 1e-15, None))
    dot = np.sum(beta * vectors[:, :3], axis=1)

    factor = np.zeros_like(dot)
    moving = beta2 > 1e-15
    factor[moving] = ((gamma[moving] - 1.0) * dot[moving] / beta2[moving]) - (
        gamma[moving] * vectors[moving, 3]
    )

    spatial = vectors[:, :3] + factor[:, None] * beta
    energy = gamma * (vectors[:, 3] - dot)
    return np.column_stack((spatial, energy))


def _zemach_angular_term(
    spin: int,
    daughter: np.ndarray,
    bachelor: np.ndarray,
    resonance: np.ndarray,
) -> np.ndarray:
    """Return Zemach angular factors for spin 0, 1, or 2.

    The implementation is valid for a spin-0 parent and spin-0 final-state
    particles. Both vectors are evaluated in the resonance rest frame:

        Z_0 = 1
        Z_1 = -2 p.q
        Z_2 = (4/3) [3 (p.q)^2 - |p|^2 |q|^2]
    """

    if spin not in (0, 1, 2):
        raise ValueError("Zemach angular terms are currently implemented for spin 0, 1, and 2")
    if spin == 0:
        return np.ones(daughter.shape[0], dtype=np.float64)

    q_vec = _lorentz_boost_to_rest(daughter, resonance)[:, :3]
    p_vec = _lorentz_boost_to_rest(bachelor, resonance)[:, :3]
    dot = np.sum(p_vec * q_vec, axis=1)

    if spin == 1:
        return -2.0 * dot

    p2 = np.sum(p_vec * p_vec, axis=1)
    q2 = np.sum(q_vec * q_vec, axis=1)
    return (4.0 / 3.0) * (3.0 * dot * dot - p2 * q2)


def _identical_particle_permutations(
    particle_ids: tuple[int, int, int],
) -> tuple[tuple[int, int, int], ...]:
    """Return permutations that exchange only physically identical daughters."""

    groups: list[tuple[int, ...]] = []
    seen: set[int] = set()
    for particle_id in particle_ids:
        if particle_id in seen:
            continue
        group = tuple(i for i, value in enumerate(particle_ids) if value == particle_id)
        groups.append(group)
        seen.add(particle_id)

    group_permutations = [tuple(permutations(group)) for group in groups]
    result: set[tuple[int, int, int]] = set()
    for choices in product(*group_permutations):
        mapping = list(range(3))
        for source_group, target_group in zip(groups, choices, strict=True):
            for source, target in zip(source_group, target_group, strict=True):
                mapping[source] = target
        result.add(tuple(mapping))
    return tuple(sorted(result))


def _mapped_decay_chains(
    ordered_pair: tuple[int, int],
    particle_ids: tuple[int, int, int],
) -> tuple[tuple[int, int, int], ...]:
    """Map one isobar chain over all distinct identical-particle assignments."""

    i0, j0 = ordered_pair[0] - 1, ordered_pair[1] - 1
    if i0 == j0 or i0 not in range(3) or j0 not in range(3):
        raise ValueError(f"Unsupported daughter pair {ordered_pair}")
    bachelor0 = next(index for index in range(3) if index not in (i0, j0))

    chains: dict[tuple[tuple[int, int], int], tuple[int, int, int]] = {}
    for permutation in _identical_particle_permutations(particle_ids):
        i, j, bachelor = permutation[i0], permutation[j0], permutation[bachelor0]
        topology_key = (tuple(sorted((i, j))), bachelor)
        chains.setdefault(topology_key, (i, j, bachelor))
    return tuple(chains.values())


class AmplitudeModel:
    """Coherent spin-0 -> spin-0 spin-0 spin-0 isobar model."""

    def __init__(
        self,
        resonances: list[ResonanceConfig],
        *,
        mother_mass: float,
        daughter_masses: tuple[float, float, float],
        daughter_ids: tuple[int, int, int],
        symmetrize: bool = True,
    ):
        self.resonances = resonances
        self.mother_mass = mother_mass
        self.daughter_masses = daughter_masses
        self.daughter_ids = daughter_ids
        self.symmetrize = symmetrize

    @staticmethod
    def _coefficient(magnitude: float, phase_deg: float) -> complex:
        return magnitude * np.exp(1j * np.deg2rad(phase_deg))

    @staticmethod
    def _invariant_for_pair(
        pair: tuple[int, int],
        s12: np.ndarray,
        s13: np.ndarray,
        s23: np.ndarray,
    ) -> np.ndarray:
        key = tuple(sorted(pair))
        invariants = {(0, 1): s12, (0, 2): s13, (1, 2): s23}
        return invariants[key]

    @staticmethod
    def _component_key(index: int, config: ResonanceConfig) -> str:
        if config.component_type == "nonresonant":
            return f"{index}:{config.name}:NR"
        return f"{index}:{config.name}:{config.pair[0]}{config.pair[1]}"

    def _validate_resonance_symmetry(self, config: ResonanceConfig, chain: tuple[int, int, int]) -> None:
        """Enforce Bose symmetry for an identical spin-0 pair."""

        i, j, _ = chain
        if self.daughter_ids[i] == self.daughter_ids[j] and config.spin % 2 != 0:
            raise ValueError(
                f"Odd orbital angular momentum L={config.spin} is forbidden for the "
                "identical spin-0 resonance daughters in component "
                f"{config.name!r}."
            )

    def _evaluate_chain(
        self,
        config: ResonanceConfig,
        chain: tuple[int, int, int],
        *,
        momenta: tuple[np.ndarray, np.ndarray, np.ndarray],
        s12: np.ndarray,
        s13: np.ndarray,
        s23: np.ndarray,
    ) -> np.ndarray:
        self._validate_resonance_symmetry(config, chain)
        i, j, bachelor_index = chain
        daughter_i = momenta[i]
        bachelor = momenta[bachelor_index]
        resonance_four_vector = momenta[i] + momenta[j]
        invariant = self._invariant_for_pair((i, j), s12, s13, s23)

        lineshape = DynamicRelativisticBreitWigner(
            pole_mass=config.mass,
            pole_width=config.width,
            orbital_l=config.spin,
            mother_mass=self.mother_mass,
            daughter_masses=(self.daughter_masses[i], self.daughter_masses[j]),
            bachelor_mass=self.daughter_masses[bachelor_index],
            resonance_radius=config.resonance_radius,
            mother_radius=config.mother_radius,
        )
        angular = _zemach_angular_term(
            config.spin,
            daughter_i,
            bachelor,
            resonance_four_vector,
        )
        return lineshape.evaluate(invariant) * angular

    def evaluate(
        self,
        *,
        momenta: tuple[np.ndarray, np.ndarray, np.ndarray],
        s12: np.ndarray,
        s13: np.ndarray,
        s23: np.ndarray,
        phase_space_weight: np.ndarray | None = None,
        normalize_components: bool = True,
        normalization_integrals: dict[str, float] | None = None,
    ) -> AmplitudeEvaluation:
        """Evaluate the coherent model.

        ``normalization_integrals`` can be supplied from a fixed integration
        sample. When present, those deterministic values are used instead of
        estimating component normalizations from the points being evaluated.
        """

        total = np.zeros_like(s12, dtype=np.complex128)
        components: dict[str, np.ndarray] = {}
        used_normalizations: dict[str, float] = {}
        max_chain_count = 1

        if phase_space_weight is not None and phase_space_weight.shape != s12.shape:
            raise ValueError("phase_space_weight must have the same shape as the invariants")

        for index, config in enumerate(self.resonances):
            if config.component_type == "nonresonant":
                symmetrized_component = np.ones_like(s12, dtype=np.complex128)
                chains = ((0, 1, 2),)
            else:
                if config.mass <= 0 or config.width <= 0:
                    raise ValueError("Resonance mass and width must be positive")
                if config.spin not in (0, 1, 2):
                    raise ValueError("RBW/Zemach model currently supports L=0, 1, and 2 only")

                if self.symmetrize:
                    chains = _mapped_decay_chains(config.pair, self.daughter_ids)
                else:
                    i, j = config.pair[0] - 1, config.pair[1] - 1
                    bachelor = next(k for k in range(3) if k not in (i, j))
                    chains = ((i, j, bachelor),)

                max_chain_count = max(max_chain_count, len(chains))
                symmetrized_component = np.zeros_like(s12, dtype=np.complex128)
                for chain in chains:
                    symmetrized_component += self._evaluate_chain(
                        config,
                        chain,
                        momenta=momenta,
                        s12=s12,
                        s13=s13,
                        s23=s23,
                    )

            key = self._component_key(index, config)
            if normalize_components:
                if normalization_integrals is not None:
                    if key not in normalization_integrals:
                        raise ValueError(f"Missing cached normalization for component {key}")
                    norm_integral = float(normalization_integrals[key])
                else:
                    if phase_space_weight is None:
                        raise ValueError(
                            "phase_space_weight is required when component normalization "
                            "is estimated from the evaluation points"
                        )
                    norm_integral = float(
                        np.mean(phase_space_weight * np.abs(symmetrized_component) ** 2)
                    )

                if not np.isfinite(norm_integral) or norm_integral <= 0.0:
                    raise ValueError(
                        f"Could not normalize amplitude component {config.name}: "
                        f"integral={norm_integral}"
                    )
                basis_component = symmetrized_component / np.sqrt(norm_integral)
            else:
                norm_integral = 1.0
                basis_component = symmetrized_component

            used_normalizations[key] = norm_integral
            component = self._coefficient(config.magnitude, config.phase_deg) * basis_component
            components[key] = component
            total += component

        if not self.resonances:
            total = np.ones_like(s12, dtype=np.complex128)

        identical_present = len(set(self.daughter_ids)) < 3
        return AmplitudeEvaluation(
            amplitude=total,
            amplitude_squared=np.abs(total) ** 2,
            component_amplitudes=components,
            component_normalization_integrals=used_normalizations,
            symmetrized=self.symmetrize and identical_present,
            symmetry_term_count=max_chain_count if identical_present else 1,
        )
