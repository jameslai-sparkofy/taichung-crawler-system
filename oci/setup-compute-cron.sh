#!/bin/bash
# 在 OCI Compute Instance 上設定自動爬蟲

echo "======================================="
echo "OCI Compute Instance 自動爬蟲設定"
echo "======================================="
echo ""
echo "這個腳本應該在您的 OCI Compute Instance 上執行"
echo ""

# 建立爬蟲目錄
mkdir -p ~/building-permit-crawler
cd ~/building-permit-crawler

# 下載爬蟲腳本
echo "📥 下載爬蟲腳本..."
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/oci-crawler.py \
    --file oci-crawler.py

chmod +x oci-crawler.py

# 建立每日執行腳本
cat > daily-crawler.sh << 'EOF'
#!/bin/bash
# 每日執行建照爬蟲

LOG_FILE="/home/opc/building-permit-crawler/logs/crawler-$(date +%Y%m%d).log"
mkdir -p /home/opc/building-permit-crawler/logs

echo "========================================" >> $LOG_FILE
echo "開始執行建照爬蟲: $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

# 執行爬蟲
cd /home/opc/building-permit-crawler
/usr/bin/python3 oci-crawler.py >> $LOG_FILE 2>&1

echo "爬蟲執行完成: $(date)" >> $LOG_FILE
echo "" >> $LOG_FILE

# 清理30天前的日誌
find /home/opc/building-permit-crawler/logs -name "*.log" -mtime +30 -delete
EOF

chmod +x daily-crawler.sh

# 建立簡化版爬蟲（只爬最新資料）
cat > daily-update-crawler.py << 'EOF'
#!/usr/bin/env python3
"""
每日更新爬蟲 - 只爬取最新的建照資料
"""

import subprocess
import json
import re
from datetime import datetime
import time
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    namespace = "nrsdi1rz5vl8"
    bucket_name = "taichung-building-permits"
    
    # 載入現有資料
    logger.info("載入現有資料...")
    permits = []
    try:
        subprocess.run(["oci", "os", "object", "get", "--namespace", namespace,
                       "--bucket-name", bucket_name, "--name", "data/permits.json",
                       "--file", "/tmp/existing.json"], capture_output=True)
        with open('/tmp/existing.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            permits = data.get('permits', [])
            logger.info(f"載入 {len(permits)} 筆現有資料")
    except:
        logger.error("無法載入現有資料")
        return
    
    # 取得當前年份（民國年）
    current_year = datetime.now().year - 1911
    
    # 爬取最新50筆
    new_count = 0
    max_crawl = 50
    permit_type = 1
    
    logger.info(f"開始爬取 {current_year} 年最新資料...")
    
    # 從大序號往回爬
    for seq in range(9999, 0, -1):
        if new_count >= max_crawl:
            break
            
        index_key = f"{current_year}{permit_type}{seq:05d}00"
        
        # 檢查是否已存在
        if any(p.get('indexKey') == index_key for p in permits):
            continue
        
        # 爬取單筆
        try:
            # 第一次訪問
            subprocess.run(["wget", "-q", "--save-cookies=/tmp/cookies.txt",
                          "--user-agent=Mozilla/5.0", "-O", "/tmp/first.html",
                          f"{base_url}?INDEX_KEY={index_key}"], capture_output=True)
            
            time.sleep(3)
            
            # 第二次訪問
            result = subprocess.run(["wget", "-q", "--load-cookies=/tmp/cookies.txt",
                                   "--user-agent=Mozilla/5.0", "-O", f"/tmp/page.html",
                                   f"{base_url}?INDEX_KEY={index_key}"], capture_output=True)
            
            if result.returncode == 0:
                with open("/tmp/page.html", "rb") as f:
                    content = f.read()
                
                if len(content) > 1000:
                    try:
                        html = content.decode('big5')
                    except:
                        html = content.decode('utf-8', errors='ignore')
                    
                    # 檢查是否有建照資料
                    if "建造執照號碼" in html:
                        # 簡單解析
                        permit_data = {'indexKey': index_key, 'crawledAt': datetime.now().isoformat()}
                        
                        # 建照號碼
                        m = re.search(r'<span class="conlist w20 tc">([^<]+號)</span>', html)
                        if m:
                            permit_data['permitNumber'] = m.group(1)
                            permit_data['permitYear'] = current_year
                            permit_data['permitType'] = permit_type
                            permit_data['sequenceNumber'] = seq
                            permit_data['versionNumber'] = 0
                            
                            permits.append(permit_data)
                            new_count += 1
                            logger.info(f"✅ 新增: {permit_data['permitNumber']}")
                        
        except Exception as e:
            logger.error(f"爬取失敗 {index_key}: {e}")
        
        time.sleep(2)
    
    # 儲存更新後的資料
    if new_count > 0:
        logger.info(f"儲存 {new_count} 筆新資料...")
        
        sorted_permits = sorted(permits, key=lambda x: (
            -x.get('permitYear', 0),
            -x.get('sequenceNumber', 0)
        ))
        
        data = {
            "lastUpdate": datetime.now().isoformat(),
            "totalCount": len(sorted_permits),
            "yearCounts": {},
            "permits": sorted_permits
        }
        
        for permit in sorted_permits:
            year = permit.get('permitYear', 0)
            if year not in data['yearCounts']:
                data['yearCounts'][year] = 0
            data['yearCounts'][year] += 1
        
        with open('/tmp/permits_updated.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        subprocess.run(["oci", "os", "object", "put", "--namespace", namespace,
                       "--bucket-name", bucket_name, "--name", "data/permits.json",
                       "--file", "/tmp/permits_updated.json", "--force"], capture_output=True)
        
        logger.info("✅ 資料更新完成")
    else:
        logger.info("沒有發現新資料")

if __name__ == "__main__":
    main()
EOF

chmod +x daily-update-crawler.py

# 設定 crontab
echo ""
echo "📅 設定 crontab..."
echo ""

# 建立 crontab 項目
CRON_CMD="/home/opc/building-permit-crawler/daily-crawler.sh"
CRON_TIME="0 3 * * *"  # 每天凌晨 3:00

# 檢查是否已存在
if crontab -l 2>/dev/null | grep -q "$CRON_CMD"; then
    echo "✅ Crontab 已經設定"
else
    # 添加到 crontab
    (crontab -l 2>/dev/null; echo "$CRON_TIME $CRON_CMD") | crontab -
    echo "✅ Crontab 設定完成"
fi

echo ""
echo "======================================="
echo "✅ 自動爬蟲設定完成！"
echo "======================================="
echo ""
echo "設定內容："
echo "- 每日凌晨 3:00 自動執行"
echo "- 爬取最新 50 筆建照資料"
echo "- 日誌保存在 ~/building-permit-crawler/logs/"
echo ""
echo "測試命令："
echo "  ./daily-crawler.sh"
echo ""
echo "查看 crontab："
echo "  crontab -l"
echo ""
echo "查看最新日誌："
echo "  tail -f ~/building-permit-crawler/logs/crawler-*.log"
echo ""