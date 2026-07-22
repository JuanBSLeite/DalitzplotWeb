# Dalitz Plot Web Visualizer

Interactive three-body amplitude-model playground.

## Current features

- particle masses and properties from `particle`;
- automatic decay validation and resonance suggestions with `qrules`;
- three-body toy generation with `phasespace`;
- dynamic relativistic Breit-Wigner;
- mass-dependent width;
- Blatt-Weisskopf factors at the mother and resonance vertices;
- Zemach angular terms for spin 0, 1 and 2;
- automatic identical-particle symmetrization;
- normalization of each complete symmetrized amplitude contribution;
- automatic theoretical Dalitz heatmap and three theoretical projections;
- optional toy Monte Carlo Dalitz plot and weighted histograms;
- toy export in CSV.

## Run on Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

## Main endpoints

- `POST /api/v1/decays/validate`
- `POST /api/v1/model/theoretical-plot`
- `POST /api/v1/toy/generate`
- `POST /api/v1/toy/export/csv`


## Toy export columns

The CSV export contains only:

- `p1_px`, `p1_py`, `p1_pz`, `p1_E`
- `p2_px`, `p2_py`, `p2_pz`, `p2_E`
- `p3_px`, `p3_py`, `p3_pz`, `p3_E`
- `s12`, `s13`, `s23`
- `dynamic_weight`, defined as the normalized model intensity `|A|^2`

Phase-space weights, complex amplitudes, total weights, event IDs, and metadata are not exported.

## Resonance parameter editing

The resonance editor accepts a numerical phase in degrees and allows the user to override the particle-database defaults for pole mass, pole width, spin/orbital L, resonance radius, and mother radius.

## Fit fractions

The theoretical-model response includes the fit fraction of every selected amplitude,

`FF_r = integral |A_r|^2 dPhi3 / integral |sum_k A_k|^2 dPhi3`.

They are displayed in **Selected amplitudes** and update automatically. Their sum can differ from 100% because interference terms are present only in the total denominator.

## Import and export amplitude models

The header includes **Export model** and **Import model** actions.

- Export creates a versioned JSON document (`schema_version: 1.0`).
- Import validates the JSON with the backend, rechecks the decay with `qrules`, and restores the channel, amplitudes, dynamic-RBW parameters, plot resolution, toy event count, and seed.
- Imported models automatically rebuild the theoretical plots, component normalizations, and fit fractions.

Model files store masses and widths in MeV for readability, while the numerical backend continues to use GeV internally.


## Non-resonant amplitude

The model can include one normalized constant scalar non-resonant term with an editable magnitude and phase. It participates coherently in the total amplitude, fit fractions, toy generation, and JSON import/export.
