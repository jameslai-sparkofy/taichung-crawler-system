#!/bin/bash

# 智慧型爬取腳本 - 處理台中市網站需要刷新兩次的問題
# 使用 curl 和基本工具

echo "🚀 開始執行台中市建照爬蟲 (智慧版)"
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

# 初始化 cookie jar
COOKIE_JAR="$TEMP_DIR/cookies.txt"

# 全域變數：記錄是否已建立格式
FORMAT_ESTABLISHED=0

# 函數：智慧爬取單一頁面
crawl_permit() {
    local INDEX_KEY=$1
    local IS_FIRST=$2
    local MAX_RETRIES=5
    local SUCCESS=0
    
    echo "🔍 爬取 INDEX_KEY: $INDEX_KEY"
    
    # 如果是第一個網址，需要多次刷新來建立格式
    if [ "$IS_FIRST" = "first" ]; then
        echo "   🔧 建立正確格式（第一個網址）..."
        MAX_RETRIES=10
        
        # 多次訪問直到建立正確格式
        for setup in $(seq 1 3); do
            curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
                -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
                -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
                -H "Accept-Language: zh-TW,zh;q=0.9,en;q=0.8" \
                "$BASE_URL?INDEX_KEY=$INDEX_KEY" > /dev/null
            sleep 1
        done
    else
        # 非第一個網址，如果格式已建立，只需要訪問一次
        if [ $FORMAT_ESTABLISHED -eq 1 ]; then
            MAX_RETRIES=3
        fi
        
        # 第一次訪問
        curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
            -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
            -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
            -H "Accept-Language: zh-TW,zh;q=0.9,en;q=0.8" \
            "$BASE_URL?INDEX_KEY=$INDEX_KEY" > /dev/null
        
        sleep 1
    fi
    
    # 取得頁面內容
    curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
        -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
        -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
        -H "Accept-Language: zh-TW,zh;q=0.9,en;q=0.8" \
        "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/page_$INDEX_KEY.html"
    
    # 檢查是否需要繼續刷新
    for i in $(seq 1 $MAX_RETRIES); do
        if grep -q "建造執照號碼" "$TEMP_DIR/page_$INDEX_KEY.html" || \
           grep -q "○○○代表遺失個資" "$TEMP_DIR/page_$INDEX_KEY.html"; then
            SUCCESS=1
            break
        else
            echo "   第 $i 次重新整理..."
            sleep 1
            
            # 重新整理
            curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
                -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
                -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
                -H "Accept-Language: zh-TW,zh;q=0.9,en;q=0.8" \
                -H "Cache-Control: no-cache" \
                -H "Pragma: no-cache" \
                "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/page_$INDEX_KEY.html"
        fi
    done
    
    # 處理結果
    if [ $SUCCESS -eq 1 ]; then
        if grep -q "○○○代表遺失個資" "$TEMP_DIR/page_$INDEX_KEY.html"; then
            echo "   ⚠️  個資已遺失"
        elif grep -q "建造執照號碼" "$TEMP_DIR/page_$INDEX_KEY.html"; then
            # 提取基本資訊
            PERMIT_NO=$(grep -oP '建造執照號碼[：:\s]*\K[^<\s]+' "$TEMP_DIR/page_$INDEX_KEY.html" | head -1 || echo "")
            
            # 嘗試提取地號
            LAND_NO=$(grep -A2 "地號" "$TEMP_DIR/page_$INDEX_KEY.html" | grep -oP '<td[^>]*>\K[^<]+' | tail -1 || echo "")
            
            # 嘗試提取起造人
            APPLICANT=$(grep -A3 "起造人" "$TEMP_DIR/page_$INDEX_KEY.html" | grep -A1 "姓名" | grep -oP '<td[^>]*>\K[^<]+' | tail -1 || echo "")
            
            echo "   ✅ 找到建照資料:"
            echo "      建照號碼: $PERMIT_NO"
            [ -n "$APPLICANT" ] && echo "      起造人: $APPLICANT"
            [ -n "$LAND_NO" ] && echo "      地號: $LAND_NO"
            
            # 儲存成功的頁面
            cp "$TEMP_DIR/page_$INDEX_KEY.html" "$TEMP_DIR/success_$INDEX_KEY.html"
            
            # 標記格式已建立
            FORMAT_ESTABLISHED=1
        else
            echo "   ❌ 無資料"
        fi
    else
        echo "   ❌ 無法取得資料（已重試 $MAX_RETRIES 次）"
    fi
    
    return $SUCCESS
}

