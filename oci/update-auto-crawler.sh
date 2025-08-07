#!/bin/bash
# 更新自動爬蟲到改進版

echo "🔄 更新自動爬蟲腳本..."

INSTALL_DIR="/home/laija/taichung-building-crawler"

# 下載改進版腳本
echo "📥 下載改進版爬蟲腳本..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/improved-daily-update.py \
    --file $INSTALL_DIR/improved-daily-update.py

chmod +x $INSTALL_DIR/improved-daily-update.py

# 更新 auto-crawler.sh
echo "📝 更新執行腳本..."
sed -i 's/python3 daily-update.py/python3 improved-daily-update.py/g' $INSTALL_DIR/auto-crawler.sh

echo "✅ 更新完成！"
echo ""
echo "新功能："
echo "  - 📍 記錄最後成功的ID，從上次位置繼續"
echo "  - 🛑 遇到連續空白資料時自動停止"
echo "  - 📊 詳細的執行記錄和進度追蹤"
echo ""
echo "測試命令："
echo "  $INSTALL_DIR/improved-daily-update.py"