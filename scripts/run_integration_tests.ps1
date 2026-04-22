# Поднимает docker compose и прогоняет pytest tests_api против Traefik.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$composeFile = if ($env:COMPOSE_FILE) { $env:COMPOSE_FILE } else { "docker-compose.yml" }
$apiBase = if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://localhost" }
$maxWaitSec = if ($env:MAX_WAIT_SEC) { [int]$env:MAX_WAIT_SEC } else { 120 }

Write-Host "Compose: $composeFile"
docker compose -f $composeFile up -d --build

Write-Host "Waiting for stack (max ${maxWaitSec}s)..."
$deadline = [DateTime]::UtcNow.AddSeconds($maxWaitSec)
$ready = $false
while ([DateTime]::UtcNow -lt $deadline) {
    try {
        $null = Invoke-WebRequest -Uri "$apiBase/catalog/api/v1/health" -UseBasicParsing -TimeoutSec 5
        $null = Invoke-WebRequest -Uri "$apiBase/identity/api/v1/health" -UseBasicParsing -TimeoutSec 5
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 3
    }
}
if (-not $ready) {
    Write-Error "Timeout: stack did not become ready."
    exit 1
}
Write-Host "Stack is up."

python -m pip install -q -r tests_api/requirements.txt
$env:API_BASE_URL = $apiBase
python -m pytest tests_api -v $args
