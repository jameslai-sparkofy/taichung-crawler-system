#!/bin/bash
# OCI Compute Instance 設定腳本

echo "🚀 開始設定 OCI Compute Instance 爬蟲環境..."

# 更新系統
echo "📦 更新系統套件..."
sudo apt-get update
sudo apt-get upgrade -y

# 安裝必要套件
echo "📦 安裝必要套件..."
sudo apt-get install -y python3-pip python3-venv wget curl git

# 建立虛擬環境
echo "🐍 建立 Python 虛擬環境..."
cd /home/ubuntu
python3 -m venv crawler_env
source crawler_env/bin/activate

# 安裝 Python 套件
echo "📦 安裝 Python 套件..."
pip install --upgrade pip
pip install oci requests beautifulsoup4 lxml

# 建立工作目錄
echo "📁 建立工作目錄..."
mkdir -p /home/ubuntu/crawler
cd /home/ubuntu/crawler

# 複製爬蟲程式（請手動上傳 crawler-compute.py）
echo "⚠️ 請將 crawler-compute.py 上傳到 /home/ubuntu/crawler/"

# 設定 OCI CLI（如果使用設定檔認證）
echo "🔧 設定 OCI CLI..."
if [ ! -f ~/.oci/config ]; then
    mkdir -p ~/.oci
    echo "⚠️ 請建立 ~/.oci/config 檔案或使用 Instance Principal"
fi

# 建立執行腳本
echo "📝 建立執行腳本..."
cat > /home/ubuntu/run_crawler.sh << 'EOF'
#!/bin/bash
# 爬蟲執行腳本

# 啟動虛擬環境
source /home/ubuntu/crawler_env/bin/activate

# 執行爬蟲
cd /home/ubuntu/crawler
python3 crawler-compute.py

# 紀錄執行時間
echo "爬蟲執行完成: $(date)" >> /home/ubuntu/crawler_run.log
EOF

chmod +x /home/ubuntu/run_crawler.sh

# 設定 cron job
echo "⏰ 設定 cron job..."
(crontab -l 2>/dev/null; echo "25 6 * * * /home/ubuntu/run_crawler.sh >> /home/ubuntu/cron.log 2>&1") | crontab -

# 建立測試腳本
echo "📝 建立測試腳本..."
cat > /home/ubuntu/test_crawler.sh << 'EOF'
#!/bin/bash
# 測試爬蟲執行

echo "開始測試爬蟲..."
source /home/ubuntu/crawler_env/bin/activate
cd /home/ubuntu/crawler
python3 -c "
from crawler_compute import OCIStorage
storage = OCIStorage()
progress = storage.get_current_progress()
print('連線測試成功！')
print(f'目前進度: {progress}')
"
EOF

chmod +x /home/ubuntu/test_crawler.sh

echo "✅ 設定完成！"
echo ""
echo "下一步："
echo "1. 上傳 crawler-compute.py 到 /home/ubuntu/crawler/"
echo "2. 設定 OCI 認證（Instance Principal 或設定檔）"
echo "3. 執行 /home/ubuntu/test_crawler.sh 測試連線"
echo "4. 執行 /home/ubuntu/run_crawler.sh 手動執行爬蟲"
echo ""
echo "Cron job 已設定為每天早上 6:25 執行"