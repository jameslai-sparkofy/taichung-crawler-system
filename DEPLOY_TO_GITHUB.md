# 🚀 GitHub 部署指南

由於GitHub MCP需要額外的OAuth認證設定，以下是手動部署到GitHub的完整步驟：

## 📋 快速部署步驟

### 1. 建立GitHub Repository

1. 前往 https://github.com/new
2. Repository name: `taichung-building-permits`
3. Description: `台中市建照資料爬蟲系統 - 基於GitHub Actions自動化爬取建築執照資料`
4. 設為 **Public** (GitHub Pages需要)
5. ✅ 勾選 "Add a README file"
6. 點擊 "Create repository"

### 2. 上傳檔案到Repository

#### 方法A: 使用GitHub網頁介面

1. 在新建的repository頁面，點擊 "uploading an existing file"
2. 將以下整個資料夾拖拽上傳：
   ```
   /mnt/c/claude code/建照爬蟲/github/
   ```
3. 或者逐一建立檔案：

**建立 `.github/workflows/crawler.yml`:**
```yaml
name: 台中市建照資料爬蟲

on:
  schedule:
    - cron: '0 0 * * *'  # 每天早上8點 (台灣時間)
  workflow_dispatch:
  push:
    branches: [ main ]

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    - name: Install dependencies
      run: |
        cd crawler
        npm install
    - name: Run crawler
      run: |
        cd crawler
        node index.js
    - name: Update data files
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add data/
        if ! git diff --staged --quiet; then
          git commit -m "🤖 自動更新建照資料 $(date +'%Y-%m-%d %H:%M:%S')"
          git push
        fi
```

**建立 `docs/index.html`:** (複製我們剛建立的完整HTML)

**建立 `crawler/package.json` 和 `crawler/index.js`:** (複製相應檔案)

**建立初始資料檔案:**
- `data/permits.json` (複製我們的測試資料)
- `data/crawl-logs.json`

#### 方法B: 使用Git命令行

```bash
# 1. Clone repository
git clone https://github.com/你的用戶名/taichung-building-permits.git
cd taichung-building-permits

# 2. 複製所有檔案
cp -r "/mnt/c/claude code/建照爬蟲/github/"* .

# 3. 提交推送
git add .
git commit -m "🚀 初始化台中市建照爬蟲系統"
git push origin main
```

### 3. 啟用GitHub Actions

1. 進入repository
2. 點擊 "Actions" 標籤
3. 如果看到提示，點擊 "I understand my workflows, go ahead and enable them"
4. 你會看到 "台中市建照資料爬蟲" workflow

### 4. 啟用GitHub Pages

1. 進入repository的 "Settings"
2. 在左側選單找到 "Pages"
3. 在 "Source" 部分：
   - 選擇 "Deploy from a branch"
   - Branch: `main`
   - Folder: `/ (root)`
4. 點擊 "Save"
5. 幾分鐘後會提供網址：`https://你的用戶名.github.io/taichung-building-permits`

### 5. 第一次執行測試

1. 進入 "Actions" 標籤
2. 選擇 "台中市建照資料爬蟲" workflow
3. 點擊 "Run workflow" 按鈕
4. 點擊 "Run workflow" 確認執行

## 🎯 完成後的結果

### 📊 監控網址
```
https://你的用戶名.github.io/taichung-building-permits
```

### 🔗 JSON API 網址
```
https://你的用戶名.github.io/taichung-building-permits/data/permits.json
```

### ⏰ 自動執行
- 系統會每天早上8點自動爬取
- 可隨時在Actions中手動觸發
- 所有執行記錄都會保存

## 🔧 檔案結構檢查清單

確保以下檔案都已正確上傳：

```
├── .github/
│   └── workflows/
│       └── crawler.yml          ✅
├── crawler/
│   ├── index.js                 ✅
│   ├── package.json             ✅
│   └── test.js                  ✅
├── data/
│   ├── permits.json             ✅
│   └── crawl-logs.json          ✅
├── docs/
│   └── index.html               ✅ (用於GitHub Pages)
└── README.md                    ✅
```

## 🚨 故障排除

### Actions不執行
- 檢查workflow檔案格式
- 確認已啟用Actions

### Pages不顯示
- 確認Pages設定正確
- 檢查index.html在docs/資料夾中

### 爬蟲失敗
- 查看Actions執行日誌
- 檢查網路連接和目標網站狀態

## 🎉 完成

完成部署後，你將擁有：
- ✅ 每日自動爬取的建照資料
- ✅ 美觀的監控網頁介面  
- ✅ JSON API供CRM系統串接
- ✅ 完整的執行記錄和統計

與我們剛才看到的demo.html完全相同的功能，但會自動更新真實資料！