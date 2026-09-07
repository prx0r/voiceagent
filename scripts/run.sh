#!/usr/bin/env bash
set -e
[ -f .env ] || cp .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --reload
