#!/bin/bash

# 透過 OCI Serial Console 執行遠端設定
# 不需要 SSH 金鑰

echo "🚀 開始透過 OCI 設定爬蟲環境"
echo "=========================================="

# Instance 資訊
INSTANCE_ID=$(oci compute instance list --compartment-id ocid1.tenancy.oc1..aaaaaaaatj2jclzf26lcsptdllggkodf4kvaj4gajrxtjngakmjl6smu3t6q --query "data[?\"display-name\"=='docuseal-vm'].id" --raw-output)

if [ -z "$INSTANCE_ID" ]; then
    echo "❌ 找不到 Instance"
    exit 1
fi

echo "✅ 找到 Instance: $INSTANCE_ID"

# 建立設定腳本
cat > /tmp/setup_commands.txt << 'EOF'
# 設定爬蟲環境
sudo -u opc bash << 'EOSU'
cd /home/opc

# 安裝必要套件
sudo yum install -y python3 python3-pip cronie
pip3 install --user requests beautifulsoup4

# 建立工作目錄
mkdir -p taichung-building-crawler
cd taichung-building-crawler

# 使用 Instance Principal 下載檔案
export OCI_CLI_AUTH=instance_principal

# 下載爬蟲檔案
oci os object get -bn taichung-building-permits -ns nrsdi1rz5vl8 --name scripts/optimized-crawler-stable.py --file optimized-crawler-stable.py --auth instance_principal
oci os object get -bn taichung-building-permits -ns nrsdi1rz5vl8 --name scripts/cron_daily_crawler_v3.py --file cron_daily_crawler_v3.py --auth instance_principal
oci os object get -bn taichung-building-permits -ns nrsdi1rz5vl8 --name scripts/backup_current_data.py --file backup_current_data.py --auth instance_principal
oci os object get -bn taichung-building-permits -ns nrsdi1rz5vl8 --name scripts/baojia_companies.json --file baojia_companies.json --auth instance_principal

# 建立每日執行腳本
cat > daily_crawler_730am.sh << 'EOFS'
#!/bin/bash
export OCI_CLI_AUTH=instance_principal
export PATH="/home/opc/bin:$PATH"
cd /home/opc/taichung-building-crawler

echo "=========================================="
echo "🕐 每日爬蟲開始: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

python3 cron_daily_crawler_v3.py >> cron_daily_7am.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ 爬蟲執行成功"
    python3 backup_current_data.py >> cron_daily_7am.log 2>&1
else
    echo "❌ 爬蟲執行失敗"
fi

echo "🕐 每日爬蟲結束: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
EOFS

chmod +x daily_crawler_730am.sh

# 修改檔案路徑
sed -i 's|/home/laija/bin/oci|oci|g' *.py
sed -i 's|/mnt/c/claude code/建照爬蟲/oci|/home/opc/taichung-building-crawler|g' *.py

# 設定 cron
(crontab -l 2>/dev/null; echo "30 7 * * * /home/opc/taichung-building-crawler/daily_crawler_730am.sh") | crontab -

# 啟動 cron 服務
sudo systemctl enable crond
sudo systemctl start crond

echo "✅ 設定完成！"
echo "Cron 設定："
crontab -l
EOSU
EOF

echo ""
echo "📌 請按照以下步驟操作："
echo ""
echo "1. 登入 OCI Console："
echo "   https://cloud.oracle.com"
echo ""
echo "2. 前往 Compute > Instances > docuseal-vm"
echo ""
echo "3. 點擊 'Console connection' > 'Launch Cloud Shell connection'"
echo ""
echo "4. 在 Serial Console 中貼上以下命令並執行："
echo ""
echo "----------------------------------------"
cat /tmp/setup_commands.txt
echo "----------------------------------------"
echo ""
echo "5. 等待設定完成後，爬蟲會在每天早上 7:30 自動執行"
echo ""
echo "💡 提示：如果無法使用 Serial Console，請提供 SSH 金鑰路徑"