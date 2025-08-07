# Google Cloud 台中建照爬蟲系統

## 概述
使用 Google Cloud Platform (GCP) 在台灣區域建立爬蟲系統，解決 OCI 國外 IP 被封鎖的問題。

## 系統架構
- **運算實例**: Google Compute Engine (asia-east1-b 台灣區域)
- **儲存**: Google Cloud Storage
- **自動化**: Cron job 每日 7:30 執行

## 快速開始

### 1. 設定 Google Cloud CLI
```bash
# 安裝 gcloud (如果尚未安裝)
# Windows: 下載 Google Cloud SDK installer

# 登入
gcloud auth login

# 設定專案
gcloud config set project taichung-crawler
```

### 2. 建立 Storage Bucket
```bash
gsutil mb -l asia-east1 gs://taichung-crawler-permits
```

### 3. 本地測試爬蟲
```bash
cd /mnt/c/claude\ code/建照爬蟲/gcp
python3 manual_gcp_crawler.py
```

### 4. 建立 GCP 實例（自動爬蟲）
```bash
# 建立實例
gcloud compute instances create taichung-crawler \
  --zone=asia-east1-b \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --metadata-from-file=startup-script=/tmp/gcp_crawler_startup.sh \
  --tags=http-server

# SSH 連線
gcloud compute ssh taichung-crawler --zone=asia-east1-b

# 檢查爬蟲狀態
tail -f /home/crawler/crawler.log
```

## 檔案說明
- `manual_gcp_crawler.py`: 手動爬蟲程式（可在本地或 GCP 執行）
- `gcp_crawler_startup.sh`: GCP 實例啟動腳本
- `setup_gcp_crawler.sh`: 設定指南

## 爬蟲功能
1. **智慧爬取**: 從最新序號開始，避免重複
2. **空白偵測**: 連續5筆空白自動停止
3. **錯誤處理**: 連續3次錯誤自動停止
4. **資料同步**: 自動上傳到 Google Cloud Storage
5. **必要欄位**: 
   - 樓層 (floors)
   - 棟數 (buildings)
   - 戶數 (units)
   - 總樓地板面積 (totalFloorArea)
   - 發照日期 (issueDate)

## 資料格式
```json
{
  "indexKey": "11410100100",
  "year": 114,
  "sequence": 1,
  "permitNumber": "114中都建字第00001號",
  "applicant": "某某建設",
  "address": "台中市XX區XX路",
  "floors": 15,
  "buildings": 1,
  "units": 60,
  "totalFloorArea": 12345.67,
  "issueDate": "2025-01-15",
  "crawlTime": "2025-08-02T10:30:00"
}
```

## 維護指令

### 檢查實例狀態
```bash
gcloud compute instances list --filter="name=taichung-crawler"
```

### 停止實例
```bash
gcloud compute instances stop taichung-crawler --zone=asia-east1-b
```

### 啟動實例
```bash
gcloud compute instances start taichung-crawler --zone=asia-east1-b
```

### 刪除實例
```bash
gcloud compute instances delete taichung-crawler --zone=asia-east1-b
```

### 下載資料
```bash
gsutil cp gs://taichung-crawler-permits/permits.json .
```

## 費用估算
- **Compute Engine e2-micro**: 免費額度內（每月 744 小時）
- **Cloud Storage**: 前 5GB 免費
- **網路流量**: 每月 1GB 免費額度
- **預估月費**: $0-5 USD（視使用量）

## 注意事項
1. 確保使用台灣區域 (asia-east1) 以獲得台灣 IP
2. 爬蟲延遲設為 1.5 秒避免被封鎖
3. 定期檢查爬蟲執行狀況
4. 資料會自動備份到 Cloud Storage