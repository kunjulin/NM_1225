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
https://clint-inexpert-mesmerizingly.ngrok-free.dev
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

### 4. 啟動前端服務（開發模式）

**選項 A：使用開發模式（推薦，便於調試）**

```bash
cd frontend
npm install  # 首次執行需要
npm run dev
```

前端將運行在 `http://localhost:5173`

**選項 B：使用 Docker 容器**

```bash
docker-compose -f docker-compose.thas.yml up -d frontend
```

### 5. 驗證服務運行

- **後端 API**: http://localhost:8000/api/docs
- **前端應用**: http://localhost:5173
- **Ngrok URL**: https://你的-ngrok-url.ngrok-free.dev

---

## 測試流程

### 1. 準備測試資料（可選）

使用 Postman 或其他工具將測試資料匯入 THAS FHIR Server：

```
POST https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest
Content-Type: application/fhir+json

{
  "resourceType": "ServiceRequest",
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "363679005",
      "display": "核醫檢查"
    }]
  }],
  ...
}
```

### 2. 從 THAS SAND-BOX 啟動

1. 在 THAS SAND-BOX 頁面點擊 **"完成"** 按鈕
2. 系統會重定向到您的應用程式
3. 如果這是首次登入，系統會自動建立使用者帳號（狀態為 PENDING）

### 3. 管理員審核使用者（如果需要）

如果使用者狀態為 PENDING，需要管理員審核：

1. 使用管理員帳號登入
2. 訪問 `/admin/users` 頁面
3. 審核並指派角色給新使用者

### 4. 測試功能

- **核醫工作清單**: `/nm/worklist`
- **藥師工作清單**: `/pharmacy/worklist`
- **分析儀表板**: `/analytics`
- **FHIR 同步記錄**: `/analytics/sync-logs`

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

```bash
# 重新啟動後端
docker-compose -f docker-compose.thas.yml restart backend

# 重新啟動所有服務
docker-compose -f docker-compose.thas.yml restart

# 完全停止並重新啟動
docker-compose -f docker-compose.thas.yml down
docker-compose -f docker-compose.thas.yml up -d
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

---

## 快速檢查清單

在開始測試前，確認以下項目：

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

---

## 下一步

- 查看 [README.md](README.md) 了解完整的系統架構
- 查看 [NGROK_SETUP.md](NGROK_SETUP.md) 了解更詳細的 ngrok 設定
- 查看 API 文檔：http://localhost:8000/api/docs

---

## 需要幫助？

如果遇到問題，請：
1. 檢查後端日誌：`docker-compose -f docker-compose.thas.yml logs backend`
2. 檢查前端控制台錯誤訊息
3. 確認所有環境變數設定正確
4. 確認 ngrok 和 THAS 設定一致

