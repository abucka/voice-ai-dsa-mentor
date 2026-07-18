#!/bin/sh

PYTHON_BIN="$PWD/.venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)"
fi

exec "$PYTHON_BIN" -m uvicorn apps.backend.main:app --reload --port 4000