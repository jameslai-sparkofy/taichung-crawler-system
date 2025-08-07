#!/bin/bash
# 在 Google Cloud Shell 中執行的部署腳本

echo "=== Google Cloud Shell 爬蟲部署 ==="
echo ""

# 建立啟動腳本
cat > /tmp/startup.sh << 'STARTUP_SCRIPT'
#!/bin/bash

# 更新系統
apt-get update
apt-get install -y python3-pip python3-dev curl jq wget unzip

# 安裝 Python 套件
pip3 install requests beautifulsoup4 lxml oci-cli

# 設定時區
timedatectl set-timezone Asia/Taipei

# 建立工作目錄
mkdir -p /home/crawler
cd /home/crawler

# 設定 OCI CLI
mkdir -p /root/.oci
cat > /root/.oci/config << 'EOF'
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaabxuqfxbheexsxha7ewice2zidrcwnswzi3jnj7lyispvvd3fepuq
fingerprint=63:46:82:b0:4a:f4:14:80:fa:58:94:8f:59:e7:88:d8
tenancy=ocid1.tenancy.oc1..aaaaaaaatj2jclzf26lcsptdllggkodf4kvaj4gajrxtjngakmjl6smu3t6q
region=ap-tokyo-1
key_file=/root/.oci/oci_api_key.pem
EOF

# OCI 私鑰
cat > /root/.oci/oci_api_key.pem << 'EOF'
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDb4qpU7Fvte6K1
T6kGfYNqKRcmJRz5U5xpHkrcjsUahhcHGXUXKK3D5CJoFH6hSDGzIDH3Mx1YqlPj
ZJf1AAbQdaOOjvE4aBKvUfQFpILquQJPTpxKdKkA9Yl8JE8sNUQkkikfLKaBCoU4
OWEebS7J8j1J6UYSVbyvTDmd7K/ilnsS0cKdQm7ATFPpCDPRGj9n4OFeMEcv6jMD
3Aax8J0LoTQDzTBH/eAK1kYCzMEYmJAxff4eANvQxRmhc5aDWm7MXVL5lR7HmKQ7
L+VtcYANKGTiDSBNO2fT8YxMEW7pwEi6oqD4OHJbFHrAL6k9Y5gqg4k9z1y8U5Rb
CcTMQC8PAgMBAAECggEABJYPN5vwKzGNKGpNLVNSCmJwWmgsB4phvUn2TooFJPBu
gCrnrEztHGz5wTbHmx1lIGi/6rWd3c7vJaM9mJ1erSQ/WaH0+YU2PYJpzPNcJtQo
eJ1Cv2RoZGD1JV7jMzInYpJwGZ9KdpQjgYHaZokOjNmFo3ixNT3i0HQCLHanTN8s
rXvgmgVMR7oxrqNRgJ1mVVEWDT4SfPBCwPzxH6Xxp4Kl3Xs9R4f5qLHtrQS7k7jh
WGxT6d2NnQLSG7DvKbwpnmUbCIPKnJUG4M4E4jBvUG0OwQxCMht8c5nbLcznEeth
8LYU2kpQxNMPWivKbU3dzfYJGsj+ByVG8Tqp2BAAAQKBgQD8M0L5LzdsM0s7vG1P
4y1btzrFBJMGdNHcJdaShips/KEvAhuGVH7X6h+ru3Z3TdPDNL6mjqGMMxtPuKWm
Hbwf8Xvv+xPJu2FEKtOh6PJvUWBGTQG1ezO9+rTgVTkAu/mFAEedmoLgf0W8S5mC
vSuKloiRMPpQA3wVaMEVYYOojwKBgQDfOJ+DdqPNMLOGp5yL+TBI9fdIcZtnYs1U
+cAv0rYy3MU/PW3r3MTkweUQ5GtqmYm1dKC/uXe+LdlKC0pqfpuva5vYcopDO9VM
bUwLPJwBTLEMnRXBpkD8vfaGvMJbW8Pf8ysnwMr0smVsPSWq/Y12YtoHvQIbxJFZ
zUwojVMgQQKBgFKdIDvDPkKqRd2NBcIBzc3FeXWjNuVUw+6F0mQPFQW6lD2HNfZ8
v+RltNk2F3cXfVqxyPK8yrBDRBsjJX2qjBZ6d0kBSm4eKPLcqMi3FP1pAHPR1bdR
tXObKpjJosjxQxXD8rxaW5Q8mLq9JpFPDKDkH7RDfvC2OUCOBQo7gfvVAoGBAKua
bgJoI2Sp0PEPszlBiYgPs4ga8dIxEHMH3gIiQF6N+fIGzJJKWU5BqOO2gLO0K4l6
l6K4FSZLPYsCg2pLzT9pNpmRH6SrojEQCdrYNLfUc5OVn5qE+mh3dW2dencXGRqk
b9VmpbcGnyMO6OvBUUmcdpPrKKoQIDTjVviHlBGBAoGAG9b1y4bNNdY3vCUgUJkY
x1Oc4rk7EE8Q/i/Lqjc0r5t7QaSlNGQF5zxbJMSEjddMNI8+t/vYdIYb06vE5oDB
fvCUXKnE5U+YFczstTnUa2LmBprgkqM4btoIl7+dXCShUfM9GyPD5aLKnr6cp9OQ
GZQT8cKndszDOazOhPoIToY=
-----END PRIVATE KEY-----
EOF

