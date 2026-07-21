.PHONY: backend-install backend-run backend-test frontend-install frontend-run

backend-install:
	cd backend && python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip setuptools wheel && .venv/bin/pip install -e '.[dev]'

backend-run:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload

backend-test:
	cd backend && .venv/bin/python -m pytest -v

frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev
