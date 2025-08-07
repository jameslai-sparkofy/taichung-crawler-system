#!/bin/bash

echo "=== Google Cloud 爬蟲實例建立腳本 ==="
echo ""

# 檢查 gcloud 是否已安裝
if ! command -v gcloud &> /dev/null; then
    echo "❌ 錯誤：gcloud 未安裝"
    echo "請先安裝 Google Cloud SDK"
    exit 1
fi

# 設定專案
echo "📋 設定專案..."
gcloud config set project taichung-crawler

# 檢查認證
echo ""
echo "🔐 檢查認證狀態..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "需要登入 Google Cloud："
    gcloud auth login
fi

# 建立 Storage Bucket
echo ""
echo "🗄️  建立 Storage Bucket..."
if gsutil ls -b gs://taichung-crawler-permits &> /dev/null; then
    echo "   Storage Bucket 已存在"
else
    gsutil mb -l asia-east1 gs://taichung-crawler-permits
    echo "   ✅ Storage Bucket 建立成功"
fi

# 檢查啟動腳本
if [ ! -f "/tmp/gcp_crawler_startup.sh" ]; then
    echo ""
    echo "❌ 錯誤：找不到啟動腳本 /tmp/gcp_crawler_startup.sh"
    echo "請確認腳本已建立"
    exit 1
fi

# 建立實例
echo ""
echo "🖥️  建立 Compute Engine 實例..."
echo "   區域: asia-east1-b (台灣)"
echo "   機器類型: e2-micro"
echo "   作業系統: Ubuntu 22.04 LTS"

gcloud compute instances create taichung-crawler \
    --zone=asia-east1-b \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --metadata-from-file=startup-script=/tmp/gcp_crawler_startup.sh \
    --tags=http-server

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 實例建立成功！"
    echo ""
    echo "📝 實例資訊："
    gcloud compute instances describe taichung-crawler --zone=asia-east1-b --format="yaml(name,status,networkInterfaces[0].accessConfigs[0].natIP)"
    
    echo ""
    echo "🚀 下一步："
    echo "1. 等待 2-3 分鐘讓實例完成初始化"
    echo "2. SSH 連線到實例："
    echo "   gcloud compute ssh taichung-crawler --zone=asia-east1-b"
    echo "3. 檢查爬蟲日誌："
    echo "   tail -f /home/crawler/crawler.log"
    echo "4. 檢查 cron 設定："
    echo "   crontab -l"
else
    echo ""
    echo "❌ 實例建立失敗，請檢查錯誤訊息"
fi