PY ?= python
.PHONY: setup env run mock test smoke zip

setup:
	$(PY) -m pip install -r requirements.txt

env:
	cat env/*.env.part > .env.example

run:
	cd backend && $(PY) -m uvicorn app.main:app --reload --port 8000

mock:
	cd backend && MOCK=1 $(PY) -m uvicorn app.main:app --reload --port 8000

test:
	$(PY) -m pytest backend

smoke:
	bash scripts/smoke.sh

zip:
	bash scripts/build_extension_zip.sh
