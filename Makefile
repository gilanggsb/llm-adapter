.PHONY: install run check docker-build docker-run

PYTHON := .venv/bin/python

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	set -a; . ./.env; set +a; $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port $$PORT --reload

check:
	$(PYTHON) -m py_compile main.py config.py schemas.py anthropic.py routes/health.py routes/models.py routes/anthropic.py routes/chat.py

docker-build:
	docker build -t llm-adapter .

docker-run:
	set -a; . ./.env; set +a; docker run --rm --env-file .env -p $$PORT:$$PORT llm-adapter
