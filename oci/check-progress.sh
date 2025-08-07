#!/bin/bash
# 檢查爬蟲進度腳本

echo "檢查爬蟲進度..."
echo "=================="

# 檢查113年爬蟲狀態
if [ -f /tmp/crawler-113.pid ]; then
    PID=$(cat /tmp/crawler-113.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 113年爬蟲運行中 (PID: $PID)"
    else
        echo "❌ 113年爬蟲已停止"
    fi
fi

# 檢查112年爬蟲狀態
if [ -f /tmp/crawler-112.pid ]; then
    PID=$(cat /tmp/crawler-112.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 112年爬蟲運行中 (PID: $PID)"
    else
        echo "❌ 112年爬蟲已停止"
    fi
fi

# 下載最新的permits.json檢查進度
echo ""
echo "下載最新資料..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name permits.json \
    --file /tmp/permits-check.json \
    >/dev/null 2>&1

if [ -f /tmp/permits-check.json ]; then
    # 計算進度
    PROGRESS=$(python3 -c "
import json
data = json.load(open('/tmp/permits-check.json'))
y113 = [p for p in data if isinstance(p, dict) and p.get('indexKey','').startswith('113')]
y112 = [p for p in data if isinstance(p, dict) and p.get('indexKey','').startswith('112')]
total = len(data)
print(f'總建照數: {total}')
print(f'113年進度: {len(y113)}/2201 ({len(y113)/2201*100:.1f}%)')
print(f'112年進度: {len(y112)}/2039 ({len(y112)/2039*100:.1f}%)')
")
    echo ""
    echo "$PROGRESS"
fi

# 顯示113年最新日誌
echo ""
echo "113年最新日誌 (最後10行)："
echo "=================="
if ls /tmp/crawler-logs/crawler-113-*.log >/dev/null 2>&1; then
    tail -n 10 /tmp/crawler-logs/crawler-113-*.log
else
    echo "找不到113年日誌檔案"
fi

# 顯示112年最新日誌
echo ""
echo "112年最新日誌 (最後10行)："
echo "=================="
if ls /tmp/crawler-logs/crawler-112-*.log >/dev/null 2>&1; then
    tail -n 10 /tmp/crawler-logs/crawler-112-*.log
else
    echo "找不到112年日誌檔案"
fi

echo ""
echo "監控面板: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/monitor.html"