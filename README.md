# 台中市建照爬蟲系統

這是一個專門用來爬取台中市政府都發局建築執照資料的系統，支援每日自動爬取並儲存到資料庫中。

## 功能特色

- 🏗️ 爬取台中市政府都發局建照資料
- 📊 自動解析建照詳細資訊
- 💾 MySQL資料庫儲存
- ⏰ 每日自動執行排程
- 🔄 自動編號遞增邏輯
- 📝 完整的爬蟲執行記錄
- 🛡️ 錯誤處理和重試機制
- 🔍 重複資料檢查和更新

## 系統架構

```
建照爬蟲/
├── database.sql              # 資料庫結構檔案
├── database_manager.py       # 資料庫管理類別
├── building_permit_crawler.py # 主要爬蟲程式
├── scheduler.py              # 排程執行器
├── test_crawler.py           # 測試程式
├── requirements.txt          # Python依賴套件
├── .env.example             # 環境變數範例
└── README.md                # 說明文件
```

## 安裝與設定

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 資料庫設定

執行 `database.sql` 建立資料庫和表格：

```bash
mysql -u your_username -p < database.sql
```

### 3. 環境變數設定

複製 `.env.example` 為 `.env` 並填入正確的資料庫資訊：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

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