# Dalitz Web Visualizer

Starter monorepo for an interactive three-body decay amplitude explorer.

## Stack
- Backend: FastAPI, Pydantic, particle, qrules
- Frontend: React, TypeScript, Vite, Plotly

## Run
```bash
make backend-install
make backend-run
# new terminal
make frontend-install
make frontend-run
```
Backend: http://localhost:8000/docs  Frontend: http://localhost:5173

## Current scope
The initial API exposes health checks, particle lookup, decay validation placeholders, and model schemas. Physics adapters are isolated so qrules and amplitude implementations can evolve without coupling to the UI.
