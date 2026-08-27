# Dalitz Plot Web Visualizer

Interactive three-body amplitude-model playground.

## Current features

- particle masses and properties from `particle`;
- automatic decay validation and resonance suggestions with `qrules`;
- three-body toy generation with `phasespace`;
- relativistic Breit-Wigner (`RBW`) as the single supported lineshape;
- mass-dependent width;
- Blatt-Weisskopf factors at the mother and resonance vertices;
- Zemach angular terms for `L = 0, 1, 2`;
- support for virtual resonance pole masses outside the accessible daughter-pair mass interval;
- automatic identical-particle symmetrization and Bose-symmetry checks;
- deterministic cached normalization of each complete symmetrized amplitude contribution;
- selectable theoretical Dalitz visualization as a 2D heatmap or 3D intensity surface;
- automatic three theoretical projections;
- fit fractions evaluated on the fixed integration grid;
- optional weighted toy Monte Carlo Dalitz plot and histograms;
- toy export in CSV.

## Physics scope and conventions

The detailed physics definitions are documented in [`docs/PHYSICS_CONVENTIONS.md`](docs/PHYSICS_CONVENTIONS.md).

The current amplitude engine is intentionally restricted to

```text
spin-0 mother -> spin-0 + spin-0 + spin-0
```

using a relativistic Breit-Wigner isobar model and Zemach angular terms. Channels containing a nonzero-spin mother or final-state particle are rejected by the amplitude layer rather than being evaluated with an inappropriate spin formalism.

Only **RBW** is supported at present. Other lineshapes are intentionally not exposed by the API yet.

The resonance-daughter momentum `q` and bachelor momentum `p` are evaluated in the resonance rest frame. Event-by-event breakup momentum is explicitly set to zero below the physical daughter threshold.

### Virtual resonances

A pole mass can lie below the daughter threshold or above the maximum daughter-pair mass accessible in the decay. In this case the nominal pole mass remains in the Breit-Wigner denominator, while the reference momenta `q0` and `p0` are evaluated at an effective reference mass smoothly mapped into the physical daughter-pair interval. The exact prescription is given in `docs/PHYSICS_CONVENTIONS.md`.

### Deterministic amplitude normalization

Component normalization is no longer estimated from the theoretical display grid or from a generated toy sample. A fixed `260 x 260` Dalitz integration grid is used for physics integrals, and the resulting component normalizations are cached.

Therefore changing only any of the following does **not** redefine the amplitude basis:

- theoretical-plot display resolution;
- toy event count;
- toy seed;
- amplitude magnitude;
- amplitude phase.

Fit fractions use the same deterministic integration grid.

## Dalitz visualization

The theoretical Dalitz plot can be switched between two visualization modes without changing the physics model:

- **2D heatmap:** `s12` on the x-axis, `s13` on the y-axis, color = `|A|^2`;
- **3D surface:** `s12` on the x-axis, `s13` on the y-axis, `|A|^2` on the z-axis.

Both views use the same theoretical intensity grid returned by the backend.

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

## Toy Monte Carlo and export

The generated toy is a **weighted phase-space sample**, with

```text
w_total = w_phase_space |A|^2.
```

It is not currently an unweighted accept-reject sample.

The CSV export contains only:

- `p1_px`, `p1_py`, `p1_pz`, `p1_E`
- `p2_px`, `p2_py`, `p2_pz`, `p2_E`
- `p3_px`, `p3_py`, `p3_pz`, `p3_E`
- `s12`, `s13`, `s23`
- `dynamic_weight`, defined as the normalized model intensity `|A|^2`

Phase-space weights, complex amplitudes, total weights, event IDs, and metadata are not exported.

## Resonance parameter editing

The resonance editor accepts a numerical phase and allows the user to override the particle-database defaults for pole mass, pole width, resonance radius, and mother radius. Spin/orbital `L` is fixed by the selected resonance and is currently restricted to `0`, `1`, or `2`.

Pole masses outside the accessible daughter-pair interval are permitted and treated as virtual contributions using the documented effective-reference-mass prescription.

## Fit fractions

The theoretical-model response includes the fit fraction of every selected amplitude,

`FF_r = integral |A_r|^2 dPhi3 / integral |sum_k A_k|^2 dPhi3`.

Fit fractions are calculated on the fixed deterministic integration grid, not on the display grid. Their sum can differ from 100% because interference terms are present only in the total denominator.

## Import and export amplitude models

The header includes **Export model** and **Import model** actions.

- Export creates a versioned JSON document (`schema_version: 1.0`).
- Import validates the JSON with the backend, rechecks the decay with `qrules`, and restores the channel, amplitudes, RBW parameters, plot resolution, toy event count, and seed.
- Imported models automatically rebuild the theoretical plots, cached component normalizations, and fit fractions.

Model files store masses and widths in MeV for readability, while the numerical backend uses GeV internally.

## Non-resonant amplitude

The model can include one normalized constant scalar non-resonant term with an editable magnitude and phase. It participates coherently in the total amplitude, fit fractions, toy generation, and JSON import/export.