# 下載現有資料
echo "📥 下載現有資料..."
oci os object get \
    --namespace "$NAMESPACE" \
    --bucket-name "$BUCKET" \
    --name "data/permits.json" \
    --file "$TEMP_DIR/permits-old.json" 2>/dev/null || echo '{"permits":[]}' > "$TEMP_DIR/permits-old.json"

# 爬取建照資料
echo ""
echo "🏗️ 開始爬取 $YEAR 年建照..."
echo ""

TOTAL_CRAWLED=0
TOTAL_SUCCESS=0
CONSECUTIVE_FAILURES=0

# 從序號 1 開始，最多爬取 50 筆或連續失敗 20 次
for SEQ in $(seq 1 100); do
    INDEX_KEY=$(printf "%d%d%05d00" $YEAR $TYPE $SEQ)
    
    # 第一個網址需要特別處理
    if [ $SEQ -eq 1 ]; then
        FIRST_FLAG="first"
    else
        FIRST_FLAG=""
    fi
    
    if crawl_permit "$INDEX_KEY" "$FIRST_FLAG"; then
        TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))
        CONSECUTIVE_FAILURES=0
    else
        CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
        
        if [ $CONSECUTIVE_FAILURES -ge 20 ]; then
            echo ""
            echo "⚠️  連續失敗 20 次，停止爬取"
            break
        fi
    fi
    
    TOTAL_CRAWLED=$((TOTAL_CRAWLED + 1))
    
    # 每爬取 10 筆顯示進度
    if [ $((TOTAL_CRAWLED % 10)) -eq 0 ]; then
        echo ""
        echo "📊 進度: 已爬取 $TOTAL_CRAWLED 筆，成功 $TOTAL_SUCCESS 筆"
        echo ""
    fi
    
    # 延遲避免過度請求
    sleep 2
done

# 統計結果
echo ""
echo "📊 爬取統計:"
echo "   總爬取數: $TOTAL_CRAWLED"
echo "   成功筆數: $TOTAL_SUCCESS"
echo "   最後序號: $SEQ"

# 更新時間戳
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

# 創建爬取記錄
cat > "$TEMP_DIR/crawl-log-new.json" << EOF
{
  "date": "$(date +%Y-%m-%d)",
  "startTime": "$TIMESTAMP",
  "endTime": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "totalCrawled": $TOTAL_CRAWLED,
  "newRecords": $TOTAL_SUCCESS,
  "errorRecords": $((TOTAL_CRAWLED - TOTAL_SUCCESS)),
  "status": "completed",
  "note": "使用 shell 腳本執行"
}
EOF

# 更新爬取記錄
echo ""
echo "📤 更新爬取記錄..."

# 下載現有記錄
oci os object get \
    --namespace "$NAMESPACE" \
    --bucket-name "$BUCKET" \
    --name "data/crawl-logs.json" \
    --file "$TEMP_DIR/logs-old.json" 2>/dev/null || echo '{"logs":[]}' > "$TEMP_DIR/logs-old.json"

# 使用 jq 合併記錄（如果可用）
if command -v jq >/dev/null 2>&1; then
    jq --slurpfile new "$TEMP_DIR/crawl-log-new.json" \
       '.logs = ([$new[0]] + .logs) | .logs = .logs[0:30]' \
       "$TEMP_DIR/logs-old.json" > "$TEMP_DIR/logs-new.json"
    
    oci os object put \
        --namespace "$NAMESPACE" \
        --bucket-name "$BUCKET" \
        --name "data/crawl-logs.json" \
        --file "$TEMP_DIR/logs-new.json" \
        --content-type "application/json" \
        --force
else
    # 沒有 jq，直接上傳新記錄
    oci os object put \
        --namespace "$NAMESPACE" \
        --bucket-name "$BUCKET" \
        --name "data/crawl-log-latest.json" \
        --file "$TEMP_DIR/crawl-log-new.json" \
        --content-type "application/json" \
        --force
fi

# 顯示成功爬取的範例
if [ $TOTAL_SUCCESS -gt 0 ]; then
    echo ""
    echo "📄 成功爬取的頁面範例:"
    ls -la "$TEMP_DIR"/success_*.html 2>/dev/null | head -5
fi

# 清理
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 爬蟲執行完成!"
echo "監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/$NAMESPACE/b/$BUCKET/o/index.html"
echo ""
echo "💡 提示："
echo "1. 完整的資料解析需要 Python 環境和 BeautifulSoup"
echo "2. 可以使用 OCI Functions 來自動化執行"
echo "3. 建議設定每日定時執行"