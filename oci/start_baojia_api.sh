#!/bin/bash

echo "🚀 啟動寶佳公司名單 API 服務..."
echo ""
echo "📌 使用說明："
echo "1. API 將在 http://localhost:8080 啟動"
echo "2. 開啟 index_with_baojia_api.html 即可使用"
echo "3. 按 Ctrl+C 停止服務"
echo ""
echo "🔧 API 端點："
echo "- GET  http://localhost:8080/api/baojia/companies"
echo "- POST http://localhost:8080/api/baojia/companies"
echo ""

# 執行 API 服務
python3 baojia_api_simple.py