#!/bin/bash

echo "=== 快速部署 Google Cloud 爬蟲 ==="
echo ""
echo "這個腳本會建立一個 GCP 實例來執行爬蟲"
echo "資料會儲存到 OCI Object Storage"
echo ""

# 檢查檔案
if [ ! -f "/tmp/gcp_oci_startup.sh" ]; then
    echo "❌ 錯誤：找不到 /tmp/gcp_oci_startup.sh"
    echo "請確認啟動腳本已建立"
    exit 1
fi

# 顯示指令
echo "請執行以下指令來建立爬蟲實例："
echo ""
echo "gcloud compute instances create taichung-crawler-gcp \\"
echo "  --zone=asia-east1-b \\"
echo "  --machine-type=e2-micro \\"
echo "  --image-family=ubuntu-2204-lts \\"
echo "  --image-project=ubuntu-os-cloud \\"
echo "  --boot-disk-size=20GB \\"
echo "  --metadata-from-file=startup-script=/tmp/gcp_oci_startup.sh \\"
echo "  --tags=http-server \\"
echo "  --project=taichung-crawler"
echo ""
echo "建立完成後，可以用以下指令連線："
echo "gcloud compute ssh taichung-crawler-gcp --zone=asia-east1-b"
echo ""
echo "查看結果："
echo "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html"