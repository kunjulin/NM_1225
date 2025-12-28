# FHIR Patient Upload Script (PowerShell)
# Purpose: Upload single Patient resource to THAS FHIR Server with proper UTF-8 encoding
# Usage: Run .\upload-patient.ps1 in PowerShell

$fhirServerUrl = "https://thas.mohw.gov.tw/v/r4/fhir"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Patient Upload Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Server: $fhirServerUrl" -ForegroundColor Yellow
Write-Host "Data Directory: $scriptDir" -ForegroundColor Yellow
Write-Host ""

# Check if file exists
$patientFile = Join-Path $scriptDir "patient_basic.json"
if (-not (Test-Path $patientFile)) {
    Write-Host "Error: Cannot find $patientFile" -ForegroundColor Red
    Write-Host "Please ensure the file exists in sample_fhir_data folder" -ForegroundColor Red
    exit 1
}

Write-Host "Reading Patient file..." -ForegroundColor Green
try {
    # 使用 UTF-8 編碼讀取文件
    $jsonContent = Get-Content -Path $patientFile -Raw -Encoding UTF8
    Write-Host "File read successfully" -ForegroundColor Green
    
    # 解析 JSON 以取得 Patient ID
    $patientJson = $jsonContent | ConvertFrom-Json
    $patientId = $patientJson.id
    if (-not $patientId) {
        Write-Host "Error: Patient ID not found in JSON file" -ForegroundColor Red
        exit 1
    }
    Write-Host "Patient ID: $patientId" -ForegroundColor Cyan
}
catch {
    Write-Host "Error: Cannot read file - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Uploading Patient to THAS..." -ForegroundColor Green
Write-Host "This may take a few seconds..." -ForegroundColor Yellow

try {
    # 使用 PUT 方法上傳單一 Patient 資源
    # PUT 到 /fhir/Patient/{id} 端點，而不是 POST 到 /fhir
    $putUrl = "$fhirServerUrl/Patient/$patientId"
    
    # 確保 JSON 內容以 UTF-8 編碼發送
    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonContent)
    
    # 建立 HTTP 請求
    $headers = @{
        "Content-Type" = "application/fhir+json; charset=utf-8"
    }
    
    # 使用 Invoke-WebRequest 並明確指定 UTF-8 編碼
    $response = Invoke-WebRequest -Uri $putUrl `
        -Method Put `
        -Headers $headers `
        -Body $utf8Bytes `
        -ContentType "application/fhir+json; charset=utf-8" `
        -ErrorAction Stop
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Upload successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "HTTP Status Code: $($response.StatusCode)" -ForegroundColor Cyan
    
    # 解析回應內容（使用 UTF-8 編碼）
    $responseContent = $response.Content
    $responseJson = $responseContent | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "Response content:" -ForegroundColor Cyan
    $responseJson | ConvertTo-Json -Depth 10 | Write-Host
    
    # 顯示 Patient 資訊
    if ($responseJson.resourceType -eq "Patient") {
        Write-Host ""
        Write-Host "Patient Information:" -ForegroundColor Cyan
        Write-Host "  ID: $($responseJson.id)" -ForegroundColor White
        if ($responseJson.name -and $responseJson.name.Count -gt 0) {
            Write-Host "  Name: $($responseJson.name[0].text)" -ForegroundColor White
        }
    }
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
            # 使用 UTF-8 編碼讀取錯誤回應
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
    Write-Host "2. Authentication may be required (some environments need login)" -ForegroundColor Yellow
    Write-Host "3. Network connection is normal" -ForegroundColor Yellow
    Write-Host "4. JSON file encoding is UTF-8" -ForegroundColor Yellow
    Write-Host "5. Patient ID exists in JSON file" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Note: For single Patient resource, use PUT to /fhir/Patient/{id}" -ForegroundColor Cyan
    Write-Host "      For multiple resources, use POST to /fhir with Bundle" -ForegroundColor Cyan
    
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Query the patient to verify encoding:" -ForegroundColor White
Write-Host "   Invoke-RestMethod -Uri `"$fhirServerUrl/Patient/patient-1007`" | ConvertTo-Json -Depth 10" -ForegroundColor Gray
Write-Host "2. Check that Chinese characters are displayed correctly" -ForegroundColor White
Write-Host ""

