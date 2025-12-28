# FHIR Demo Data Upload Script (PowerShell)
# Purpose: Upload complete Demo Patient data to THAS FHIR Server
# Usage: Run .\upload-demo-data.ps1 in PowerShell
#
# This script uploads patient_complete_bundle.json which contains:
# - 7 Patients (patient-1001 to patient-1007 with complete clinical data)
# - 7 ServiceRequests (exam-001 to exam-007 for nuclear medicine exams)
# - Multiple Encounters (medical encounters for each patient)
# - Multiple Conditions (diagnoses/conditions for each patient)
# - Multiple MedicationStatements (medication records for each patient)
# - Multiple Observations (lab results: weight, renal, hepatic, thyroid, blood, etc.)
# - Multiple AllergyIntolerances (allergy records)
# - Multiple Procedures (procedure records)
# - Practitioners (physicians)
#
# Note: patient-1007 has the most complete clinical data for testing Patient Information Card

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
    Write-Host "  - 7 Patients (patient-1001 to patient-1007)" -ForegroundColor White
    Write-Host "  - 7 ServiceRequests (exam-001 to exam-007 for nuclear medicine exams)" -ForegroundColor White
    Write-Host "  - 15 Encounters (medical encounters for each patient)" -ForegroundColor White
    Write-Host "  - 16 Conditions (diagnoses/conditions for each patient)" -ForegroundColor White
    Write-Host "  - 10 MedicationStatements (medication records for each patient)" -ForegroundColor White
    Write-Host "  - 32 Observations (lab results: weight, renal, hepatic, thyroid, blood, etc.)" -ForegroundColor White
    Write-Host "  - 4 AllergyIntolerances (allergy records)" -ForegroundColor White
    Write-Host "  - 2 Procedures (procedure records)" -ForegroundColor White
    Write-Host "  - 2 Practitioners (physicians)" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: patient-1007 has the most complete clinical data for testing Patient Information Card" -ForegroundColor Yellow
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
Write-Host "1. Verify all Patients uploaded successfully (patient-1001 to patient-1007)" -ForegroundColor White
Write-Host "2. Verify all ServiceRequests uploaded successfully (exam-001 to exam-007)" -ForegroundColor White
Write-Host "3. Sync FHIR data in application (click 'Sync FHIR' button)" -ForegroundColor White
Write-Host "4. Check if patient cases appear in nuclear medicine worklist" -ForegroundColor White
Write-Host "5. Open case detail page (e.g., exam-007 for patient-1007), verify Patient Information Card displays:" -ForegroundColor White
Write-Host "   - Encounters" -ForegroundColor Gray
Write-Host "   - Conditions" -ForegroundColor Gray
Write-Host "   - Medications" -ForegroundColor Gray
Write-Host "   - Lab Results" -ForegroundColor Gray
Write-Host "   - Allergies" -ForegroundColor Gray
Write-Host "   - Procedures" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: patient-1007 (exam-007) has the most complete clinical data for testing" -ForegroundColor Cyan
Write-Host ""
