# 台中市建照爬蟲專案

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Taiwan IP Required](https://img.shields.io/badge/Taiwan%20IP-Required-red.svg)](https://github.com/your-username/taichung-building-permits)

自動爬取台中市建築執照資料的專案，包含網頁查詢介面和寶佳建案識別功能。

## 🚀 快速開始

### 選擇部署方式

本專案提供兩種部署方式：

#### 📱 方式一：本地手動執行 (main 分支)
```bash
git clone https://github.com/your-username/taichung-building-permits.git
cd taichung-building-permits/oci
python3 simple-crawl.py 114 1143
```
適用於：偶爾手動執行爬蟲的使用者

#### ☁️ 方式二：GCP 自動化部署 (gcp-deploy 分支) **推薦**
```bash
git clone -b gcp-deploy https://github.com/your-username/taichung-building-permits.git
cd taichung-building-permits
./gcp-deploy/deploy.sh
```
適用於：希望自動化定時執行的使用者

## 📊 專案特色

- **✅ 4,599+ 建照資料** - 涵蓋114年、113年、112年
- **✅ 台灣IP優勢** - 支援GCP台灣區域部署
- **✅ 網頁查詢介面** - 即時搜尋和篩選功能
- **✅ 寶佳建案識別** - 自動標記74家寶佳體系公司
- **✅ 自動化執行** - 每日定時爬取和備份
- **✅ 錯誤處理** - 完整的重試機制和日誌記錄

## 📁 分支說明

### 🔹 main 分支 - 本地手動版本
- 適合本地執行和開發
- 包含完整的爬蟲程式和文檔
- 需要手動執行和管理

**主要文件**：
```
oci/
├── simple-crawl.py              # 主要爬蟲腳本 ⭐
├── optimized-crawler-stable.py  # 核心穩定版  
├── recrawl-empty-stable.py      # 空白資料重爬
├── enhanced-crawler.py          # 增強版（含寶佳識別）
├── cron_daily_crawler_v2.py     # 每日排程爬蟲
├── index.html                   # 網頁查詢介面
└── CLAUDE.md                    # 完整使用指南
```

### 🔹 gcp-deploy 分支 - GCP 自動化版本 **推薦**
- 專為 Google Cloud Platform 設計
- 使用台灣IP (asia-east1-b) 無地域限制
- 全自動化部署和執行
- 每日 8:00 自動爬取，每週日自動備份

**主要功能**：
- 🤖 **一鍵部署** - 執行 `deploy.sh` 即可完成設定
- ⏰ **定時執行** - 每日 8:00 自動爬取新建照
- 💾 **自動備份** - 每週日 2:00 備份資料  
- 📊 **監控面板** - GCP Console 完整監控
- 💰 **成本優化** - 使用 e2-micro 免費額度，約 $5-10/月

## 🌐 線上查詢

**建照查詢網頁**: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html

功能包括：
- 🔍 即時搜尋建照資料
- 📅 日期區間篩選
- 🏠 行政區篩選  
- 🏢 寶佳建案一鍵篩選
- 📊 統計資訊顯示

## 🔧 技術架構

### 核心技術
- **Python 3.8+** - 爬蟲程式語言
- **wget + cookie** - 關鍵爬取機制（不能用 requests）
- **BeautifulSoup** - HTML 解析
- **OCI Object Storage** - 資料儲存

### 地域限制解決方案
台中市政府網站有地域限制，必須使用**台灣IP**：
- **本地版本**: 需要台灣網路環境
- **GCP版本**: 使用 asia-east1-b (台灣) 區域 ✅

### 資料格式
```json
{
  "permitNumber": "114中都建字第01142號",
  "applicantName": "張登Ｏ 等如附表",
  "siteAddress": "臺中市北屯區...",
  "district": "北屯區",
  "floors": 3,
  "buildings": 1,
  "units": 1,
  "totalFloorArea": 150.5,
  "issueDate": "2025-07-31"
}
```

## 📊 資料統計 (2025-08-07)

| 年份 | 建照數量 | 最新序號 | 最後更新 |
|------|----------|----------|----------|
| 114年 | 1,142筆 | 1142號 | 2025-08-07 |
| 113年 | 2,112筆 | 完整 | 2025-07-28 |
| 112年 | 1,345筆 | 完整 | 2025-07-28 |
| **總計** | **4,599筆** | | |

### 寶佳建案統計
- **寶佳體系公司**: 74家
- **寶佳建照總數**: 205筆
- **主要建商**: 勝發建設(189件)、泓瑞建設(2件)、勝華建設(2件)

## ⚙️ 部署指南

### GCP 自動化部署 (推薦)

1. **安裝 Google Cloud SDK**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud auth login
```

2. **克隆並部署**
```bash
git clone -b gcp-deploy https://github.com/your-username/taichung-building-permits.git
cd taichung-building-permits
chmod +x gcp-deploy/deploy.sh
./gcp-deploy/deploy.sh
```

3. **設定 OCI 認證**
```bash
# SSH 連接到 GCP 實例
gcloud compute ssh taichung-crawler --zone=asia-east1-b

# 編輯配置文件
sudo nano /root/.oci/config
sudo nano /root/.oci/key.pem

# 測試連接
/root/bin/oci os ns get
```

### 本地手動部署

1. **安裝依賴**
```bash
pip3 install requests beautifulsoup4 lxml
```

2. **設定 OCI CLI**
```bash
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
oci setup config
```

3. **執行爬蟲**
```bash
cd oci
python3 simple-crawl.py 114 1143
```

## 🔍 使用方法

### 基本爬取
```bash
# 爬取特定範圍
python3 simple-crawl.py 114 1143 1200

# 爬取直到空白
python3 simple-crawl.py 114 1143

# 重新爬取空白資料
python3 recrawl-empty-stable.py

# 使用增強版（含寶佳識別）
python3 enhanced-crawler.py 114 1143 1200
```

### GCP 管理指令
```bash
# 查看實例狀態
gcloud compute instances list --filter="name=taichung-crawler"

# 立即執行爬蟲
gcloud compute ssh taichung-crawler --zone=asia-east1-b --command="sudo systemctl start crawler.service"

# 查看爬蟲日誌
gcloud compute ssh taichung-crawler --zone=asia-east1-b --command="sudo journalctl -u crawler -f"

# 檢查整體狀態
gcloud compute ssh taichung-crawler --zone=asia-east1-b --command="sudo /opt/crawler/check-status.sh"
```

## ⚠️ 重要注意事項

### 關鍵成功因素
1. **必須使用台灣IP** - 台中市政府網站有地域限制
2. **必須使用 wget + cookie 機制** - Python requests 會失敗
3. **必須解析完整欄位** - floors, buildings, units, totalFloorArea, issueDate

### 常見問題
- ❌ **爬蟲沒取得資料** → 確保使用 `simple-crawl.py`
- ❌ **地域限制錯誤** → 使用台灣IP或GCP台灣區域  
- ❌ **網頁執行記錄不正確** → 檢查日誌格式

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

## 🤝 貢獻

歡迎提交 Issues 和 Pull Requests！

## 📞 支援

如有問題，請：
1. 查看 `oci/CLAUDE.md` 完整文檔
2. 檢查 GitHub Issues  
3. 查看 `oci/CLEANUP_SUMMARY.md` 了解專案清理記錄

---

**🚀 Generated with [Claude Code](https://claude.ai/code)**

最後更新：2025-08-07

```env
# 資料庫設定
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=taichung_building_permits

# 爬蟲設定
START_YEAR=114
CRAWL_TYPE=1
DELAY_MIN=1
DELAY_MAX=3

# 日誌設定
LOG_LEVEL=INFO
LOG_FILE=crawler.log
```

## 使用方式

### 測試系統

在正式使用前，建議先執行測試：

```bash
python test_crawler.py
```

### 手動執行爬蟲

```bash
python building_permit_crawler.py
```

### 啟動排程器

```bash
python scheduler.py
```

## 資料格式

### 建照資料表 (building_permits)

| 欄位 | 類型 | 說明 |
|------|------|------|
| permit_number | VARCHAR(20) | 建照執照號碼 |
| permit_year | INT | 年份 |
| permit_type | INT | 類型(1=建照) |
| sequence_number | INT | 編號 |
| version_number | INT | 版本號 |
| applicant_name | VARCHAR(100) | 起造人姓名 |
| designer_name | VARCHAR(100) | 設計人姓名 |
| designer_company | VARCHAR(200) | 設計人事務所 |
| supervisor_name | VARCHAR(100) | 監造人姓名 |
| supervisor_company | VARCHAR(200) | 監造人事務所 |
| contractor_name | VARCHAR(100) | 承造人姓名 |
| contractor_company | VARCHAR(200) | 承造廠商 |
| engineer_name | VARCHAR(100) | 專任工程人員 |
| site_address | TEXT | 基地地址 |
| site_city | VARCHAR(50) | 地址城市 |
| site_zone | VARCHAR(100) | 使用分區 |
| site_area | DECIMAL(10,2) | 基地面積 |

### INDEX_KEY格式說明

INDEX_KEY格式：`YYYTSSSSSVV`

- `YYY`: 年份 (如114代表民國114年)
- `T`: 類型 (1=建照)
- `SSSSS`: 編號 (00001-99999)
- `VV`: 版本號 (00-99)

範例：`11410000100` = 114年建照第1號第0版

## 爬蟲策略

1. **編號遞增邏輯**：從資料庫中取得最大編號，從下一個編號開始爬取
2. **失敗處理**：連續失敗50次後停止該年份的爬取
3. **重試機制**：每個頁面最多重試3次
4. **延遲設定**：每次請求間隔1-3秒隨機延遲
5. **重新整理**：根據網站特性，每個頁面重新整理2次確保載入

## 排程設定

預設每日早上8點執行，可透過環境變數 `DAILY_SCHEDULE_TIME` 調整：

```env
DAILY_SCHEDULE_TIME=08:00
```

## 日誌記錄

系統會記錄詳細的執行日誌，包括：

- 爬取進度和結果
- 錯誤訊息和重試情況
- 資料庫操作記錄
- 每日執行統計

## 注意事項

1. **網站特性**：台中市政府網站有時需要重新整理兩次才能正常載入
2. **個資保護**：遇到包含「○○○代表遺失個資」的資料會自動跳過
3. **重複處理**：系統會自動處理重複資料，使用 `ON DUPLICATE KEY UPDATE`
4. **連接池**：使用 session 保持連接，提高爬取效率

## CRM串接準備

資料庫結構已考慮CRM串接需求：

- 標準化的資料欄位
- 完整的索引設計
- 時間戳記錄
- 唯一性約束

## 故障排除

### 常見問題

1. **資料庫連接失敗**
   - 檢查 `.env` 檔案設定
   - 確認 MySQL 服務正在運行
   - 驗證使用者權限

2. **爬取失敗率過高**
   - 調整延遲時間（增加 `DELAY_MAX`）
   - 檢查網路連接
   - 確認目標網站是否正常

3. **資料解析錯誤**
   - 檢查網站是否更新格式
   - 查看日誌檔案瞭解詳細錯誤

## 版本資訊

- 版本：1.0.0
- 支援年份：民國114年起
- 資料類型：建照（類型1）

## 授權

本專案僅供學習和研究使用，請遵守相關法律法規和網站使用條款。