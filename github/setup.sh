#!/bin/bash

# 台中市建照爬蟲 - GitHub 快速部署腳本

echo "🚀 台中市建照爬蟲系統 - GitHub 部署"
echo "=================================="

# 檢查是否在正確的目錄
if [ ! -f "README.md" ]; then
    echo "❌ 請在專案根目錄執行此腳本"
    exit 1
fi

# 檢查是否安裝git
if ! command -v git &> /dev/null; then
    echo "❌ 未安裝 Git"
    echo "請先安裝 Git: https://git-scm.com/"
    exit 1
fi

# 檢查是否安裝node和npm
if ! command -v node &> /dev/null; then
    echo "❌ 未安裝 Node.js"
    echo "請先安裝 Node.js: https://nodejs.org/"
    exit 1
fi

echo "✅ 環境檢查通過"

# 提示用戶輸入資訊
echo ""
echo "📋 請提供以下資訊:"
read -p "GitHub 用戶名: " github_username
read -p "Repository 名稱 [taichung-building-permits]: " repo_name
repo_name=${repo_name:-taichung-building-permits}

echo ""
echo "📝 設定資訊:"
echo "GitHub 用戶名: $github_username"
echo "Repository 名稱: $repo_name"
echo "GitHub Pages URL: https://$github_username.github.io/$repo_name"

read -p "確認以上資訊正確嗎? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ 部署已取消"
    exit 1
fi

# 初始化 Git repository
if [ ! -d ".git" ]; then
    echo "🔧 初始化 Git repository..."
    git init
fi

# 設定 Git 用戶資訊 (如果尚未設定)
if [ -z "$(git config user.name)" ]; then
    read -p "Git 用戶名: " git_username
    git config user.name "$git_username"
fi

if [ -z "$(git config user.email)" ]; then
    read -p "Git 電子郵件: " git_email
    git config user.email "$git_email"
fi

# 更新 HTML 中的 GitHub 連結
echo "🔧 更新網頁設定..."
sed -i.bak "s/your-username/$github_username/g" docs/index.html
sed -i.bak "s/your-repo-name/$repo_name/g" docs/index.html
rm docs/index.html.bak 2>/dev/null || true

# 安裝爬蟲依賴
echo "📦 安裝爬蟲依賴..."
cd crawler
npm install --silent
cd ..

# 建立初始資料目錄和檔案
echo "📁 建立資料目錄..."
mkdir -p data

# 建立初始 permits.json
cat > data/permits.json << EOF
{
  "lastUpdate": "$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")",
  "totalCount": 0,
  "permits": []
}
EOF

# 建立初始 crawl-logs.json
cat > data/crawl-logs.json << EOF
{
  "logs": []
}
EOF

# 建立 .gitignore
cat > .gitignore << EOF
# Dependencies
node_modules/
npm-debug.log*

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/

# Logs
*.log

# Backup files
*.bak
EOF

# 添加所有檔案到 Git
echo "📋 準備 Git 提交..."
git add .

# 檢查是否有變更
if git diff --staged --quiet; then
    echo "ℹ️  沒有檔案變更，跳過提交"
else
    git commit -m "🚀 初始化台中市建照爬蟲系統

- 建立 GitHub Actions 自動爬蟲
- 設定 GitHub Pages 監控介面
- 配置 JSON 資料存儲
- 準備 CRM 系統串接 API"
fi

# 設定遠端 repository
echo "🔗 設定遠端 repository..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$github_username/$repo_name.git"

# 設定主分支
git branch -M main

echo ""
echo "✅ 本地設定完成!"
echo ""
echo "📋 下一步手動操作:"
echo "1. 在 GitHub 建立新 repository: https://github.com/new"
echo "   - Repository 名稱: $repo_name"
echo "   - 設為 Public (GitHub Pages 需要)"
echo ""
echo "2. 推送程式碼到 GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. 啟用 GitHub Actions:"
echo "   - 進入 repository > Actions 標籤"
echo "   - 點擊 'I understand my workflows, go ahead and enable them'"
echo ""
echo "4. 啟用 GitHub Pages:"
echo "   - 進入 repository > Settings > Pages"
echo "   - Source: Deploy from a branch"
echo "   - Branch: main / (root)"
echo "   - 點擊 Save"
echo ""
echo "5. 手動執行第一次爬蟲 (可選):"
echo "   - 進入 Actions 標籤"
echo "   - 選擇 '台中市建照資料爬蟲'"
echo "   - 點擊 'Run workflow'"
echo ""
echo "🌐 完成後的網址:"
echo "   監控介面: https://$github_username.github.io/$repo_name"
echo "   原始資料: https://$github_username.github.io/$repo_name/data/permits.json"
echo ""
echo "🔄 系統將每天早上8點自動執行爬蟲任務"
echo "📊 資料可通過 JSON API 串接到你的 CRM 系統"

# 提供推送命令提示
echo ""
echo "💡 快速推送命令:"
echo "git push -u origin main"