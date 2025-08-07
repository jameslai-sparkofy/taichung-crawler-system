#!/bin/bash

# 快速爬取並更新到 OCI 的腳本
# 使用 curl 和基本工具，避免 Python 依賴

echo "🚀 開始執行台中市建照爬蟲 (簡化版)"
echo "================================================"

# 設定變數
BASE_URL="https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"
YEAR=114
TYPE=1

# 建立臨時目錄
TEMP_DIR="/tmp/taichung-crawler-$$"
mkdir -p "$TEMP_DIR"

# 下載現有資料
echo "📥 下載現有資料..."
oci os object get \
    --namespace "$NAMESPACE" \
    --bucket-name "$BUCKET" \
    --name "data/permits.json" \
    --file "$TEMP_DIR/permits-old.json" 2>/dev/null || echo '{"permits":[]}' > "$TEMP_DIR/permits-old.json"

# 爬取幾筆測試資料
echo "🔍 爬取最新建照資料..."

# 爬取序號 1-10 的建照
for SEQ in {1..10}; do
    INDEX_KEY=$(printf "%d%d%05d00" $YEAR $TYPE $SEQ)
    echo "爬取 INDEX_KEY: $INDEX_KEY"
    
    # 下載頁面（需要請求兩次）
    curl -s "$BASE_URL?INDEX_KEY=$INDEX_KEY" > /dev/null
    sleep 1
    curl -s "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/page_$INDEX_KEY.html"
    
    # 簡單檢查是否有資料
    if grep -q "建造執照號碼" "$TEMP_DIR/page_$INDEX_KEY.html"; then
        echo "✅ 找到建照資料: $INDEX_KEY"
        
        # 提取基本資訊（使用 grep 和 sed）
        PERMIT_NO=$(grep -oP '建造執照號碼[：:\s]*\K[^<\s]+' "$TEMP_DIR/page_$INDEX_KEY.html" | head -1)
        echo "   建照號碼: $PERMIT_NO"
    else
        echo "❌ 無資料: $INDEX_KEY"
    fi
    
    sleep 2
done

# 更新時間戳
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

# 創建簡單的更新檔案
cat > "$TEMP_DIR/update.json" << EOF
{
  "lastUpdate": "$TIMESTAMP",
  "message": "爬蟲執行於 $TIMESTAMP",
  "note": "這是簡化版爬蟲，完整功能需要 Python 環境"
}
EOF

# 上傳更新通知
echo "📤 上傳更新通知..."
oci os object put \
    --namespace "$NAMESPACE" \
    --bucket-name "$BUCKET" \
    --name "data/crawler-update.json" \
    --file "$TEMP_DIR/update.json" \
    --content-type "application/json" \
    --force

# 清理
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 爬蟲執行完成!"
echo "監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/$NAMESPACE/b/$BUCKET/o/index.html"
echo ""
echo "⚠️  注意：這是簡化版本，完整的爬蟲功能需要："
echo "1. Python 3 環境"
echo "2. requests 和 beautifulsoup4 套件"
echo "3. 或使用 OCI Functions 部署"