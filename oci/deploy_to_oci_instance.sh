#!/bin/bash

# OCI Compute Instance 部署腳本
# 將爬蟲程式部署到 OCI VM 並設定每日 7:30 執行

echo "🚀 開始部署爬蟲到 OCI Compute Instance"
echo "=========================================="

# 設定變數
INSTANCE_IP="168.138.213.65"
SSH_KEY_PATH="~/.ssh/id_rsa"  # 請修改為你的 SSH 金鑰路徑
REMOTE_USER="opc"  # OCI 預設使用者名稱
REMOTE_DIR="/home/opc/taichung-building-crawler"

# 檢查 IP 是否已設定
if [ "$INSTANCE_IP" = "<請填入你的 OCI Instance IP>" ]; then
    echo "❌ 請先編輯此腳本，填入你的 OCI Instance IP"
    echo "   編輯第 9 行的 INSTANCE_IP 變數"
    exit 1
fi

# 建立部署用的壓縮檔
echo "📦 準備部署檔案..."
tar -czf crawler_deploy.tar.gz \
    optimized-crawler-stable.py \
    cron_daily_crawler_v3.py \
    backup_current_data.py \
    sync_to_github.py \
    baojia_companies.json \
    daily_crawler_730am.sh

# 上傳到遠端伺服器
echo "📤 上傳檔案到 OCI Instance..."
scp -i "$SSH_KEY_PATH" crawler_deploy.tar.gz "$REMOTE_USER@$INSTANCE_IP:/tmp/"

# 建立遠端設定腳本
cat > remote_setup.sh << 'EOF'
#!/bin/bash

# 在 OCI Instance 上執行的設定腳本

echo "🔧 在 OCI Instance 上設定爬蟲..."

# 安裝必要套件
echo "📦 安裝 Python 套件..."
sudo yum install -y python3 python3-pip
pip3 install --user requests beautifulsoup4

# 安裝 OCI CLI (如果還沒安裝)
if ! command -v oci &> /dev/null; then
    echo "📥 安裝 OCI CLI..."
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
fi

# 建立工作目錄
mkdir -p ~/taichung-building-crawler
cd ~/taichung-building-crawler

# 解壓縮檔案
tar -xzf /tmp/crawler_deploy.tar.gz

# 設定執行權限
chmod +x daily_crawler_730am.sh

# 修改腳本中的路徑
sed -i 's|/mnt/c/claude code/建照爬蟲/oci|/home/opc/taichung-building-crawler|g' daily_crawler_730am.sh
sed -i 's|/home/laija/bin/oci|/home/opc/bin/oci|g' daily_crawler_730am.sh
sed -i 's|/home/laija/bin/oci|/home/opc/bin/oci|g' *.py

# 設定 cron job
echo "⏰ 設定 cron 排程..."
(crontab -l 2>/dev/null | grep -v "daily_crawler_730am.sh"; echo "30 7 * * * /home/opc/taichung-building-crawler/daily_crawler_730am.sh") | crontab -

# 建立日誌目錄
mkdir -p logs

# 測試執行
echo "🧪 測試爬蟲..."
python3 -c "import requests, bs4; print('✅ Python 套件已安裝')"

# 顯示 cron 設定
echo ""
echo "✅ 部署完成！"
echo "📅 Cron 設定："
crontab -l | grep daily_crawler
echo ""
echo "💡 提示："
echo "   - 爬蟲將在每天早上 7:30 自動執行"
echo "   - 日誌檔案: ~/taichung-building-crawler/cron_daily_7am.log"
echo "   - 手動執行: ~/taichung-building-crawler/daily_crawler_730am.sh"

# 清理暫存檔
rm -f /tmp/crawler_deploy.tar.gz
EOF

# 上傳並執行遠端設定腳本
echo "🚀 執行遠端設定..."
scp -i "$SSH_KEY_PATH" remote_setup.sh "$REMOTE_USER@$INSTANCE_IP:/tmp/"
ssh -i "$SSH_KEY_PATH" "$REMOTE_USER@$INSTANCE_IP" "bash /tmp/remote_setup.sh"

# 清理本地檔案
rm -f crawler_deploy.tar.gz remote_setup.sh

echo ""
echo "✅ 部署完成！"
echo ""
echo "📌 後續管理："
echo "   1. SSH 連線到 Instance:"
echo "      ssh -i $SSH_KEY_PATH $REMOTE_USER@$INSTANCE_IP"
echo ""
echo "   2. 查看爬蟲狀態:"
echo "      ssh -i $SSH_KEY_PATH $REMOTE_USER@$INSTANCE_IP 'tail -f ~/taichung-building-crawler/cron_daily_7am.log'"
echo ""
echo "   3. 手動執行爬蟲:"
echo "      ssh -i $SSH_KEY_PATH $REMOTE_USER@$INSTANCE_IP '~/taichung-building-crawler/daily_crawler_730am.sh'"
echo ""