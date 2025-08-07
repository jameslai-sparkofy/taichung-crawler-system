# OCI Compute Instance 爬蟲部署指南

## 前置準備

### 1. 建立 OCI Compute Instance（如果還沒有）

1. 登入 [OCI Console](https://cloud.oracle.com)
2. 前往 **Compute** > **Instances**
3. 點擊 **Create Instance**
4. 選擇配置：
   - **Shape**: VM.Standard.E2.1.Micro (Always Free)
   - **Image**: Oracle Linux 8 或 Ubuntu 22.04
   - **VCN**: 使用現有或建立新的
   - **SSH Keys**: 上傳你的公鑰

### 2. 設定安全規則

確保 Instance 可以對外連線（爬蟲需要）：
1. 前往 **Networking** > **Virtual Cloud Networks**
2. 選擇你的 VCN > **Security Lists**
3. 確認有以下出站規則：
   - Destination: 0.0.0.0/0
   - Protocol: All Protocols

### 3. 取得 Instance 資訊

記下以下資訊：
- **Public IP**: 在 Instance 詳情頁面可看到
- **SSH Key Path**: 你的私鑰檔案路徑

## 部署步驟

### 1. 編輯部署腳本

```bash
# 編輯部署腳本
nano deploy_to_oci_instance.sh

# 修改第 9 行，填入你的 Instance IP
INSTANCE_IP="你的.OCI.Instance.IP"

# 修改第 10 行，填入你的 SSH 私鑰路徑（如需要）
SSH_KEY_PATH="~/.ssh/你的私鑰檔名"
```

### 2. 執行部署

```bash
# 執行部署腳本
./deploy_to_oci_instance.sh
```

部署腳本會自動：
- 上傳所有必要檔案
- 安裝 Python 和相關套件
- 設定 OCI CLI
- 配置 cron 排程（每天 7:30）
- 測試環境設定

### 3. 設定 OCI 認證

SSH 連線到 Instance 設定 OCI CLI：

```bash
# 連線到 Instance
ssh -i ~/.ssh/你的私鑰 opc@你的.Instance.IP

# 設定 OCI CLI
oci setup config

# 依照提示輸入：
# - User OCID
# - Tenancy OCID
# - Region
# - 建立新的 API Key
```

或者使用 Instance Principal（推薦）：

1. 在 OCI Console 建立 Dynamic Group
2. 建立 Policy 允許 Dynamic Group 存取 Object Storage
3. 在程式中使用 Instance Principal 認證

## 驗證部署

### 1. 檢查 cron 設定

```bash
# 在 Instance 上執行
crontab -l

# 應該看到：
# 30 7 * * * /home/opc/taichung-building-crawler/daily_crawler_730am.sh
```

### 2. 手動測試爬蟲

```bash
# 在 Instance 上執行
cd ~/taichung-building-crawler
./daily_crawler_730am.sh

# 查看日誌
tail -f cron_daily_7am.log
```

### 3. 監控執行狀態

```bash
# 從本地查看遠端日誌
ssh -i ~/.ssh/你的私鑰 opc@你的.Instance.IP 'tail -f ~/taichung-building-crawler/cron_daily_7am.log'
```

## 故障排除

### 問題 1：OCI CLI 認證錯誤
```bash
# 檢查設定
oci setup repair-file-permissions
cat ~/.oci/config
```

### 問題 2：Python 套件缺失
```bash
# 重新安裝套件
pip3 install --user requests beautifulsoup4
```

### 問題 3：cron 沒有執行
```bash
# 檢查 cron 服務
sudo systemctl status crond
sudo systemctl start crond
sudo systemctl enable crond
```

## 日常維護

### 查看執行記錄
```bash
# 最近的執行記錄
tail -100 ~/taichung-building-crawler/cron_daily_7am.log

# 特定日期的記錄
grep "2025-01-30" ~/taichung-building-crawler/cron_daily_7am.log
```

### 更新爬蟲程式
```bash
# 從本地更新特定檔案
scp -i ~/.ssh/你的私鑰 optimized-crawler-stable.py opc@你的.Instance.IP:~/taichung-building-crawler/
```

### 停止/啟動爬蟲
```bash
# 停止
crontab -r

# 重新啟動
crontab -e
# 加入：30 7 * * * /home/opc/taichung-building-crawler/daily_crawler_730am.sh
```

## 安全建議

1. **限制 SSH 存取**：在 Security List 中限制 SSH (port 22) 只允許你的 IP
2. **定期更新**：`sudo yum update -y`
3. **備份設定**：定期備份 ~/.oci/config 和爬蟲資料