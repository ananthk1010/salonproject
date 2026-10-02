.PHONY: install test contract eval seed lint build-web dev-api dev-web docker-up docker-down

API_PY := apps/api/.venv/Scripts/python.exe
ifeq ($(wildcard $(API_PY)),)
	API_PY := apps/api/.venv/bin/python
endif

install:
	python -m venv apps/api/.venv
	$(API_PY) -m pip install -r apps/api/requirements-dev.txt
	cd apps/web && npm install

seed:
	cd apps/api && ../../$(API_PY) scripts/generate_seed.py

test:
	cd apps/api && ../../$(API_PY) -m pytest -q

contract:
	cd apps/api && ../../$(API_PY) scripts/export_openapi.py
	cd apps/web && npx --yes openapi-typescript ../../packages/contracts/openapi.json -o ../../packages/contracts/src/api.d.ts
	@git diff --exit-code packages/contracts || (echo "contract drift detected: commit the regenerated files" && exit 1)

eval:
	$(API_PY) lab/jev_eval.py --mode replay

eval-live:
	$(API_PY) lab/jev_eval.py --mode live --runs 3

lint:
	cd apps/api && ../../$(API_PY) -m ruff check app tests
	cd apps/web && npm run lint

build-web:
	cd apps/web && npm run build

dev-api:
	cd apps/api && ../../$(API_PY) -m uvicorn app.main:app --reload --port 8010

dev-web:
	cd apps/web && npm run dev -- --port 3010

docker-up:
	docker compose up --build

docker-down:
	docker compose down
