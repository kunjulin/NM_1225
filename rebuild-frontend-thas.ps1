# Rebuild Frontend Container for THAS
# 重新建置 THAS 前端容器

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rebuilding THAS Frontend Container" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if port 5173 is in use
Write-Host "Checking if port 5173 is available..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host ""
    Write-Host "WARNING: Port 5173 is already in use!" -ForegroundColor Red
    Write-Host "This usually means you're running 'npm run dev' in development mode." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "1. Stop the development server (Ctrl+C in the terminal running 'npm run dev')" -ForegroundColor Yellow
    Write-Host "2. Or use Docker container instead (recommended)" -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "Press Enter to continue anyway (will fail), or type 'skip' to exit"
    if ($response -eq 'skip') {
        exit 1
    }
}

# Stop existing frontend container
Write-Host ""
Write-Host "Stopping existing frontend container..." -ForegroundColor Yellow
docker-compose -f docker-compose.thas.yml stop frontend
docker-compose -f docker-compose.thas.yml rm -f frontend

Write-Host ""
Write-Host "Rebuilding frontend container (this may take a few minutes)..." -ForegroundColor Yellow
Write-Host ""

# Rebuild and start frontend container
try {
    docker-compose -f docker-compose.thas.yml build --no-cache frontend
    
    Write-Host ""
    Write-Host "Starting frontend container..." -ForegroundColor Green
    docker-compose -f docker-compose.thas.yml up -d frontend
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Frontend container rebuilt and started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Waiting for frontend to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "Checking container status..." -ForegroundColor Cyan
    docker-compose -f docker-compose.thas.yml ps frontend
    
    Write-Host ""
    Write-Host "Frontend should be available at:" -ForegroundColor Green
    Write-Host "  http://localhost:5173" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To view logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.thas.yml logs -f frontend" -ForegroundColor Cyan
}
catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error occurred during rebuild!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "1. Docker is running" -ForegroundColor Yellow
    Write-Host "2. Port 5173 is not in use (stop 'npm run dev' if running)" -ForegroundColor Yellow
    Write-Host "3. Check logs: docker-compose -f docker-compose.thas.yml logs frontend" -ForegroundColor Yellow
    exit 1
}

