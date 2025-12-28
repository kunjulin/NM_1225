# Check Uploaded Data Script (PowerShell)
# Purpose: 檢查 THAS FHIR Server 上是否有我們上傳的資料
# Usage: Run .\check-uploaded-data.ps1 in PowerShell

$ErrorActionPreference = "Stop"

$fhirServerUrl = "https://thas.mohw.gov.tw/v/r4/fhir"
$patientId = "patient-1007"
$serviceRequestId = "exam-007"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "檢查上傳的資料" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FHIR Server: $fhirServerUrl" -ForegroundColor Yellow
Write-Host "Patient ID: $patientId" -ForegroundColor Yellow
Write-Host "ServiceRequest ID: $serviceRequestId" -ForegroundColor Yellow
Write-Host ""

# 1. 檢查 Patient 是否存在
Write-Host "1. 檢查 Patient/$patientId..." -ForegroundColor Green
try {
    $patientUrl = "$fhirServerUrl/Patient/$patientId"
    $patientResponse = Invoke-WebRequest -Uri $patientUrl -Method Get -ErrorAction Stop
    
    if ($patientResponse.StatusCode -eq 200) {
        $patientJson = $patientResponse.Content | ConvertFrom-Json
        $patientName = $patientJson.name[0].text
        Write-Host "   ✓ Patient 存在" -ForegroundColor Green
        Write-Host "   姓名: $patientName" -ForegroundColor Cyan
        Write-Host "   ID: $($patientJson.id)" -ForegroundColor Cyan
    }
}
catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ✗ Patient 不存在（可能需要先上傳）" -ForegroundColor Red
    }
    else {
        Write-Host "   ✗ 查詢失敗: $_" -ForegroundColor Red
    }
}

Write-Host ""

# 2. 檢查 ServiceRequest 是否存在
Write-Host "2. 檢查 ServiceRequest/$serviceRequestId..." -ForegroundColor Green
try {
    $srUrl = "$fhirServerUrl/ServiceRequest/$serviceRequestId"
    $srResponse = Invoke-WebRequest -Uri $srUrl -Method Get -ErrorAction Stop
    
    if ($srResponse.StatusCode -eq 200) {
        $srJson = $srResponse.Content | ConvertFrom-Json
        $srPatient = $srJson.subject.reference
        $srCategory = $srJson.category[0].text
        $srCode = $srJson.code.text
        
        Write-Host "   ✓ ServiceRequest 存在" -ForegroundColor Green
        Write-Host "   Patient: $srPatient" -ForegroundColor Cyan
        Write-Host "   Category: $srCategory" -ForegroundColor Cyan
        Write-Host "   檢查: $srCode" -ForegroundColor Cyan
        Write-Host "   狀態: $($srJson.status)" -ForegroundColor Cyan
    }
}
catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ✗ ServiceRequest 不存在（可能需要先上傳）" -ForegroundColor Red
    }
    else {
        Write-Host "   ✗ 查詢失敗: $_" -ForegroundColor Red
    }
}

Write-Host ""

# 3. 查詢所有 active 的 ServiceRequest
Write-Host "3. 查詢所有 active 的 ServiceRequest（使用 category=nuclear-medicine 過濾）..." -ForegroundColor Green
try {
    $queryUrl = "$fhirServerUrl/ServiceRequest?status=active&category=nuclear-medicine"
    $queryResponse = Invoke-WebRequest -Uri $queryUrl -Method Get -ErrorAction Stop
    
    if ($queryResponse.StatusCode -eq 200) {
        $queryJson = $queryResponse.Content | ConvertFrom-Json
        
        if ($queryJson.entry -and $queryJson.entry.Count -gt 0) {
            Write-Host "   找到 $($queryJson.entry.Count) 個 ServiceRequest:" -ForegroundColor Cyan
            foreach ($entry in $queryJson.entry) {
                $sr = $entry.resource
                $srId = $sr.id
                $srPatient = $sr.subject.reference
                $srCode = $sr.code.text
                
                Write-Host "   - ID: $srId, Patient: $srPatient, 檢查: $srCode" -ForegroundColor White
                
                if ($srId -eq $serviceRequestId) {
                    Write-Host "     ✓ 這是我們上傳的 ServiceRequest" -ForegroundColor Green
                }
            }
        }
        else {
            Write-Host "   未找到任何 ServiceRequest" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "   ✗ 查詢失敗: $_" -ForegroundColor Red
}

Write-Host ""

# 4. 查詢特定 Patient 的所有 ServiceRequest
Write-Host "4. 查詢 Patient/$patientId 的所有 ServiceRequest..." -ForegroundColor Green
try {
    $patientSrUrl = "$fhirServerUrl/ServiceRequest?status=active&subject=Patient/$patientId"
    $patientSrResponse = Invoke-WebRequest -Uri $patientSrUrl -Method Get -ErrorAction Stop
    
    if ($patientSrResponse.StatusCode -eq 200) {
        $patientSrJson = $patientSrResponse.Content | ConvertFrom-Json
        
        if ($patientSrJson.entry -and $patientSrJson.entry.Count -gt 0) {
            Write-Host "   找到 $($patientSrJson.entry.Count) 個 ServiceRequest:" -ForegroundColor Cyan
            foreach ($entry in $patientSrJson.entry) {
                $sr = $entry.resource
                $srId = $sr.id
                $srCode = $sr.code.text
                $srCategory = $sr.category[0].text
                
                Write-Host "   - ID: $srId, 檢查: $srCode, Category: $srCategory" -ForegroundColor White
            }
        }
        else {
            Write-Host "   未找到任何 ServiceRequest（可能需要先上傳或同步）" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "   ✗ 查詢失敗: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "檢查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "說明：" -ForegroundColor Yellow
Write-Host "- 如果 Patient 或 ServiceRequest 不存在，請執行 .\upload-demo-data.ps1 上傳資料" -ForegroundColor White
Write-Host "- 如果資料已存在但工作清單中看不到，請檢查 ServiceRequest 的 category 是否為 'nuclear-medicine'" -ForegroundColor White
Write-Host "- 如果 category 正確但仍無法同步，請檢查系統的同步設定和過濾條件" -ForegroundColor White
Write-Host ""

