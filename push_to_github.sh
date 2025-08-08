#!/bin/bash
# 推送到GitHub的腳本

echo "🚀 推送台中市建照爬蟲專案到GitHub..."

# 請將 your-username 替換為你的GitHub用戶名
GITHUB_USERNAME="your-username"
REPO_URL="https://github.com/$GITHUB_USERNAME/taichung-building-permits.git"

echo "📝 更新遠端repository URL..."
git remote set-url origin $REPO_URL

echo "📋 檢查分支狀態..."
git branch -a
git status

echo "📤 推送main分支..."
git push -u origin main

echo "📤 推送gcp-deploy分支..."  
git push -u origin gcp-deploy

echo "✅ 推送完成！"
echo "🌐 Repository URL: $REPO_URL"
echo ""
echo "📁 分支說明："
echo "   🔹 main - 本地手動執行版本"
echo "   🔹 gcp-deploy - GCP自動化版本 (推薦)"
echo ""
echo "🚀 快速開始："
echo "   本地版本: git clone $REPO_URL"
echo "   GCP版本:  git clone -b gcp-deploy $REPO_URL"