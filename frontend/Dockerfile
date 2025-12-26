# NM Medication Stewardship Frontend
# 核醫藥物管理系統前端 Docker 映像檔
# 多階段建構: Node.js 建構 + Nginx 服務

# ===== 第一階段: 建構 =====
FROM node:18-alpine AS builder

WORKDIR /app

# 複製 package 檔案
COPY package*.json ./

# 安裝依賴
RUN npm ci --silent

# 複製原始碼
COPY . .

# 建構生產版本
RUN npm run build

# ===== 第二階段: 生產環境 =====
FROM nginx:alpine

# 複製自訂 Nginx 設定
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 從建構階段複製產出
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露連接埠
EXPOSE 80

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]


