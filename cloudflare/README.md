# 台中市建照爬蟲系統 - Cloudflare 版本

基於 Cloudflare Workers 和 D1 資料庫的無服務器建照資料爬蟲系統，具備自動排程爬取和網頁監控介面。

## ✨ 功能特色

- 🔄 **自動化爬取**: 每日定時爬取台中市政府都發局建照資料
- 📊 **即時監控**: 美觀的網頁儀表板顯示同步狀態
- ☁️ **無服務器**: 基於 Cloudflare Workers，無需維護服務器
- 💾 **雲端資料庫**: 使用 Cloudflare D1 SQLite 資料庫
- 🔗 **API 接口**: 完整的 REST API 供 CRM 系統串接
- 📈 **統計分析**: 爬取記錄和統計資料分析
- 🛡️ **錯誤處理**: 完善的重試機制和錯誤記錄

## 🏗️ 系統架構

```
台中市建照爬蟲/
├── cloudflare/
│   ├── src/
│   │   ├── index.js         # 主程式和API端點
│   │   └── crawler.js       # 爬蟲核心邏輯
│   ├── schema.sql           # D1資料庫結構
│   ├── wrangler.toml        # Cloudflare設定
│   ├── package.json         # 依賴和腳本
│   ├── deploy.sh           # 快速部署腳本
│   ├── DEPLOYMENT.md        # 詳細部署說明
│   └── README.md           # 本檔案
└── database.sql            # 原MySQL版本資料庫結構
```

## 🚀 快速開始

### 1. 環境準備

```bash
# 安裝 Cloudflare CLI
npm install -g wrangler

# 登入 Cloudflare 帳號
wrangler login
```

### 2. 一鍵部署

```bash
cd cloudflare
chmod +x deploy.sh
./deploy.sh
```

### 3. 手動部署 (詳細步驟)

```bash
# 1. 建立 D1 資料庫
wrangler d1 create taichung-permits

# 2. 更新 wrangler.toml 中的 database_id

# 3. 初始化資料庫
wrangler d1 execute taichung-permits --file=./schema.sql

# 4. 部署 Worker
npm install
npm run deploy
```

## 📱 網頁介面

部署後造訪你的 Worker URL，將看到包含以下功能的儀表板：

- **統計卡片**: 總建照數量、今日新增、最後更新時間、系統狀態
- **爬取記錄**: 每日執行記錄和詳細統計
- **即時更新**: 每30秒自動重新整理資料
- **響應式設計**: 支援桌面和行動裝置

## 🔌 API 端點

### 基本端點

- `GET /` - 網頁儀表板
- `GET /api/status` - 系統狀態
- `GET /api/stats` - 統計資料
- `GET /api/logs?limit=20` - 爬取記錄
- `GET /api/permits?page=1&limit=50` - 建照資料

### API 回應範例

```json
// GET /api/stats
{
  "totalPermits": 1250,
  "todayNew": 15,
  "lastUpdate": "2024/1/15 上午10:30:00",
  "status": "completed"
}

// GET /api/permits
{
  "data": [
    {
      "permit_number": "114中建字第00001號",
      "permit_year": 114,
      "applicant_name": "某某建設",
      "site_address": "台中市某區某路...",
      // ... 其他欄位
    }
  ],
  "total": 1250,
  "page": 1,
  "limit": 50
}
```

## ⏰ CRON 排程

系統預設每日早上 8:00 執行爬蟲任務，可在 `wrangler.toml` 中調整：

```toml
[triggers]
crons = ["0 8 * * *"]  # 每天早上8點
# crons = ["0 */6 * * *"]  # 每6小時執行一次
```

## 📊 資料庫結構

### building_permits (建照資料表)

| 欄位 | 類型 | 說明 |
|------|------|------|
| permit_number | TEXT | 建照號碼 |
| permit_year | INTEGER | 年份 |
| sequence_number | INTEGER | 編號 |
| applicant_name | TEXT | 起造人 |
| designer_name | TEXT | 設計人 |
| site_address | TEXT | 基地地址 |
| site_area | REAL | 基地面積 |
| ... | ... | 其他詳細資訊 |

### crawl_logs (爬取記錄表)

| 欄位 | 類型 | 說明 |
|------|------|------|
| crawl_date | DATE | 爬取日期 |
| total_records | INTEGER | 總爬取筆數 |
| new_records | INTEGER | 新增筆數 |
| status | TEXT | 執行狀態 |

## 🔧 管理指令

```bash
# 查看即時日誌
npm run tail

# 重新部署
npm run deploy

# 資料庫查詢
npm run db:query "SELECT COUNT(*) FROM building_permits"

# 查看今日新增
wrangler d1 execute taichung-permits --command="SELECT * FROM building_permits WHERE DATE(created_at) = DATE('now')"
```

## 🔗 CRM 系統串接

### 方式一: API 調用

```javascript
// 獲取最新建照資料
const response = await fetch('https://your-worker.workers.dev/api/permits?limit=100');
const permits = await response.json();

// 處理資料
permits.data.forEach(permit => {
  // 同步到你的CRM系統
  syncToCRM(permit);
});
```

### 方式二: 直接資料庫查詢

```sql
-- 如果需要直接查詢，可以匯出D1資料
-- 然後導入到你的系統資料庫
```

### 方式三: Webhook (未來版本)

可以擴展系統在有新資料時主動推送到你的CRM系統。

## 📈 監控和維護

### 1. 查看執行狀態

在 Cloudflare Dashboard > Workers & Pages > 你的Worker > Logs

### 2. 監控資料品質

```bash
# 檢查最近爬取記錄
wrangler d1 execute taichung-permits --command="SELECT * FROM crawl_logs ORDER BY crawl_date DESC LIMIT 7"

# 檢查錯誤記錄
wrangler d1 execute taichung-permits --command="SELECT * FROM crawl_logs WHERE status = 'failed'"
```

### 3. 手動觸發爬蟲

在 Cloudflare Dashboard 中可以手動觸發 CRON 執行。

## 💰 費用說明

Cloudflare 免費方案包含：
- Workers: 每日 100,000 請求
- D1 資料庫: 5GB 儲存 + 每日 100,000 寫入

對於建照爬蟲系統，免費方案通常已經足夠。

## 🛠️ 故障排除

### 常見問題

1. **CRON 不執行**
   - 檢查觸發器設定
   - 查看 Worker 日誌

2. **爬取失敗率高**
   - 調整延遲時間
   - 檢查目標網站狀態

3. **資料庫錯誤**
   - 確認 database_id 正確
   - 重新執行 schema.sql

詳細故障排除請參考 `DEPLOYMENT.md`。

## 📝 更新記錄

- v1.0.0: 初始版本，支援基本爬取和監控功能
- 計劃功能: Webhook 推送、更多統計圖表、資料匯出

## 📄 授權

本專案僅供學習和研究使用，請遵守相關法律法規。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 改善系統功能。

---

## 📞 支援

如有問題請參考：
- [Cloudflare Workers 文件](https://developers.cloudflare.com/workers/)
- [D1 資料庫文件](https://developers.cloudflare.com/d1/)
- 專案 `DEPLOYMENT.md` 詳細說明