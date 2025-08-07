#!/bin/bash
# 保持 WSL 活躍的腳本

echo "🔄 保持 WSL 活躍中..."
echo "按 Ctrl+C 結束"

while true; do
    # 每5分鐘檢查一次爬蟲狀態
    echo -n "$(date '+%Y-%m-%d %H:%M:%S') - "
    
    # 檢查爬蟲進程
    crawler_count=$(ps aux | grep -E "python.*crawler" | grep -v grep | wc -l)
    echo "爬蟲進程數: $crawler_count"
    
    # 簡單的網路檢查
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo "  網路連線: ✅"
    else
        echo "  網路連線: ❌"
    fi
    
    sleep 300  # 5分鐘
done