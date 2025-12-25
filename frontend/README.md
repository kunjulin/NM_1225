# NM SMART on FHIR Medication Stewardship - Frontend

核子醫學放射藥物用藥治理系統前端

## 技術堆疊

- **框架**: React 18 + TypeScript
- **建置工具**: Vite
- **路由**: React Router v6
- **狀態管理**: @tanstack/react-query
- **UI 框架**: Material UI (MUI)
- **圖表**: Recharts

## 快速開始

### 1. 安裝依賴

```bash
cd frontend
npm install
```

### 2. 啟動開發伺服器

```bash
npm run dev
```

開發伺服器會在 http://localhost:5173 啟動

### 3. 建置生產版本

```bash
npm run build
```

## 環境設定

前端透過 Vite proxy 連接後端 API：

- API Base URL: `/api` (proxy 到 `http://localhost:8000/api`)

## 頁面說明

| 路徑 | 頁面 | 說明 |
|------|------|------|
| `/login` | 登入頁 | Demo 模式登入 + 角色選擇 |
| `/nm/worklist` | 核醫工作清單 | 核醫醫師查看待處理案件 |
| `/pharmacy/worklist` | 藥師工作清單 | 藥師審核 + 批次核准 |
| `/case/:caseId` | 案件詳情 | 病人快照 + CDS + 操作 |
| `/analytics` | 分析儀表板 | KPI 統計 + 圖表 |

## 認證機制

使用 Header-based 認證 (Demo Mode)：

- `X-Subject`: 使用者識別碼
- `X-Acting-Role`: 操作角色 (NM_PHYSICIAN / PHARMACIST)

## 目錄結構

```
frontend/
├── src/
│   ├── main.tsx           # 進入點
│   ├── App.tsx            # 路由設定
│   ├── theme.ts           # MUI 主題
│   ├── api/
│   │   └── client.ts      # API Client
│   ├── components/
│   │   ├── AppShell.tsx   # 應用程式外殼
│   │   └── ProtectedRoute.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx
│   ├── hooks/
│   │   └── useApi.ts      # API Hooks
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── NMWorklistPage.tsx
│   │   ├── PharmacyWorklistPage.tsx
│   │   ├── CaseDetailPage.tsx
│   │   └── AnalyticsPage.tsx
│   └── types/
│       └── index.ts       # TypeScript 型別定義
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 開發指令

```bash
# 開發模式
npm run dev

# 建置
npm run build

# 預覽建置結果
npm run preview

# Lint 檢查
npm run lint
```

## 授權

MIT License

