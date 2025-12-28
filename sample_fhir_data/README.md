# FHIR 範例資料

本資料夾包含可上傳至 THAS 競賽環境 (https://thas.mohw.gov.tw/v/r4/fhir) 的 FHIR R4 範例資料。

## 檔案說明

| 檔案名稱 | 說明 |
|----------|------|
| `upload-demo-data.ps1` | **統一上傳腳本（推薦使用）** - 上傳完整的 Demo Patient 資料到 THAS FHIR Server |
| `check-uploaded-data.ps1` | **檢查腳本（推薦使用）** - 檢查上傳的資料是否成功上傳到 FHIR Server |
| `upload-fhir-data.ps1` | 完整 Bundle 上傳腳本（已棄用，請使用 upload-demo-data.ps1） |
| `upload-patient.ps1` | 單一 Patient 資源上傳腳本（僅用於測試編碼，不推薦用於 Demo） |
| `query-patient.ps1` | Patient 查詢腳本（用於驗證編碼是否正確） |
| `clear-snapshots.ps1` | 清除 Docker 容器內 APP DB 的所有 snapshot 資料腳本 |
| `patient_complete_bundle.json` | 完整病人資料 Bundle（包含所有臨床資料） |
| `patient_basic.json` | 基本病人資料 (Patient) |
| `encounters.json` | 就醫紀錄 (Encounter) |
| `conditions.json` | 診斷/病史 (Condition) |
| `observations_labs.json` | 檢驗資料 (Observation) |
| `allergies.json` | 過敏史 (AllergyIntolerance) |
| `medications.json` | 用藥紀錄 (MedicationStatement) |
| `procedures.json` | 處置紀錄 (Procedure) |
| `service_request.json` | 核醫檢查申請 (ServiceRequest) |

## 資料庫管理

### 清除 Snapshot 資料

**清除 Docker 容器內的所有 snapshot 資料（示範前使用）：**

```powershell
cd sample_fhir_data
.\clear-snapshots.ps1
```

腳本會自動：
- 檢查 Docker 容器 `nm-backend-thas` 是否運行
- 複製清理腳本到容器內
- 執行清理並顯示統計資訊（案件數、審查事件數、Outbox 項目數）
- 清除所有 OrderCase、ReviewEvent 和 Outbox 資料

**注意：** 此操作會刪除所有案件資料，請在示範前使用。

## 上傳方式

### 方式一：使用統一上傳腳本（推薦）

**上傳完整 Demo 資料（包含所有測試 Patient Information Card 所需的資料）：**

```powershell
cd sample_fhir_data
.\upload-demo-data.ps1
```

腳本會自動：
- 讀取 `patient_complete_bundle.json`（包含所有需要的資料）
- 上傳到 THAS FHIR Server（使用 POST）
- 顯示上傳結果和統計資訊

**上傳的資源包含：**
- **7 個 Patient** (病人基本資料，包含 patient-1001 到 patient-1007)
- **7 個 ServiceRequest** (核醫檢查申請：exam-001 到 exam-007)
  - exam-001: 全身 FDG PET/CT (patient-1001)
  - exam-002: 三相骨骼掃描 (patient-1002)
  - exam-003: 腎皮質掃描 DMSA (patient-1006)
  - exam-004: MIBG 心臟交感神經顯像 (patient-1005)
  - exam-005: 甲狀腺攝取率 (patient-1003)
  - exam-006: 腎功能掃描 MAG3 (patient-1004)
  - exam-007: 骨骼掃描 (patient-1007)
- **15 個 Encounter** (就醫紀錄)
- **16 個 Condition** (診斷/病史)
- **10 個 MedicationStatement** (用藥紀錄)
- **32 個 Observation** (檢驗資料：體重、腎功能、肝功能、甲狀腺、血液等)
- **4 個 AllergyIntolerance** (過敏史)
- **2 個 Procedure** (處置紀錄)
- **2 個 Practitioner** (醫師)

**注意：** `patient_complete_bundle.json` 已經包含了所有測試 Patient Information Card 所需的資料，無需單獨上傳 conditions.json、encounters.json、medications.json、observations_labs.json 等檔案。

### 檢查上傳的資料

**確認資料是否成功上傳：**

```powershell
cd sample_fhir_data
.\check-uploaded-data.ps1
```

腳本會檢查：
- Patient/patient-1007 是否存在
- ServiceRequest/exam-007 是否存在
- 使用 category=nuclear-medicine 過濾的 ServiceRequest 列表
- Patient/patient-1007 的所有 ServiceRequest

**上傳的資料規格：**
- **Patient ID**: patient-1007
- **Patient Name**: 王大明
- **ServiceRequest ID**: exam-007
- **檢查**: 骨骼掃描 (Tc-99m MDP)
- **Category**: 
  - SNOMED CT Code: `394649004` (Nuclear medicine)
  - Text: `核子醫學科`
  - 符合 TW Core IG 規範

如果工作清單中顯示的不是這些資料，請：
1. 執行檢查腳本確認資料是否已成功上傳
2. 如果資料不存在，重新執行上傳腳本
3. 如果資料存在但工作清單中看不到，檢查 ServiceRequest 的 category 是否使用正確的 SNOMED CT 代碼 `394649004`

### 方式二：使用其他腳本（進階使用）

**上傳單一 Patient 資源（僅用於測試編碼）：**

```powershell
cd sample_fhir_data
.\upload-patient.ps1
```

此腳本僅上傳 `patient_basic.json`，不包含臨床資料，**不推薦用於 Demo**。

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
# 1. 上傳 Patient（使用 PUT 方法，確保 UTF-8 編碼）
$patientJson = Get-Content -Path "patient_basic.json" -Raw -Encoding UTF8
$utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($patientJson)
Invoke-WebRequest -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" `
  -Method Put `
  -ContentType "application/fhir+json; charset=utf-8" `
  -Body $utf8Bytes

# 或使用專用腳本（推薦）
.\upload-patient.ps1

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

## 中文編碼問題解決方案

### 問題描述
如果上傳後查詢時發現中文變成亂碼，這是因為 PowerShell 的 `Invoke-RestMethod` 在發送請求時可能使用系統預設編碼（如 Big5），而不是 UTF-8。

### 解決方案

**方法一：使用修正後的上傳腳本（推薦）**

腳本已更新，會自動使用 UTF-8 編碼：

```powershell
.\upload-fhir-data.ps1
```

或使用單一 Patient 上傳腳本：

```powershell
.\upload-patient.ps1
```

**方法二：手動指定 UTF-8 編碼**

如果使用 PowerShell 手動上傳，請使用以下方式：

```powershell
# 讀取 JSON 檔案（使用 UTF-8）
$jsonContent = Get-Content -Path "patient_basic.json" -Raw -Encoding UTF8

# 轉換為 UTF-8 位元組陣列
$utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonContent)

# 使用 Invoke-WebRequest 並明確指定 UTF-8
Invoke-WebRequest -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" `
    -Method Put `
    -ContentType "application/fhir+json; charset=utf-8" `
    -Body $utf8Bytes
```

**方法三：使用 curl（Linux/macOS/Git Bash）**

curl 預設使用 UTF-8，不會有編碼問題：

```bash
curl -X PUT "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" \
  -H "Content-Type: application/fhir+json; charset=utf-8" \
  -d @patient_basic.json
```

### 驗證編碼

上傳後，使用查詢腳本驗證中文是否正確：

```powershell
.\query-patient.ps1
```

腳本會檢查：
- 病人姓名中的中文字元是否正確顯示
- 地址等中文欄位是否正常
- 完整 JSON 回應內容

## TW Core IG 規範

本專案遵循 [TW Core IG (臺灣核心實作指引)](https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition-ServiceRequest-twcore.html) 的規範。

### ServiceRequest Category 規範

根據 TW Core IG 規範，ServiceRequest 的 `category` 欄位應使用標準 SNOMED CT 代碼：

**核子醫學科（Nuclear medicine）**:
- **SNOMED CT Code**: `394649004`
- **對應 NHI 代碼**: `84` (核子醫學科)
- **Display**: `Nuclear medicine`
- **Text**: `核子醫學科` (建議使用中文)

**ServiceRequest category 範例格式**:

```json
{
  "category": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "394649004",
          "display": "Nuclear medicine"
        }
      ],
      "text": "核子醫學科"
    }
  ]
}
```

**參考資料**:
- [TW Core ServiceRequest Profile](https://twcore.mohw.gov.tw/ig/twcore/StructureDefinition-ServiceRequest-twcore.html)
- 核子醫學科對應：84 (核子醫學科) = 394649004 (Nuclear medicine)

### 查詢參數支援

根據 TW Core IG，系統支援以下查詢參數：
- `status`: 狀態過濾（如 `active`）
- `category`: 類別過濾（如 `nuclear-medicine` 或使用 SNOMED code）
- `patient`: 病人參考
- `authored`: 建立日期範圍

## 注意事項

1. **編碼問題**：所有 JSON 檔案必須使用 UTF-8 編碼儲存
2. **上傳前請確認 THAS 環境的存取權限**
3. 資源 ID 使用固定格式以便測試和追蹤
4. 所有日期時間使用 ISO 8601 格式
5. LOINC 代碼用於檢驗項目識別
6. ICD-10 代碼用於診斷碼
7. **ServiceRequest category** 必須使用標準 SNOMED CT 代碼（核子醫學：394649004）

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

