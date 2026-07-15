.PHONY: install run check docker-build docker-up docker-down

PYTHON := .venv/bin/python

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	set -a; . ./.env; set +a; $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port $$PORT --reload

check:
	$(PYTHON) -m py_compile main.py config.py schemas.py anthropic.py routes/health.py routes/models.py routes/anthropic.py routes/chat.py

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
