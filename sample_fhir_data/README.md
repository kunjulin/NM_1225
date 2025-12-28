# FHIR 範例資料

本資料夾包含可上傳至 THAS 競賽環境 (https://thas.mohw.gov.tw/v/r4/fhir) 的 FHIR R4 範例資料。

## 檔案說明

| 檔案名稱 | 說明 |
|----------|------|
| `upload-fhir-data.ps1` | PowerShell 上傳腳本（Windows 推薦使用） |
| `patient_complete_bundle.json` | 完整病人資料 Bundle（包含所有臨床資料） |
| `patient_basic.json` | 基本病人資料 (Patient) |
| `encounters.json` | 就醫紀錄 (Encounter) |
| `conditions.json` | 診斷/病史 (Condition) |
| `observations_labs.json` | 檢驗資料 (Observation) |
| `allergies.json` | 過敏史 (AllergyIntolerance) |
| `medications.json` | 用藥紀錄 (MedicationStatement) |
| `procedures.json` | 處置紀錄 (Procedure) |
| `service_request.json` | 核醫檢查申請 (ServiceRequest) |

## 上傳方式

### 方式一：使用 PowerShell 腳本（最簡單，Windows 推薦）

在 PowerShell 中執行：

```powershell
cd sample_fhir_data
.\upload-fhir-data.ps1
```

腳本會自動：
- 讀取 `patient_complete_bundle.json`
- 上傳到 THAS FHIR Server
- 顯示上傳結果和統計資訊

### 方式二：使用完整 Bundle（推薦）

**使用 curl（Linux/macOS/Git Bash）：**

```bash
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @patient_complete_bundle.json
```

**使用 PowerShell：**

```powershell
$jsonContent = Get-Content -Path "patient_complete_bundle.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $jsonContent
```

### 方式三：個別上傳資源

**使用 curl（Linux/macOS/Git Bash）：**

```bash
# 1. 上傳 Patient
curl -X PUT "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" \
  -H "Content-Type: application/fhir+json" \
  -d @patient_basic.json

# 2. 上傳其他資源...
```

**使用 PowerShell：**

```powershell
# 1. 上傳 Patient
$patientJson = Get-Content -Path "patient_basic.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" `
  -Method Put `
  -ContentType "application/fhir+json" `
  -Body $patientJson

# 2. 上傳其他資源...
```

## 資料內容

範例資料模擬一位 45 歲男性病人（王大明），包含：

- **就醫紀錄**: 3 筆（門診、急診、住院）
- **診斷**: 4 筆（甲狀腺結節、高血壓、糖尿病前期、骨質疏鬆）
- **過敏**: 2 筆（Penicillin 藥物過敏、碘顯影劑過敏）
- **檢驗**: 11 筆（腎功能、肝功能、甲狀腺、血液）
- **用藥**: 3 筆（降血壓藥、胃藥、維生素D）
- **處置**: 2 筆（超音波、核醫檢查）
- **核醫申請**: 1 筆（骨骼掃描）

## 注意事項

1. 上傳前請確認 THAS 環境的存取權限
2. 資源 ID 使用固定格式以便測試和追蹤
3. 所有日期時間使用 ISO 8601 格式
4. LOINC 代碼用於檢驗項目識別
5. ICD-10 代碼用於診斷碼

## 相關 LOINC 代碼

| LOINC | 檢驗項目 | 類別 |
|-------|----------|------|
| 2160-0 | Creatinine (肌酸酐) | 腎功能 |
| 33914-3 | eGFR (腎絲球過濾率) | 腎功能 |
| 3094-0 | BUN (血中尿素氮) | 腎功能 |
| 1742-6 | ALT (丙氨酸轉氨酶) | 肝功能 |
| 1920-8 | AST (天門冬氨酸轉氨酶) | 肝功能 |
| 1975-2 | Bilirubin Total (總膽紅素) | 肝功能 |
| 3016-3 | TSH (促甲狀腺激素) | 甲狀腺 |
| 3026-2 | T4 Free (游離甲狀腺素) | 甲狀腺 |
| 718-7 | Hemoglobin (血紅素) | 血液 |
| 6690-2 | WBC (白血球) | 血液 |
| 777-3 | Platelet (血小板) | 血液 |
| 29463-7 | Body Weight (體重) | 生命徵象 |

