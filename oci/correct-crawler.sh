#!/bin/bash

# 正確的爬蟲策略 - 處理登入頁面重定向
echo "🚀 台中市建照爬蟲 - 正確策略版本"
echo "================================================"

BASE_URL="https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"

# 建立工作目錄
WORK_DIR="/tmp/crawler-correct-$$"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 函數：爬取單一建照
crawl_permit() {
    local INDEX_KEY=$1
    local SUCCESS=0
    
    echo "🔍 爬取 INDEX_KEY: $INDEX_KEY"
    
    # 第一次訪問 - 會被重定向到登入頁面
    echo "   第一次訪問（建立 session）..."
    wget -q --save-cookies=cookies.txt --keep-session-cookies \
         --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
         -O "first_$INDEX_KEY.html" \
         "$BASE_URL?INDEX_KEY=$INDEX_KEY"
    
    # 重要：等待一段時間，不要太快
    echo "   等待 3 秒..."
    sleep 3
    
    # 第二次訪問 - 使用相同的 cookies，訪問原網址
    echo "   第二次訪問（取得資料）..."
    wget -q --load-cookies=cookies.txt --save-cookies=cookies.txt --keep-session-cookies \
         --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
         -O "page_$INDEX_KEY.html" \
         "$BASE_URL?INDEX_KEY=$INDEX_KEY"
    
    # 檢查檔案大小
    FILE_SIZE=$(wc -c < "page_$INDEX_KEY.html" 2>/dev/null || echo 0)
    echo "   檔案大小: $FILE_SIZE bytes"
    
    # 分析內容
    if [ -f "page_$INDEX_KEY.html" ] && [ $FILE_SIZE -gt 1000 ]; then
        # 嘗試轉換編碼（台灣網站可能使用 Big5）
        iconv -f big5 -t utf-8 "page_$INDEX_KEY.html" 2>/dev/null > "page_$INDEX_KEY.utf8.html" || cp "page_$INDEX_KEY.html" "page_$INDEX_KEY.utf8.html"
        
        # 檢查內容
        if grep -q "建造執照號碼" "page_$INDEX_KEY.utf8.html"; then
            echo "   ✅ 找到建照資料!"
            
            # 提取建照號碼（簡單提取）
            PERMIT_NO=$(grep -A2 "建造執照號碼" "page_$INDEX_KEY.utf8.html" | grep -oE ">[^<]+<" | sed 's/[><]//g' | grep -v "^$" | head -1)
            [ -n "$PERMIT_NO" ] && echo "      建照號碼: $PERMIT_NO"
            
            # 提取起造人
            APPLICANT=$(grep -A5 "起造人" "page_$INDEX_KEY.utf8.html" | grep -A2 "姓名" | grep -oE ">[^<]+<" | sed 's/[><]//g' | grep -v "^$" | grep -v "姓名" | head -1)
            [ -n "$APPLICANT" ] && echo "      起造人: $APPLICANT"
            
            # 提取地號
            LAND_NO=$(grep -A2 "地號" "page_$INDEX_KEY.utf8.html" | grep -oE ">[^<]+<" | sed 's/[><]//g' | grep -v "^$" | grep -v "地號" | head -1)
            [ -n "$LAND_NO" ] && echo "      地號: $LAND_NO"
            
            SUCCESS=1
            
            # 保存成功的頁面
            cp "page_$INDEX_KEY.utf8.html" "success_$INDEX_KEY.html"
            
        elif grep -q "○○○代表遺失個資" "page_$INDEX_KEY.utf8.html"; then
            echo "   ⚠️  個資已遺失"
        elif grep -q "查無任何資訊" "page_$INDEX_KEY.utf8.html"; then
            echo "   ❌ 查無資料"
        else
            echo "   ❓ 未知狀態（可能需要再次嘗試）"
            # 保存供除錯
            cp "page_$INDEX_KEY.utf8.html" "unknown_$INDEX_KEY.html"
        fi
    else
        echo "   ❌ 無法取得頁面"
    fi
    
    return $SUCCESS
}

# 開始爬取
echo ""
echo "📊 開始爬取建照資料..."
echo ""

# 年份和類型
YEAR=114
TYPE=1

# 爬取統計
TOTAL_CRAWLED=0
SUCCESS_COUNT=0
CONSECUTIVE_FAILURES=0

# 從序號 1 開始爬取
for SEQ in {1..20}; do
    INDEX_KEY=$(printf "%d%d%05d00" $YEAR $TYPE $SEQ)
    
    if crawl_permit "$INDEX_KEY"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        CONSECUTIVE_FAILURES=0
    else
        CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
        
        # 連續失敗太多次就停止
        if [ $CONSECUTIVE_FAILURES -ge 10 ]; then
            echo ""
            echo "⚠️  連續失敗 10 次，停止爬取"
            break
        fi
    fi
    
    TOTAL_CRAWLED=$((TOTAL_CRAWLED + 1))
    
    # 每個請求之間等待，避免太頻繁
    echo "   等待 2 秒後繼續..."
    sleep 2
    echo ""
done

# 統計結果
echo "📊 爬取統計:"
echo "   總爬取數: $TOTAL_CRAWLED"
echo "   成功數量: $SUCCESS_COUNT"

# 如果有成功的資料，創建結果檔案
if [ $SUCCESS_COUNT -gt 0 ]; then
    echo ""
    echo "📝 創建結果檔案..."
    
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    
    # 創建簡單的結果 JSON
    cat > crawl-result.json << EOF
{
  "lastUpdate": "$TIMESTAMP",
  "crawlDate": "$(date +%Y-%m-%d)",
  "totalCrawled": $TOTAL_CRAWLED,
  "successCount": $SUCCESS_COUNT,
  "year": $YEAR,
  "strategy": "兩次訪問策略（間隔3秒）"
}
EOF
    
    # 上傳結果
    echo "📤 上傳結果到 OCI..."
    oci os object put \
        --namespace "$NAMESPACE" \
        --bucket-name "$BUCKET" \
        --name "data/crawl-strategy-test.json" \
        --file crawl-result.json \
        --content-type "application/json" \
        --force
    
    # 保存成功範例
    if ls success_*.html >/dev/null 2>&1; then
        SAMPLE=$(ls success_*.html | head -1)
        echo ""
        echo "💾 保存成功範例到: /tmp/crawl-success-sample.html"
        cp "$SAMPLE" /tmp/crawl-success-sample.html
        
        # 顯示範例內容片段
        echo ""
        echo "📄 成功頁面片段:"
        grep -A5 "建造執照號碼" "$SAMPLE" | head -10
    fi
fi

# 清理
cd /
rm -rf "$WORK_DIR"

echo ""
echo "🎉 爬蟲執行完成!"
echo "監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/$NAMESPACE/b/$BUCKET/o/index.html"