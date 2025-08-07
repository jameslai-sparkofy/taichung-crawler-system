# 元心建材台中市建照監控系統

台中市建築執照自動爬蟲與監控系統，每日凌晨3:00自動更新。

## 功能特色

- 🔍 智慧自然語言搜尋（支援公司名稱搜尋）
- 📊 即時數據統計與視覺化
- 🤖 每日自動爬蟲（3:00 AM）
- 📱 響應式網頁設計
- ☁️ 部署於 Oracle Cloud Infrastructure

## 系統架構

- **前端**: HTML + JavaScript（純前端，無框架）
- **爬蟲**: Python (requests + BeautifulSoup)
- **儲存**: OCI Object Storage
- **排程**: Cron 自動執行

## 主要檔案

- `index.html` - 主要監控介面
- `monitor.html` - 進度監控面板
- `improved-daily-update.py` - 每日自動爬蟲程式
- `auto-crawler.sh` - 自動執行腳本

## 智慧搜尋範例

- "北屯區200戶以上"
- "太子建設的建案"
- "113年大里區透天"
- "興富發在西屯區"

## 部署說明

系統已部署於 OCI，透過以下網址存取：
- 主介面: [https://objectstorage.ap-tokyo-1.oraclecloud.com/.../index.html](https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html)
- 監控面板: [https://objectstorage.ap-tokyo-1.oraclecloud.com/.../monitor.html](https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/monitor.html)