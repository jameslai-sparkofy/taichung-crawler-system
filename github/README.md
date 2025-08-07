# 台中市建照資料爬蟲系統 - GitHub 版本

🏗️ 基於 GitHub Actions 和 GitHub Pages 的無服務器建照資料爬蟲系統

## ✨ 功能特色

- 🔄 **自動化爬取**: 使用 GitHub Actions 每日定時爬取台中市政府都發局建照資料
- 📊 **即時監控**: GitHub Pages 提供美觀的網頁儀表板
- ☁️ **完全免費**: 基於 GitHub 免費服務，無需額外費用
- 💾 **JSON 儲存**: 資料以 JSON 格式存放在 repository 中
- 🔗 **API 友善**: JSON 格式便於 CRM 系統串接
- 📈 **執行記錄**: 完整的爬取歷史和統計資料

## 🚀 快速開始

### 1. Fork 這個 Repository

點擊右上角的 "Fork" 按鈕，將此 repository 複製到你的 GitHub 帳號下。

### 2. 啟用 GitHub Actions

1. 進入你的 forked repository
2. 點擊 "Actions" 標籤
3. 如果看到提示，點擊 "I understand my workflows, go ahead and enable them"

### 3. 啟用 GitHub Pages

1. 進入 repository 的 "Settings"
2. 在左側選單找到 "Pages"
3. 在 "Source" 部分選擇 "Deploy from a branch"
4. 選擇 "main" branch 和 "/ (root)" folder
5. 點擊 "Save"

### 4. 手動執行第一次爬取 (可選)

1. 進入 "Actions" 標籤
2. 選擇 "台中市建照資料爬蟲" workflow
3. 點擊 "Run workflow" 按鈕
4. 點擊 "Run workflow" 確認

### 5. 查看結果

幾分鐘後，你可以通過以下方式查看結果：
- **網頁介面**: `https://your-username.github.io/your-repo-name`
- **原始資料**: repository 中的 `data/` 資料夾

## 📁 專案結構

```
├── .github/
│   └── workflows/
│       └── crawler.yml          # GitHub Actions 工作流程
├── crawler/
│   ├── index.js                 # 爬蟲主程式
│   └── package.json             # Node.js 依賴
├── data/
│   ├── permits.json             # 建照資料 (爬取後產生)
│   └── crawl-logs.json          # 執行記錄 (爬取後產生)
├── docs/
│   └── index.html               # GitHub Pages 網頁
└── README.md                    # 本說明文件
```

## ⏰ 執行排程

系統預設每日早上 8:00 (台灣時間) 自動執行爬蟲任務。

要修改執行時間，編輯 `.github/workflows/crawler.yml` 中的 cron 設定：

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 00:00 = 台灣時間 08:00
  # - cron: '0 12 * * *'  # UTC 12:00 = 台灣時間 20:00
```

## 📊 資料格式

### 建照資料 (permits.json)

```json
{
  "lastUpdate": "2024-01-15T10:30:00.000Z",
  "totalCount": 1250,
  "permits": [
    {
      "indexKey": "11410000100",
      "permitNumber": "114中建字第00001號",
      "permitYear": 114,
      "permitType": 1,
      "sequenceNumber": 1,
      "versionNumber": 0,
      "applicantName": "某某建設",
      "designerName": "某建築師",
      "designerCompany": "某建築師事務所",
      "supervisorName": "某監造",
      "supervisorCompany": "某監造事務所",
      "contractorName": "某營造",
      "contractorCompany": "某營造廠",
      "engineerName": "某工程師",
      "siteAddress": "台中市某區某路某號",
      "siteCity": "台中市",
      "siteZone": "第二種住宅區",
      "siteArea": 204.9,
      "crawledAt": "2024-01-15T10:30:00.000Z"
    }
  ]
}
```

### 執行記錄 (crawl-logs.json)

```json
{
  "logs": [
    {
      "date": "2024-01-15",
      "startTime": "2024-01-15T00:00:00.000Z",
      "endTime": "2024-01-15T00:05:30.000Z",
      "totalCrawled": 25,
      "newRecords": 15,
      "errorRecords": 2,
      "status": "completed"
    }
  ]
}
```

## 🔗 CRM 系統串接

### 方式一: 直接讀取 JSON 檔案

```javascript
// 讀取最新建照資料
const response = await fetch('https://your-username.github.io/your-repo-name/data/permits.json');
const data = await response.json();

