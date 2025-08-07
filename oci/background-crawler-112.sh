#!/bin/bash
# 背景執行112年爬蟲腳本

echo "開始執行112年建照爬蟲..."
echo "執行時間: $(date '+%Y-%m-%d %H:%M:%S')"

# 建立日誌目錄
mkdir -p /tmp/crawler-logs

# 下載最新的爬蟲腳本
echo "下載爬蟲腳本..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/simple-crawler-112.py \
    --file /tmp/simple-crawler-112.py

# 在背景執行爬蟲
echo "開始爬取112年資料 (1-2039)..."
cd /tmp
nohup python3 simple-crawler-112.py 1 2039 > /tmp/crawler-logs/crawler-112-$(date +%Y%m%d-%H%M%S).log 2>&1 &

CRAWLER_PID=$!
echo "爬蟲已在背景執行，PID: $CRAWLER_PID"

# 儲存PID
echo $CRAWLER_PID > /tmp/crawler-112.pid

# 建立狀態檔案
cat > /tmp/crawler-status-112.json << EOF
{
  "status": "running",
  "pid": $CRAWLER_PID,
  "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "year": 112,
  "total": 2039,
  "log_file": "crawler-112-$(date +%Y%m%d-%H%M%S).log"
}
EOF

# 上傳狀態到OCI
oci os object put \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name logs/crawler-112-status.json \
    --file /tmp/crawler-status-112.json \
    --content-type "application/json" \
    --force

echo ""
echo "✅ 112年爬蟲已開始在背景執行！"