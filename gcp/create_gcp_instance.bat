@echo off
echo === Google Cloud 爬蟲實例建立腳本 ===
echo.

REM 設定專案
echo 設定專案...
gcloud config set project taichung-crawler

REM 建立 Storage Bucket
echo.
echo 建立 Storage Bucket...
gsutil mb -l asia-east1 gs://taichung-crawler-permits 2>NUL
if %errorlevel% neq 0 (
    echo Storage Bucket 可能已存在，繼續執行...
)

REM 複製啟動腳本
echo.
echo 準備啟動腳本...
copy /Y C:\tmp\gcp_crawler_startup.sh %TEMP%\gcp_crawler_startup.sh >NUL

REM 建立實例
echo.
echo 建立 Compute Engine 實例...
gcloud compute instances create taichung-crawler ^
    --zone=asia-east1-b ^
    --machine-type=e2-micro ^
    --image-family=ubuntu-2204-lts ^
    --image-project=ubuntu-os-cloud ^
    --boot-disk-size=20GB ^
    --metadata-from-file=startup-script=%TEMP%\gcp_crawler_startup.sh ^
    --tags=http-server

if %errorlevel% equ 0 (
    echo.
    echo ✅ 實例建立成功！
    echo.
    echo 下一步：
    echo 1. 等待 2-3 分鐘讓實例完成初始化
    echo 2. SSH 連線到實例：
    echo    gcloud compute ssh taichung-crawler --zone=asia-east1-b
    echo 3. 檢查爬蟲日誌：
    echo    tail -f /home/crawler/crawler.log
) else (
    echo.
    echo ❌ 實例建立失敗，請檢查錯誤訊息
)

pause