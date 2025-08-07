# PowerShell 腳本 - 檢查 GCP 爬蟲狀態

Write-Host "=== 檢查 Google Cloud 爬蟲狀態 ===" -ForegroundColor Green
Write-Host ""

# 1. 檢查實例狀態
Write-Host "1. 檢查實例狀態..." -ForegroundColor Yellow
gcloud compute instances describe taichung-crawler-gcp --zone=asia-east1-b --format="yaml(name,status,networkInterfaces[0].accessConfigs[0].natIP)"

Write-Host ""
Write-Host "2. SSH 連線並檢查爬蟲..." -ForegroundColor Yellow
Write-Host "執行以下指令："
Write-Host ""
Write-Host "gcloud compute ssh taichung-crawler-gcp --zone=asia-east1-b" -ForegroundColor Cyan
Write-Host ""
Write-Host "連線後，在實例內執行：" -ForegroundColor Yellow
Write-Host @"
# 檢查爬蟲程式是否存在
ls -la /home/crawler/

# 如果存在，查看日誌
if [ -f /home/crawler/crawler.log ]; then
    echo "=== 爬蟲日誌 ==="
    sudo tail -20 /home/crawler/crawler.log
fi

# 檢查啟動腳本執行狀態
echo "=== 啟動腳本狀態 ==="
sudo journalctl -u google-startup-scripts.service --no-pager -n 50

# 手動執行爬蟲
if [ -f /home/crawler/gcp_to_oci_crawler.py ]; then
    echo "=== 手動執行爬蟲 ==="
    cd /home/crawler
    sudo python3 gcp_to_oci_crawler.py
fi

# 檢查 cron 設定
echo "=== Cron 設定 ==="
sudo crontab -l
"@ -ForegroundColor White

Write-Host ""
Write-Host "3. 檢查 OCI 資料更新..." -ForegroundColor Yellow
Write-Host "開啟瀏覽器查看："
Write-Host "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html" -ForegroundColor Cyan