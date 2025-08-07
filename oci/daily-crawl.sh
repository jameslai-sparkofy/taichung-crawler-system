#!/bin/bash

# 台中市建照爬蟲 - 每日執行腳本

SCRIPT_DIR="/mnt/c/claude code/建照爬蟲/oci"
LOG_FILE="/tmp/taichung-crawler-$(date +%Y%m%d).log"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 🚀 開始執行台中市建照爬蟲" | tee -a $LOG_FILE

cd "$SCRIPT_DIR"

# 執行多年份爬蟲
if [ -f "multi-year-crawler.py" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 📊 執行多年份爬蟲" | tee -a $LOG_FILE
    python3 multi-year-crawler.py 114 113 112 >> $LOG_FILE 2>&1
    RESULT=$?
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ⚠️  找不到爬蟲程式" | tee -a $LOG_FILE
    exit 1
fi

if [ $RESULT -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 爬蟲執行成功" | tee -a $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ 爬蟲執行失敗 (退出碼: $RESULT)" | tee -a $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 🏁 爬蟲任務完成" | tee -a $LOG_FILE

exit $RESULT