from __future__ import annotations

from functools import lru_cache

import qrules

from app.schemas import DecayRequest, DecayValidation, SuggestedResonance

PAIR_KEYS = {(0, 1): "12", (0, 2): "13", (1, 2): "23"}


class QRulesValidationError(RuntimeError):
    """Raised when qrules cannot construct or inspect the requested reaction."""


def _channel(req: DecayRequest) -> str:
    daughters = " ".join(item.name for item in req.daughters)
    return f"{req.mother.name} -> {daughters}"


def _fraction_to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_suggestions(reaction: object) -> dict[str, list[SuggestedResonance]]:
    grouped: dict[str, dict[str, SuggestedResonance]] = {
        "12": {},
        "13": {},
        "23": {},
    }

    for transition in reaction.transitions:
        final_edge_to_index = {
            edge_id: index for index, edge_id in enumerate(sorted(transition.final_states))
        }
        for edge_id, state in transition.intermediate_states.items():
            edge = transition.topology.edges[edge_id]
            decay_node = edge.ending_node_id
            if decay_node is None:
                continue
            final_edges = transition.topology.get_originating_final_state_edge_ids(
                decay_node
            )
            try:
                pair_indices = tuple(
                    sorted(final_edge_to_index[final_edge] for final_edge in final_edges)
                )
            except KeyError:
                continue
            pair_key = PAIR_KEYS.get(pair_indices)
            if pair_key is None:
                continue

            particle = state.particle
            item = SuggestedResonance(
                name=particle.name,
                pdgid=int(particle.pid),
                pair=pair_key,
                mass_gev=_fraction_to_float(particle.mass),
                width_gev=_fraction_to_float(particle.width),
                spin=_fraction_to_float(particle.spin),
            )
            grouped[pair_key][item.name] = item

    return {
        key: sorted(values.values(), key=lambda item: (item.mass_gev or 0.0, item.name))
        for key, values in grouped.items()
    }


@lru_cache(maxsize=128)
def _validate_cached(mother: str, daughters: tuple[str, str, str]) -> DecayValidation:
    channel = f"{mother} -> {' '.join(daughters)}"
    try:
        reaction = qrules.generate_transitions(
            initial_state=mother,
            final_state=list(daughters),
            allowed_interaction_types=["strong", "em", "weak"],
            formalism="canonical-helicity",
            topology_building="isobar",
            max_angular_momentum=2,
            number_of_threads=1,
        )
    except (LookupError, ValueError, KeyError) as exc:
        return DecayValidation(
            allowed=False,
            channel=channel,
            message=f"QRules could not build this reaction: {exc}",
        )
    except Exception as exc:  # qrules currently exposes several solver exceptions
        raise QRulesValidationError(str(exc)) from exc

    transition_count = len(reaction.transitions)
    if transition_count == 0:
        return DecayValidation(
            allowed=False,
            channel=channel,
            message="No transition satisfying the selected conservation rules was found.",
        )

    suggestions = _extract_suggestions(reaction)
    return DecayValidation(
        allowed=True,
        channel=channel,
        message="Decay allowed by qrules.",
        transition_count=transition_count,
        suggested_resonances=suggestions,
    )


def validate_decay_with_qrules(req: DecayRequest) -> DecayValidation:
    daughters = tuple(item.name.strip() for item in req.daughters)
    if len(daughters) != 3:
        raise ValueError("Exactly three daughter particles are required.")
    return _validate_cached(req.mother.name.strip(), daughters)
