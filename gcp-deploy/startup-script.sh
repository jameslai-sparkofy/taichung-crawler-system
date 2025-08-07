#!/bin/bash
# GCP VM 啟動腳本 - 自動安裝並配置建照爬蟲

set -e

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/crawler-setup.log
}

log "🚀 開始設定建照爬蟲環境..."

# 更新系統
log "📦 更新系統套件..."
apt-get update -y
apt-get upgrade -y

# 安裝必要套件
log "📦 安裝必要套件..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    git \
    unzip \
    cron \
    supervisor \
    jq

# 安裝 Python 套件
log "🐍 安裝 Python 套件..."
pip3 install \
    requests \
    beautifulsoup4 \
    lxml \
    python-dateutil

# 安裝 OCI CLI
log "☁️ 安裝 OCI CLI..."
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
export PATH="$PATH:/root/bin"
echo 'export PATH="$PATH:/root/bin"' >> /root/.bashrc

# 創建工作目錄
log "📁 創建工作目錄..."
mkdir -p /opt/crawler
cd /opt/crawler

# 下載專案代碼
log "📥 下載專案代碼..."
git clone -b gcp-deploy https://github.com/your-username/taichung-building-permits.git .

# 設定 OCI 配置（需要用戶提供）
log "⚙️ 設定 OCI 配置..."
mkdir -p /root/.oci
cat > /root/.oci/config << 'EOL'
[DEFAULT]
user=ocid1.user.oc1..your-user-ocid
fingerprint=your-fingerprint
tenancy=ocid1.tenancy.oc1..your-tenancy-ocid
region=ap-tokyo-1
key_file=/root/.oci/key.pem
EOL

# 創建佔位符金鑰文件（需要用戶手動上傳真實金鑰）
log "🔑 創建 OCI 金鑰佔位符..."
cat > /root/.oci/key.pem << 'EOL'
# 請將您的 OCI 私鑰內容放在這裡
# 格式：
# -----BEGIN PRIVATE KEY-----
# [your-private-key-content]
# -----END PRIVATE KEY-----
EOL
chmod 600 /root/.oci/key.pem

