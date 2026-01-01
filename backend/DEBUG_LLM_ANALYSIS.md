# LLM 分析除錯指南

當遇到「分析失敗：未知錯誤」時，可以按照以下步驟進行除錯。

## 1. 查看後端日誌

後端服務會將詳細的錯誤資訊記錄到日誌中。查看方式：

### 如果使用 Docker Compose
```bash
docker-compose logs -f backend | grep -i "llm\|error\|failed"
```

### 如果直接執行 Python
查看終端機輸出，錯誤會以 `ERROR` 級別記錄，包含完整的 traceback。

## 2. 使用除錯腳本查詢資料庫

我們提供了一個除錯腳本來查詢 LLM 分析記錄：

### 查看特定案件的分析記錄
```bash
cd backend
python debug_llm_analysis.py <case_id>
```

例如：
```bash
python debug_llm_analysis.py 74c6764b-1234-5678-9abc-def012345678
```

### 查看最近失敗的分析記錄
```bash
python debug_llm_analysis.py --recent 10
```

### 查看所有失敗的分析記錄
```bash
python debug_llm_analysis.py --failed
```

### 查看所有分析記錄（最近 20 筆）
```bash
python debug_llm_analysis.py --all
```

## 3. 常見錯誤類型與解決方法

### 連線超時
**錯誤訊息**: `連線超時（60秒）`

**可能原因**:
- LLM API 服務回應太慢
- 網路連線不穩定
- Payload 太大導致處理時間過長

**解決方法**:
1. 檢查 LLM API 服務是否正常運作
2. 在「系統設定」頁面增加 `timeout_seconds` 設定值
3. 檢查網路連線

### 網路連線錯誤
**錯誤訊息**: `網路連線錯誤: ...`

**可能原因**:
- LLM API endpoint URL 設定錯誤
- 無法連線到 LLM API 服務
- 防火牆或代理設定問題

**解決方法**:
1. 在「系統設定」頁面檢查 `endpoint_url` 是否正確
2. 使用「測試連線」功能驗證連線
3. 檢查防火牆設定

### HTTP 錯誤
**錯誤訊息**: `HTTP 401: ...` 或 `HTTP 403: ...` 等

**可能原因**:
- API Key 無效或過期
- 權限不足
- 請求格式錯誤

**解決方法**:
1. 檢查 API Key 是否正確設定
2. 確認 API Key 是否有足夠權限
3. 檢查 LLM API 服務的文件確認請求格式

### JSON 解析錯誤
**錯誤訊息**: `JSON 解析錯誤: ...`

**可能原因**:
- LLM 回應格式不符合預期
- LLM 回應包含非 JSON 內容（如 markdown 標記）

**解決方法**:
1. 檢查 LLM 回應的原始內容（使用除錯腳本）
2. 調整 System Prompt 或 User Prompt Template，明確要求 JSON 格式
3. 檢查 LLM 模型是否支援結構化輸出

### 其他例外
**錯誤訊息**: `TypeError: ...` 或 `ValueError: ...` 等

**可能原因**:
- 程式碼邏輯錯誤
- 資料格式不符合預期
- 依賴套件版本問題

**解決方法**:
1. 查看完整的 traceback（在日誌或除錯腳本中）
2. 檢查相關的資料格式
3. 更新依賴套件

## 4. 檢查資料庫記錄

如果無法使用除錯腳本，可以直接查詢資料庫：

```sql
-- 查看特定案件的分析記錄
SELECT * FROM llm_analyses 
WHERE case_id = '74c6764b-1234-5678-9abc-def012345678' 
ORDER BY created_at DESC;

-- 查看最近失敗的分析
SELECT case_id, status, error_message, created_at 
FROM llm_analyses 
WHERE status = 'FAILED' 
ORDER BY created_at DESC 
LIMIT 10;

-- 查看完整的錯誤訊息（可能很長）
SELECT id, case_id, error_message, raw_response, prompt_used
FROM llm_analyses 
WHERE status = 'FAILED' 
ORDER BY created_at DESC;
```

## 5. 檢查 LLM 設定

在「系統設定」頁面確認：

1. **Endpoint URL**: 是否正確指向 LLM API 服務
2. **API Key**: 是否正確設定
3. **Model Name**: 是否使用支援的模型
4. **Timeout**: 是否設定合理（建議至少 60 秒）
5. **Max Tokens**: 是否足夠（建議至少 4096）

## 6. 測試連線

在「系統設定」頁面使用「測試連線」功能，確認：
- 可以成功連線到 LLM API
- API Key 有效
- 模型名稱正確

## 7. 查看 Prompt 內容

如果分析失敗，可以查看實際使用的 Prompt：

```bash
python debug_llm_analysis.py <case_id>
```

腳本會顯示 `使用的 Prompt` 部分，可以：
1. 複製 Prompt 內容
2. 手動在 LLM API 測試工具中測試
3. 確認 Prompt 格式是否正確

## 8. 查看 LLM 原始回應

即使分析失敗，系統也會儲存 LLM 的原始回應（如果有收到）。使用除錯腳本可以查看：
- `LLM 原始回應`: 顯示 LLM 實際回傳的內容
- `解析結果`: 顯示解析後的 JSON（如果有）

## 9. 重新執行分析

在確認問題後，可以在前端頁面點擊「重新分析」按鈕，系統會：
1. 建立新的分析記錄
2. 重新呼叫 LLM API
3. 記錄新的錯誤訊息（如果仍然失敗）

## 10. 聯絡支援

如果以上方法都無法解決問題，請準備以下資訊：
1. 案件 ID
2. 分析記錄 ID（從除錯腳本取得）
3. 完整的錯誤訊息（從除錯腳本或資料庫取得）
4. LLM 設定資訊（不包含 API Key）
5. 後端日誌片段

