# 快速開始指南 - THAS 測試環境

本指南將幫助您快速設定並在 THAS (臺灣醫療資訊標準大平台) 上測試核醫藥物管理系統。

## 📋 目錄

- [系統需求](#系統需求)
- [安裝步驟](#安裝步驟)
- [Ngrok 設定](#ngrok-設定)
- [Docker Compose 設定](#docker-compose-設定)
- [THAS SAND-BOX 設定](#thas-sand-box-設定)
- [啟動應用程式](#啟動應用程式)
- [測試流程](#測試流程)
- [常見問題](#常見問題)

---

## 系統需求

- **Docker** 和 **Docker Compose** (已安裝並運行)
- **Node.js** 和 **npm** (用於前端開發模式)
- **Ngrok** (用於公開 URL，從 [ngrok.com](https://ngrok.com/) 下載)
- **THAS 帳號** (用於存取 SAND-BOX)

---

## 安裝步驟

### 1. 複製專案

```bash
git clone <repository-url>
cd NM_1225
```

### 2. 檢查 Docker 環境

```bash
docker --version
docker-compose --version
```

---

## Ngrok 設定

### 為什麼需要 Ngrok？

THAS SAND-BOX 要求 `redirect_uri` 必須是公開的 HTTPS URL，不接受 `localhost`。Ngrok 可以將本地服務暴露為公開 URL。

### 1. 安裝 Ngrok

從 [ngrok.com](https://ngrok.com/) 下載並安裝 ngrok。

**Windows:**
- 下載 `ngrok.exe` 並放到系統 PATH 中
- 或使用 Chocolatey: `choco install ngrok`

**macOS:**
```bash
brew install ngrok
```

**Linux:**
```bash
# 下載並解壓縮
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

### 2. 設定 Ngrok Authtoken

首次使用需要設定 authtoken：

```bash
ngrok config add-authtoken <YOUR_AUTHTOKEN>
```

Authtoken 可以在 [ngrok Dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) 取得。

### 3. 啟動 Ngrok

在專案根目錄執行：

```bash
ngrok http 5173
```

**輸出範例：**
```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxxx-xxxx.ngrok-free.dev -> http://localhost:5173
```

**重要：** 記下 `Forwarding` 中的 HTTPS URL，例如：
```
https://cgmh.ddns.net/fhir
```

### 4. 驗證 Ngrok 運行

開啟瀏覽器訪問 `http://localhost:4040` 查看 Ngrok Web 介面，可以監控所有請求。

---

## Docker Compose 設定

### 1. 檢查 docker-compose.thas.yml

確認 `docker-compose.thas.yml` 文件存在並包含正確的配置。

### 2. 設定環境變數

創建 `.env` 文件（可選，或直接在 docker-compose 中設定）：

```bash
# .env
NM_APP_MODE=production
NM_SMART_CLIENT_ID=你的_CLIENT_ID
NM_SMART_CLIENT_SECRET=你的_CLIENT_SECRET
NM_SMART_REDIRECT_URI=https://你的-ngrok-url.ngrok-free.dev/auth/callback
NM_SMART_AUTHORIZATION_ENDPOINT=THAS授權端點
NM_SMART_TOKEN_ENDPOINT=THAS_Token端點
```

**或者** 直接在 `docker-compose.thas.yml` 中更新 `NM_SMART_REDIRECT_URI`：

```yaml
- NM_SMART_REDIRECT_URI=${NM_SMART_REDIRECT_URI:-https://你的-ngrok-url.ngrok-free.dev/auth/callback}
```

### 3. 更新 Ngrok URL

如果您的 ngrok URL 改變了，需要更新 `docker-compose.thas.yml` 第 62 行：

```yaml
- NM_SMART_REDIRECT_URI=${NM_SMART_REDIRECT_URI:-https://新的-ngrok-url.ngrok-free.dev/auth/callback}
```

---

## THAS SAND-BOX 設定

### 1. 登入 THAS 平台

訪問 [THAS 平台](https://thas.mohw.gov.tw/) 並登入。

### 2. 進入 SAND-BOX

點擊導航欄中的 **"Sand box"**。

### 3. 選擇測試模式

在 SAND-BOX 對話框中：
- 選擇 **"EHR Launch"** 或 **"Provider Standalone Launch"**

### 4. 設定 Launch URL

在 **"請輸入網址"** (Launch URL) 欄位中，輸入：

```
https://你的-ngrok-url.ngrok-free.dev/auth/callback
```

**重要：** 此 URL 必須與 `docker-compose.thas.yml` 中的 `NM_SMART_REDIRECT_URI` **完全一致**。

### 5. 取得 FHIR Server URL

複製 **"FHIR Server URL"**，例如：
```
https://thas.mohw.gov.tw/v/r4/fhir
```

此 URL 會用於後續的 FHIR 資料同步。

### 6. 取得 SMART 設定

從 THAS 取得以下資訊（通常在 SAND-BOX 頁面或文件中有說明）：
- **Client ID**
- **Client Secret** (如果有)
- **Authorization Endpoint**
- **Token Endpoint**

這些資訊通常可以從 THAS 的 `.well-known/smart-configuration` 端點取得：
```
https://thas.mohw.gov.tw/.well-known/smart-configuration
```

### 7. 更新 docker-compose.thas.yml

將取得的資訊更新到環境變數中：

```yaml
- NM_SMART_CLIENT_ID=從THAS取得的CLIENT_ID
- NM_SMART_CLIENT_SECRET=從THAS取得的CLIENT_SECRET
- NM_SMART_AUTHORIZATION_ENDPOINT=從THAS取得的授權端點
- NM_SMART_TOKEN_ENDPOINT=從THAS取得的Token端點
```

---

## 啟動應用程式

### 1. 確保 Ngrok 正在運行

```bash
# 檢查 ngrok 是否運行
# 訪問 http://localhost:4040 確認
```

### 2. 啟動後端服務

```bash
docker-compose -f docker-compose.thas.yml up -d backend
```

### 3. 檢查後端狀態

```bash
docker-compose -f docker-compose.thas.yml logs backend --tail 20
```

應該看到：
```
[OutboxWorker] Started (polling every 10.0s)
[FHIRSyncWorker] Started (polling every 60.0s)
INFO:     Application startup complete.
```

### 4. 啟動前端服務

**選項 A：使用開發模式（推薦，便於調試）**

```bash
cd frontend
npm install  # 首次執行需要
npm run dev
```

前端將運行在 `http://localhost:5173`

**注意：** 如果修改了前端程式碼，開發模式會自動重新編譯（Hot Module Replacement）。如果沒有看到更新：
1. 檢查終端機是否有編譯錯誤
2. 強制重新整理瀏覽器（Ctrl+Shift+R 或 Cmd+Shift+R）
3. 清除瀏覽器快取

**選項 B：使用 Docker 容器**

```bash
# 如果修改了前端程式碼，需要重新建置容器
docker-compose -f docker-compose.thas.yml build frontend
docker-compose -f docker-compose.thas.yml up -d frontend

# 或使用 --build 參數一次完成
docker-compose -f docker-compose.thas.yml up -d --build frontend
```

**重要：** 如果使用 Docker 且修改了前端程式碼，必須重新建置容器才能看到更新！

### 5. 驗證服務運行

- **後端 API**: http://localhost:8000/api/docs
- **前端應用**: http://localhost:5173
- **Ngrok URL**: https://你的-ngrok-url.ngrok-free.dev

---

## 測試流程

### 1. 上傳 FHIR 測試資料（推薦）

為了測試完整的臨床資料功能（就醫紀錄、檢驗資料、過敏史等），建議先上傳範例 FHIR 資料到 THAS FHIR Server。

#### 方法一：使用完整 Bundle（推薦）

專案中已準備好完整的 FHIR Bundle 範例資料，位於 `sample_fhir_data/` 資料夾：

**使用 PowerShell 腳本（Windows 最簡單）：**

```powershell
# 進入專案根目錄
cd NM_1225

# 執行上傳腳本
cd sample_fhir_data
.\upload-fhir-data.ps1
```

腳本會自動處理所有上傳流程並顯示結果。

**使用 curl 上傳（Linux/macOS/Git Bash）：**

```bash
# 進入專案根目錄
cd NM_1225

# 上傳完整 Bundle（包含所有臨床資料）
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/patient_complete_bundle.json
```

**使用 PowerShell 上傳（Windows）：**

```powershell
# 進入專案根目錄
cd NM_1225

# 方法 1: 使用 Invoke-RestMethod（推薦）
$jsonContent = Get-Content -Path "sample_fhir_data\patient_complete_bundle.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $jsonContent

# 方法 2: 使用真正的 curl.exe（如果已安裝）
curl.exe -X POST "https://thas.mohw.gov.tw/v/r4/fhir" `
  -H "Content-Type: application/fhir+json" `
  -d "@sample_fhir_data\patient_complete_bundle.json"
```

**使用 Postman 上傳：**

1. 開啟 Postman
2. 建立新的 POST 請求
3. URL: `https://thas.mohw.gov.tw/v/r4/fhir`
4. Headers: `Content-Type: application/fhir+json`
5. Body: 選擇 "raw" 和 "JSON"，貼上 `patient_complete_bundle.json` 的內容

**範例資料包含：**
- ✅ Patient 資源（病人基本資料）
- ✅ 3 筆 Encounter（就醫紀錄：門診、急診、住院）
- ✅ 4 筆 Condition（診斷/病史：甲狀腺結節、高血壓、糖尿病前期、骨質疏鬆）
- ✅ 2 筆 AllergyIntolerance（過敏：Penicillin、碘顯影劑）
- ✅ 12 筆 Observation（檢驗資料：腎功能、肝功能、甲狀腺、血液）
- ✅ 3 筆 MedicationStatement（用藥紀錄）
- ✅ 2 筆 Procedure（處置紀錄）
- ✅ 1 筆 ServiceRequest（核醫檢查申請）

#### 方法二：個別上傳資源

如果需要個別上傳，可以使用 `sample_fhir_data/` 資料夾中的個別檔案：

**使用 curl（Linux/macOS/Git Bash）：**

```bash
# 上傳病人基本資料
curl -X PUT "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/patient_basic.json

# 上傳就醫紀錄
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/encounters.json

# 上傳檢驗資料
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/observations_labs.json

# 上傳過敏史
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/allergies.json

# 上傳診斷/病史
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/conditions.json

# 上傳用藥紀錄
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/medications.json

# 上傳處置紀錄
curl -X POST "https://thas.mohw.gov.tw/v/r4/fhir" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/procedures.json

# 上傳核醫檢查申請
curl -X PUT "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/service_request.json
```

**使用 PowerShell（Windows）：**

```powershell
# 上傳病人基本資料
$patientJson = Get-Content -Path "sample_fhir_data\patient_basic.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" `
  -Method Put `
  -ContentType "application/fhir+json" `
  -Body $patientJson

# 上傳就醫紀錄
$encountersJson = Get-Content -Path "sample_fhir_data\encounters.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $encountersJson

# 上傳檢驗資料
$labsJson = Get-Content -Path "sample_fhir_data\observations_labs.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $labsJson

# 上傳過敏史
$allergiesJson = Get-Content -Path "sample_fhir_data\allergies.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $allergiesJson

# 上傳診斷/病史
$conditionsJson = Get-Content -Path "sample_fhir_data\conditions.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $conditionsJson

# 上傳用藥紀錄
$medicationsJson = Get-Content -Path "sample_fhir_data\medications.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $medicationsJson

# 上傳處置紀錄
$proceduresJson = Get-Content -Path "sample_fhir_data\procedures.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $proceduresJson

# 上傳核醫檢查申請
$serviceRequestJson = Get-Content -Path "sample_fhir_data\service_request.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007" `
  -Method Put `
  -ContentType "application/fhir+json" `
  -Body $serviceRequestJson
```

#### 驗證資料上傳成功

上傳後可以查詢確認：

**使用 curl（Linux/macOS/Git Bash）：**

```bash
# 查詢病人資料
curl "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007"

# 查詢 ServiceRequest
curl "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007"

# 查詢檢驗資料
curl "https://thas.mohw.gov.tw/v/r4/fhir/Observation?patient=patient-1007&category=laboratory"
```

**使用 PowerShell（Windows）：**

```powershell
# 查詢病人資料
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" | ConvertTo-Json -Depth 10

# 查詢 ServiceRequest
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007" | ConvertTo-Json -Depth 10

# 查詢檢驗資料
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Observation?patient=patient-1007&category=laboratory" | ConvertTo-Json -Depth 10
```

**注意事項：**
- 如果資源已存在，使用 `PUT` 方法會覆蓋現有資料
- 使用 `POST` 方法會建立新資源（如果 ID 衝突會失敗）
- 建議先上傳 Patient，再上傳其他相關資源
- 詳細說明請參考 `sample_fhir_data/README.md`

### 2. 同步 ServiceRequest 到工作清單

上傳 FHIR 資料後，需要觸發同步將 `ServiceRequest` 轉換為系統中的案件：

**方法一：使用 API 端點（推薦）**

```bash
# 使用 curl
curl -X POST "http://localhost:8000/api/nm/sync-worklist" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**方法二：使用前端介面**

1. 登入應用程式
2. 訪問 `/analytics/sync-logs` 頁面
3. 點擊「同步工作清單」按鈕（如果有提供）

**方法三：等待自動同步**

系統會每 60 秒自動同步一次（如果後端 Worker 正在運行）。

**驗證同步成功：**

同步後，您應該能在核醫工作清單中看到新案件：
- 訪問 `/nm/worklist`
- 應該能看到引用 `Patient/patient-1007` 和 `ServiceRequest/exam-007` 的案件

### 3. 從 THAS SAND-BOX 啟動（可選）

1. 在 THAS SAND-BOX 頁面點擊 **"完成"** 按鈕
2. 系統會重定向到您的應用程式
3. 如果這是首次登入，系統會自動建立使用者帳號（狀態為 PENDING）

### 4. 管理員審核使用者（重要）

如果從 THAS SAND-BOX 登入的使用者狀態為 PENDING，需要管理員審核：

#### 步驟 1：使用管理員帳號登入

在 Production Mode 下，即使啟用了 SMART 登入，您仍然可以使用 Demo 登入來管理帳號：

1. **訪問登入頁面**: `http://localhost:5173/login` 或您的 ngrok URL
2. **使用 Demo 登入表單**（在 SMART 登入按鈕下方）
3. **輸入管理員資訊**:
   - **使用者識別碼**: `admin` 或 `admin123`
   - **操作角色**: 選擇「系統管理員」
4. **點擊「Demo 登入」按鈕**

**注意：**
- 在 Production Mode 下，Demo 登入表單仍然可用（用於管理目的）
- 系統會自動建立管理員帳號（如果不存在）
- 管理員帳號狀態為 ACTIVE，可以立即使用

#### 步驟 2：審核並指派角色

1. 登入後，系統會自動導向 `/admin/users` 頁面
2. 在「待審核使用者」區塊中，找到狀態為 PENDING 的使用者
3. 點擊「審核」按鈕
4. 選擇允許的角色（例如：`NM_PHYSICIAN`、`PHARMACIST`）
5. 點擊「啟用帳號」

#### 步驟 3：使用者重新登入

審核完成後，使用者可以：
1. 返回登入頁面
2. 再次透過 THAS SAND-BOX 登入
3. 或使用 Demo 登入（如果已指派角色）

**快速檢查：**
- 確認後端正在運行
- 確認可以訪問 `http://localhost:8000/api/docs` 查看 API 文檔
- 如果無法登入，檢查後端日誌：`docker-compose -f docker-compose.thas.yml logs backend`

### 5. 測試功能

#### 基本功能
- **核醫工作清單**: `/nm/worklist` - 查看待處理的核醫案件
- **藥師工作清單**: `/pharmacy/worklist` - 查看待審查的案件
- **分析儀表板**: `/analytics` - 查看統計分析
- **FHIR 同步記錄**: `/analytics/sync-logs` - 查看 FHIR 同步狀態

#### 臨床資料功能（新功能）

**測試步驟：**

1. **進入核醫工作清單**
   - 訪問 `/nm/worklist`
   - 找到引用 `Patient/patient-1007` 的案件（如果已同步）

2. **進入案件詳情**
   - 點擊案件進入詳情頁面
   - 或直接訪問 `/case/{caseId}`（從工作清單取得 caseId）

3. **查看臨床資料**
   在「病人資訊」區塊下方，會顯示以下可折疊的面板：
   
   - **臨床紀錄** 📋
     - **就醫紀錄**：3 筆（門診、急診、住院）
     - **診斷/病史**：4 筆（甲狀腺結節、高血壓、糖尿病前期、骨質疏鬆）
     - **用藥紀錄**：3 筆（降血壓藥、胃藥、維生素D）
     - **處置紀錄**：2 筆（甲狀腺超音波、骨骼掃描）
   
   - **重要檢驗資料** 🧪
     - **腎功能**：Creatinine (1.1 mg/dL)、eGFR (78 mL/min/1.73m2)、BUN (18 mg/dL)
     - **肝功能**：AST (32 U/L)、ALT (28 U/L)、Bilirubin (0.8 mg/dL)
     - **甲狀腺功能**：TSH (2.5 mIU/L)、Free T4 (1.2 ng/dL)
     - **血液檢驗**：Hemoglobin (14.5 g/dL)、WBC (7.2 x10^3/uL)、Platelet (245 x10^3/uL)
     - 顯示數值、單位、參考範圍、異常標示
   
   - **過敏史** ⚠️
     - **Penicillin**：高危過敏（皮疹、呼吸困難）
     - **碘顯影劑**：低危過敏（蕁麻疹）

4. **驗證資料正確性**
   - 確認所有資料都正確顯示
   - 檢查日期格式是否正確
   - 驗證數值與參考範圍是否對應

**如果沒有看到臨床資料：**

1. **檢查案件是否正確引用 Patient**
   - 確認案件的 `patient_ref` 為 `Patient/patient-1007`
   - 可以在案件詳情頁面頂部看到病人參考

2. **手動重新整理快照**
   - 在案件詳情頁面點擊右上角的「重新整理」按鈕
   - 這會強制從 FHIR Server 重新擷取所有臨床資料

3. **檢查後端連線**
   ```bash
   # 查看後端日誌
   docker-compose -f docker-compose.thas.yml logs backend | grep -i fhir
   
   # 或直接測試 FHIR 連線
   curl "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007"
   ```

4. **確認 FHIR Server URL 設定**
   - 檢查後端的 `FHIR_BASE_URL` 環境變數
   - 應該設定為 `https://thas.mohw.gov.tw/v/r4/fhir`

---

## 常見問題

### Q1: Ngrok URL 每次啟動都不同？

**A:** 這是 ngrok 免費版的限制。解決方案：
1. 每次啟動 ngrok 後，更新 `docker-compose.thas.yml` 中的 `NM_SMART_REDIRECT_URI`
2. 同時更新 THAS SAND-BOX 中的 Launch URL
3. 重新啟動後端容器：`docker-compose -f docker-compose.thas.yml restart backend`
4. 或升級到 ngrok 付費版以使用固定域名

### Q2: 出現 "Token exchange failed" 錯誤？

**A:** 檢查以下項目：
1. **Redirect URI 不匹配**: 確認 THAS SAND-BOX 的 Launch URL 與 `NM_SMART_REDIRECT_URI` 完全一致
2. **Client ID/Secret 錯誤**: 確認環境變數中的 CLIENT_ID 和 CLIENT_SECRET 正確
3. **Token Endpoint 錯誤**: 確認 `NM_SMART_TOKEN_ENDPOINT` 設定正確
4. **Ngrok 未運行**: 確認 ngrok 正在運行並轉發到正確的端口

### Q3: 前端顯示 "User not found"？

**A:** 這表示認證失敗。可能原因：
1. 後端未正確處理 SMART callback
2. Token exchange 失敗（見 Q2）
3. 檢查後端日誌：`docker-compose -f docker-compose.thas.yml logs backend`

### Q3a: 從 THAS 登入後顯示「帳號待審核」，但無法使用 admin 登入？

**A:** 在 Production Mode 下，您仍然可以使用 Demo 登入來管理帳號：

1. **確認登入頁面顯示 Demo 登入表單**
   - 在 SMART 登入按鈕下方應該有「或使用 Demo 登入」分隔線
   - 下方有 Demo 登入表單

2. **使用正確的管理員帳號**
   - 使用者識別碼：`admin` 或 `admin123`
   - 操作角色：選擇「系統管理員」
   - 點擊「Demo 登入」

3. **如果仍然無法登入**
   - 檢查後端是否正在運行
   - 檢查後端日誌是否有錯誤
   - 確認後端環境變數 `NM_APP_MODE` 設定正確

4. **替代方案：直接使用 API**
   如果前端登入有問題，可以直接使用 API 審核帳號：
   ```bash
   # 使用 curl（需要先取得管理員 token 或使用 Header）
   curl -X PUT "http://localhost:8000/api/admin/users/{userId}/approve" \
     -H "X-Subject: admin" \
     -H "X-Acting-Role: ADMIN" \
     -H "Content-Type: application/json" \
     -d '{"allowed_roles": ["NM_PHYSICIAN"]}'
   ```

### Q4: 如何查看後端日誌？

```bash
# 查看所有日誌
docker-compose -f docker-compose.thas.yml logs backend

# 查看最新 50 行
docker-compose -f docker-compose.thas.yml logs backend --tail 50

# 即時追蹤日誌
docker-compose -f docker-compose.thas.yml logs -f backend
```

### Q5: 如何重新啟動服務？

**重新啟動（不重新建置）：**
```bash
# 重新啟動後端
docker-compose -f docker-compose.thas.yml restart backend

# 重新啟動所有服務
docker-compose -f docker-compose.thas.yml restart
```

**完全重新建置（修改程式碼後需要）：**
```bash
# 停止並重新建置所有服務
docker-compose -f docker-compose.thas.yml down
docker-compose -f docker-compose.thas.yml build --no-cache
docker-compose -f docker-compose.thas.yml up -d
```

**使用 PowerShell 腳本（推薦）：**
```powershell
# 執行重新建置腳本
.\rebuild-thas.ps1
```

**只重新建置前端（如果只修改前端程式碼）：**
```bash
docker-compose -f docker-compose.thas.yml build frontend
docker-compose -f docker-compose.thas.yml up -d frontend
```

**只重新建置後端（如果只修改後端程式碼）：**
```bash
docker-compose -f docker-compose.thas.yml build backend
docker-compose -f docker-compose.thas.yml up -d backend
```

### Q6: Ngrok 配置檔版本錯誤？

如果看到 `unknown version '3'` 錯誤：

1. 檢查 ngrok 配置檔位置：
   - Windows: `%LOCALAPPDATA%\ngrok\ngrok.yml`
   - macOS/Linux: `~/.ngrok2/ngrok.yml`

2. 更新配置檔版本：
   ```yaml
   version: "2"
   authtoken: 你的_AUTHTOKEN
   ```

3. 或更新 ngrok 到最新版本：
   ```bash
   ngrok update
   ```

### Q7: Vite 顯示 "Blocked request"？

**A:** 需要在 `frontend/vite.config.ts` 中允許 ngrok 主機：

```typescript
export default defineConfig({
  server: {
    port: 5173,
    host: true, // 允許外部主機訪問
    allowedHosts: [
      'localhost',
      '.ngrok.io',
      '.ngrok-free.dev',
      '.ngrok.app',
    ],
  },
})
```

然後重新啟動前端服務。

### Q8: 如何確認環境變數是否正確設定？

```bash
# 進入後端容器
docker-compose -f docker-compose.thas.yml exec backend bash

# 查看環境變數
env | grep NM_SMART
```

### Q9: 在 PowerShell 中使用 curl 出現錯誤？

**A:** PowerShell 中的 `curl` 是 `Invoke-WebRequest` 的別名，不支援 curl 的參數。解決方案：

**方法 1：使用 Invoke-RestMethod（推薦）**
```powershell
$jsonContent = Get-Content -Path "sample_fhir_data\patient_complete_bundle.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir" `
  -Method Post `
  -ContentType "application/fhir+json" `
  -Body $jsonContent
```

**方法 2：使用真正的 curl.exe**
```powershell
# 明確指定使用 curl.exe（需要先安裝 curl）
curl.exe -X POST "https://thas.mohw.gov.tw/v/r4/fhir" `
  -H "Content-Type: application/fhir+json" `
  -d "@sample_fhir_data\patient_complete_bundle.json"
```

**方法 3：使用 Git Bash**
如果已安裝 Git for Windows，可以在 Git Bash 中使用標準的 curl 命令。

### Q10: 上傳 FHIR 資料時出現 401/403 錯誤？

**A:** 這表示認證失敗。可能原因：
1. **需要 THAS 認證**: 某些 THAS 環境需要先登入並取得授權 token
2. **檢查 THAS 文件**: 確認是否需要特殊的認證方式
3. **使用 Postman**: 在 Postman 中設定 Authorization header（如果 THAS 要求）

### Q10: 修改前端程式碼後看不到更新（例如新的臨床資料面板）？

**A:** 根據您使用的方式：

**如果使用開發模式（npm run dev）：**
1. 檢查終端機是否有編譯錯誤
2. 強制重新整理瀏覽器：`Ctrl+Shift+R` (Windows/Linux) 或 `Cmd+Shift+R` (Mac)
3. 清除瀏覽器快取
4. 如果還是不行，重新啟動前端服務：
   ```powershell
   # 停止前端（Ctrl+C）
   # 然後重新啟動
   cd frontend
   npm run dev
   ```

**如果使用 Docker：**
1. **必須重新建置前端容器**才能看到程式碼更新：
   ```powershell
   # 方法 1: 使用腳本（推薦）
   .\rebuild-frontend-thas.ps1
   
   # 方法 2: 手動執行
   docker-compose -f docker-compose.thas.yml stop frontend
   docker-compose -f docker-compose.thas.yml rm -f frontend
   docker-compose -f docker-compose.thas.yml build --no-cache frontend
   docker-compose -f docker-compose.thas.yml up -d frontend
   ```
2. **重要：如果端口 5173 被佔用（例如正在運行 npm run dev），需要先停止開發模式**
3. 清除瀏覽器快取並強制重新整理（`Ctrl+Shift+R`）
4. 檢查容器日誌確認沒有錯誤：
   ```bash
   docker-compose -f docker-compose.thas.yml logs frontend
   ```

**驗證新功能是否載入：**
- 打開瀏覽器開發者工具（F12）
- 查看 Console 是否有錯誤
- 檢查 Network 標籤，確認載入的 JavaScript 檔案是最新的（查看檔案修改時間）
- 確認進入案件詳情頁面後，在「病人資訊」卡片下方看到臨床資料面板

**如果仍然看不到臨床資料面板：**
1. 確認案件有對應的臨床資料（已上傳 FHIR 資料且 Patient ID 一致）
2. 點擊案件詳情頁面右上角的「重新整理」按鈕，強制重新載入資料
3. 檢查後端日誌確認 FHIR 查詢成功：
   ```bash
   docker-compose -f docker-compose.thas.yml logs backend | grep -i fhir
   ```

### Q11: 上傳後在案件詳情看不到臨床資料？

**A:** 檢查以下項目：
1. **Patient ID 是否一致**: 確認案件中的 `patient_ref` 與上傳的 Patient ID 一致
   - 例如：如果上傳的是 `Patient/patient-1007`，案件也應該引用 `Patient/patient-1007`
2. **重新整理快照**: 在案件詳情頁面點擊「重新整理」按鈕，強制從 FHIR Server 重新擷取資料
3. **檢查後端日誌**: 查看是否有 FHIR 查詢錯誤
   ```bash
   docker-compose -f docker-compose.thas.yml logs backend | grep -i fhir
   ```
4. **確認 FHIR Server URL**: 檢查後端設定的 `FHIR_BASE_URL` 是否正確
5. **驗證資料存在**: 直接查詢 FHIR Server 確認資料已上傳
   ```bash
   # Linux/macOS/Git Bash
   curl "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007"
   
   # PowerShell
   Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007"
   ```

### Q12: 如何更新或修改已上傳的 FHIR 資料？

**A:** 使用 `PUT` 方法更新現有資源：

**使用 curl（Linux/macOS/Git Bash）：**
```bash
# 更新病人資料
curl -X PUT "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" \
  -H "Content-Type: application/fhir+json" \
  -d @sample_fhir_data/patient_basic.json
```

**使用 PowerShell：**
```powershell
$jsonContent = Get-Content -Path "sample_fhir_data\patient_basic.json" -Raw -Encoding UTF8
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" `
  -Method Put `
  -ContentType "application/fhir+json" `
  -Body $jsonContent
```

**注意：** `PUT` 會完全覆蓋現有資源，請確保提供完整的資源內容。

### Q13: 可以刪除已上傳的 FHIR 資料嗎？

**A:** 可以，使用 `DELETE` 方法：

**使用 curl（Linux/macOS/Git Bash）：**
```bash
# 刪除特定資源
curl -X DELETE "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007"

# 刪除 ServiceRequest
curl -X DELETE "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007"
```

**使用 PowerShell：**
```powershell
# 刪除特定資源
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007" -Method Delete

# 刪除 ServiceRequest
Invoke-RestMethod -Uri "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007" -Method Delete
```

**注意：** 刪除資源前請確認不會影響其他相關資源（如 Observation、Condition 等）。

---

## 快速檢查清單

在開始測試前，確認以下項目：

### 基本設定
- [ ] Docker 和 Docker Compose 已安裝並運行
- [ ] Ngrok 已安裝並設定 authtoken
- [ ] Ngrok 正在運行並轉發到端口 5173
- [ ] 已記錄 ngrok URL（例如：`https://xxxx.ngrok-free.dev`）
- [ ] `docker-compose.thas.yml` 中的 `NM_SMART_REDIRECT_URI` 已更新為 ngrok URL
- [ ] THAS SAND-BOX 中的 Launch URL 已設定為相同的 ngrok URL
- [ ] 已從 THAS 取得並設定 CLIENT_ID、CLIENT_SECRET、授權端點、Token 端點
- [ ] 後端容器已啟動並運行正常
- [ ] 前端服務已啟動（開發模式或 Docker 容器）
- [ ] 可以訪問 http://localhost:5173 和 ngrok URL

### FHIR 測試資料（推薦）
- [ ] 已上傳 FHIR 測試資料到 THAS FHIR Server（使用 `sample_fhir_data/patient_complete_bundle.json`）
- [ ] 已驗證 Patient 資源存在（查詢 `Patient/patient-1007`）
- [ ] 已驗證 ServiceRequest 資源存在（查詢 `ServiceRequest/exam-007`）
- [ ] 已確認可以查詢到檢驗資料、過敏史等臨床資料

---

## 下一步

- 查看 [README.md](README.md) 了解完整的系統架構
- 查看 [NGROK_SETUP.md](NGROK_SETUP.md) 了解更詳細的 ngrok 設定
- 查看 API 文檔：http://localhost:8000/api/docs
- 查看 [sample_fhir_data/README.md](sample_fhir_data/README.md) 了解 FHIR 範例資料的詳細說明
- 上傳 FHIR 測試資料以測試完整的臨床資料功能

---

## 需要幫助？

如果遇到問題，請：
1. 檢查後端日誌：`docker-compose -f docker-compose.thas.yml logs backend`
2. 檢查前端控制台錯誤訊息
3. 確認所有環境變數設定正確
4. 確認 ngrok 和 THAS 設定一致

