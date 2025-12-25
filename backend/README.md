# NM SMART on FHIR Medication Stewardship - Backend

核子醫學放射藥物用藥治理系統後端服務

## 技術堆疊

- **語言**: Python 3.11+
- **框架**: FastAPI
- **資料庫**: SQLite (via SQLAlchemy 2.x async)
- **HTTP Client**: httpx
- **驗證**: Pydantic

## 快速開始

### 1. 建立虛擬環境

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 根據需要修改設定
```

### 4. 啟動服務

```bash
# 開發模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Python 直接執行
python -m app.main
```

### 5. 存取 API 文件

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `NM_APP_MODE` | 應用程式模式 (production/demo) | demo |
| `NM_DEBUG` | Debug 模式 | false |
| `NM_DATABASE_URL` | 資料庫 URL | sqlite:///./nm_stewardship.db |
| `NM_FHIR_SERVER_TYPE` | FHIR Server 類型 (local/thas) | local |
| `NM_FHIR_LOCAL_BASE_URL` | Local FHIR Server URL | http://localhost:8080/fhir |
| `NM_FHIR_THAS_BASE_URL` | THAS 競賽環境 URL | (見 .env.example) |

## API 端點

### NM Physician (核醫醫師)

- `GET /api/nm/worklist` - 取得工作清單
- `POST /api/nm/cases/{caseId}/draft` - 建立/更新草案
- `POST /api/nm/cases/{caseId}/submit` - 送審
- `POST /api/nm/cases/{caseId}/respond` - 回應退回

### Pharmacy (藥師)

- `GET /api/pharmacy/worklist` - 取得工作清單
- `POST /api/pharmacy/cases/{caseId}/claim` - Claim 案件
- `POST /api/pharmacy/cases/{caseId}/approve` - 核准
- `POST /api/pharmacy/cases/{caseId}/return` - 退回
- `POST /api/pharmacy/bulk-approve` - 批次核准

### Cases (案件)

- `GET /api/cases/{caseId}/snapshot` - 取得病人快照
- `POST /api/cases/{caseId}/autofill/accept` - 接受自動填入
- `POST /api/cases/{caseId}/autofill/reject` - 拒絕自動填入

### Analytics (分析)

- `GET /api/analytics/summary` - KPI 摘要
- `GET /api/analytics/autofill/summary` - Auto-fill 統計

### Demo Mode

- `GET /api/demo/whoami` - 當前身份
- `POST /api/demo/set-acting-role` - 切換角色
- `POST /api/demo/seed` - 建立示範資料
- `POST /api/demo/reset` - 重置資料

## 目錄結構

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 應用程式
│   ├── config.py         # 設定管理
│   ├── database.py       # 資料庫連線
│   ├── api/              # API 路由
│   │   ├── nm.py
│   │   ├── pharmacy.py
│   │   ├── cases.py
│   │   ├── analytics.py
│   │   └── demo.py
│   ├── models/           # SQLAlchemy 模型
│   │   ├── order_case.py
│   │   ├── review_event.py
│   │   └── outbox.py
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # 業務邏輯
│   ├── rules/            # 規則引擎
│   └── fhir/             # FHIR Client
├── tests/
├── rules_config.yaml     # 劑量規則設定
├── requirements.txt
└── .env.example
```

## 授權

MIT License

