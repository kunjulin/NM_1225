# Check and Compare ServiceRequest Format Script (PowerShell)
# Purpose: Check if uploaded data exists and compare formats
# Usage: Run .\check-and-compare.ps1 in PowerShell

$ErrorActionPreference = "Stop"

$fhirServerUrl = "https://thas.mohw.gov.tw/v/r4/fhir"
$patientId = "patient-1007"
$serviceRequestId = "exam-007"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Check Uploaded Data and Compare Formats" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check if exam-007 exists
Write-Host "1. Checking ServiceRequest/$serviceRequestId..." -ForegroundColor Green
$exam007Found = $false
$exam007Category = $null

try {
    $srUrl = "$fhirServerUrl/ServiceRequest/$serviceRequestId"
    $srResponse = Invoke-WebRequest -Uri $srUrl -Method Get -ErrorAction Stop
    
    if ($srResponse.StatusCode -eq 200) {
        $exam007Found = $true
        $srJson = $srResponse.Content | ConvertFrom-Json
        $exam007Category = $srJson.category[0]
        
        Write-Host "   ✓ ServiceRequest exists" -ForegroundColor Green
        Write-Host "   Patient: $($srJson.subject.reference)" -ForegroundColor Cyan
        Write-Host "   Status: $($srJson.status)" -ForegroundColor Cyan
        Write-Host "   Category text: $($srJson.category[0].text)" -ForegroundColor Cyan
        if ($srJson.category[0].coding) {
            Write-Host "   Category coding.display: $($srJson.category[0].coding[0].display)" -ForegroundColor Cyan
            Write-Host "   Category coding.code: $($srJson.category[0].coding[0].code)" -ForegroundColor Cyan
        }
    }
}
catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ✗ ServiceRequest NOT FOUND (data may not be uploaded)" -ForegroundColor Red
    }
    else {
        Write-Host "   ✗ Query failed: $_" -ForegroundColor Red
    }
}

Write-Host ""

# 2. Query all ServiceRequests with category=nuclear-medicine
Write-Host "2. Querying ServiceRequests with category=nuclear-medicine..." -ForegroundColor Green
try {
    $queryUrl = "$fhirServerUrl/ServiceRequest?status=active&category=nuclear-medicine"
    $queryResponse = Invoke-WebRequest -Uri $queryUrl -Method Get -ErrorAction Stop
    
    if ($queryResponse.StatusCode -eq 200) {
        $queryJson = $queryResponse.Content | ConvertFrom-Json
        
        if ($queryJson.entry -and $queryJson.entry.Count -gt 0) {
            Write-Host "   Found $($queryJson.entry.Count) ServiceRequests:" -ForegroundColor Cyan
            Write-Host ""
            
            foreach ($entry in $queryJson.entry) {
                $sr = $entry.resource
                $srId = $sr.id
                $srPatient = $sr.subject.reference
                $srCode = $sr.code.text
                $catText = $sr.category[0].text
                $catDisplay = if ($sr.category[0].coding) { $sr.category[0].coding[0].display } else { "N/A" }
                $catCode = if ($sr.category[0].coding) { $sr.category[0].coding[0].code } else { "N/A" }
                
                $isExam007 = ($srId -eq $serviceRequestId)
                $marker = if ($isExam007) { "✓ YOUR DATA" } else { "  " }
                
                Write-Host "   $marker ID: $srId" -ForegroundColor $(if ($isExam007) { "Green" } else { "White" })
                Write-Host "      Patient: $srPatient" -ForegroundColor White
                Write-Host "      Exam: $srCode" -ForegroundColor White
                Write-Host "      Category text: $catText" -ForegroundColor White
                Write-Host "      Category display: $catDisplay" -ForegroundColor White
                Write-Host "      Category code: $catCode" -ForegroundColor White
                Write-Host ""
            }
            
            # Check if exam-007 is in the list
            $exam007InList = ($queryJson.entry | Where-Object { $_.resource.id -eq $serviceRequestId }).Count -gt 0
            if (-not $exam007InList) {
                Write-Host "   ⚠ WARNING: exam-007 is NOT in the query results!" -ForegroundColor Yellow
                Write-Host "   This means the category filter is not matching your data." -ForegroundColor Yellow
                Write-Host ""
                if ($exam007Found) {
                    Write-Host "   exam-007 exists but category format may not match the filter." -ForegroundColor Yellow
                }
            }
        }
        else {
            Write-Host "   No ServiceRequests found" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "   ✗ Query failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not $exam007Found) {
    Write-Host "✗ exam-007 does not exist on FHIR Server" -ForegroundColor Red
    Write-Host "  Action: Run .\upload-demo-data.ps1 to upload data" -ForegroundColor Yellow
}
else {
    Write-Host "✓ exam-007 exists on FHIR Server" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If exam-007 not found: Upload data using .\upload-demo-data.ps1" -ForegroundColor White
Write-Host "2. If exam-007 found but not in query results: Category format may not match filter" -ForegroundColor White
Write-Host "3. Compare category formats between your data and the 6 successful entries" -ForegroundColor White
Write-Host ""

