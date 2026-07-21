from __future__ import annotations

import csv
import io
import numpy as np
from app.schemas import PhaseSpaceGenerateRequest
from app.services.monte_carlo import generate_weighted_sample


# Export only the quantities requested for each generated event:
# daughter four-momenta, pairwise invariant masses, and the dynamic weight |A|^2.
COLUMNS = [
    "p1_px", "p1_py", "p1_pz", "p1_E",
    "p2_px", "p2_py", "p2_pz", "p2_E",
    "p3_px", "p3_py", "p3_pz", "p3_E",
    "s12", "s13", "s23",
    "dynamic_weight",
]


def _arrays(payload: PhaseSpaceGenerateRequest) -> dict[str, np.ndarray]:
    result = generate_weighted_sample(payload, include_complex_amplitude=False)
    events = result.events
    arrays: dict[str, np.ndarray] = {}

    for particle_index in range(1, 4):
        vectors = np.asarray(
            [getattr(event, f"p{particle_index}") for event in events],
            dtype=np.float64,
        )
        for component_index, label in enumerate(("px", "py", "pz", "E")):
            arrays[f"p{particle_index}_{label}"] = vectors[:, component_index]

    for name in ("s12", "s13", "s23"):
        arrays[name] = np.asarray(
            [getattr(event, name) for event in events],
            dtype=np.float64,
        )

    arrays["dynamic_weight"] = np.asarray(
        [event.amplitude_squared for event in events],
        dtype=np.float64,
    )
    return arrays


def export_csv(payload: PhaseSpaceGenerateRequest) -> bytes:
    arrays = _arrays(payload)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(COLUMNS)
    for index in range(payload.n_events):
        writer.writerow([arrays[column][index] for column in COLUMNS])
    return stream.getvalue().encode("utf-8")
