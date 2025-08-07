#!/bin/bash
# 在 OCI Cloud Shell 中設定自動爬蟲

echo "======================================="
echo "OCI Cloud Shell 自動爬蟲設定"
echo "======================================="

NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"

# 建立工作目錄
echo "建立工作目錄..."
mkdir -p ~/building-crawler
cd ~/building-crawler

# 下載每日更新爬蟲
echo "下載爬蟲腳本..."
oci os object get \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name scripts/daily-update.py \
    --file daily-update.py

chmod +x daily-update.py

# 建立執行腳本
cat > run-daily-crawler.sh << 'EOF'
#!/bin/bash
# 執行每日爬蟲

LOG_DIR="$HOME/building-crawler/logs"
LOG_FILE="$LOG_DIR/crawler-$(date +%Y%m%d-%H%M%S).log"

# 建立日誌目錄
mkdir -p $LOG_DIR

echo "=======================================" | tee -a $LOG_FILE
echo "開始執行建照爬蟲: $(date)" | tee -a $LOG_FILE
echo "=======================================" | tee -a $LOG_FILE

# 執行爬蟲
cd $HOME/building-crawler
python3 daily-update.py 2>&1 | tee -a $LOG_FILE

echo "爬蟲執行完成: $(date)" | tee -a $LOG_FILE

# 清理30天前的日誌
find $LOG_DIR -name "*.log" -mtime +30 -delete

# 顯示最後結果
echo ""
echo "最新日誌："
tail -20 $LOG_FILE
EOF

chmod +x run-daily-crawler.sh

# 建立完整爬蟲腳本（用於手動執行大量爬取）
cat > run-full-crawler.sh << 'EOF'
#!/bin/bash
# 執行完整爬蟲（爬取113和112年剩餘資料）

echo "下載完整爬蟲腳本..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/oci-crawler.py \
    --file oci-crawler.py

chmod +x oci-crawler.py

echo "開始執行完整爬蟲..."
python3 oci-crawler.py
EOF

chmod +x run-full-crawler.sh

# 建立 OCI CLI 設定檢查
cat > check-setup.sh << 'EOF'
#!/bin/bash
# 檢查設定狀態

echo "======================================="
echo "檢查 OCI 設定狀態"
echo "======================================="

# 檢查 OCI CLI
echo -n "OCI CLI: "
if command -v oci &> /dev/null; then
    echo "✅ 已安裝"
else
    echo "❌ 未安裝"
fi

# 檢查命名空間
echo -n "命名空間: "
oci os ns get 2>/dev/null || echo "❌ 無法取得"

# 檢查存取權限
echo -n "Object Storage 存取: "
if oci os object list --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --limit 1 &>/dev/null; then
    echo "✅ 正常"
else
    echo "❌ 無權限"
fi

# 檢查爬蟲腳本
echo -n "爬蟲腳本: "
if [ -f "daily-update.py" ]; then
    echo "✅ 已下載"
else
    echo "❌ 未下載"
fi

echo ""
echo "======================================="
EOF

chmod +x check-setup.sh

echo ""
echo "======================================="
echo "✅ 設定完成！"
echo "======================================="
echo ""
echo "可用命令："
echo ""
echo "1. 執行每日更新爬蟲（爬取最新100筆）："
echo "   ./run-daily-crawler.sh"
echo ""
echo "2. 執行完整爬蟲（爬取113和112年所有資料）："
echo "   ./run-full-crawler.sh"
echo ""
echo "3. 檢查設定狀態："
echo "   ./check-setup.sh"
echo ""
echo "4. 查看最新日誌："
echo "   ls -la logs/"
echo "   tail -f logs/crawler-*.log"
echo ""
echo "======================================="
echo "自動執行設定："
echo "======================================="
echo ""
echo "由於 Cloud Shell 會自動關閉，建議："
echo ""
echo "1. 使用 OCI Resource Scheduler（推薦）"
echo "   - 在 OCI Console 建立 Resource Schedule"
echo "   - 設定每日 3:00 AM 執行"
echo "   - 執行命令：~/building-crawler/run-daily-crawler.sh"
echo ""
echo "2. 或使用永久 Compute Instance"
echo "   - 建立免費 ARM Instance"
echo "   - 設定 crontab: 0 3 * * * ~/building-crawler/run-daily-crawler.sh"
echo ""