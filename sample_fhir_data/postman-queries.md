# Postman 查詢範例 - FHIR Server ServiceRequest 查詢

## 基本資訊

- **FHIR Server URL**: `https://thas.mohw.gov.tw/v/r4/fhir`
- **Headers**: 
  - `Accept: application/fhir+json`
  - `Content-Type: application/fhir+json` (POST/PUT 時需要)

---

## 1. 查詢您上傳的 ServiceRequest (exam-007)

**Method**: `GET`

**URL**: 
```
https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007
```

**Headers**:
```
Accept: application/fhir+json
```

**說明**: 
- 直接查詢特定 ID 的 ServiceRequest
- 如果找不到會回傳 404
- 如果找到，檢查 `category` 欄位的格式

---

## 2. 查詢所有 category=nuclear-medicine 的 ServiceRequest

**Method**: `GET`

**URL**: 
```
https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest?status=active&category=nuclear-medicine
```

**Headers**:
```
Accept: application/fhir+json
```

**說明**: 
- 這是最重要的查詢，因為系統同步時使用此查詢參數
- 查看結果中是否包含 `exam-007`
- 比較其他成功項目的 `category` 格式

**預期結果格式**:
```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "entry": [
    {
      "resource": {
        "resourceType": "ServiceRequest",
        "id": "exam-007",
        "category": [...],
        ...
      }
    }
  ]
}
```

---

## 3. 查詢所有 active 的 ServiceRequest（不篩選 category）

**Method**: `GET`

**URL**: 
```
https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest?status=active
```

**Headers**:
```
Accept: application/fhir+json
```

**說明**: 
- 查看所有 active 的 ServiceRequest
- 檢查 `exam-007` 是否存在
- 比較其他項目的 `category` 格式

---

## 4. 查詢特定 Patient 的所有 ServiceRequest

**Method**: `GET`

**URL**: 
```
https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest?status=active&subject=Patient/patient-1007
```

**Headers**:
```
Accept: application/fhir+json
```

**說明**: 
- 查詢 patient-1007 的所有 ServiceRequest
- 確認資料是否已成功上傳
- 檢查 category 格式

---

## 5. 查詢 Patient (patient-1007)

**Method**: `GET`

**URL**: 
```
https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007
```

**Headers**:
```
Accept: application/fhir+json
```

**說明**: 
- 確認 Patient 是否已成功上傳
- 這是上傳資料的基礎

---

## 比較重點

### 需要比較的欄位

在查詢結果中，特別注意比較 `category` 欄位：

**您上傳的格式 (exam-007)**:
```json
{
  "category": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "363679005",
          "display": "nuclear-medicine"
        }
      ],
      "text": "nuclear-medicine"
    }
  ]
}
```

**成功同步的 6 個項目可能有的格式** (需要實際查詢確認):
- `category[].text` 的值
- `category[].coding[].display` 的值
- `category[].coding[].code` 的值
- 是否有其他欄位差異

---

## Postman Collection JSON (可匯入)

將以下內容儲存為 `.json` 檔案，可在 Postman 中匯入：

```json
{
  "info": {
    "name": "FHIR ServiceRequest Queries",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get ServiceRequest exam-007",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Accept",
            "value": "application/fhir+json"
          }
        ],
        "url": {
          "raw": "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest/exam-007",
          "protocol": "https",
          "host": ["thas", "mohw", "gov", "tw"],
          "path": ["v", "r4", "fhir", "ServiceRequest", "exam-007"]
        }
      }
    },
    {
      "name": "Search ServiceRequest by category=nuclear-medicine",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Accept",
            "value": "application/fhir+json"
          }
        ],
        "url": {
          "raw": "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest?status=active&category=nuclear-medicine",
          "protocol": "https",
          "host": ["thas", "mohw", "gov", "tw"],
          "path": ["v", "r4", "fhir", "ServiceRequest"],
          "query": [
            {
              "key": "status",
              "value": "active"
            },
            {
              "key": "category",
              "value": "nuclear-medicine"
            }
          ]
        }
      }
    },
    {
      "name": "Search all active ServiceRequest",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Accept",
            "value": "application/fhir+json"
          }
        ],
        "url": {
          "raw": "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest?status=active",
          "protocol": "https",
          "host": ["thas", "mohw", "gov", "tw"],
          "path": ["v", "r4", "fhir", "ServiceRequest"],
          "query": [
            {
              "key": "status",
              "value": "active"
            }
          ]
        }
      }
    },
    {
      "name": "Search ServiceRequest by Patient",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Accept",
            "value": "application/fhir+json"
          }
        ],
        "url": {
          "raw": "https://thas.mohw.gov.tw/v/r4/fhir/ServiceRequest?status=active&subject=Patient/patient-1007",
          "protocol": "https",
          "host": ["thas", "mohw", "gov", "tw"],
          "path": ["v", "r4", "fhir", "ServiceRequest"],
          "query": [
            {
              "key": "status",
              "value": "active"
            },
            {
              "key": "subject",
              "value": "Patient/patient-1007"
            }
          ]
        }
      }
    },
    {
      "name": "Get Patient patient-1007",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Accept",
            "value": "application/fhir+json"
          }
        ],
        "url": {
          "raw": "https://thas.mohw.gov.tw/v/r4/fhir/Patient/patient-1007",
          "protocol": "https",
          "host": ["thas", "mohw", "gov", "tw"],
          "path": ["v", "r4", "fhir", "Patient", "patient-1007"]
        }
      }
    }
  ]
}
```

---

## 使用步驟

1. **匯入 Collection** (選用):
   - 在 Postman 點擊 Import
   - 選擇上面的 JSON 內容建立檔案並匯入

2. **或手動建立請求**:
   - 使用上面的 URL 和 Method
   - 設定 Headers: `Accept: application/fhir+json`

3. **執行查詢並比較**:
   - 先執行「Get ServiceRequest exam-007」確認資料是否存在
   - 執行「Search ServiceRequest by category=nuclear-medicine」查看能查詢到的項目
   - 比較 exam-007 和其他成功項目的 `category` 欄位格式

4. **重點檢查項目**:
   - exam-007 的 `category[].text` 值
   - exam-007 的 `category[].coding[].display` 值
   - 其他成功項目的相同欄位值
   - 是否有結構上的差異（例如欄位順序、額外欄位等）

---

## 預期發現

如果 exam-007 存在但不在 category=nuclear-medicine 查詢結果中，可能的原因：

1. **category.text 值不同**: 雖然 JSON 中寫的是 "nuclear-medicine"，但 FHIR Server 可能儲存為其他值
2. **category.coding.display 值不同**: 同上
3. **FHIR Server 查詢實現差異**: 某些 FHIR Server 可能只匹配 coding.code 而不匹配 text/display
4. **大小寫敏感**: 某些實現可能對大小寫敏感