chmod 600 /root/.oci/oci_api_key.pem

# 建立爬蟲程式
cat > /home/crawler/crawler.py << 'CRAWLER_SCRIPT'
#!/usr/bin/env python3
import os
import json
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import subprocess
import re

OCI_NAMESPACE = "nrsdi1rz5vl8"
OCI_BUCKET = "taichung-building-permits"

def upload_to_oci(file_path, object_name):
    try:
        cmd = f"oci os object put --namespace {OCI_NAMESPACE} --bucket-name {OCI_BUCKET} --name {object_name} --file {file_path} --force"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def download_from_oci(object_name, local_path):
    try:
        cmd = f"oci os object get --namespace {OCI_NAMESPACE} --bucket-name {OCI_BUCKET} --name {object_name} --file {local_path} --force"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def crawl_single_permit(year, seq):
    index_key = f"{year}10{seq:05d}00"
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "查無此案件編號資料" in response.text or len(response.text) < 1000:
            return "BLANK"
        
        permit_data = {
            'indexKey': index_key,
            'year': year,
            'sequence': seq,
            'crawlTime': datetime.now().isoformat()
        }
        
        fields = soup.find_all('td', class_='tit_intd2 w15')
        for field in fields:
            label = field.text.strip()
            value_elem = field.find_next_sibling('td')
            if value_elem:
                value = value_elem.text.strip()
                
                if '建照號碼' in label:
                    permit_data['permitNumber'] = value
                elif '申請人' in label:
                    permit_data['applicant'] = value
                elif '地址' in label:
                    permit_data['address'] = value
                elif '建築物概要' in label:
                    floor_info = value
                    permit_data['buildingSummary'] = floor_info
                    
                    floor_match = re.search(r'地上(\d+)層', floor_info)
                    if floor_match:
                        permit_data['floors'] = int(floor_match.group(1))
                    
                    building_match = re.search(r'(\d+)棟', floor_info)
                    if building_match:
                        permit_data['buildings'] = int(building_match.group(1))
                        permit_data['buildingCount'] = int(building_match.group(1))
                    
                    unit_match = re.search(r'(\d+)戶', floor_info)
                    if unit_match:
                        permit_data['units'] = int(unit_match.group(1))
        
        area_match = re.search(r'總樓地板面積.*?<span class="conlist w50">([0-9.,]+)', response.text)
        if area_match:
            permit_data['totalFloorArea'] = float(area_match.group(1).replace(',', ''))
        
        date_match = re.search(r'發照日期.*?(\d{4})/(\d{2})/(\d{2})', response.text)
        if date_match:
            year_date = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            permit_data['issueDate'] = f"{year_date}-{month:02d}-{day:02d}"
        
        return permit_data
        
    except Exception as e:
        print(f"❌ 爬取失敗 {index_key}: {e}")
        return None

