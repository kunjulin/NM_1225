# ServiceRequest Category 格式比較分析

## 差異對照表

### 成功的 6 個項目 (exam-001 到 exam-006)

```json
"category": [
    {
        "coding": [
            {
                "system": "http://example.org/exam-category",
                "code": "nuclear-medicine",        // ← 字串值
                "display": "核醫檢查"              // ← 中文顯示
            }
        ]
        // ← 沒有 text 欄位
    }
]
```

### 您上傳的 exam-007

```json
"category": [
    {
        "coding": [
            {
                "system": "http://snomed.info/sct",  // ← 不同
                "code": "363679005",                 // ← SNOMED code (數字)
                "display": "nuclear-medicine"        // ← 英文顯示
            }
        ],
        "text": "nuclear-medicine"                  // ← 有 text 欄位
    }
]
```

## 關鍵差異

| 欄位 | 成功的項目 | 您的 exam-007 | 說明 |
|------|-----------|--------------|------|
| `coding[].system` | `http://example.org/exam-category` | `http://snomed.info/sct` | **不同系統** |
| `coding[].code` | `"nuclear-medicine"` (字串) | `"363679005"` (SNOMED code) | **完全不同的值** |
| `coding[].display` | `"核醫檢查"` (中文) | `"nuclear-medicine"` (英文) | 不同 |
| `text` | **不存在** | `"nuclear-medicine"` | **結構差異** |

## 問題根源

當系統使用查詢參數 `category=nuclear-medicine` 時，FHIR Server 的查詢實現可能：

1. **優先匹配 `coding.code` 欄位**：成功的項目 `coding.code = "nuclear-medicine"`，可以直接匹配；您的項目 `coding.code = "363679005"`，無法匹配
2. **不匹配 `text` 欄位**：雖然您的資料有 `text: "nuclear-medicine"`，但查詢可能不匹配 text 欄位
3. **不匹配 `coding.display`**：即使 `display = "nuclear-medicine"`，也可能不匹配

## 解決方案

需要修改 exam-007 的 category 格式，使其與成功的項目格式一致：

```json
"category": [
    {
        "coding": [
            {
                "system": "http://example.org/exam-category",
                "code": "nuclear-medicine",
                "display": "核醫檢查"
            }
        ]
        // 移除 text 欄位
    }
]
```

