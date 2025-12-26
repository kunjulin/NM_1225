# NM Medication Stewardship - Frontend Startup Script (PowerShell)
# Nuclear Medicine Drug Management System - Frontend Service

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NM Medication Stewardship - Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the project root directory
if (-not (Test-Path "frontend")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Change to frontend directory
Set-Location frontend

# Check node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install
}

# Start development server
Write-Host ""
Write-Host "Starting Frontend service..." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

npm run dev
