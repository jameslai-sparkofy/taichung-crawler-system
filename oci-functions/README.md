# OCI Functions 建照爬蟲部署指南

## 前置作業

1. 安裝 OCI CLI 和 Fn CLI：
```bash
# 安裝 OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# 安裝 Fn CLI
curl -LSs https://raw.githubusercontent.com/fnproject/cli/master/install | sh
```

2. 設定 OCI CLI：
```bash
oci setup config
```

## 建立 Function Application

1. 在 OCI Console 建立 Application：
   - 進入 Functions > Applications
   - 點擊 Create Application
   - 名稱：`building-permit-crawler-app`
   - VCN：選擇你的 VCN
   - Subnet：選擇 Public Subnet

2. 取得 Application OCID 和設定環境：
```bash
# 設定 Fn context
fn create context oci --provider oracle

# 設定 compartment
fn update context oracle.compartment-id <your-compartment-ocid>

# 設定 registry (替換 <region> 和 <namespace>)
fn update context registry <region>.ocir.io/<namespace>/building-permit-crawler

# 登入 Docker Registry
docker login -u '<namespace>/<username>' <region>.ocir.io
```

## 部署 Function

1. 初始化和部署：
```bash
cd /mnt/c/claude\ code/建照爬蟲/oci-functions

# 部署到 Application
fn -v deploy --app building-permit-crawler-app
```

2. 設定 Function 環境變數（在 OCI Console）：
   - `OCI_COMPARTMENT_ID`: 你的 Compartment OCID

## 設定定時觸發

1. 建立 OCI Events Rule：
   - 進入 Events Service > Rules
   - Create Rule：
     - Name: `building-permit-daily-crawl`
     - Description: 每日爬蟲觸發
     - Rule Conditions: 
       - Event Type: Timer
       - Schedule: `0 25 6 ? * * *` (每天 6:25)

2. 設定 Action：
   - Action Type: Functions
   - Function: 選擇 `building-permit-crawler`

## 測試執行

1. 手動觸發測試：
```bash
# 調用函數
fn invoke building-permit-crawler-app building-permit-crawler

# 查看日誌
fn logs building-permit-crawler-app building-permit-crawler
```

2. 在 OCI Console 查看執行結果：
   - Functions > Applications > 你的 App > Metrics

## 監控

1. 查看 Object Storage 中的日誌：
   - `data/crawl-logs.json`: 執行記錄
   - `data/permits.json`: 爬取的建照資料

2. 設定告警（選用）：
   - 在 Monitoring > Alarms 設定函數失敗告警

## 注意事項

- Function 執行時間上限為 5 分鐘（300秒）
- 每次最多爬取 50 筆資料
- 使用 Instance Principal 自動認證，無需設定 API Key
- wget 在 Function 環境中可用，適合爬取政府網站

## 更新 Function

修改程式碼後重新部署：
```bash
fn -v deploy --app building-permit-crawler-app
```