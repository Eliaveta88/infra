#!/usr/bin/env bash
# Запуск генератора данных из корня репозитория (все seed_* по цепочке).
# Пример: bash scripts/run_data_generator.sh --count 10000 --truncate
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m pip install -q -r data_generator/requirements.txt
exec python data_generator/run_all.py "$@"
