# FHIR Demo Data Upload Script (PowerShell)
# Purpose: Upload complete Demo Patient data to THAS FHIR Server
# Usage: Run .\upload-demo-data.ps1 in PowerShell
#
# This script uploads patient_complete_bundle.json which contains:
# - Patient (basic patient info)
# - Encounter (3 medical encounters)
# - Condition (4 diagnoses/conditions)
# - MedicationStatement (3 medication records)
# - Observation (11 lab results: weight, renal, hepatic, thyroid, blood, etc.)
# - AllergyIntolerance (2 allergy records)
# - Procedure (2 procedure records)
# - ServiceRequest (nuclear medicine exam request)
# - Practitioner (physician)

$ErrorActionPreference = "Stop"

$fhirServerUrl = "https://thas.mohw.gov.tw/v/r4/fhir"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Demo Data Upload Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Server: $fhirServerUrl" -ForegroundColor Yellow
Write-Host "Data Directory: $scriptDir" -ForegroundColor Yellow
Write-Host ""

# Use patient_complete_bundle.json (complete bundle with all data)
$bundleFile = Join-Path $scriptDir "patient_complete_bundle.json"

# Check if file exists
if (-not (Test-Path $bundleFile)) {
    Write-Host "Error: Cannot find $bundleFile" -ForegroundColor Red
    Write-Host "Please ensure patient_complete_bundle.json exists in sample_fhir_data folder" -ForegroundColor Red
    exit 1
}

Write-Host "Reading Bundle file..." -ForegroundColor Green
try {
    # Read file with UTF-8 encoding
    $jsonContent = Get-Content -Path $bundleFile -Raw -Encoding UTF8
    Write-Host "File read successfully" -ForegroundColor Green
    
    # Parse JSON to check content
    $bundleJson = $jsonContent | ConvertFrom-Json
    $entryCount = $bundleJson.entry.Count
    Write-Host "Bundle contains $entryCount resources" -ForegroundColor Cyan
}
catch {
    Write-Host "Error: Cannot read file - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Uploading FHIR Bundle to THAS..." -ForegroundColor Green
Write-Host "This may take a few seconds..." -ForegroundColor Yellow
Write-Host ""

try {
    # Ensure UTF-8 encoding for JSON
    # Convert string to UTF-8 byte array to avoid PowerShell using system default encoding
    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonContent)
    
    # Use Invoke-WebRequest with explicit UTF-8 encoding
    $response = Invoke-WebRequest -Uri $fhirServerUrl `
        -Method Post `
        -ContentType "application/fhir+json; charset=utf-8" `
        -Body $utf8Bytes `
        -ErrorAction Stop
    
    # Parse response (using UTF-8 encoding)
    $responseContent = $response.Content
    $responseJson = $responseContent | ConvertFrom-Json
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Upload successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Display response summary
    if ($responseJson.resourceType -eq "Bundle") {
        $total = $responseJson.entry.Count
        $success = ($responseJson.entry | Where-Object { 
            $status = $_.response.status
            $status -like "200*" -or $status -like "201*" -or $status -like "204*"
        }).Count
        $failed = $total - $success
        
        Write-Host "Total uploaded: $total resources" -ForegroundColor Cyan
        Write-Host "Success: $success resources" -ForegroundColor Green
        
        if ($failed -gt 0) {
            Write-Host "Failed: $failed resources" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Failed resources:" -ForegroundColor Yellow
            foreach ($entry in $responseJson.entry) {
                $status = $entry.response.status
                if ($status -notlike "200*" -and $status -notlike "201*" -and $status -notlike "204*") {
                    $resourceType = $entry.resource.resourceType
                    $resourceId = $entry.resource.id
                    Write-Host "  - $resourceType/$resourceId : $status" -ForegroundColor Red
                }
            }
        }
        
        if ($success -eq $total) {
            Write-Host ""
            Write-Host "All resources uploaded successfully!" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "Uploaded resources include:" -ForegroundColor Cyan
    Write-Host "  - Patient (basic patient info)" -ForegroundColor White
    Write-Host "  - Encounter (3 medical encounters)" -ForegroundColor White
    Write-Host "  - Condition (4 diagnoses/conditions)" -ForegroundColor White
    Write-Host "  - MedicationStatement (3 medication records)" -ForegroundColor White
    Write-Host "  - Observation (11 lab results)" -ForegroundColor White
    Write-Host "  - AllergyIntolerance (2 allergy records)" -ForegroundColor White
    Write-Host "  - Procedure (2 procedure records)" -ForegroundColor White
    Write-Host "  - ServiceRequest (nuclear medicine exam request)" -ForegroundColor White
    Write-Host "  - Practitioner (physician)" -ForegroundColor White
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
            # Read error response with UTF-8 encoding
            $reader = New-Object System.IO.StreamReader($errorStream, [System.Text.Encoding]::UTF8)
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
    Write-Host "2. Authentication required (some environments need login)" -ForegroundColor Yellow
    Write-Host "3. Network connection is normal" -ForegroundColor Yellow
    Write-Host "4. JSON file encoding is UTF-8" -ForegroundColor Yellow
    
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify Patient ID: patient-1007 uploaded successfully" -ForegroundColor White
Write-Host "2. Sync FHIR data in application (click 'Sync FHIR' button)" -ForegroundColor White
Write-Host "3. Check if the patient case appears in nuclear medicine worklist" -ForegroundColor White
Write-Host "4. Open case detail page, verify Patient Information Card displays:" -ForegroundColor White
Write-Host "   - Encounters" -ForegroundColor Gray
Write-Host "   - Conditions" -ForegroundColor Gray
Write-Host "   - Medications" -ForegroundColor Gray
Write-Host "   - Lab Results" -ForegroundColor Gray
Write-Host "   - Allergies" -ForegroundColor Gray
Write-Host "   - Procedures" -ForegroundColor Gray
Write-Host ""
