# 快速啟動指南 (不使用 Docker)

## 前置需求

- Python 3.11+
- Node.js 18+
- (選用) Docker - 僅用於啟動 HAPI FHIR Server

## 快速啟動

### Windows PowerShell

開啟**兩個終端機視窗**：

**終端機 1 - Backend:**
```powershell
.\start-backend.ps1
```

**終端機 2 - Frontend:**
```powershell
.\start-frontend.ps1
```

### Linux/Mac

開啟**兩個終端機視窗**：

**終端機 1 - Backend:**
```bash
./start-backend.sh
```

**終端機 2 - Frontend:**
```bash
./start-frontend.sh
```

## 服務端點

啟動成功後，可存取：

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/docs
- **健康檢查**: http://localhost:8000/api/health

## 建立測試資料

### 方法一：自動重置並添加範例資料（推薦）

在啟動 Backend 時使用 `-ResetAndSeed` 參數，會自動清除現有資料並添加範例資料：

**Windows PowerShell:**
```powershell
.\start-backend.ps1 -ResetAndSeed
```

**Linux/Mac:**
```bash
./start-backend.sh -ResetAndSeed
```

或者使用簡寫：
```powershell
.\start-backend.ps1 -reset
```

**說明：**
- 如果 Backend 已經在運行，會立即執行重置和種子，然後退出
- 如果 Backend 未運行，會啟動 Backend，並在背景自動等待 Backend 準備好後執行重置和種子

### 方法二：手動添加測試資料

啟動服務後，在**新的終端機**執行：

**PowerShell:**
```powershell
$headers = @{ 
    "X-Subject" = "demo-admin"
    "X-Acting-Role" = "ADMIN"
    "Content-Type" = "application/json"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/demo/seed" -Method Post -Headers $headers
```

**Bash/curl:**
```bash
curl -X POST http://localhost:8000/api/demo/seed \
  -H "Content-Type: application/json" \
  -H "X-Subject: demo-admin" \
  -H "X-Acting-Role: ADMIN"
```

### 重置資料庫並重新添加範例資料

如果需要清除所有資料並重新添加範例資料：

**PowerShell:**
```powershell
# 重置資料庫
$headers = @{
    "Content-Type" = "application/json"
    "X-Subject" = "demo-admin"
    "X-Acting-Role" = "ADMIN"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/demo/reset" -Method POST -Headers $headers

# 添加範例資料
$body = @{clearExisting = $true} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/demo/seed" -Method POST -Headers $headers -Body $body
```

**Bash/curl:**
```bash
# 重置資料庫
curl -X POST http://localhost:8000/api/demo/reset \
  -H "Content-Type: application/json" \
  -H "X-Subject: demo-admin" \
  -H "X-Acting-Role: ADMIN"

# 添加範例資料
curl -X POST http://localhost:8000/api/demo/seed \
  -H "Content-Type: application/json" \
  -H "X-Subject: demo-admin" \
  -H "X-Acting-Role: ADMIN" \
  -d '{"clearExisting": true}'
```

## 連接 THAS 臺灣50競賽環境

### 方法一：修改環境變數

**PowerShell:**
```powershell
$env:NM_FHIR_SERVER_TYPE="thas"
# 然後重新啟動 Backend
```

**Bash:**
```bash
export NM_FHIR_SERVER_TYPE=thas
# 然後重新啟動 Backend
```

### 方法二：修改 .env 檔案

編輯 `backend/.env` 檔案：
```
NM_FHIR_SERVER_TYPE=thas
```

然後重新啟動 Backend 服務。

## 使用 Local HAPI FHIR Server

如果需要使用本地 HAPI FHIR Server，請先啟動：

```bash
# 使用 Docker
docker run -d \
  --name hapi-fhir \
  -p 8080:8080 \
  -e hapi.fhir.default_encoding=json \
  -e hapi.fhir.fhir_version=R4 \
  -e hapi.fhir.allow_external_references=true \
  -e hapi.fhir.cors.allowed_origin=* \
  hapiproject/hapi:latest
```

確保 `backend/.env` 中設定：
```
NM_FHIR_SERVER_TYPE=local
NM_FHIR_LOCAL_BASE_URL=http://localhost:8080/fhir
```

## 疑難排解

### Backend 無法啟動

1. 確認 Python 版本：`python --version` (應為 3.11+)
2. 確認虛擬環境已啟動
3. 確認依賴已安裝：`pip list | grep fastapi`
4. 檢查連接埠 8000 是否被占用

### Frontend 無法啟動

1. 確認 Node.js 版本：`node --version` (應為 18+)
2. 確認依賴已安裝：`ls node_modules`
3. 檢查連接埠 5173 是否被占用

### 無法連接 FHIR Server

1. 確認 FHIR Server 類型設定正確
2. 檢查 FHIR Server URL 是否可存取
3. 查看 Backend 日誌中的錯誤訊息

## 停止服務

在各自的終端機視窗按 `Ctrl+C` 停止服務。

