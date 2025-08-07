# Google Cloud 認證步驟

## 方法 1：使用 gcloud 指令（推薦）

在 Windows PowerShell 或 CMD 中執行：

```cmd
gcloud auth login
```

這會自動開啟瀏覽器進行認證。

## 方法 2：使用服務帳號金鑰

1. 前往 Google Cloud Console：https://console.cloud.google.com
2. 選擇專案 "taichung-crawler"
3. 前往「IAM 與管理」>「服務帳號」
4. 建立服務帳號或使用現有的
5. 下載 JSON 金鑰檔案
6. 設定環境變數：
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/keyfile.json"
   ```

## 方法 3：使用 Cloud Shell（最簡單）

1. 開啟 https://console.cloud.google.com
2. 點擊右上角的 Cloud Shell 圖示（終端機圖示）
3. 在 Cloud Shell 中執行：
   ```bash
   # 下載啟動腳本
   curl -o startup.sh https://your-startup-script-url
   # 或直接貼上腳本內容
   
   # 建立實例
   gcloud compute instances create taichung-crawler-gcp \
     --zone=asia-east1-b \
     --machine-type=e2-micro \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --boot-disk-size=20GB \
     --metadata-from-file=startup-script=startup.sh \
     --tags=http-server
   ```

## 方法 4：透過網頁介面建立

最直接的方式是透過 Google Cloud Console 網頁介面：

1. 前往：https://console.cloud.google.com/compute/instances
2. 點擊「建立執行個體」
3. 設定參數：
   - 名稱：taichung-crawler-gcp
   - 區域：asia-east1 (台灣)
   - 區域：asia-east1-b
   - 機器系列：E2
   - 機器類型：e2-micro
   - 開機磁碟：
     - 作業系統：Ubuntu
     - 版本：Ubuntu 22.04 LTS
     - 大小：20 GB
4. 展開「進階選項」
5. 在「管理」>「自動化」>「啟動指令碼」貼上腳本內容

這樣就不需要處理認證問題了！