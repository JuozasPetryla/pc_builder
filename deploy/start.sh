#!/bin/sh
set -eu

python -m scripts.prepare_deploy
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}" --proxy-headers
