# NM SMART on FHIR Medication Stewardship System

核子醫學放射藥物用藥治理與臨床決策支援系統

## 專案概述

本系統為基於 FHIR R4、TW Core 與 SMART on FHIR 架構之核子醫學放射藥物用藥治理系統，提供：

- 核醫醫師用藥草案建立與送審
- 藥師工作清單與批次核准
- 臨床決策支援 (CDS) 規則引擎
- 病人快照與自動填入 (Auto-fill)
- KPI 統計分析儀表板
- Demo Mode 支援競賽展示

## 系統架構

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │
│  React + Vite   │     │    FastAPI      │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  SQLite  │ │   HAPI   │ │   THAS   │
              │   (本地)  │ │   FHIR   │ │  Server  │
              └──────────┘ └──────────┘ └──────────┘
```

## 快速開始

### 前置需求

- Python 3.11+
- Node.js 18+
- (選用) Docker - 用於執行 HAPI FHIR Server

### 1. 啟動 Backend

```bash
cd backend

# 建立虛擬環境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt

# 啟動服務
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API 文件：http://localhost:8000/api/docs

### 2. 啟動 Frontend

```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

Frontend：http://localhost:5173

### 3. 建立示範資料

```bash
# 使用 curl 或在 Frontend 登入後操作
curl -X POST http://localhost:8000/api/demo/seed \
  -H "Content-Type: application/json" \
  -H "X-Subject: demo-admin" \
  -H "X-Acting-Role: ADMIN"
```

## 目錄結構

```
NM_1225/
├── backend/               # FastAPI 後端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # 業務邏輯
│   │   ├── rules/        # 規則引擎
│   │   └── fhir/         # FHIR Client
│   ├── tests/            # 測試
│   └── requirements.txt
├── frontend/              # React 前端
│   ├── src/
│   │   ├── pages/        # 頁面元件
│   │   ├── components/   # 共用元件
│   │   ├── contexts/     # React Context
│   │   ├── hooks/        # Custom Hooks
│   │   ├── api/          # API Client
│   │   └── types/        # TypeScript 型別
│   └── package.json
├── spec/                  # 規格文件
└── README.md
```

## 環境設定

### Backend 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `NM_APP_MODE` | 執行模式 (production/demo) | demo |
| `NM_FHIR_SERVER_TYPE` | FHIR Server 類型 (local/thas) | local |
| `NM_FHIR_LOCAL_BASE_URL` | Local FHIR URL | http://localhost:8080/fhir |
| `NM_FHIR_THAS_BASE_URL` | THAS URL | (見 env.example.txt) |

### 切換至 THAS 競賽環境

```bash
# 設定環境變數
export NM_FHIR_SERVER_TYPE=thas
```

## 使用者角色

| 角色 | 說明 | 功能 |
|------|------|------|
| NM_PHYSICIAN | 核醫醫師 | 建立草案、送審、回應退回 |
| PHARMACIST | 藥師 | Claim、核准、退回、批次核准 |
| ADMIN | 管理員 | 全部功能 |

## API 端點

### NM Physician
- `GET /api/nm/worklist` - 工作清單
- `POST /api/nm/cases/{id}/draft` - 建立草案
- `POST /api/nm/cases/{id}/submit` - 送審
- `POST /api/nm/cases/{id}/respond` - 回應退回

### Pharmacy
- `GET /api/pharmacy/worklist` - 工作清單
- `POST /api/pharmacy/cases/{id}/claim` - Claim
- `POST /api/pharmacy/cases/{id}/approve` - 核准
- `POST /api/pharmacy/cases/{id}/return` - 退回
- `POST /api/pharmacy/bulk-approve` - 批次核准

### Cases
- `GET /api/cases/{id}/snapshot` - 病人快照
- `POST /api/cases/{id}/autofill/accept` - 接受自動填入
- `POST /api/cases/{id}/autofill/reject` - 拒絕自動填入

### Analytics
- `GET /api/analytics/summary` - KPI 摘要
- `GET /api/analytics/autofill/summary` - Auto-fill 統計

### Demo
- `POST /api/demo/seed` - 建立示範資料
- `POST /api/demo/set-acting-role` - 切換角色
- `GET /api/demo/whoami` - 當前身份

## 測試

```bash
cd backend
pytest tests/ -v
```

## 競賽 Demo 模式

系統支援 Demo Mode 用於 FHIR 50 競賽展示：

1. 設定 `NM_APP_MODE=demo`
2. 使用 `/api/demo/seed` 建立示範案例
3. 在 Frontend 使用角色切換模擬多角色操作
4. 切換 `NM_FHIR_SERVER_TYPE=thas` 連接競賽環境

## 規格文件

詳細規格請參考 `spec/` 目錄：

- `00_overview.md` - 專案概述
- `01_architecture_low_coupling.md` - 架構設計
- `02_data_model.md` - 資料模型
- `03_api_contract.md` - API 合約
- `04_rules_engine.md` - 規則引擎
- `05_demo_mode_thas.md` - Demo Mode
- `06_analytics_kpi.md` - 分析與 KPI
- `07_nonfunctional_security.md` - 非功能性需求
- `08_acceptance_tests.md` - 驗收測試
- `09_frontend_codex_task.md` - 前端任務
- `99_full_spec_reference.md` - 完整規格

## 授權

MIT License

## 聯絡

衛福部 FHIR 50 競賽專案