# 創建爬蟲服務腳本
log "🤖 創建爬蟲服務..."
cat > /opt/crawler/crawler-service.py << 'EOL'
#!/usr/bin/env python3
"""
GCP 爬蟲服務 - 定時執行建照爬取
"""
import subprocess
import sys
import os
import json
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def run_crawler():
    """執行爬蟲"""
    log("🚀 開始執行建照爬蟲...")
    
    try:
        # 切換到爬蟲目錄
        os.chdir('/opt/crawler/oci')
        
        # 檢查當前最新序號
        log("📊 檢查當前資料狀態...")
        result = subprocess.run([
            '/root/bin/oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits', 
            '--name', 'permits.json',
            '--file', '/tmp/current_permits.json'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"❌ 下載現有資料失敗: {result.stderr}")
            return False
        
        # 解析當前最新序號
        with open('/tmp/current_permits.json', 'r') as f:
            data = json.load(f)
            permits = data.get('permits', [])
            y114_permits = [p for p in permits if p.get('permitYear') == 114]
            
            if y114_permits:
                latest = max(y114_permits, key=lambda x: x.get('sequenceNumber', 0))
                current_seq = latest['sequenceNumber']
                log(f"📍 當前最新序號: {current_seq} ({latest['permitNumber']})")
                start_seq = current_seq + 1
            else:
                log("⚠️ 未找到114年資料，從1開始爬取")
                start_seq = 1
        
        # 執行爬蟲（爬取50筆或直到空白）
        log(f"🔍 開始從序號 {start_seq} 爬取...")
        result = subprocess.run([
            'python3', 'simple-crawl.py', '114', str(start_seq), str(start_seq + 49)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            log("✅ 爬蟲執行成功")
            log(f"📄 輸出: {result.stdout}")
            return True
        else:
            log(f"❌ 爬蟲執行失敗: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"💥 爬蟲執行異常: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_crawler()
    sys.exit(0 if success else 1)
EOL

chmod +x /opt/crawler/crawler-service.py

# 創建 systemd 服務
log "⚙️ 創建 systemd 服務..."
cat > /etc/systemd/system/crawler.service << 'EOL'
[Unit]
Description=Taiwan Building Permit Crawler
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/opt/crawler
ExecStart=/usr/bin/python3 /opt/crawler/crawler-service.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

# 創建 cron 任務
log "⏰ 設定定時任務..."
cat > /etc/cron.d/crawler << 'EOL'
# 每日上午8:00執行爬蟲
0 8 * * * root /bin/systemctl start crawler.service

# 每週日凌晨2:00備份
0 2 * * 0 root /opt/crawler/backup.sh
EOL

# 創建備份腳本
log "💾 創建備份腳本..."
cat > /opt/crawler/backup.sh << 'EOL'
#!/bin/bash
# 每週備份腳本

DATE=$(date +%Y%m%d)
BACKUP_DIR="/opt/crawler/backups"

mkdir -p $BACKUP_DIR

# 下載當前資料進行備份
/root/bin/oci os object get \
  --namespace nrsdi1rz5vl8 \
  --bucket-name taichung-building-permits \
  --name permits.json \
  --file "$BACKUP_DIR/permits_$DATE.json"

# 只保留最近30天的備份
find $BACKUP_DIR -name "permits_*.json" -mtime +30 -delete

echo "[$(date)] 備份完成: permits_$DATE.json"
EOL

chmod +x /opt/crawler/backup.sh

# 啟用服務
log "🔄 啟用服務..."
systemctl daemon-reload
systemctl enable cron

# 測試 OCI 連接（會失敗，因為需要真實金鑰）
log "🔗 測試 OCI 連接..."
/root/bin/oci os ns get || log "⚠️ OCI 連接失敗 - 請手動設定金鑰"

# 創建狀態檢查腳本
log "📊 創建狀態檢查腳本..."
cat > /opt/crawler/check-status.sh << 'EOL'
#!/bin/bash
echo "=== 建照爬蟲狀態檢查 ==="
echo "時間: $(date)"
echo "系統: $(uname -a)"
echo "Python: $(python3 --version)"
echo "OCI CLI: $(/root/bin/oci --version || echo '未安裝或配置錯誤')"
echo "磁碟空間: $(df -h / | tail -1)"
echo "記憶體使用: $(free -h)"
echo "最近爬蟲執行:"
journalctl -u crawler --since "24 hours ago" | tail -10
echo "========================="
EOL

chmod +x /opt/crawler/check-status.sh

# 設定完成
log "✅ 建照爬蟲環境設定完成！"
log "📋 後續步驟："
log "   1. SSH 連接到此實例"
log "   2. 編輯 /root/.oci/config 設定您的 OCI 認證"
log "   3. 將您的私鑰內容放入 /root/.oci/key.pem"
log "   4. 執行 /opt/crawler/check-status.sh 檢查狀態"
log "   5. 手動測試: python3 /opt/crawler/crawler-service.py"

# 創建設定指南
cat > /root/SETUP_GUIDE.txt << 'EOL'
建照爬蟲 GCP 設定指南
====================

1. 編輯 OCI 配置:
   nano /root/.oci/config
   
2. 設定 OCI 私鑰:
   nano /root/.oci/key.pem
   （貼上您的 OCI 私鑰內容）
   
3. 測試連接:
   /root/bin/oci os ns get
   
4. 手動執行爬蟲測試:
   python3 /opt/crawler/crawler-service.py
   
5. 檢查服務狀態:
   systemctl status crawler
   
6. 查看爬蟲日誌:
   journalctl -u crawler -f
   
7. 立即執行爬蟲:
   systemctl start crawler.service

定時任務已設定為每日上午 8:00 自動執行。
EOL

log "📖 設定指南已保存至 /root/SETUP_GUIDE.txt"