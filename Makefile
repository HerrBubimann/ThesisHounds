# Thin wrapper around infrastructure/scripts/run_ci.py (the single source of truth).
# Windows without make: .\.venv\Scripts\python.exe infrastructure/scripts/run_ci.py <target>

ifeq ($(OS),Windows_NT)
PYTHON ?= .venv/Scripts/python.exe
else
PYTHON ?= .venv/bin/python
endif
RUN_CI := $(PYTHON) infrastructure/scripts/run_ci.py

TARGETS := lint format-check test test-unit test-integration test-security coverage \
           security docker-check docker-smoke ci

.PHONY: help install format $(TARGETS)

help:
	@echo "Targets: install format $(TARGETS)"

install:
	$(PYTHON) -m pip install --require-hashes -r requirements-dev.lock

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

$(TARGETS):
	$(RUN_CI) $@
