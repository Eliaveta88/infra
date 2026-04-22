# Запуск генератора данных из корня репозитория (все seed_* по цепочке).
# Пример: powershell -ExecutionPolicy Bypass -File scripts/run_data_generator.ps1 --count 10000 --truncate
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m pip install -q -r data_generator/requirements.txt
python data_generator/run_all.py @args
