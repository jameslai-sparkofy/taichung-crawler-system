#!/bin/bash
# 直接執行 OCI Function 的腳本

echo "======================================="
echo "執行建照爬蟲 OCI Function"
echo "======================================="

# 設定參數
FUNCTION_ENDPOINT="https://xxxxx.call.test.ap-tokyo-1.functions.oci.oraclecloud.com"
APPLICATION_NAME="building-permit-crawler"
FUNCTION_NAME="taichung-crawler"

echo "正在觸發 Function 執行..."

# 方法1: 如果有設定好的 Function endpoint
if [ ! -z "$FUNCTION_ENDPOINT" ] && [ "$FUNCTION_ENDPOINT" != "https://xxxxx.call.test.ap-tokyo-1.functions.oci.oraclecloud.com" ]; then
    echo "使用 HTTP 觸發..."
    curl -X POST "$FUNCTION_ENDPOINT" \
         -H "Content-Type: application/json" \
         -d '{"action": "crawl_permits", "year": 112, "start": 1564, "end": 2039}'
else
    echo "使用 OCI CLI 觸發..."
    # 方法2: 使用 OCI CLI 觸發 Function
    oci fn function invoke \
        --function-id $(oci fn function list \
            --application-id $(oci fn application list \
                --compartment-id $(oci iam compartment list \
                    --name "root" \
                    --query 'data[0].id' \
                    --raw-output) \
                --display-name "$APPLICATION_NAME" \
                --query 'data[0].id' \
                --raw-output) \
            --display-name "$FUNCTION_NAME" \
            --query 'data[0].id' \
            --raw-output) \
        --body '{"action": "crawl_permits"}' \
        --file response.json
    
    echo "Function 執行結果:"
    cat response.json
fi

echo ""
echo "======================================="
echo "✅ Function 觸發完成"
echo ""
echo "請檢查以下項目確認執行狀態："
echo "1. OCI Console -> Functions -> Applications -> building-permit-crawler"
echo "2. 檢查 Function 執行日誌"
echo "3. 監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html"
echo "4. 資料檔案: permits.json 是否有更新"
echo "======================================="