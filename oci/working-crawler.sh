#!/bin/bash

# 工作版本的爬蟲 - 處理 session 和重定向
echo "🚀 台中市建照爬蟲 - 工作版本"
echo "================================================"

BASE_URL="https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"

# 建立工作目錄
WORK_DIR="/tmp/crawler-work-$$"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 使用 wget 處理 cookies 和 session
echo "🔧 建立 session..."

# 先訪問主頁建立 session
wget -q --save-cookies=cookies.txt --keep-session-cookies \
     --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
     -O /dev/null \
     "https://mcgbm.taichung.gov.tw/bupic/"

sleep 1

# 測試幾個已知的 INDEX_KEY
echo ""
echo "📊 開始爬取建照資料..."
echo ""

# 測試的 INDEX_KEY 列表
TEST_KEYS=(
    "11410005100"  # 您提供的
    "11410000100"
    "11410001000"
    "11410010000"
    "11410050000"
)

SUCCESS_COUNT=0

for INDEX_KEY in "${TEST_KEYS[@]}"; do
    echo "🔍 爬取 INDEX_KEY: $INDEX_KEY"
    
    # 使用建立的 session 爬取
    wget -q --load-cookies=cookies.txt --save-cookies=cookies.txt --keep-session-cookies \
         --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
         -O "page_$INDEX_KEY.html" \
         "$BASE_URL?INDEX_KEY=$INDEX_KEY"
    
    # 檢查檔案大小
    FILE_SIZE=$(wc -c < "page_$INDEX_KEY.html" 2>/dev/null || echo 0)
    echo "   檔案大小: $FILE_SIZE bytes"
    
    # 如果第一次沒成功，再試一次（刷新）
    if [ $FILE_SIZE -lt 1000 ]; then
        echo "   重新嘗試..."
        sleep 1
        wget -q --load-cookies=cookies.txt --save-cookies=cookies.txt --keep-session-cookies \
             --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
             --referer="$BASE_URL?INDEX_KEY=$INDEX_KEY" \
             -O "page_$INDEX_KEY.html" \
             "$BASE_URL?INDEX_KEY=$INDEX_KEY"
        
        FILE_SIZE=$(wc -c < "page_$INDEX_KEY.html" 2>/dev/null || echo 0)
        echo "   新檔案大小: $FILE_SIZE bytes"
    fi
    
    # 分析內容
    if [ -f "page_$INDEX_KEY.html" ] && [ $FILE_SIZE -gt 1000 ]; then
        # 轉換編碼並檢查內容
        iconv -f big5 -t utf-8 "page_$INDEX_KEY.html" 2>/dev/null > "page_$INDEX_KEY.utf8.html" || cp "page_$INDEX_KEY.html" "page_$INDEX_KEY.utf8.html"
        
        if grep -q "建造執照號碼" "page_$INDEX_KEY.utf8.html"; then
            echo "   ✅ 找到建照資料!"
            
            # 提取建照號碼
            PERMIT_NO=$(grep -oE '建造執照號碼[^<]*<[^>]*>[^<]*<[^>]*>([^<]+)' "page_$INDEX_KEY.utf8.html" | sed 's/.*>\([^<]*\)$/\1/' | head -1)
            [ -n "$PERMIT_NO" ] && echo "   建照號碼: $PERMIT_NO"
            
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            
            # 保存成功的頁面
            cp "page_$INDEX_KEY.utf8.html" "success_$INDEX_KEY.html"
            
        elif grep -q "○○○代表遺失個資" "page_$INDEX_KEY.utf8.html"; then
            echo "   ⚠️  個資已遺失"
        elif grep -q "查無任何資訊" "page_$INDEX_KEY.utf8.html"; then
            echo "   ❌ 查無資料"
        else
            echo "   ❓ 未知狀態"
        fi
    else
        echo "   ❌ 無法取得頁面"
    fi
    
    sleep 2
done

echo ""
echo "📊 爬取結果統計:"
echo "   測試數量: ${#TEST_KEYS[@]}"
echo "   成功數量: $SUCCESS_COUNT"

# 如果有成功的頁面，創建簡單的資料檔案
if [ $SUCCESS_COUNT -gt 0 ]; then
    echo ""
    echo "📝 創建資料檔案..."
    
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    
    cat > crawl-result.json << EOF
{
  "lastUpdate": "$TIMESTAMP",
  "totalCrawled": ${#TEST_KEYS[@]},
  "successCount": $SUCCESS_COUNT,
  "message": "使用 wget 成功爬取建照資料",
  "testedKeys": [
$(printf '    "%s"' "${TEST_KEYS[@]}" | sed 's/" "/",\n    "/g')
  ]
}
EOF
    
    # 上傳結果
    echo "📤 上傳結果到 OCI..."
    oci os object put \
        --namespace "$NAMESPACE" \
        --bucket-name "$BUCKET" \
        --name "data/crawler-test-result.json" \
        --file crawl-result.json \
        --content-type "application/json" \
        --force
    
    # 保存一個成功的範例
    if ls success_*.html >/dev/null 2>&1; then
        SAMPLE=$(ls success_*.html | head -1)
        echo ""
        echo "💾 保存成功範例到: /tmp/success-sample.html"
        cp "$SAMPLE" /tmp/success-sample.html
    fi
fi

# 清理
cd /
rm -rf "$WORK_DIR"

echo ""
echo "🎉 爬蟲測試完成!"
echo "監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/$NAMESPACE/b/$BUCKET/o/index.html"