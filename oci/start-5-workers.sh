#!/bin/bash
# 啟動5個並行爬蟲工作進程

echo "🚀 啟動5個並行爬蟲進程"
echo "======================================"

# 停止現有的爬蟲
echo "⏹️  停止現有爬蟲..."
pkill -f 'main-crawler-continue.py'
sleep 2

# 檢查當前進度
echo "📊 檢查當前進度..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name data/permits.json \
    --file /tmp/check_progress.json > /dev/null 2>&1

# 提取114年最大序號
MAX_SEQ=$(python3 -c "
import json
with open('/tmp/check_progress.json', 'r') as f:
    data = json.load(f)
permits_114 = [p for p in data['permits'] if p.get('permitYear') == 114]
max_seq = max([p.get('sequenceNumber', 0) for p in permits_114]) if permits_114 else 0
print(max_seq)
")

echo "📍 114年當前最大序號: $MAX_SEQ"

# 計算起始序號
START=$((MAX_SEQ + 1))
if [ $START -lt 881 ]; then
    START=881
fi

# 每個進程處理200個序號
CHUNK=200

echo ""
echo "📋 工作分配:"

# 啟動5個工作進程
for i in {1..5}; do
    WORKER_START=$((START + (i-1) * CHUNK))
    WORKER_END=$((WORKER_START + CHUNK - 1))
    
    echo "   Worker $i: $WORKER_START - $WORKER_END"
    
    # 創建並執行工作腳本
    cat > worker_$i.sh << EOF
#!/bin/bash
cd "/mnt/c/claude code/建照爬蟲/oci"
python3 -c "
import sys
sys.path.append('.')
# 載入爬蟲類別
exec(open('optimized-crawler.py').read().split('if __name__ == \"__main__\":')[0])

# 建立爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 1.5  # 增加延遲避免並發問題
crawler.batch_size = 20

print(f'🔧 Worker $i: 爬取 114年 $WORKER_START-$WORKER_END')
print('=' * 70)

try:
    crawler.crawl_year_range(114, $WORKER_START, $WORKER_END, False)
    print(f'\\n✅ Worker $i 完成任務')
except Exception as e:
    print(f'\\n❌ Worker $i 錯誤: {e}')
    crawler.save_progress()
"
EOF
    
    chmod +x worker_$i.sh
    
    # 啟動工作進程
    LOG_FILE="worker_${i}_$(date +%Y%m%d_%H%M%S).log"
    nohup ./worker_$i.sh > $LOG_FILE 2>&1 &
    PID=$!
    echo "   ✅ Worker $i 已啟動 (PID: $PID, Log: $LOG_FILE)"
    
    sleep 2  # 避免同時啟動造成問題
done

echo ""
echo "💡 監控指令:"
echo "   查看所有工作進程: ps aux | grep 'worker_[0-9].sh' | grep -v grep"
echo "   查看工作日誌: tail -f worker_1_*.log"
echo "   停止所有工作進程: pkill -f 'worker_[0-9].sh'"
echo ""
echo "✅ 5個並行爬蟲已啟動！"