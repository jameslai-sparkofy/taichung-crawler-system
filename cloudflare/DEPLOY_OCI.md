# Cloudflare Worker + OCI Storage 部署指南

本指南說明如何部署 Cloudflare Worker 來自動爬取台中市建照資料，並儲存到 OCI Object Storage。

## 架構優勢

- ☁️ **無伺服器架構**: 使用 Cloudflare Workers，無需維護伺服器
- 🌍 **全球網路**: 利用 Cloudflare 的全球節點
- 💾 **OCI 儲存**: 資料儲存在你現有的 OCI Object Storage
- ⏰ **自動排程**: 每日凌晨 3:00 自動執行
- 💰 **成本效益**: Cloudflare 免費方案即可滿足需求

## 前置準備

### 1. OCI 設定

在 OCI 控制台建立預驗證請求（Pre-Authenticated Request）：

```bash
# 登入 OCI 控制台
# 前往 Object Storage > 你的 Bucket
# 建立預驗證請求，權限設為「讀取物件」和「寫入物件」
# 複製產生的 URL 中的金鑰部分
```

### 2. 安裝 Wrangler CLI

```bash
npm install -g wrangler
wrangler login
```

## 部署步驟

### 1. 複製專案

```bash
cd cloudflare
npm install
```

### 2. 設定環境變數

編輯 `wrangler.toml`，更新 OCI 預驗證請求金鑰：

```toml
[vars]
# ... 其他變數保持不變

# 新增這行
OCI_PREAUTH_KEY = "你的預驗證請求金鑰"
```

### 3. 部署 Worker

```bash
npm run deploy
```

部署成功後會顯示你的 Worker URL：
```
https://taichung-permits-crawler.YOUR-SUBDOMAIN.workers.dev
```

### 4. 測試

訪問你的 Worker URL，應該會看到監控介面。

測試單一爬取：
```
https://your-worker-url/api/test?year=114&seq=1
```

### 5. 設定 Cron（可選）

如果要調整執行時間，編輯 `wrangler.toml`：

```toml
[triggers]
crons = ["0 19 * * *"]  # UTC 19:00 = 台灣時間凌晨 3:00
```

## 手動觸發

在監控介面點擊「手動觸發爬蟲」按鈕，或使用 API：

```bash
curl -X POST https://your-worker-url/api/trigger
```

## 監控

### 查看即時日誌

```bash
npm run tail
```

### 查看爬蟲進度

訪問監控介面或 API：
```
https://your-worker-url/api/status
```

## 注意事項

1. **執行限制**: Cloudflare Workers 有執行時間限制（CPU 時間 10ms-50ms），所以每次最多爬取 50 筆資料
2. **請求限制**: 免費方案每日 100,000 次請求，對爬蟲來說綽綽有餘
3. **資料同步**: 爬取的資料會即時同步到 OCI Object Storage

## 故障排除

### 預驗證請求失敗

- 檢查預驗證請求是否過期
- 確認權限包含讀取和寫入
- 確認 bucket 名稱和 namespace 正確

### 爬蟲執行失敗

- 查看 Worker 日誌：`npm run tail`
- 檢查目標網站是否正常
- 調整延遲時間（REQUEST_DELAY_MS）

### 資料未更新

- 檢查 OCI Object Storage 中的檔案
- 確認 permits.json 有正確的寫入權限
- 查看爬蟲記錄（crawl-logs.json）

## 成本預估

Cloudflare Workers 免費方案：
- 每日 100,000 次請求
- 每次請求 10ms CPU 時間

對於每日爬取 50-100 筆資料的需求，免費方案完全足夠。

## 後續優化

1. **增加重試機制**: 對失敗的爬取進行重試
2. **通知功能**: 爬取完成後發送通知
3. **資料驗證**: 增加資料完整性檢查
4. **效能優化**: 批次處理減少 API 呼叫

## 相關連結

- [Cloudflare Workers 文件](https://developers.cloudflare.com/workers/)
- [Wrangler CLI 文件](https://developers.cloudflare.com/workers/wrangler/)
- [OCI Object Storage 文件](https://docs.oracle.com/en-us/iaas/Content/Object/home.htm)