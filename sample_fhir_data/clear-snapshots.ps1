# Clear Snapshots Script (PowerShell)
# Purpose: 清除 Docker 容器內 APP DB 的所有 snapshot FHIR data
# Usage: Run .\clear-snapshots.ps1 in PowerShell

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "清除 Snapshot 資料腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 取得專案根目錄（從 sample_fhir_data 往上ㄧ層）
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir  # sample_fhir_data 的父目錄就是專案根目錄
$backendDir = Join-Path $projectRoot "backend"
$clearScript = Join-Path $backendDir "clear_snapshots.py"

# Docker 容器名稱
$containerName = "nm-backend-thas"

# 檢查 clear_snapshots.py 是否存在
if (-not (Test-Path $clearScript)) {
    Write-Host "錯誤: 找不到清理腳本 $clearScript" -ForegroundColor Red
    Write-Host "請確認 backend/clear_snapshots.py 檔案存在" -ForegroundColor Red
    exit 1
}

Write-Host "檢查 Docker 容器狀態..." -ForegroundColor Yellow

# 檢查 Docker 是否可用
try {
    docker --version | Out-Null
} catch {
    Write-Host "錯誤: 無法執行 Docker 命令" -ForegroundColor Red
    Write-Host "請確認 Docker 已安裝並正在運行" -ForegroundColor Red
    exit 1
}

# 檢查容器是否存在且正在運行
$containerStatus = docker ps -a --filter "name=$containerName" --format "{{.Status}}" 2>&1
if ($LASTEXITCODE -ne 0 -or -not $containerStatus) {
    Write-Host "錯誤: 找不到容器 $containerName" -ForegroundColor Red
    Write-Host "請確認容器已建立並正在運行" -ForegroundColor Red
    exit 1
}

# 檢查容器是否正在運行
$isRunning = docker ps --filter "name=$containerName" --format "{{.Names}}" 2>&1
if (-not $isRunning -or $isRunning -ne $containerName) {
    Write-Host "錯誤: 容器 $containerName 未運行" -ForegroundColor Red
    Write-Host "請先啟動容器: docker-compose -f docker-compose.thas.yml up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "容器狀態: 運行中" -ForegroundColor Green
Write-Host ""

# 複製清理腳本到容器
Write-Host "複製清理腳本到容器..." -ForegroundColor Yellow
try {
    docker cp $clearScript "${containerName}:/app/clear_snapshots.py"
    if ($LASTEXITCODE -ne 0) {
        throw "複製失敗"
    }
    Write-Host "複製成功" -ForegroundColor Green
} catch {
    Write-Host "錯誤: 無法複製腳本到容器 - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "在容器內執行清理腳本..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 在容器內執行清理腳本
try {
    docker exec $containerName python clear_snapshots.py
    if ($LASTEXITCODE -ne 0) {
        throw "執行失敗"
    }
} catch {
    Write-Host ""
    Write-Host "錯誤: 清理腳本執行失敗 - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host ""
Write-Host "提示: 您可能需要重新整理前端頁面或等待同步以查看更新後的狀態" -ForegroundColor Yellow

