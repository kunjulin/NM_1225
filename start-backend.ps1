# NM Medication Stewardship - Backend Startup Script (PowerShell)
# Nuclear Medicine Drug Management System - Backend Service

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NM Medication Stewardship - Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the project root directory
if (-not (Test-Path "backend")) {
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# Change to backend directory
Set-Location backend

# Check virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Check dependencies
if (-not (Test-Path "venv\Lib\site-packages\fastapi")) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item env.example.txt .env
    Write-Host ".env file created. Please modify settings as needed" -ForegroundColor Green
}

# Check for reset and seed parameter
$resetAndSeed = $args -contains "-ResetAndSeed" -or $args -contains "-reset"

# Function to reset and seed database
function Reset-AndSeedDatabase {
    $headers = @{
        "Content-Type" = "application/json"
        "X-Subject" = "demo-admin"
        "X-Acting-Role" = "ADMIN"
    }
    
    Write-Host "Resetting database..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod -Uri "http://localhost:8000/api/demo/reset" -Method POST -Headers $headers -TimeoutSec 5 | Out-Null
        Write-Host "Database reset completed." -ForegroundColor Green
    } catch {
        Write-Host "Warning: Failed to reset database. Error: $_" -ForegroundColor Yellow
        return $false
    }
    
    Start-Sleep -Seconds 1
    
    Write-Host "Seeding sample data..." -ForegroundColor Yellow
    try {
        $body = @{clearExisting = $true} | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/demo/seed" -Method POST -Headers $headers -Body $body -TimeoutSec 10
        Write-Host "Sample data seeded successfully!" -ForegroundColor Green
        Write-Host "Created: $($response.created) cases in $($response.scenarios.Count) scenarios" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "Warning: Failed to seed sample data. Error: $_" -ForegroundColor Yellow
        return $false
    }
}

# If reset and seed is requested, check if backend is running
if ($resetAndSeed) {
    Write-Host "Checking if backend is running..." -ForegroundColor Yellow
    $backendRunning = $false
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/docs" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendRunning = $true
        }
    } catch {
        $backendRunning = $false
    }
    
    if ($backendRunning) {
        Write-Host "Backend is running. Executing reset and seed..." -ForegroundColor Green
        Reset-AndSeedDatabase
        Write-Host ""
        Write-Host "Reset and seed completed. Backend is already running." -ForegroundColor Green
        Write-Host "Exiting script. Backend will continue running." -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "Backend is not running. Will start backend and execute reset/seed after startup." -ForegroundColor Yellow
        Write-Host ""
        
        # Start a background job to wait for backend and execute reset/seed
        $scriptBlock = {
            param($maxWait)
            $attempt = 0
            $ready = $false
            
            while ($attempt -lt $maxWait -and -not $ready) {
                Start-Sleep -Seconds 2
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/docs" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
                    if ($response.StatusCode -eq 200) {
                        $ready = $true
                    }
                } catch {
                    $attempt++
                }
            }
            
            if ($ready) {
                $headers = @{
                    "Content-Type" = "application/json"
                    "X-Subject" = "demo-admin"
                    "X-Acting-Role" = "ADMIN"
                }
                
                Write-Host "`n[Background Task] Backend is ready. Resetting database..." -ForegroundColor Green
                try {
                    Invoke-RestMethod -Uri "http://localhost:8000/api/demo/reset" -Method POST -Headers $headers -TimeoutSec 5 | Out-Null
                    Write-Host "[Background Task] Database reset completed." -ForegroundColor Green
                } catch {
                    Write-Host "[Background Task] Warning: Failed to reset database. Error: $_" -ForegroundColor Yellow
                    return
                }
                
                Start-Sleep -Seconds 1
                
                Write-Host "[Background Task] Seeding sample data..." -ForegroundColor Green
                try {
                    $body = @{clearExisting = $true} | ConvertTo-Json
                    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/demo/seed" -Method POST -Headers $headers -Body $body -TimeoutSec 10
                    Write-Host "[Background Task] Sample data seeded successfully!" -ForegroundColor Green
                    Write-Host "[Background Task] Created: $($response.created) cases in $($response.scenarios.Count) scenarios" -ForegroundColor Cyan
                } catch {
                    Write-Host "[Background Task] Warning: Failed to seed sample data. Error: $_" -ForegroundColor Yellow
                }
            } else {
                Write-Host "[Background Task] Warning: Backend did not start in time. Reset/seed skipped." -ForegroundColor Yellow
            }
        }
        
        Start-Job -ScriptBlock $scriptBlock -ArgumentList 30 | Out-Null
    }
}

# Start service
Write-Host ""
Write-Host "Starting Backend service..." -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000/api/docs" -ForegroundColor Cyan
if ($resetAndSeed) {
    Write-Host "Reset/seed will be executed automatically after backend starts (in background)." -ForegroundColor Cyan
}
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