// 處理資料
data.permits.forEach(permit => {
  // 同步到你的 CRM 系統
  syncToCRM(permit);
});
```

### 方式二: Clone Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# 直接讀取 JSON 檔案
cat data/permits.json | jq '.permits[] | select(.permitYear == 114)'
```

### 方式三: GitHub API

```javascript
// 通過 GitHub API 讀取檔案
const response = await fetch('https://api.github.com/repos/your-username/your-repo-name/contents/data/permits.json');
const fileData = await response.json();
const content = JSON.parse(atob(fileData.content));
```

## 🔧 自訂設定

### 修改爬取參數

編輯 `crawler/index.js` 中的設定：

```javascript
class TaichungBuildingCrawler {
  constructor() {
    this.startYear = 114;        // 起始年份
    this.crawlType = 1;          // 建照類型
    this.delayMs = 2000;         // 請求間隔 (毫秒)
    // ...
  }
}
```

### 修改資料保留數量

```javascript
// 修改記錄保留天數
logs = logs.slice(0, 30);  // 保留 30 天記錄

// 修改單次爬取上限
while (consecutiveFailures < maxConsecutiveFailures && newPermits.length < 100) {
  // 將 100 改為你想要的數量
}
```

## 📈 監控和維護

### 查看執行狀態

1. **GitHub Actions**: repository > Actions 標籤
2. **網頁介面**: 你的 GitHub Pages URL
3. **原始日誌**: Actions 執行記錄中的詳細日誌

### 手動觸發爬蟲

1. 進入 Actions 標籤
2. 選擇 "台中市建照資料爬蟲"
3. 點擊 "Run workflow"

### 故障排除

**常見問題:**

1. **Actions 不執行**
   - 檢查是否已啟用 Actions
   - 確認 workflow 檔案格式正確

2. **GitHub Pages 不更新**
   - 檢查 Pages 設定
   - 確認檔案路徑正確

3. **爬取失敗率高**
   - 查看 Actions 日誌
   - 調整 `delayMs` 增加延遲時間

4. **JSON 檔案格式錯誤**
   - 檢查 Actions 執行日誌
   - 確認寫入權限正常

## 💰 費用說明

GitHub 免費方案包含：
- ✅ 無限公開 repositories
- ✅ GitHub Actions: 每月 2000 分鐘
- ✅ GitHub Pages: 無限靜態網站託管
- ✅ 每個 repository 1GB 儲存空間

對於這個建照爬蟲系統完全免費！

## 🔒 隱私和安全

- ✅ 資料完全存放在你的 GitHub repository
- ✅ 無需第三方服務或資料庫
- ✅ 開源透明，可完全控制
- ✅ 支援 private repository (付費方案)

## 🛠️ 進階功能

### 資料備份

```bash
# 定期備份到本地
git clone https://github.com/your-username/your-repo-name.git backup/
```

### 多個爬蟲實例

可以 fork 多個版本爬取不同年份或類型的資料。

### 資料分析

```bash
# 使用 jq 分析資料
cat data/permits.json | jq '.permits | group_by(.permitYear) | map({year: .[0].permitYear, count: length})'
```

## 📝 更新記錄

- v1.0.0: 初始版本，支援基本爬取和 GitHub Pages 顯示
- 規劃中: 資料統計圖表、匯出功能、Webhook 通知

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 改善系統功能。

## 📄 授權

本專案採用 MIT 授權，僅供學習和研究使用，請遵守相關法律法規。

---

## 🔗 相關連結

- [台中市政府都市發展局](https://mcgbm.taichung.gov.tw/)
- [GitHub Actions 文件](https://docs.github.com/en/actions)
- [GitHub Pages 文件](https://docs.github.com/en/pages)

## 📞 支援

如有問題請：
1. 查看 Actions 執行日誌
2. 提交 GitHub Issue
3. 參考本 README 故障排除章節