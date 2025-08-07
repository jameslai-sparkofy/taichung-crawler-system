#!/bin/bash

# OCI Functions 部署腳本
# 部署台中市建照爬蟲函數到 OCI

echo "🚀 開始部署台中市建照爬蟲函數到 OCI Functions"
echo "================================================"

# 設定變數
APP_NAME="taichung-building-crawler"
FUNCTION_NAME="taichung-crawler"
FUNCTION_DIR="taichung-crawler-function"

# 進入函數目錄
cd "$FUNCTION_DIR"

echo "📦 打包函數..."
# 創建新的 tar.gz 檔案
tar -czf function.tar.gz func.py func.yaml requirements.txt

echo "✅ 函數打包完成"

# 使用 OCI CLI 部署函數
echo "🔧 部署函數到 OCI..."
echo ""
echo "請執行以下步驟來部署函數："
echo ""
echo "1. 登入 OCI Console"
echo "2. 進入 Functions 服務"
echo "3. 找到應用程式: $APP_NAME"
echo "4. 更新函數: $FUNCTION_NAME"
echo "5. 上傳 function.tar.gz"
echo ""
echo "或使用 Fn CLI："
echo ""
echo "fn deploy --app $APP_NAME"
echo ""

# 函數調用範例
echo "📝 函數調用範例："
echo ""
echo "使用 OCI CLI:"
echo "oci fn function invoke --function-id <FUNCTION_OCID> --file - --body '{}'"
echo ""
echo "使用 Fn CLI:"
echo "fn invoke $APP_NAME $FUNCTION_NAME"
echo ""

echo "🎯 部署準備完成！"
echo ""
echo "函數將會："
echo "1. 爬取最新的114年建照資料"
echo "2. 提取新的欄位（地號、行政區、棟數、戶數等）"
echo "3. 更新到 OCI Object Storage"
echo "4. 自動更新網頁顯示"