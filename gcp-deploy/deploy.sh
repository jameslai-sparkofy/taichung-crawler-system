#!/bin/bash
# GCP 部署腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# 檢查必要工具
log "🔍 檢查必要工具..."
command -v gcloud >/dev/null 2>&1 || error "請先安裝 Google Cloud SDK"

# 設定變數
PROJECT_ID="${PROJECT_ID:-}"
INSTANCE_NAME="${INSTANCE_NAME:-taichung-crawler}"
ZONE="${ZONE:-asia-east1-b}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-micro}"
GITHUB_REPO="${GITHUB_REPO:-}"

# 互動式設定
if [ -z "$PROJECT_ID" ]; then
    echo -n "請輸入 GCP Project ID: "
    read PROJECT_ID
fi

if [ -z "$GITHUB_REPO" ]; then
    echo -n "請輸入 GitHub Repository (格式: username/repo-name): "
    read GITHUB_REPO
fi

log "📋 部署配置："
log "   Project ID: $PROJECT_ID"
log "   Instance Name: $INSTANCE_NAME" 
log "   Zone: $ZONE"
log "   Machine Type: $MACHINE_TYPE"
log "   GitHub Repo: $GITHUB_REPO"

echo -n "確認開始部署? (y/N): "
read confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    log "🚫 部署取消"
    exit 0
fi

# 設定 GCP 專案
log "⚙️ 設定 GCP 專案..."
gcloud config set project $PROJECT_ID

# 啟用必要的 API
log "🔌 啟用必要的 GCP API..."
gcloud services enable compute.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

# 更新啟動腳本中的 GitHub 倉庫
log "📝 更新啟動腳本..."
sed -i "s|https://github.com/your-username/taichung-building-permits.git|https://github.com/$GITHUB_REPO.git|g" startup-script.sh

# 檢查實例是否已存在
if gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE >/dev/null 2>&1; then
    warn "實例 $INSTANCE_NAME 已存在"
    echo -n "是否刪除並重新創建? (y/N): "
    read recreate
    if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
        log "🗑️ 刪除現有實例..."
        gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet
    else
        error "部署取消"
    fi
fi

# 創建實例
log "🚀 創建 GCP 實例..."
gcloud compute instances create $INSTANCE_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --metadata-from-file=startup-script=startup-script.sh \
    --tags=http-server,crawler \
    --scopes=cloud-platform \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --create-disk=auto-delete=yes,boot=yes

# 等待實例啟動
log "⏳ 等待實例啟動..."
sleep 30

# 檢查實例狀態
log "📊 檢查實例狀態..."
gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="table(name,status,machineType.scope(machineTypes),networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"

# 獲取外部 IP
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

success "🎉 部署完成！"
log "📋 實例資訊："
log "   名稱: $INSTANCE_NAME"
log "   區域: $ZONE"
log "   外部 IP: $EXTERNAL_IP"
log "   SSH 連接: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"

log "📖 後續設定步驟："
log "   1. 等待 5-10 分鐘讓啟動腳本完成安裝"
log "   2. SSH 連接到實例："
log "      gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
log "   3. 查看設定指南："
log "      cat /root/SETUP_GUIDE.txt"
log "   4. 設定 OCI 認證資訊"
log "   5. 測試爬蟲執行"

log "🔍 實用指令："
log "   查看啟動日誌: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo tail -f /var/log/crawler-setup.log'"
log "   檢查爬蟲狀態: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo /opt/crawler/check-status.sh'"
log "   立即執行爬蟲: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo systemctl start crawler.service'"
log "   查看爬蟲日誌: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u crawler -f'"

log "💰 預估成本: 使用 e2-micro 實例，每月約 $5-10 USD"