#!/bin/bash
# 快速檢查腳本 - 在 GCP 實例內執行

echo "=== GCP 爬蟲狀態檢查 ==="
echo "時間: $(date)"
echo ""

# 1. 檢查爬蟲目錄
echo "📁 爬蟲目錄內容:"
ls -la /home/crawler/ 2>/dev/null || echo "目錄不存在"
echo ""

# 2. 檢查 Python 環境
echo "🐍 Python 環境:"
python3 --version
pip3 list | grep -E "requests|beautifulsoup4|oci-cli" || echo "套件未安裝"
echo ""

# 3. 檢查 OCI 設定
echo "☁️  OCI 設定:"
ls -la /root/.oci/ 2>/dev/null || echo "OCI 設定不存在"
echo ""

# 4. 檢查爬蟲日誌
echo "📋 爬蟲日誌 (最後 10 行):"
if [ -f /home/crawler/crawler.log ]; then
    tail -10 /home/crawler/crawler.log
else
    echo "日誌檔案不存在"
fi
echo ""

# 5. 檢查 cron 設定
echo "⏰ Cron 排程:"
crontab -l 2>/dev/null || echo "無 cron 設定"
echo ""

# 6. 檢查啟動腳本狀態
echo "🚀 啟動腳本狀態:"
systemctl status google-startup-scripts.service --no-pager | head -20
echo ""

# 7. 測試 OCI 連線
echo "🔗 測試 OCI 連線:"
oci os object list --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --limit 3 2>&1 | head -10
echo ""

echo "=== 檢查完成 ==="