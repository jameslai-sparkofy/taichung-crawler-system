#!/bin/bash
# 背景執行113年爬蟲腳本

echo "開始執行113年建照爬蟲..."
echo "執行時間: $(date '+%Y-%m-%d %H:%M:%S')"

# 建立日誌目錄
mkdir -p /tmp/crawler-logs

# 下載最新的爬蟲腳本
echo "下載爬蟲腳本..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/simple-crawler-113.py \
    --file /tmp/simple-crawler-113.py

# 安裝必要套件
echo "檢查Python套件..."
pip3 install --user beautifulsoup4 >/dev/null 2>&1

# 在背景執行爬蟲
echo "開始爬取113年資料 (1-2201)..."
cd /tmp
nohup python3 simple-crawler-113.py 1 2201 > /tmp/crawler-logs/crawler-113-$(date +%Y%m%d-%H%M%S).log 2>&1 &

CRAWLER_PID=$!
echo "爬蟲已在背景執行，PID: $CRAWLER_PID"

# 儲存PID以便之後查詢
echo $CRAWLER_PID > /tmp/crawler-113.pid

# 建立狀態檔案
cat > /tmp/crawler-status-113.json << EOF
{
  "status": "running",
  "pid": $CRAWLER_PID,
  "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "year": 113,
  "total": 2201,
  "log_file": "crawler-113-$(date +%Y%m%d-%H%M%S).log"
}
EOF

# 上傳狀態到OCI
oci os object put \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name logs/crawler-113-status.json \
    --file /tmp/crawler-status-113.json \
    --content-type "application/json" \
    --force

echo ""
echo "✅ 爬蟲已開始在背景執行！"
echo ""
echo "查看進度指令："
echo "  tail -f /tmp/crawler-logs/crawler-113-*.log"
echo ""
echo "檢查爬蟲狀態："
echo "  ps -p $CRAWLER_PID"
echo ""
echo "停止爬蟲："
echo "  kill $CRAWLER_PID"