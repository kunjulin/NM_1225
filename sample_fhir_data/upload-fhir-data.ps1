# FHIR Data Upload Script (PowerShell)
# Purpose: Upload sample FHIR data to THAS FHIR Server
# Usage: Run .\upload-fhir-data.ps1 in PowerShell

$fhirServerUrl = "https://thas.mohw.gov.tw/v/r4/fhir"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Data Upload Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Server: $fhirServerUrl" -ForegroundColor Yellow
Write-Host "Data Directory: $scriptDir" -ForegroundColor Yellow
Write-Host ""

# Check if file exists
$bundleFile = Join-Path $scriptDir "patient_complete_bundle.json"
if (-not (Test-Path $bundleFile)) {
    Write-Host "Error: Cannot find $bundleFile" -ForegroundColor Red
    Write-Host "Please ensure the file exists in sample_fhir_data folder" -ForegroundColor Red
    exit 1
}

Write-Host "Reading Bundle file..." -ForegroundColor Green
try {
    $jsonContent = Get-Content -Path $bundleFile -Raw -Encoding UTF8
    Write-Host "File read successfully" -ForegroundColor Green
}
catch {
    Write-Host "Error: Cannot read file - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Uploading FHIR Bundle to THAS..." -ForegroundColor Green
Write-Host "This may take a few seconds..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri $fhirServerUrl -Method Post -ContentType "application/fhir+json" -Body $jsonContent -ErrorAction Stop
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Upload successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Display response summary
    if ($response.resourceType -eq "Bundle") {
        $total = $response.entry.Count
        $success = ($response.entry | Where-Object { $_.response.status -like "200*" -or $_.response.status -like "201*" }).Count
        Write-Host "Total uploaded: $total resources" -ForegroundColor Cyan
        Write-Host "Successful: $success resources" -ForegroundColor Green
        
        if ($success -lt $total) {
            Write-Host "Warning: Some resources failed to upload" -ForegroundColor Yellow
            Write-Host "Please check the response for details" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Response content:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 5 | Write-Host
}
catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Upload failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error message: $_" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "HTTP Status Code: $statusCode" -ForegroundColor Red
        
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "Error response: $errorBody" -ForegroundColor Red
        }
        catch {
            Write-Host "Cannot read error response content" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "1. THAS FHIR Server URL is correct" -ForegroundColor Yellow
    Write-Host "2. Authentication may be required (some environments need login)" -ForegroundColor Yellow
    Write-Host "3. Network connection is normal" -ForegroundColor Yellow
    
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create a case in the application referencing Patient/patient-1007" -ForegroundColor White
Write-Host "2. Open case details to view clinical data" -ForegroundColor White
Write-Host "3. Verify that data is displayed correctly" -ForegroundColor White
Write-Host ""
