# OCI Compute Instance 爬蟲部署指南

## 步驟 1：建立 Compute Instance

### 在 OCI Console 建立 VM

1. **進入 Compute > Instances**
2. **點擊 Create Instance**
3. **設定如下**：
   - Name: `building-permit-crawler`
   - Image: Ubuntu 22.04
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - Network: 選擇你的 VCN 和 Public Subnet
   - SSH keys: 上傳或貼上你的 SSH 公鑰

4. **點擊 Create**

## 步驟 2：設定 Instance Principal（推薦）

### 建立 Dynamic Group

1. **Identity & Security > Dynamic Groups**
2. **Create Dynamic Group**：
   ```
   Name: crawler-instances
   Description: Instances for building permit crawler
   Rule: instance.compartment.id = '<你的compartment-ocid>'
   ```

### 建立 Policy

1. **Identity & Security > Policies**
2. **Create Policy**：
   ```
   Name: crawler-instance-policy
   Description: Allow crawler instances to access object storage
   
   Statements:
   Allow dynamic-group crawler-instances to manage objects in compartment <compartment-name> where target.bucket.name='taichung-building-permits'
   Allow dynamic-group crawler-instances to read buckets in compartment <compartment-name>
   ```

## 步驟 3：連線到 Instance

```bash
# 使用 SSH 連線（替換 IP）
ssh ubuntu@<instance-public-ip>
```

## 步驟 4：執行設定

1. **上傳檔案**：
```bash
# 在本機執行
scp setup.sh crawler-compute.py ubuntu@<instance-ip>:~/
```

2. **執行設定腳本**：
```bash
# 在 Instance 上執行
chmod +x setup.sh
./setup.sh
```

3. **移動爬蟲程式**：
```bash
mv ~/crawler-compute.py /home/ubuntu/crawler/
```

## 步驟 5：測試執行

1. **測試 OCI 連線**：
```bash
./test_crawler.sh
```

2. **手動執行爬蟲**：
```bash
./run_crawler.sh
```

3. **檢查 cron 設定**：
```bash
crontab -l
# 應該看到: 25 6 * * * /home/ubuntu/run_crawler.sh
```

## 步驟 6：監控

### 查看日誌

```bash
# 爬蟲執行日誌
tail -f ~/crawler.log

# Cron 執行日誌
tail -f ~/cron.log

# 執行記錄
cat ~/crawler_run.log
```

### 查看 OCI Object Storage

檢查以下檔案是否有更新：
- `data/permits.json` - 建照資料
- `data/crawl-logs.json` - 執行記錄

## 維護指令

### 手動執行爬蟲
```bash
/home/ubuntu/run_crawler.sh
```

### 修改爬蟲參數
編輯 `/home/ubuntu/crawler/crawler-compute.py` 中的參數：
- `max_consecutive_failures = 5` - 連續失敗次數
- `max_crawl_per_run = 50` - 每次最多爬取筆數
- `request_delay = 0.8` - 請求延遲（秒）

### 更新 Python 套件
```bash
source /home/ubuntu/crawler_env/bin/activate
pip install --upgrade oci requests beautifulsoup4 lxml
```

### 修改執行時間
```bash
# 編輯 crontab
crontab -e
# 修改時間（分 時 日 月 星期）
# 例如改為早上 7:00: 0 7 * * *
```

## 故障排除

### 1. OCI 認證錯誤
- 確認 Instance Principal 設定正確
- 或建立 `~/.oci/config` 檔案

### 2. 爬蟲無法執行
- 檢查虛擬環境：`source /home/ubuntu/crawler_env/bin/activate`
- 檢查套件安裝：`pip list`

### 3. Cron 不執行
- 檢查 cron 服務：`sudo service cron status`
- 查看系統日誌：`grep CRON /var/log/syslog`

## 優點

✅ **永久免費**：使用 Always Free VM.Standard.E2.1.Micro
✅ **穩定可靠**：24/7 運行，不需要保持電腦開機
✅ **自動執行**：cron 自動定時執行
✅ **原生整合**：直接存取 OCI Object Storage
✅ **易於維護**：SSH 連線即可管理