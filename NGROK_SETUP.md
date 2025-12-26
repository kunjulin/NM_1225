# Ngrok 設定說明

## 何時需要 Ngrok？

如果 THAS 競賽平台要求 `redirect_uri` 必須是公開的 HTTPS URL（不接受 localhost），則需要使用 ngrok。

## 設定步驟

### 1. 安裝 Ngrok

從 [ngrok.com](https://ngrok.com/) 下載並安裝 ngrok。

### 2. 啟動 Ngrok

在終端機執行：

```bash
ngrok http 5173
```

這會產生一個公開 URL，例如：`https://xxxx-xxxx-xxxx.ngrok.io`

### 3. 更新 THAS SAND-BOX 設定

在 THAS SAND-BOX 的 Launch URL 設定中，使用 ngrok URL：

```
https://xxxx-xxxx-xxxx.ngrok.io/auth/callback
```

### 4. 更新環境變數

更新 `docker-compose.thas.yml` 或 `.env` 檔案：

```yaml
- NM_SMART_REDIRECT_URI=https://xxxx-xxxx-xxxx.ngrok.io/auth/callback
```

### 5. 重新啟動容器

```bash
docker-compose -f docker-compose.thas.yml restart backend
```

## 注意事項

- Ngrok 免費版每次啟動 URL 會改變，需要重新設定
- Ngrok 付費版可以設定固定域名
- 確保 ngrok 在應用程式運行期間保持開啟

## 替代方案

如果 THAS 接受 localhost，則不需要 ngrok，直接使用：

```
http://localhost:5173/auth/callback
```

