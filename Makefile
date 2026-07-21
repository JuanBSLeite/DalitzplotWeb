backend-install:
	cd backend && python -m venv .venv && .venv/bin/pip install -e '.[dev]'
backend-run:
	cd backend && .venv/bin/uvicorn app.main:app --reload
backend-test:
	cd backend && .venv/bin/pytest
frontend-install:
	cd frontend && npm install
frontend-run:
	cd frontend && npm run dev
