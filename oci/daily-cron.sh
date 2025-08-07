#!/bin/bash

# 台中市建照爬蟲 - 每日定時執行腳本
# 可以設定在crontab中每日執行

# 設定日誌檔案
LOG_FILE="/tmp/taichung-crawler-$(date +%Y%m%d).log"
SCRIPT_DIR="/mnt/c/claude code/建照爬蟲/oci"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 🚀 開始執行台中市建照爬蟲" >> $LOG_FILE

# 檢查網路連接
if ping -c 1 mcgbm.taichung.gov.tw > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 網路連接正常" >> $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ 網路連接失敗" >> $LOG_FILE
    exit 1
fi

# 執行爬蟲
cd "$SCRIPT_DIR"

if [ -f "simple-crawler.py" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 📊 執行完整版爬蟲" >> $LOG_FILE
    python3 simple-crawler.py >> $LOG_FILE 2>&1
    RESULT=$?
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 📊 執行測試版爬蟲" >> $LOG_FILE
    python3 test-crawler-simple.py >> $LOG_FILE 2>&1
    RESULT=$?
fi

if [ $RESULT -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 爬蟲執行成功" >> $LOG_FILE
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ 爬蟲執行失敗 (退出碼: $RESULT)" >> $LOG_FILE
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 🏁 爬蟲任務完成" >> $LOG_FILE
echo "----------------------------------------" >> $LOG_FILE

# 清理7天前的日誌
find /tmp -name "taichung-crawler-*.log" -mtime +7 -delete 2>/dev/null

exit $RESULT