# Dalitz Web Visualizer

Interactive web application for constructing and exploring amplitude models for three-body decays.

## Current stack

- Backend: FastAPI, Pydantic, NumPy, SciPy
- Particle data: `particle`
- Reaction rules: `qrules` (adapter planned/in progress)
- Phase-space generation: `phasespace[tf]`
- Frontend: React, TypeScript, Vite

## Implemented backend features

- Health endpoint
- Particle lookup from the PDG table
- Automatic conversion of particle masses from MeV to GeV
- Three-body kinematic validation
- Three-body phase-space generation
- Four-momenta in `(px, py, pz, E)` convention
- Computation of `s12`, `s13`, and `s23`
- Separate `phase_space_weight`, `amplitude_squared`, and `total_weight`
- Event limit of 1,000,000

The amplitude engine is not connected yet, so `amplitude_squared` is currently equal to one.

## Linux requirements

- Python 3.11+
- Node.js 22+
- npm
- make
- build tools required by Python packages

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y git make unzip build-essential python3 python3-pip python3-venv python3-dev
```

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Makefile shortcuts

```bash
make backend-install
make backend-run
make backend-test
make frontend-install
make frontend-run
```

## Example phase-space request

Use `POST /api/v1/phase-space/generate`:

```json
{
  "mother": {"name": "D0"},
  "daughters": [
    {"name": "pi+"},
    {"name": "pi-"},
    {"name": "pi0"}
  ],
  "n_events": 100,
  "seed": 7
}
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
ruff check app tests
```

## Repository structure

```text
dalitz-web-visualizer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── physics/
│   │   └── services/
│   └── tests/
├── frontend/
│   └── src/
├── docs/
├── Makefile
└── README.md
```

## Frontend functionality

The React frontend now calls `POST /api/v1/phase-space/generate`, resolves the selected particles through the backend, generates three-body phase-space events, and displays:

- the resolved PDG particle information;
- an interactive Dalitz scatter plot in `(s12, s13)`;
- the three one-dimensional invariant-mass-squared projections.

The default backend URL is `http://localhost:8000/api/v1`. Override it with `VITE_API_URL` when needed.

## Automatic qrules validation

The frontend calls `POST /api/v1/decays/validate` automatically after any change
to the mother or daughter particles. The backend generates isobar transitions with
`qrules`, reports whether at least one allowed transition exists, and groups the
intermediate-state suggestions by the daughter pairs `12`, `13`, and `23`.

Example request:

```json
{
  "mother": {"name": "D0"},
  "daughters": [{"name": "pi+"}, {"name": "pi-"}, {"name": "pi0"}]
}
```

The result is cached in memory, because transition generation can take a few
seconds for a channel that has not been evaluated before.

## Resonance-weighted Dalitz model

The current implementation supports a coherent sum of selected suggested resonances using constant-width relativistic Breit-Wigner line shapes:

```text
A(s12,s13,s23) = sum_r a_r exp(i phi_r) RBW_r(s_pair)
total_weight = phase_space_weight * |A|^2
```

Magnitude and phase are editable in the frontend. Spin factors, Blatt-Weisskopf factors, Gounaris-Sakurai and Flatte remain planned extensions and are not silently approximated.

## Dynamic RBW model

The RBW amplitude now includes a mass-dependent width, normalised
Blatt-Weisskopf barrier factors at the resonance and mother vertices, and
Zemach angular terms for spin 0, 1 and 2. The default radii are 1.5 GeV^-1 for
the resonance and 5.0 GeV^-1 for the mother, and both can be edited in the UI.

## Identical-particle symmetrization

The amplitude engine automatically detects identical final-state particles from their PDG IDs. Each isobar component is summed coherently over all distinct bachelor/pair assignments before calculating the intensity:

\[
\mathcal A_{\rm sym} = \sum_{\pi\in S_{\rm identical}} \mathcal A_\pi,
\qquad I = |\mathcal A_{\rm sym}|^2.
\]

Permutations that only reverse the two daughters inside the same isobar are deduplicated, avoiding double counting. For `D+ -> pi+ pi- pi+`, a resonance configured in pair `12` is therefore evaluated in both `12` and `23`. The request field `symmetrize` defaults to `true`.


## Component normalization

Each selected resonance basis amplitude is normalized numerically over the generated three-body phase-space sample before applying its magnitude and phase:

`F_r -> F_r / sqrt(<w_PS |F_r|^2>)`.

The normalized object already includes the dynamic lineshape, Blatt-Weisskopf factors, Zemach angular term, and identical-particle symmetrization. The API returns the raw normalization integral and applied amplitude scale for every component.
