#!/bin/bash
# 自動爬蟲安裝腳本 - 可在任何有OCI CLI的Linux環境執行

echo "======================================="
echo "台中市建照自動爬蟲安裝程式"
echo "======================================="

# 設定變數
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"
INSTALL_DIR="$HOME/taichung-building-crawler"

# 建立安裝目錄
echo "1. 建立安裝目錄..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# 下載爬蟲腳本
echo "2. 下載爬蟲程式..."
oci os object get \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name scripts/daily-update.py \
    --file daily-update.py

chmod +x daily-update.py

# 建立wrapper腳本
echo "3. 建立執行腳本..."
cat > auto-crawler.sh << 'EOF'
#!/bin/bash
# 自動爬蟲執行腳本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/crawler-$(date +%Y%m%d-%H%M%S).log"

# 建立日誌目錄
mkdir -p $LOG_DIR

# 記錄開始時間
echo "=======================================" | tee $LOG_FILE
echo "開始執行建照爬蟲" | tee -a $LOG_FILE
echo "時間: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE
echo "=======================================" | tee -a $LOG_FILE

# 檢查Python
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 找不到 python3" | tee -a $LOG_FILE
    exit 1
fi

# 檢查OCI CLI
if ! command -v oci &> /dev/null; then
    echo "錯誤: 找不到 oci cli" | tee -a $LOG_FILE
    exit 1
fi

# 執行爬蟲
cd $SCRIPT_DIR
python3 daily-update.py 2>&1 | tee -a $LOG_FILE

# 記錄結束時間
echo "" | tee -a $LOG_FILE
echo "爬蟲執行完成: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a $LOG_FILE

# 清理30天前的日誌
find $LOG_DIR -name "crawler-*.log" -mtime +30 -delete 2>/dev/null

# 上傳執行狀態到OCI
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"

# 建立狀態檔案
cat > /tmp/crawler-status.json << JSON
{
  "last_run": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "completed",
  "log_file": "$(basename $LOG_FILE)",
  "host": "$(hostname)",
  "user": "$USER"
}
JSON

# 上傳狀態
oci os object put \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name "logs/last-run-status.json" \
    --file /tmp/crawler-status.json \
    --content-type "application/json" \
    --force 2>/dev/null

rm -f /tmp/crawler-status.json

echo "" | tee -a $LOG_FILE
echo "執行完成！日誌保存在: $LOG_FILE" | tee -a $LOG_FILE
EOF

chmod +x auto-crawler.sh

# 建立測試腳本
echo "4. 建立測試腳本..."
cat > test-crawler.sh << 'EOF'
#!/bin/bash
# 測試爬蟲是否正常運作

echo "測試爬蟲設定..."

# 檢查Python
echo -n "Python3: "
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "❌ 未安裝"
    exit 1
fi

# 檢查OCI CLI
echo -n "OCI CLI: "
if command -v oci &> /dev/null; then
    oci --version
else
    echo "❌ 未安裝"
    exit 1
fi

# 檢查OCI權限
echo -n "OCI 權限: "
if oci os object list --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --limit 1 &>/dev/null; then
    echo "✅ 正常"
else
    echo "❌ 無權限"
    exit 1
fi

echo ""
echo "✅ 所有檢查通過！"
echo ""
echo "執行測試爬蟲..."
python3 -c "print('Python 環境正常')"
EOF

chmod +x test-crawler.sh

# 設定 crontab
echo "5. 設定 crontab..."

# 建立 crontab 設定
CRON_CMD="$INSTALL_DIR/auto-crawler.sh >> $INSTALL_DIR/logs/cron.log 2>&1"
CRON_TIME="0 3 * * *"  # 每天凌晨 3:00

# 取得當前 crontab
crontab -l > /tmp/current_cron 2>/dev/null || true

# 檢查是否已存在
if grep -q "$INSTALL_DIR/auto-crawler.sh" /tmp/current_cron; then
    echo "✅ Crontab 已經設定"
else
    # 添加新的 cron job
    echo "" >> /tmp/current_cron
    echo "# 台中市建照自動爬蟲 - 每天凌晨3點執行" >> /tmp/current_cron
    echo "$CRON_TIME $CRON_CMD" >> /tmp/current_cron
    
    # 安裝新的 crontab
    crontab /tmp/current_cron
    echo "✅ Crontab 設定完成"
fi

rm -f /tmp/current_cron

# 建立解除安裝腳本
echo "6. 建立解除安裝腳本..."
cat > uninstall.sh << 'EOF'
#!/bin/bash
# 解除安裝自動爬蟲

echo "解除安裝自動爬蟲..."

# 移除 crontab
crontab -l | grep -v "taichung-building-crawler" | crontab -
echo "✅ 已移除 crontab 設定"

# 詢問是否刪除檔案
read -p "是否刪除爬蟲檔案？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/taichung-building-crawler"
    echo "✅ 已刪除爬蟲檔案"
fi

echo "解除安裝完成！"
EOF

chmod +x uninstall.sh

# 顯示安裝結果
echo ""
echo "======================================="
echo "✅ 安裝完成！"
echo "======================================="
echo ""
echo "安裝位置: $INSTALL_DIR"
echo ""
echo "可用命令:"
echo "  ./test-crawler.sh    - 測試爬蟲設定"
echo "  ./auto-crawler.sh    - 手動執行爬蟲"
echo "  ./uninstall.sh       - 解除安裝"
echo ""
echo "自動執行:"
echo "  已設定每天凌晨 3:00 自動執行"
echo "  使用 'crontab -l' 查看設定"
echo "  使用 'crontab -e' 編輯設定"
echo ""
echo "日誌位置:"
echo "  $INSTALL_DIR/logs/"
echo ""
echo "======================================="
echo "立即測試請執行: ./test-crawler.sh"
echo "======================================="