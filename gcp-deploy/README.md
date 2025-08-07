# GCP 自動化部署版本

這個分支專為在 Google Cloud Platform (GCP) 上自動運行建照爬蟲而設計，使用台灣IP進行爬取。

## 🚀 快速部署

### 步驟 1：創建 GCP 實例
```bash
# 設定專案ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 創建台灣區域的 VM 實例
gcloud compute instances create taichung-crawler \
  --zone=asia-east1-b \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --metadata-from-file=startup-script=startup-script.sh \
  --tags=http-server \
  --scopes=cloud-platform
```

### 步驟 2：自動安裝與配置
實例啟動時會自動執行 `startup-script.sh`：
- 安裝必要套件（python3, wget, git等）
- 下載專案代碼
- 設定OCI CLI
- 啟動定時爬蟲服務

### 步驟 3：監控與管理
```bash
# 查看實例狀態
gcloud compute instances list --filter="name=taichung-crawler"

# SSH 連接實例
gcloud compute ssh taichung-crawler --zone=asia-east1-b

# 查看爬蟲日誌
gcloud compute ssh taichung-crawler --zone=asia-east1-b --command="sudo journalctl -u crawler -f"
```

## 📁 GCP 專用文件

- `startup-script.sh` - 實例啟動腳本
- `gcp-crawler.py` - GCP 環境優化的爬蟲
- `systemd/crawler.service` - 系統服務配置
- `cron/crawler-cron` - 定時任務配置
- `config/oci-config.template` - OCI配置模板

## ⚙️ 自動化功能

### 定時執行
- 每日上午8:00自動執行爬蟲
- 每週日進行完整備份
- 自動更新執行日誌

### 錯誤處理
- 爬蟲失敗時自動重試
- 發送通知到指定郵箱
- 自動備份錯誤日誌

### 成本優化
- 使用 e2-micro 免費額度實例
- 自動關閉閒置連線
- 僅在需要時運行

## 🌐 台灣IP優勢

使用 asia-east1-b (台灣) 區域：
- ✅ 台灣IP位址，無地域限制
- ✅ 低延遲連線到台中市政府網站
- ✅ 穩定的網路連線品質

## 📊 監控面板

GCP Console 監控項目：
- CPU 使用率
- 記憶體使用率  
- 網路流量
- 磁碟使用量
- 爬蟲成功率

## 🔐 安全設定

- 使用 Service Account 進行認證
- OCI 金鑰加密存儲
- 防火牆規則僅允許必要連線
- 定期更新系統套件

---

## 手動執行（可選）

如果需要立即爬取：
```bash
# SSH 連接到實例
gcloud compute ssh taichung-crawler --zone=asia-east1-b

# 手動執行爬蟲
cd /opt/crawler && python3 simple-crawl.py 114 1143
```