.PHONY: install run test lint format

install:
	python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -r requirements-dev.txt

run:
	FLASK_ENV=development .venv/bin/flask --app wsgi run --debug

test:
	.venv/bin/pytest

lint:
	.venv/bin/flake8 app/ tests/ --max-line-length=100

format:
	.venv/bin/black app/ tests/
