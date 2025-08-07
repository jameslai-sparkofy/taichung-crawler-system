# 設定 OCI Functions 自動爬蟲

本指南說明如何在 OCI 上設定每日凌晨 3:00 自動執行的建照爬蟲。

## 前置準備

1. 確保已安裝 Fn CLI
2. 已設定 OCI CLI
3. 有適當的 OCI 權限

## 步驟 1：建立 Application

```bash
# 設定變數
COMPARTMENT_ID="<your-compartment-id>"
SUBNET_ID="<your-subnet-id>"

# 建立 Application
oci fn application create \
    --compartment-id $COMPARTMENT_ID \
    --display-name "building-permit-crawler" \
    --subnet-ids '["'$SUBNET_ID'"]'
```

## 步驟 2：設定 Fn CLI

```bash
# 取得 Application OCID
APP_ID=$(oci fn application list --compartment-id $COMPARTMENT_ID --display-name "building-permit-crawler" --query "data[0].id" --raw-output)

# 設定 context
fn create context oci-crawler --provider oracle
fn use context oci-crawler

# 設定 registry（使用您的區域）
REGION="ap-tokyo-1"
NAMESPACE=$(oci os ns get --query data --raw-output)
fn update context oracle.compartment-id $COMPARTMENT_ID
fn update context registry ${REGION}.ocir.io/${NAMESPACE}

# 登入 Docker Registry
echo $OCI_AUTH_TOKEN | docker login -u ${NAMESPACE}/oracleidentitycloudservice/<your-email> ${REGION}.ocir.io --password-stdin
```

## 步驟 3：部署 Function

```bash
# 進入 function 目錄
cd "/mnt/c/claude code/建照爬蟲/oci/function"

# 部署
fn -v deploy --app building-permit-crawler
```

## 步驟 4：設定 Function 權限

建立動態群組（Dynamic Group）：
```bash
oci iam dynamic-group create \
    --compartment-id $COMPARTMENT_ID \
    --name "building-permit-functions" \
    --description "Functions for building permit crawler" \
    --matching-rule "ALL {resource.type = 'fnfunc', resource.compartment.id = '$COMPARTMENT_ID'}"
```

建立政策（Policy）允許 Function 存取 Object Storage：
```bash
oci iam policy create \
    --compartment-id $COMPARTMENT_ID \
    --name "building-permit-function-policy" \
    --description "Allow functions to access object storage" \
    --statements '[
        "Allow dynamic-group building-permit-functions to manage objects in compartment id '$COMPARTMENT_ID' where target.bucket.name='"'"'taichung-building-permits'"'"'",
        "Allow dynamic-group building-permit-functions to read objectstorage-namespaces in compartment id '$COMPARTMENT_ID'"
    ]'
```

## 步驟 5：建立定時觸發器

使用 OCI Events 和 Alarms 建立定時觸發：

### 方法 1：使用 OCI Alarm（推薦）

```bash
# 建立 Topic
oci ons topic create \
    --compartment-id $COMPARTMENT_ID \
    --name "building-permit-scheduler" \
    --description "Scheduler for building permit crawler"

TOPIC_ID=$(oci ons topic list --compartment-id $COMPARTMENT_ID --name "building-permit-scheduler" --query "data[0].\"topic-id\"" --raw-output)

# 建立 Subscription 觸發 Function
FUNCTION_ID=$(oci fn function list --application-id $APP_ID --display-name "taichung-building-permit-crawler" --query "data[0].id" --raw-output)

oci ons subscription create \
    --compartment-id $COMPARTMENT_ID \
    --topic-id $TOPIC_ID \
    --protocol "ORACLE_FUNCTIONS" \
    --subscription-endpoint $FUNCTION_ID
```

### 方法 2：使用 OCI Resource Scheduler

建立排程作業：
```bash
# 建立排程
cat > schedule.json << EOF
{
  "compartmentId": "$COMPARTMENT_ID",
  "displayName": "Daily Building Permit Crawler",
  "description": "Run building permit crawler daily at 3:00 AM",
  "schedule": {
    "scheduleType": "CRON",
    "cronExpression": "0 3 * * *",
    "timeZone": "Asia/Taipei"
  },
  "resources": [{
    "id": "$FUNCTION_ID",
    "region": "$REGION"
  }],
  "operation": "INVOKE_FUNCTION"
}
EOF

oci resource-scheduler schedule create --from-json file://schedule.json
```

## 步驟 6：測試 Function

```bash
# 手動觸發測試
echo '{}' | fn invoke building-permit-crawler taichung-building-permit-crawler

# 查看日誌
oci logging-search search-logs \
    --search-query "search \"$COMPARTMENT_ID\" | source='$FUNCTION_ID'" \
    --time-start $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S.000Z) \
    --time-end $(date -u +%Y-%m-%dT%H:%M:%S.000Z)
```

## 監控與維護

1. **查看執行日誌**：
   - 在 OCI Console → Functions → 選擇您的 Function → Logs

2. **查看爬蟲記錄**：
   ```bash
   oci os object get \
       --namespace $NAMESPACE \
       --bucket-name taichung-building-permits \
       --name logs/crawler-logs.json \
       --file - | jq .
   ```

3. **調整爬取數量**：
   - 修改 `func.py` 中的 `max_crawl = 50` 來調整每次爬取的數量

4. **更新 Function**：
   ```bash
   fn -v deploy --app building-permit-crawler
   ```

## 注意事項

1. Function 有 5 分鐘的執行時間限制（已在 func.yaml 設定為 300 秒）
2. 每次執行最多爬取 50 筆新資料，避免超時
3. Function 會自動檢查重複，不會重複爬取已存在的資料
4. 所有爬取記錄都會保存在 `logs/crawler-logs.json`

## 費用估算

- Functions: 每月前 200 萬次調用免費
- Object Storage: 前 10 GB 免費
- 預估每月費用：幾乎為 0（在免費額度內）