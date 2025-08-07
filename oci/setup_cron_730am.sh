#!/bin/bash

# 設定每天 7:30 執行的 cron 任務

SCRIPT_PATH="/mnt/c/claude code/建照爬蟲/oci/daily_crawler_730am.sh"
CRON_TIME="30 7 * * *"

# 檢查腳本是否存在
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 錯誤: 找不到腳本 $SCRIPT_PATH"
    exit 1
fi

# 備份現有的 crontab (如果有的話)
crontab -l > /tmp/crontab.backup 2>/dev/null

# 檢查是否已經有相同的任務
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "⚠️  已經存在相同的 cron 任務，移除舊的設定..."
    crontab -l | grep -v "$SCRIPT_PATH" | crontab -
fi

# 添加新的 cron 任務
(crontab -l 2>/dev/null; echo "$CRON_TIME $SCRIPT_PATH") | crontab -

# 確認設定成功
if crontab -l | grep -q "$SCRIPT_PATH"; then
    echo "✅ Cron 任務設定成功！"
    echo "📅 執行時間: 每天早上 7:30"
    echo "📄 執行腳本: $SCRIPT_PATH"
    echo ""
    echo "目前的 cron 設定:"
    crontab -l
else
    echo "❌ Cron 任務設定失敗"
    exit 1
fi