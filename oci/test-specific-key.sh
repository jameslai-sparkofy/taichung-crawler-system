#!/bin/bash

# 測試特定的 INDEX_KEY
echo "🔍 測試特定的 INDEX_KEY: 11410005100"
echo "網址: https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY=11410005100"
echo "================================================"

BASE_URL="https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
INDEX_KEY="11410005100"
TEMP_DIR="/tmp/test-$$"
mkdir -p "$TEMP_DIR"

# 測試不同的爬取策略
echo ""
echo "策略 1: 簡單請求"
curl -s "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/test1.html"
echo "檔案大小: $(wc -c < "$TEMP_DIR/test1.html") bytes"
grep -q "建造執照號碼" "$TEMP_DIR/test1.html" && echo "✅ 找到建照資料" || echo "❌ 沒有找到建照資料"

echo ""
echo "策略 2: 帶完整 headers"
curl -s \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" \
    -H "Accept-Language: zh-TW,zh;q=0.9,en;q=0.8" \
    "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/test2.html"
echo "檔案大小: $(wc -c < "$TEMP_DIR/test2.html") bytes"
grep -q "建造執照號碼" "$TEMP_DIR/test2.html" && echo "✅ 找到建照資料" || echo "❌ 沒有找到建照資料"

echo ""
echo "策略 3: 使用 cookies 並刷新兩次"
COOKIE_JAR="$TEMP_DIR/cookies.txt"

# 第一次請求
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/test3a.html"
sleep 1

# 第二次請求（刷新）
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    "$BASE_URL?INDEX_KEY=$INDEX_KEY" > "$TEMP_DIR/test3b.html"

echo "第一次檔案大小: $(wc -c < "$TEMP_DIR/test3a.html") bytes"
echo "第二次檔案大小: $(wc -c < "$TEMP_DIR/test3b.html") bytes"
grep -q "建造執照號碼" "$TEMP_DIR/test3b.html" && echo "✅ 找到建照資料" || echo "❌ 沒有找到建照資料"

# 檢查是否有特定內容
echo ""
echo "📝 檢查頁面內容:"
if grep -q "○○○代表遺失個資" "$TEMP_DIR/test3b.html"; then
    echo "⚠️  找到個資遺失訊息"
fi

if grep -q "查無任何資訊" "$TEMP_DIR/test3b.html"; then
    echo "⚠️  查無任何資訊"
fi

# 嘗試提取一些資訊
echo ""
echo "📊 嘗試提取資訊:"
if [ -f "$TEMP_DIR/test3b.html" ]; then
    # 提取建照號碼
    PERMIT=$(grep -oP '建造執照號碼[：:\s]*\K[^<\s]+' "$TEMP_DIR/test3b.html" | head -1 || echo "未找到")
    echo "建照號碼: $PERMIT"
    
    # 檢查頁面結構
    echo ""
    echo "頁面包含的表格數量: $(grep -c "<table" "$TEMP_DIR/test3b.html")"
    echo "頁面包含的 tr 數量: $(grep -c "<tr" "$TEMP_DIR/test3b.html")"
fi

# 保存最後的檔案供檢查
cp "$TEMP_DIR/test3b.html" "/tmp/last-crawl-result.html"
echo ""
echo "💾 最後的爬取結果已保存到: /tmp/last-crawl-result.html"

# 清理
rm -rf "$TEMP_DIR"