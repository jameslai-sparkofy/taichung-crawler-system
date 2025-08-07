# 部署說明 - 台中市建照爬蟲系統

## 📋 系統概述

已完成的系統包含：

1. **監控網頁** (`index.html`)
   - 顯示建照資料統計
   - 多條件篩選功能（年份、樓層、地區）
   - 建照詳細資料檢視
   - 最新執行記錄顯示

2. **歷史記錄頁面** (`logs.html`)
   - 30天執行記錄
   - 執行趨勢圖表
   - 統計分析

3. **測試資料**
   - 112-114年共100筆建照資料
   - 30天執行記錄

## 🚀 部署步驟

### 1. 上傳到 OCI Object Storage

需要上傳以下檔案：

```bash
# 網頁檔案（根目錄）
index.html      # 主監控頁面
logs.html       # 歷史記錄頁面

# 資料檔案（data/目錄下）
data/permits.json      # 建照資料
data/crawl-logs.json   # 執行記錄
```

### 2. 使用 OCI CLI 上傳

```bash
# 設定變數
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"

# 上傳網頁檔案
oci os object put --namespace $NAMESPACE --bucket-name $BUCKET \
  --file index.html --name index.html \
  --content-type "text/html" --force

oci os object put --namespace $NAMESPACE --bucket-name $BUCKET \
  --file logs.html --name logs.html \
  --content-type "text/html" --force

# 上傳資料檔案
oci os object put --namespace $NAMESPACE --bucket-name $BUCKET \
  --file permits.json --name data/permits.json \
  --content-type "application/json" --force

oci os object put --namespace $NAMESPACE --bucket-name $BUCKET \
  --file crawl-logs.json --name data/crawl-logs.json \
  --content-type "application/json" --force
```

### 3. 設定公開存取（如果尚未設定）

確保 bucket 有正確的公開存取政策：

```json
{
  "Version": "2020-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": [
        "GetObject"
      ],
      "Resource": "arn:aws:s3:::taichung-building-permits/*"
    }
  ]
}
```

## 📊 測試資料內容

### 建照資料分布
- **112年**: 20筆 (序號 1000-1019)
- **113年**: 30筆 (序號 500-790，間隔10)
- **114年**: 50筆 (序號 100-345，間隔5)

### 資料欄位
- 建照號碼、起造人、設計人、監造人、承造人
- 基地地址、使用分區、基地面積
- 樓層數（用於篩選）
- 爬取時間

## 🔗 訪問網址

部署完成後，可透過以下網址訪問：

- 主頁面: `https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html`
- 歷史記錄: `https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/logs.html`

## 🔧 爬蟲程式

系統包含多個爬蟲版本：

1. **smart-crawler.py** - 智慧型爬蟲（需要OCI SDK）
2. **multi-year-crawler.py** - 多年份爬蟲（需要OCI SDK）
3. **final-crawler.py** - 最終版本（不需要OCI）
4. **daily-cron.sh** - 每日定時執行腳本

### 設定定時執行

```bash
# 編輯 crontab
crontab -e

# 新增每日早上8點執行
0 8 * * * /path/to/daily-cron.sh
```

## 📝 注意事項

1. 真實爬蟲需要處理網站的「刷新兩次」機制
2. 建議從較大序號開始爬取（如1000、500等）
3. 每次請求間隔至少1.5秒避免過度請求
4. 定期檢查網站結構是否有變化

## 🎯 下一步優化建議

1. 加入更多篩選條件（如建照類型、申請日期等）
2. 實作資料匯出功能（CSV、Excel）
3. 加入資料視覺化圖表
4. 實作 API 端點供 CRM 系統串接
5. 加入錯誤通知機制（Email、Line）