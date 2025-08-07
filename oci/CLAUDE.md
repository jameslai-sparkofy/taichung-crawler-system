# 台中市建照爬蟲專案記錄 (GCP 自動化版本)

## 🚀 GCP 自動化部署

這個版本專為在 Google Cloud Platform 上自動運行而設計，使用台灣 IP 進行爬取。

### 一鍵部署
```bash
# 克隆專案
git clone -b gcp-deploy https://github.com/your-username/taichung-building-permits.git
cd taichung-building-permits

# 執行部署腳本
chmod +x gcp-deploy/deploy.sh
./gcp-deploy/deploy.sh
```

### 手動部署步驟
```bash
# 1. 設定 GCP 專案
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 2. 創建 VM 實例
gcloud compute instances create taichung-crawler \
  --zone=asia-east1-b \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --metadata-from-file=startup-script=gcp-deploy/startup-script.sh \
  --tags=http-server \
  --scopes=cloud-platform

# 3. SSH 連接並設定 OCI 認證
gcloud compute ssh taichung-crawler --zone=asia-east1-b
```

## 🤖 自動化功能

### 定時執行
- **每日 8:00** 自動爬取最新建照
- **每週日 2:00** 自動備份資料
- **錯誤重試機制** 自動處理失敗

### 監控與通知
- 系統日誌記錄
- 爬蟲執行狀態追蹤
- GCP 監控面板

### 成本優化
- 使用 e2-micro 免費額度
- 自動關閉閒置資源
- 預估每月 $5-10 USD

## 📊 原始項目資訊

### 保留的正確爬蟲程式（共5個）

#### 1. **simple-crawl.py** ⭐ 主要使用
- 簡單執行腳本，最常用
- 用法：`python3 simple-crawl.py 年份 起始序號 [結束序號]`
- 使用wget + cookie機制（關鍵成功因素）
- 自動上傳到OCI

#### 2. **optimized-crawler-stable.py**
- 核心穩定版爬蟲
- simple-crawl.py的基礎

#### 3. **recrawl-empty-stable.py**
- 專門重新爬取空白資料

#### 4. **enhanced-crawler.py**
- 增強版，包含寶佳建案識別

#### 5. **cron_daily_crawler_v2.py**
- 每日排程爬蟲

## ⚠️ 重要提醒

### 關鍵成功因素
1. **必須使用台灣IP** - GCP asia-east1-b 區域
2. **必須使用wget + cookie機制**
   - 第一次請求：建立session並儲存cookie
   - 第二次請求：使用cookie取得實際資料
   - Python requests庫會失敗！

### 必須解析的欄位
- 樓層 (floors)
- 棟數 (buildings) 
- 戶數 (units)
- 總樓地板面積 (totalFloorArea)
- 發照日期 (issueDate)

## 📊 資料統計（2025-08-07更新）

- **總計**: 4,599 筆
- **114年**: 1,142 筆（最新序號：1142，114中都建字第01142號）
- **113年**: 2,112 筆
- **112年**: 1,345 筆

### 最近爬取記錄
- 2025-08-07：成功爬取114年序號1137-1142共6筆

## 🔧 GCP 管理指令

### 實例管理
```bash
# 查看實例狀態
gcloud compute instances list --filter="name=taichung-crawler"

# 啟動/停止實例
gcloud compute instances start taichung-crawler --zone=asia-east1-b
gcloud compute instances stop taichung-crawler --zone=asia-east1-b

# SSH 連接
gcloud compute ssh taichung-crawler --zone=asia-east1-b
```

### 服務管理
```bash
# 查看爬蟲服務狀態
sudo systemctl status crawler

# 立即執行爬蟲
sudo systemctl start crawler.service

# 查看日誌
sudo journalctl -u crawler -f

# 檢查整體狀態
sudo /opt/crawler/check-status.sh
```

### 資料備份
```bash
# 手動備份
sudo /opt/crawler/backup.sh

# 查看備份
ls -la /opt/crawler/backups/
```

## 🔐 安全設定

### OCI 認證設定
```bash
# 編輯 OCI 配置
sudo nano /root/.oci/config

# 設定私鑰
sudo nano /root/.oci/key.pem
sudo chmod 600 /root/.oci/key.pem

# 測試連接
/root/bin/oci os ns get
```

## 🌐 線上資源

- **查詢網頁**: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html
- **建照資料**: permits.json
- **執行日誌**: data/crawl-logs.json

## 📁 GCP 專案結構

```
/opt/crawler/                    # GCP 實例上的位置
├── oci/
│   ├── simple-crawl.py         # 主要爬蟲腳本 ⭐
│   ├── optimized-crawler-stable.py
│   ├── recrawl-empty-stable.py
│   ├── enhanced-crawler.py
│   └── cron_daily_crawler_v2.py
├── crawler-service.py          # GCP 服務包裝腳本
├── backup.sh                   # 自動備份腳本
├── check-status.sh             # 狀態檢查腳本
└── backups/                    # 備份目錄
```

## 🎯 預期效果

1. **自動化運行** - 無需手動干預
2. **台灣IP優勢** - 無地域限制問題
3. **定時更新** - 每日自動爬取新建照
4. **成本控制** - 使用免費額度，低成本運行
5. **監控完善** - 完整的日誌和狀態追蹤

---
最後更新：2025-08-07
版本：GCP 自動化版本
作者：Claude