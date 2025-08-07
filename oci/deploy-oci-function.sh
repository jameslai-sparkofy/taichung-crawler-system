#!/bin/bash
# 快速部署 OCI Function 腳本

echo "======================================="
echo "部署建照爬蟲 Function 到 OCI"
echo "======================================="

# 上傳 Function 相關檔案到 OCI Object Storage
NAMESPACE="nrsdi1rz5vl8"
BUCKET="taichung-building-permits"

echo "📤 上傳 Function 檔案..."

# 上傳 func.py
oci os object put \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name "function/func.py" \
    --file "function/func.py" \
    --content-type "text/x-python" \
    --force

# 上傳 func.yaml
oci os object put \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name "function/func.yaml" \
    --file "function/func.yaml" \
    --content-type "text/yaml" \
    --force

# 上傳 requirements.txt
oci os object put \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name "function/requirements.txt" \
    --file "function/requirements.txt" \
    --content-type "text/plain" \
    --force

# 上傳設定指南
oci os object put \
    --namespace $NAMESPACE \
    --bucket-name $BUCKET \
    --name "function/setup-guide.md" \
    --file "setup-oci-function.md" \
    --content-type "text/markdown" \
    --force

echo ""
echo "✅ Function 檔案上傳完成！"
echo ""
echo "======================================="
echo "📋 下一步："
echo "======================================="
echo ""
echo "1. 在 OCI Console 中建立 Function Application"
echo "   - 名稱: building-permit-crawler"
echo "   - VCN: 選擇您的 VCN"
echo "   - Subnet: 選擇公共子網"
echo ""
echo "2. 在 Cloud Shell 中執行以下命令下載並部署 Function："
echo ""
echo "# 建立目錄"
echo "mkdir -p building-permit-function"
echo "cd building-permit-function"
echo ""
echo "# 下載檔案"
echo "oci os object get --namespace $NAMESPACE --bucket-name $BUCKET --name function/func.py --file func.py"
echo "oci os object get --namespace $NAMESPACE --bucket-name $BUCKET --name function/func.yaml --file func.yaml"
echo "oci os object get --namespace $NAMESPACE --bucket-name $BUCKET --name function/requirements.txt --file requirements.txt"
echo ""
echo "# 部署 Function"
echo "fn deploy --app building-permit-crawler"
echo ""
echo "3. 設定自動排程（使用 OCI Console）："
echo "   - 進入 Events Service"
echo "   - 建立 Rule，設定 CRON 表達式: 0 3 * * * (每天凌晨3點)"
echo "   - Action 選擇觸發 Function"
echo ""
echo "======================================="
echo ""
echo "💡 簡化方案：使用 OCI Compute Instance + Crontab"
echo ""
echo "如果 Function 設定太複雜，可以考慮："
echo "1. 建立一個永久免費的 Compute Instance"
echo "2. 使用 crontab 設定每日執行"
echo "3. 執行我們之前的 oci-crawler.py"
echo ""
echo "這樣更簡單且容易維護！"