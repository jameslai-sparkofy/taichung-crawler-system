# Google Cloud 爬蟲手動設定指南

## 認證問題說明
Google Cloud CLI (gcloud) 需要 OAuth 認證才能操作資源。如果遇到逾時問題，通常是因為：
1. 認證過期
2. 需要瀏覽器互動式登入
3. WSL 環境無法開啟瀏覽器

## 解決方案

### 方案 1：使用 Windows CMD 執行
在 Windows 命令提示字元中執行：
```cmd
cd C:\tmp
gcloud auth login
gcloud compute instances create taichung-crawler-gcp --zone=asia-east1-b --machine-type=e2-micro --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud --boot-disk-size=20GB --metadata-from-file=startup-script=gcp_oci_startup.sh --tags=http-server --project=taichung-crawler
```

### 方案 2：使用無瀏覽器認證
```bash
gcloud auth login --no-launch-browser
```
會顯示一個網址，手動在瀏覽器開啟並複製驗證碼回來。

### 方案 3：使用 Google Cloud Console 網頁介面
1. 開啟 https://console.cloud.google.com
2. 選擇專案 "taichung-crawler"
3. 前往 Compute Engine > VM 執行個體
4. 點擊「建立執行個體」
5. 設定：
   - 名稱：taichung-crawler-gcp
   - 區域：asia-east1 (台灣)
   - 區域：asia-east1-b
   - 機器類型：E2-micro
   - 開機磁碟：Ubuntu 22.04 LTS, 20GB
   - 進階選項 > 管理 > 中繼資料：
     - 金鑰：startup-script
     - 值：貼上 /tmp/gcp_oci_startup.sh 的內容

## 建立後的驗證步驟

### 1. 使用 Cloud Shell (網頁版)
在 Google Cloud Console 右上角點擊 Cloud Shell 圖示，然後：
```bash
gcloud compute ssh taichung-crawler-gcp --zone=asia-east1-b
```

### 2. 檢查爬蟲執行狀態
```bash
# 查看爬蟲日誌
sudo tail -f /home/crawler/crawler.log

# 檢查 cron 設定
sudo crontab -l -u root

# 手動執行爬蟲
cd /home/crawler
sudo python3 gcp_to_oci_crawler.py
```

### 3. 驗證 OCI 上傳
檢查以下網址是否有更新：
https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html

## 常見問題

### Q: 實例建立失敗
A: 檢查是否有啟用 Compute Engine API，或是否超過免費額度。

### Q: 爬蟲無法執行
A: SSH 進入實例，檢查 `/var/log/syslog` 查看啟動腳本是否正確執行。

### Q: OCI 上傳失敗
A: 確認 OCI 認證資訊是否正確，可以手動測試：
```bash
oci os object list --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits
```

## 替代方案：本地執行爬蟲
如果 GCP 部署有問題，可以在本地執行：
```bash
cd /mnt/c/claude\ code/建照爬蟲/gcp
python3 manual_gcp_crawler.py
```
但注意本地 IP 可能被封鎖。