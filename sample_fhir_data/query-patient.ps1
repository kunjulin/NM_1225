# FHIR Patient Query Script (PowerShell)
# Purpose: Query Patient from THAS FHIR Server and verify UTF-8 encoding
# Usage: Run .\query-patient.ps1 in PowerShell

$fhirServerUrl = "https://thas.mohw.gov.tw/v/r4/fhir"
$patientId = "patient-1007"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Patient Query Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Server: $fhirServerUrl" -ForegroundColor Yellow
Write-Host "Patient ID: $patientId" -ForegroundColor Yellow
Write-Host ""

Write-Host "Querying Patient from THAS..." -ForegroundColor Green

try {
    # 使用 Invoke-WebRequest 並明確指定 UTF-8 編碼接收回應
    $response = Invoke-WebRequest -Uri "$fhirServerUrl/Patient/$patientId" `
        -Method Get `
        -Headers @{"Accept" = "application/fhir+json; charset=utf-8"} `
        -ErrorAction Stop
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Query successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "HTTP Status Code: $($response.StatusCode)" -ForegroundColor Cyan
    Write-Host "Content Encoding: $($response.Headers.'Content-Type')" -ForegroundColor Cyan
    Write-Host ""
    
    # 解析回應內容（確保使用 UTF-8 編碼）
    $responseContent = $response.Content
    $patient = $responseContent | ConvertFrom-Json
    
    Write-Host "Patient Information:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host "ID: $($patient.id)" -ForegroundColor White
    Write-Host "Name: $($patient.name[0].text)" -ForegroundColor White
    Write-Host "Family: $($patient.name[0].family)" -ForegroundColor White
    Write-Host "Given: $($patient.name[0].given -join ' ')" -ForegroundColor White
    Write-Host "Gender: $($patient.gender)" -ForegroundColor White
    Write-Host "Birth Date: $($patient.birthDate)" -ForegroundColor White
    
    if ($patient.address) {
        Write-Host "Address: $($patient.address[0].text)" -ForegroundColor White
    }
    
    if ($patient.telecom) {
        Write-Host "Phone: $($patient.telecom[0].value)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "Full JSON Response:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    $patient | ConvertTo-Json -Depth 10 | Write-Host
    
    # 檢查中文是否正確顯示
    Write-Host ""
    Write-Host "Encoding Check:" -ForegroundColor Yellow
    Write-Host "==============" -ForegroundColor Yellow
    $nameText = $patient.name[0].text
    if ($nameText -match "[\u4e00-\u9fff]") {
        Write-Host "✓ Chinese characters detected in name: $nameText" -ForegroundColor Green
    } else {
        Write-Host "✗ Warning: Chinese characters may be corrupted!" -ForegroundColor Red
        Write-Host "  Name value: $nameText" -ForegroundColor Red
    }
}
catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Query failed!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error message: $_" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "HTTP Status Code: $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 404) {
            Write-Host ""
            Write-Host "Patient not found. Please upload the patient first:" -ForegroundColor Yellow
            Write-Host "  .\upload-patient.ps1" -ForegroundColor White
        }
    }
    
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Query completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""



