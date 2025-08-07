# Cloudflare 部署指南

## 前置準備

1. **安裝 Cloudflare CLI (Wrangler)**
   ```bash
   npm install -g wrangler
   ```

2. **登入 Cloudflare 帳號**
   ```bash
   wrangler login
   ```

## 部署步驟

### 1. 建立 D1 資料庫

```bash
# 進入cloudflare目錄
cd cloudflare

# 建立D1資料庫
wrangler d1 create taichung-permits
```

執行後會得到資料庫ID，請將ID複製到 `wrangler.toml` 中的 `database_id` 欄位。

### 2. 初始化資料庫結構

```bash
# 執行schema.sql建立表格
wrangler d1 execute taichung-permits --file=./schema.sql
```

### 3. 更新 wrangler.toml 設定

編輯 `wrangler.toml`，確保以下設定正確：

```toml
name = "taichung-building-permits"
compatibility_date = "2024-01-01"
main = "src/index.js"

[[d1_databases]]
binding = "DB"
database_name = "taichung-permits"
database_id = "your-actual-database-id"  # 替換為步驟1得到的ID

[triggers]
crons = ["0 8 * * *"]  # 每天早上8點執行

[vars]
ENVIRONMENT = "production"
```

### 4. 部署 Worker

```bash
# 安裝依賴
npm install

# 部署到Cloudflare
npm run deploy
```

### 5. 設定 CRON 觸發器

部署完成後，CRON觸發器會自動生效。你可以在 Cloudflare Dashboard 中查看：

1. 進入 Workers & Pages
2. 選擇你的 Worker
3. 點選 "Triggers" 標籤
4. 確認 CRON 觸發器已設定

## 驗證部署

### 1. 檢查網站

造訪你的 Worker URL (例如: `https://taichung-building-permits.your-subdomain.workers.dev`)

你應該看到建照資料同步系統的儀表板。

### 2. 測試 API 端點

```bash
# 檢查系統狀態
curl https://your-worker-url.workers.dev/api/status

# 檢查統計資料
curl https://your-worker-url.workers.dev/api/stats

# 檢查爬取記錄
curl https://your-worker-url.workers.dev/api/logs
```

### 3. 手動觸發 CRON

在 Cloudflare Dashboard 中：

1. 進入你的 Worker
2. 點選 "Triggers" 標籤
3. 找到 CRON 觸發器
4. 點選 "Send test request" 手動執行

## 監控和維護

### 1. 查看日誌

```bash
# 即時查看Worker日誌
npm run tail
```

### 2. 資料庫查詢

```bash
# 查看建照總數
wrangler d1 execute taichung-permits --command="SELECT COUNT(*) FROM building_permits"

# 查看最新記錄
wrangler d1 execute taichung-permits --command="SELECT * FROM crawl_logs ORDER BY crawl_date DESC LIMIT 5"

# 查看今日新增
wrangler d1 execute taichung-permits --command="SELECT * FROM building_permits WHERE DATE(created_at) = DATE('now') ORDER BY created_at DESC"
```

### 3. 更新程式碼

```bash
# 修改程式碼後重新部署
npm run deploy
```

## 故障排除

### 1. CRON 不執行

- 檢查 `wrangler.toml` 中的 crons 設定
- 確認在 Cloudflare Dashboard 中看到觸發器
- 查看 Worker 日誌是否有錯誤

### 2. 資料庫連接失敗

- 確認 `database_id` 正確
- 檢查資料庫binding名稱是否為 "DB"
- 重新部署 Worker

### 3. 爬蟲失敗率過高

- 檢查台中市政府網站是否正常
- 調整 `crawler.js` 中的延遲時間
- 查看具體錯誤訊息

### 4. 網站無法載入

- 檢查 Worker 是否成功部署
- 確認路由設定正確
- 查看瀏覽器控制台錯誤

## 效能調整

### 1. 調整爬取頻率

修改 `wrangler.toml` 中的 crons 設定：

```toml
[triggers]
crons = ["0 */6 * * *"]  # 每6小時執行一次
```

### 2. 調整單次爬取數量

修改 `crawler.js` 中的限制：

```javascript
// 調整最大爬取數量
if (this.totalCrawled >= 200) {  // 從100改為200
  console.log('達到單次執行最大爬取數量限制');
  break;
}
```

### 3. 調整延遲時間

```javascript
// 調整延遲避免過度請求
this.delayMs = 3000; // 從2000ms改為3000ms
```

## 費用說明

Cloudflare Workers 免費方案包含：
- 每日 100,000 個請求
- 每次執行最多 10ms CPU 時間
- D1 資料庫: 5GB 儲存空間，每日 100,000 次寫入

對於這個建照爬蟲系統，免費方案通常已經足夠使用。

## 自訂域名 (可選)

如果要使用自訂域名：

1. 在 Cloudflare Dashboard 中添加你的域名
2. 在 Worker 設定中綁定自訂域名
3. 更新 DNS 記錄指向 Worker

## 備份策略

定期備份 D1 資料庫：

```bash
# 匯出資料
wrangler d1 export taichung-permits --output=backup.sql
```

## 支援

如遇問題，請查看：
- Cloudflare Workers 文件
- D1 資料庫文件
- Wrangler CLI 文件