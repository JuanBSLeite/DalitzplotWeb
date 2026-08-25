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

## Physics conventions

The detailed definitions used for breakup momenta, Blatt-Weisskopf barrier factors, Zemach angular terms, the mass-dependent width, and the relativistic Breit-Wigner are documented in [`docs/PHYSICS_CONVENTIONS.md`](docs/PHYSICS_CONVENTIONS.md).

The current implementation adopts the spin-0 Dalitz/Zemach convention in which the resonance-daughter momentum `q` and bachelor momentum `p` are evaluated in the resonance rest frame. The physical threshold is explicitly enforced when calculating breakup momenta.

## Tested environment

The backend has been tested with **Python 3.12**.

The frontend has been tested with **Node.js 22**. On Linux, using `nvm` is recommended because it makes it easy to install and switch Node.js versions without replacing system packages.

## AlmaLinux 9 setup

### Install Python 3.12

```bash
sudo dnf install -y python3.12 python3.12-pip
```

Check the installation:

```bash
python3.12 --version
python3.12 -m pip --version
```

Create the backend virtual environment explicitly with Python 3.12:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

The last command should report Python 3.12.x.

### Install Node.js 22 with NVM

Install the basic tools first:

```bash
sudo dnf install -y curl ca-certificates
```

Install NVM:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

Load NVM in the current shell without logging out:

```bash
\. "$HOME/.nvm/nvm.sh"
```

Install and select Node.js 22:

```bash
nvm install 22
nvm use 22
nvm alias default 22
```

Check the installed versions:

```bash
node --version
npm --version
```

A tested Node.js version for this project is:

```text
v22.23.2
```

If a new shell does not recognize `nvm`, reload your shell configuration:

```bash
source ~/.bashrc
```

or load NVM directly again:

```bash
\. "$HOME/.nvm/nvm.sh"
```

## Run on Linux

Start the backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server listens on `0.0.0.0:8016` with `strictPort: true`.

Open the application locally at:

```text
http://localhost:8016/
```

or, from another machine on the network:

```text
http://SERVER_IP:8016/
```

API documentation is available directly from the backend at:

```text
http://localhost:8000/docs
```

## Frontend-backend communication

During development, the frontend uses a relative API URL:

```text
/api/v1
```

The Vite development server proxies `/api/*` requests to the FastAPI backend at:

```text
http://127.0.0.1:8000
```

This is configured in `frontend/vite.config.ts`, while `frontend/.env.development` defines:

```text
VITE_API_URL=/api/v1
```

Using a relative API URL is important for remote testing. If the frontend is opened from another computer, `localhost` would otherwise refer to that computer rather than to the AlmaLinux server running the backend.

For example, a browser request to:

```text
http://SERVER_IP:8016/api/v1/decays/validate
```

is received by Vite and forwarded internally to:

```text
http://127.0.0.1:8000/api/v1/decays/validate
```

After changing `vite.config.ts` or `.env.development`, restart `npm run dev`.

## Network and firewall

Port 8016 does not require root privileges, but it must be allowed through the firewall for remote access:

```bash
sudo firewall-cmd --permanent --add-port=8016/tcp
sudo firewall-cmd --reload
```

Confirm the rule:

```bash
sudo firewall-cmd --query-port=8016/tcp
```

Confirm that Vite is listening externally:

```bash
sudo ss -lptn 'sport = :8016'
```

The backend only needs to be reachable by Vite on the same server for the development proxy setup. You can test it locally with:

```bash
curl http://127.0.0.1:8000/docs
```

Then test the complete frontend path from the server:

```bash
curl http://127.0.0.1:8016/
```

For the remote connectivity test, open:

```text
http://SERVER_IP:8016/
```

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