def main():
    print(f"🚀 Google Cloud 爬蟲開始執行: {datetime.now()}")
    
    permits_data = []
    if download_from_oci("all_permits.json", "/tmp/all_permits.json"):
        with open("/tmp/all_permits.json", "r", encoding="utf-8") as f:
            permits_data = json.load(f)
        print(f"📊 載入現有資料: {len(permits_data)} 筆")
    
    crawl_logs = []
    if download_from_oci("data/crawl-logs.json", "/tmp/crawl-logs.json"):
        with open("/tmp/crawl-logs.json", "r", encoding="utf-8") as f:
            crawl_logs = json.load(f)
    
    latest_seq = 0
    for permit in permits_data:
        if permit.get('year') == 114:
            seq = permit.get('sequence', 0)
            if seq > latest_seq:
                latest_seq = seq
    
    print(f"📊 最新序號: {latest_seq}")
    
    new_count = 0
    blank_count = 0
    error_count = 0
    
    for seq in range(latest_seq + 1, latest_seq + 31):
        print(f"\n🔍 爬取: 114年 序號{seq}")
        
        result = crawl_single_permit(114, seq)
        
        if result == "BLANK":
            print("   ⚪ 空白資料")
            blank_count += 1
            if blank_count >= 5:
                print("❌ 連續空白資料，停止爬取")
                break
        elif result:
            permits_data.append(result)
            print(f"   ✅ 成功: {result.get('permitNumber', 'N/A')}")
            new_count += 1
            blank_count = 0
        else:
            print("   ❌ 失敗")
            error_count += 1
            if error_count >= 3:
                print("❌ 連續錯誤，停止爬取")
                break
        
        time.sleep(1.5)
    
    log_entry = {
        'executionTime': datetime.now().isoformat(),
        'newRecords': new_count,
        'totalRecords': len(permits_data),
        'latestSequence': latest_seq + new_count,
        'source': 'Google Cloud Taiwan'
    }
    crawl_logs.append(log_entry)
    
    print("\n💾 儲存資料到 OCI...")
    
    with open("/tmp/all_permits.json", "w", encoding="utf-8") as f:
        json.dump(permits_data, f, ensure_ascii=False, indent=2)
    upload_to_oci("/tmp/all_permits.json", "all_permits.json")
    
    with open("/tmp/crawl-logs.json", "w", encoding="utf-8") as f:
        json.dump(crawl_logs, f, ensure_ascii=False, indent=2)
    upload_to_oci("/tmp/crawl-logs.json", "data/crawl-logs.json")
    
    # 更新 HTML
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>台中市建照查詢</title></head>
<body>
<h1>台中市建照查詢系統</h1>
<p>最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>總資料數: {len(permits_data)} 筆</p>
<p>最新執行: 新增 {new_count} 筆</p>
<p>資料來源: Google Cloud (台灣 IP)</p>
</body></html>'''
    
    with open("/tmp/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    upload_to_oci("/tmp/index.html", "index.html")
    
    print(f"\n📊 執行統計:")
    print(f"   新增: {new_count} 筆")
    print(f"   總計: {len(permits_data)} 筆")
    print(f"\n🌐 查看結果: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html")

if __name__ == "__main__":
    main()
CRAWLER_SCRIPT

chmod +x /home/crawler/crawler.py

# 建立每日執行腳本
cat > /home/crawler/daily_crawler.sh << 'EOF'
#!/bin/bash
cd /home/crawler
echo "=== 每日爬蟲開始: $(date) ===" >> /home/crawler/crawler.log
python3 /home/crawler/crawler.py >> /home/crawler/crawler.log 2>&1
echo "=== 每日爬蟲結束: $(date) ===" >> /home/crawler/crawler.log
EOF

chmod +x /home/crawler/daily_crawler.sh

# 設定 cron job
echo "30 7 * * * /home/crawler/daily_crawler.sh" | crontab -

# 立即執行一次
cd /home/crawler
python3 crawler.py

echo "=== 爬蟲環境設定完成 ==="
STARTUP_SCRIPT

# 建立實例
echo "建立 GCP 實例..."
gcloud compute instances create taichung-crawler-gcp \
  --zone=asia-east1-b \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --metadata-from-file=startup-script=/tmp/startup.sh \
  --tags=http-server

echo ""
echo "✅ 部署完成！"
echo ""
echo "檢查狀態："
echo "gcloud compute ssh taichung-crawler-gcp --zone=asia-east1-b"
echo ""
echo "查看結果："
echo "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html"