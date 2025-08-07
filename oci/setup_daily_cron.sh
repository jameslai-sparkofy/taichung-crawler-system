#!/bin/bash

# OCI 每日定時爬蟲設定腳本

echo "設定 OCI 每日定時爬蟲..."

# 設定變數
FUNCTION_NAME="taichung-building-permit-daily-crawler"
NAMESPACE="nrsdi1rz5vl8"
BUCKET_NAME="taichung-building-permits"

# 1. 部署函數
echo "1. 部署 OCI Function..."
cd function
# 這裡需要使用 fn CLI 或 OCI Console 手動部署

# 2. 建立初始進度檔案
echo "2. 建立初始進度檔案..."
cat > /tmp/crawler_progress.json <<EOF
{
  "year": 114,
  "currentSequence": 1100,
  "consecutiveEmpty": 0,
  "lastCrawledAt": null
}
EOF

oci os object put \
  --namespace $NAMESPACE \
  --bucket-name $BUCKET_NAME \
  --name "data/crawler_progress.json" \
  --file /tmp/crawler_progress.json \
  --content-type "application/json" \
  --force

echo "3. 設定完成！"
echo ""
echo "請在 OCI Console 中："
echo "1. 部署 Function: $FUNCTION_NAME"
echo "2. 設定 Application Configuration:"
echo "   - OCI_RESOURCE_PRINCIPAL_VERSION=2.2"
echo "3. 建立 Scheduled Job:"
echo "   - 執行時間: 每天 23:50 (台北時間)"
echo "   - Cron Expression: 50 15 * * * (UTC時間)"
echo ""
echo "或使用 OCI CLI 建立排程："
echo "oci fn application invoke --function-id <FUNCTION_OCID> --async"