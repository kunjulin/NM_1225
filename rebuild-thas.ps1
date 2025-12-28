# Rebuild THAS Docker Containers Script
# 重新建置 THAS 環境的 Docker 容器（包含前端和後端）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rebuilding THAS Docker Containers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Error: docker-compose is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Stop existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.thas.yml down

Write-Host ""
Write-Host "Rebuilding containers (this may take a few minutes)..." -ForegroundColor Yellow
Write-Host ""

# Rebuild and start containers
try {
    docker-compose -f docker-compose.thas.yml build --no-cache
    
    Write-Host ""
    Write-Host "Starting containers..." -ForegroundColor Green
    docker-compose -f docker-compose.thas.yml up -d
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Containers rebuilt and started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "Checking container status..." -ForegroundColor Cyan
    docker-compose -f docker-compose.thas.yml ps
    
    Write-Host ""
    Write-Host "Viewing logs (press Ctrl+C to exit)..." -ForegroundColor Yellow
    Write-Host ""
    docker-compose -f docker-compose.thas.yml logs -f
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
    Write-Host "2. No other containers are using ports 8000 or 5173" -ForegroundColor Yellow
    Write-Host "3. Check logs: docker-compose -f docker-compose.thas.yml logs" -ForegroundColor Yellow
    exit 1
}

