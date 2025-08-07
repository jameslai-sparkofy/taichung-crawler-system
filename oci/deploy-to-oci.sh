#!/bin/bash
# 部署爬蟲到OCI並執行

echo "==================================="
echo "部署爬蟲到 OCI Object Storage"
echo "==================================="

# 設定變數
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"
SCRIPT_NAME="oci-crawler.py"

# 1. 上傳爬蟲腳本到OCI
echo "📤 上傳爬蟲腳本..."
oci os object put \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name "scripts/$SCRIPT_NAME" \
    --file "$SCRIPT_NAME" \
    --content-type "text/x-python" \
    --force

if [ $? -eq 0 ]; then
    echo "✅ 爬蟲腳本上傳成功"
else
    echo "❌ 爬蟲腳本上傳失敗"
    exit 1
fi

# 2. 產生下載URL
echo ""
echo "📋 在OCI Cloud Shell中執行以下命令："
echo "==================================="
echo ""
echo "# 1. 下載爬蟲腳本"
echo "oci os object get \\"
echo "    --namespace $NAMESPACE \\"
echo "    --bucket-name $BUCKET \\"
echo "    --name scripts/$SCRIPT_NAME \\"
echo "    --file $SCRIPT_NAME"
echo ""
echo "# 2. 安裝必要套件（如果需要）"
echo "pip3 install --user requests"
echo ""
echo "# 3. 執行爬蟲"
echo "python3 $SCRIPT_NAME"
echo ""
echo "# 或在背景執行"
echo "nohup python3 $SCRIPT_NAME > crawler.log 2>&1 &"
echo ""
echo "# 查看執行進度"
echo "tail -f crawler.log"
echo ""
echo "==================================="
echo ""
echo "💡 提示："
echo "1. 請在 OCI Cloud Shell 中執行上述命令"
echo "2. Cloud Shell 已預裝 OCI CLI，無需額外配置"
echo "3. 爬蟲會自動儲存進度，可隨時中斷並續傳"
echo "4. 預估執行時間: 4-6 小時"