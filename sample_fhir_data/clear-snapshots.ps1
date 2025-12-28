# Clear Snapshots Script (PowerShell)
# Purpose: Clear all snapshot FHIR data from Docker container APP DB
# Usage: Run .\clear-snapshots.ps1 in PowerShell

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Clear Snapshot Data Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory (one level up from sample_fhir_data)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $projectRoot "backend"
$clearScript = Join-Path $backendDir "clear_snapshots.py"

# Docker container name
$containerName = "nm-backend-thas"

# Check if clear_snapshots.py exists
if (-not (Test-Path $clearScript)) {
    Write-Host "Error: Cannot find script $clearScript" -ForegroundColor Red
    Write-Host "Please ensure backend/clear_snapshots.py file exists" -ForegroundColor Red
    exit 1
}

Write-Host "Checking Docker container status..." -ForegroundColor Yellow

# Check if Docker is available
try {
    docker --version | Out-Null
} catch {
    Write-Host "Error: Cannot execute Docker command" -ForegroundColor Red
    Write-Host "Please ensure Docker is installed and running" -ForegroundColor Red
    exit 1
}

# Check if container exists and is running
$containerStatus = docker ps -a --filter "name=$containerName" --format "{{.Status}}" 2>&1
if ($LASTEXITCODE -ne 0 -or -not $containerStatus) {
    Write-Host "Error: Cannot find container $containerName" -ForegroundColor Red
    Write-Host "Please ensure container is created and running" -ForegroundColor Red
    exit 1
}

# Check if container is running
$isRunning = docker ps --filter "name=$containerName" --format "{{.Names}}" 2>&1
if (-not $isRunning -or $isRunning -ne $containerName) {
    Write-Host "Error: Container $containerName is not running" -ForegroundColor Red
    Write-Host "Please start container: docker-compose -f docker-compose.thas.yml up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "Container status: Running" -ForegroundColor Green
Write-Host ""

# Copy script to container
Write-Host "Copying script to container..." -ForegroundColor Yellow
try {
    docker cp $clearScript "${containerName}:/app/clear_snapshots.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Copy failed"
    }
    Write-Host "Copy successful" -ForegroundColor Green
} catch {
    Write-Host "Error: Cannot copy script to container - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Executing script in container..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Execute script in container
try {
    docker exec $containerName python clear_snapshots.py
    if ($LASTEXITCODE -ne 0) {
        throw "Execution failed"
    }
} catch {
    Write-Host ""
    Write-Host "Error: Script execution failed - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: You may need to refresh the frontend page or wait for sync to see updated status" -ForegroundColor Yellow
Write-Host ""
