#!/bin/bash

# 台中市建照爬蟲 - Cloudflare 快速部署腳本

echo "🚀 台中市建照爬蟲系統 - Cloudflare 部署"
echo "====================================="

# 檢查是否安裝wrangler
if ! command -v wrangler &> /dev/null; then
    echo "❌ 未安裝 Wrangler CLI"
    echo "請執行: npm install -g wrangler"
    exit 1
fi

# 檢查是否已登入
if ! wrangler whoami &> /dev/null; then
    echo "🔐 請先登入 Cloudflare 帳號"
    wrangler login
fi

echo "📦 安裝依賴..."
npm install

echo "🗄️ 建立 D1 資料庫..."
echo "請複製以下命令的輸出中的 database_id 到 wrangler.toml 檔案中"
echo "正在建立資料庫..."
wrangler d1 create taichung-permits

echo ""
echo "⚠️  重要: 請更新 wrangler.toml 中的 database_id"
echo "按 Enter 繼續 (確保已更新 database_id)..."
read

echo "🏗️ 初始化資料庫結構..."
wrangler d1 execute taichung-permits --file=./schema.sql

echo "🚀 部署 Worker..."
npm run deploy

echo ""
echo "✅ 部署完成!"
echo ""
echo "📋 下一步:"
echo "1. 造訪你的 Worker URL 查看儀表板"
echo "2. CRON 將於每天早上8點自動執行"
echo "3. 可在 Cloudflare Dashboard 中手動觸發測試"
echo ""
echo "🔧 常用命令:"
echo "- 查看日誌: npm run tail"
echo "- 重新部署: npm run deploy"
echo "- 資料庫查詢: npm run db:query \"SELECT COUNT(*) FROM building_permits\""
echo ""
echo "📊 監控網址:"
wrangler deploy --dry-run 2>/dev/null | grep "https://" || echo "請在 Cloudflare Dashboard 中查看 Worker URL"