#!/bin/bash

# 部署 OCI Functions 爬蟲
# 這個方案不需要 VM，使用無伺服器架構

echo "🚀 開始部署 OCI Functions 爬蟲"
echo "=========================================="

# 取得必要的 OCID
TENANCY_OCID=$(oci iam availability-domain list --query "data[0].\"compartment-id\"" --raw-output)
NAMESPACE=$(oci os ns get --query "data" --raw-output)
REGION=$(oci iam region-subscription list --query "data[0].\"region-name\"" --raw-output)

echo "📊 環境資訊："
echo "   Tenancy: $TENANCY_OCID"
echo "   Namespace: $NAMESPACE"
echo "   Region: $REGION"

# 建立 Application（如果不存在）
APP_NAME="taichung-crawler-app"
echo ""
echo "🔧 檢查 Functions Application..."

APP_ID=$(oci fn application list --compartment-id $TENANCY_OCID --query "data[?\"display-name\"=='$APP_NAME'].id" --raw-output 2>/dev/null)

if [ -z "$APP_ID" ]; then
    echo "📦 建立新的 Application..."
    
    # 取得或建立子網路
    SUBNET_ID=$(oci network subnet list --compartment-id $TENANCY_OCID --query "data[0].id" --raw-output 2>/dev/null)
    
    if [ -z "$SUBNET_ID" ]; then
        echo "❌ 找不到子網路，請先在 OCI Console 建立 VCN 和子網路"
        exit 1
    fi
    
    APP_ID=$(oci fn application create \
        --compartment-id $TENANCY_OCID \
        --display-name $APP_NAME \
        --subnet-ids "[\"$SUBNET_ID\"]" \
        --query "data.id" \
        --raw-output)
        
    echo "✅ Application 建立成功: $APP_ID"
else
    echo "✅ 使用現有 Application: $APP_ID"
fi

# 設定 Application 環境變數
echo ""
echo "🔧 設定環境變數..."
oci fn application update \
    --application-id $APP_ID \
    --config '{"OCI_RESOURCE_PRINCIPAL_VERSION": "2.2", "NAMESPACE": "'$NAMESPACE'", "BUCKET_NAME": "taichung-building-permits"}'

# 準備 Function 檔案
echo ""
echo "📦 準備 Function 檔案..."

cd /mnt/c/claude\ code/建照爬蟲/oci
mkdir -p daily-crawler-function

# 複製並修改檔案
cp optimized-crawler-stable.py daily-crawler-function/
cp baojia_companies.json daily-crawler-function/

# 建立 func.py
cat > daily-crawler-function/func.py << 'EOF'
import io
import json
import logging
import oci
import sys
from datetime import datetime
from fdk import response

# 添加當前目錄到 Python 路徑
sys.path.append('/function')

# 載入爬蟲模組
from optimized_crawler_stable import AdvancedCrawler

def handler(ctx, data: io.BytesIO = None):
    """每日爬蟲 Function"""
    logging.getLogger().info("開始每日爬蟲任務")
    
    try:
        # 使用資源主體認證
        signer = oci.auth.signers.get_resource_principals_signer()
        object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        
        namespace = ctx.Config()['NAMESPACE']
        bucket_name = ctx.Config()['BUCKET_NAME']
        
        # 下載現有資料
        try:
            obj = object_storage.get_object(namespace, bucket_name, 'data/permits.json')
            existing_data = json.loads(obj.data.content.decode('utf-8'))
            
            # 找出114年最大序號
            seq_114 = [p['sequenceNumber'] for p in existing_data['permits'] if p.get('permitYear') == 114]
            start_seq = max(seq_114) + 1 if seq_114 else 1
        except:
            start_seq = 1
            
        logging.getLogger().info(f"從序號 {start_seq} 開始爬取")
        
        # 執行爬蟲
        crawler = AdvancedCrawler()
        results = []
        consecutive_empty = 0
        
        for i in range(50):  # 每次最多爬取50筆
            seq = start_seq + i
            index_key = f'1141{seq:05d}00'
            
            result = crawler.crawl_single_permit(index_key)
            
            if result and result != 'NO_DATA':
                results.append(result)
                consecutive_empty = 0
            elif result == 'NO_DATA':
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
            else:
                break
                
        # 上傳結果
        if results:
            crawler.upload_batch_data(results)
            message = f"成功爬取 {len(results)} 筆資料"
        else:
            message = "沒有新資料"
            
        logging.getLogger().info(message)
        
        return response.Response(
            ctx, 
            response_data=json.dumps({
                "status": "success",
                "message": message,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }),
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logging.getLogger().error(f"錯誤: {str(e)}")
        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": "error",
                "message": str(e)
            }),
            headers={"Content-Type": "application/json"}
        )
EOF

# 建立 func.yaml
cat > daily-crawler-function/func.yaml << EOF
schema_version: 20180708
name: daily-crawler
version: 0.0.1
runtime: python
build_image: fnproject/python:3.9-dev
run_image: fnproject/python:3.9
entrypoint: /python/bin/fdk /function/func.py handler
memory: 256
timeout: 300
EOF

# 建立 requirements.txt
cat > daily-crawler-function/requirements.txt << EOF
fdk>=0.1.50
oci>=2.88.0
requests>=2.28.0
beautifulsoup4>=4.11.0
EOF

# 修改爬蟲檔案名稱（移除連字號）
cd daily-crawler-function
mv optimized-crawler-stable.py optimized_crawler_stable.py

echo ""
echo "📤 部署 Function..."
echo ""
echo "請執行以下命令來完成部署："
echo ""
echo "1. 登入 Docker Registry:"
echo "   docker login -u '$NAMESPACE/oracleidentitycloudservice/<your-email>' $REGION.ocir.io"
echo ""
echo "2. 部署 Function:"
echo "   cd daily-crawler-function"
echo "   fn deploy --app $APP_NAME"
echo ""
echo "3. 建立定時觸發器（在 OCI Console）："
echo "   - 前往 Events Service"
echo "   - 建立 Rule，使用 Timer 類型"
echo "   - Cron Expression: 30 7 * * *"
echo "   - Action: 呼叫 Function daily-crawler"
echo ""
echo "💡 或使用 OCI Alarms + Notifications 來定時觸發"