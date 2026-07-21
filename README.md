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
