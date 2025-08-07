#!/usr/bin/env python3
"""
測試爬取序號 1137 的建照
"""
import json
import logging
import subprocess
import time
from datetime import datetime

import oci
from oci.object_storage import ObjectStorageClient

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OCI 設定
NAMESPACE = "nrsdi1rz5vl8"
BUCKET_NAME = "taichung-building-permits"

class OCIStorage:
    def __init__(self):
        # 使用 Instance Principal 認證
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            self.object_storage = ObjectStorageClient(config={}, signer=signer)
            logger.info("使用 Instance Principal 認證")
        except Exception:
            # 如果 Instance Principal 失敗，使用預設設定檔
            config = oci.config.from_file()
            self.object_storage = ObjectStorageClient(config)
            logger.info("使用設定檔認證")
    
    def get_json_object(self, object_name):
        """從 OCI 讀取 JSON 物件"""
        try:
            response = self.object_storage.get_object(NAMESPACE, BUCKET_NAME, object_name)
            return json.loads(response.data.content.decode('utf-8'))
        except Exception as e:
            logger.error(f"讀取物件失敗 {object_name}: {str(e)}")
            return None
    
    def put_json_object(self, object_name, data):
        """寫入 JSON 物件到 OCI"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.object_storage.put_object(
                NAMESPACE, 
                BUCKET_NAME, 
                object_name,
                json_data.encode('utf-8')
            )
            logger.info(f"成功寫入 {object_name}")
            return True
        except Exception as e:
            logger.error(f"寫入物件失敗 {object_name}: {str(e)}")
            return False

def fetch_permit_1137():
    """抓取序號 1137 的建照"""
    index_key = "11410113700"
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    logger.info(f"開始爬取建照 {index_key}")
    
    try:
        # 使用 wget 下載，不指定編碼
        temp_file = f"/tmp/permit_{index_key}.html"
        
        cmd = [
            'wget', '-q', '-O', temp_file,
            '--timeout=30',
            '--tries=3',
            '--waitretry=2',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 嘗試用 BIG5 讀取
            try:
                with open(temp_file, 'r', encoding='big5') as f:
                    content = f.read()
                logger.info("成功使用 BIG5 編碼讀取")
            except:
                # 如果 BIG5 失敗，試試 UTF-8
                with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                logger.info("使用 UTF-8 編碼讀取")
            
            # 解析資料
            permit_data = parse_permit_data(content, index_key)
            
            if permit_data and permit_data != "NO_DATA":
                logger.info(f"✅ 成功爬取: {permit_data.get('permitNumber', '')}")
                
                # 儲存到 OCI
                storage = OCIStorage()
                
                # 讀取現有資料
                permits = storage.get_json_object('data/permits.json') or []
                
                # 檢查是否已存在
                existing_keys = {p['indexKey'] for p in permits if isinstance(p, dict)}
                
                if index_key not in existing_keys:
                    permits.append(permit_data)
                    permits.sort(key=lambda x: x.get('indexKey', ''))
                    
                    # 儲存回 OCI
                    if storage.put_json_object('data/permits.json', permits):
                        logger.info(f"✅ 已儲存到 OCI (總計 {len(permits)} 筆)")
                else:
                    logger.info("資料已存在，更新現有記錄")
                    # 更新現有記錄
                    for i, p in enumerate(permits):
                        if isinstance(p, dict) and p.get('indexKey') == index_key:
                            permits[i] = permit_data
                            break
                    
                    if storage.put_json_object('data/permits.json', permits):
                        logger.info("✅ 已更新 OCI 資料")
                
                # 更新爬蟲記錄
                log_entry = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'startTime': datetime.now().isoformat(),
                    'endTime': datetime.now().isoformat(),
                    'message': f'測試爬取序號 1137 - {permit_data.get("permitNumber", "")}',
                    'status': 'completed'
                }
                
                logs_data = storage.get_json_object('data/crawl-logs.json') or {'logs': []}
                logs_data['logs'].insert(0, log_entry)
                logs_data['logs'] = logs_data['logs'][:100]
                logs_data['lastUpdate'] = datetime.now().isoformat()
                storage.put_json_object('data/crawl-logs.json', logs_data)
                
                return permit_data
            else:
                logger.error("解析失敗或無資料")
                return None
                
        else:
            logger.error(f"wget 失敗: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"爬取錯誤: {str(e)}")
        return None
    finally:
        # 清理暫存檔案
        try:
            import os
            os.unlink(temp_file)
        except:
            pass

def parse_permit_data(html_content, index_key):
    """解析建照資料"""
    try:
        import re
        
        # 檢查是否包含遺失個資
        if '○○○代表遺失個資' in html_content:
            return "NO_DATA"
        
        permit_data = {
            'indexKey': index_key,
            'permitYear': int(index_key[0:3]),
            'permitType': int(index_key[3:4]),
            'sequenceNumber': int(index_key[4:9]),
            'versionNumber': int(index_key[9:11]),
            'crawledAt': datetime.now().isoformat()
        }
        
        # 建照號碼
        match = re.search(r'建造執照號碼[：:]\s*([^\s<]+)', html_content)
        if not match:
            match = re.search(r'建築執照號碼[：:]\s*([^\s<]+)', html_content)
        if match:
            permit_data['permitNumber'] = match.group(1).strip()
        else:
            return None
        
        # 申請人
        match = re.search(r'起造人[^>]*姓名[^>]*>([^<]+)', html_content)
        if match:
            permit_data['applicantName'] = match.group(1).strip()
        
        # 地址
        match = re.search(r'地號[^>]*>([^<]+)', html_content)
        if not match:
            match = re.search(r'地址[^>]*>([^<]+)', html_content)
        if match:
            permit_data['siteAddress'] = match.group(1).strip()
        
        # 行政區
        if permit_data.get('siteAddress'):
            district_match = re.search(r'臺中市([^區]+區)', permit_data['siteAddress'])
            if district_match:
                permit_data['district'] = district_match.group(1)
        
        # 樓層資訊
        match = re.search(r'地上.*?層.*?棟.*?戶|地上.*?層.*?幢.*?棟.*?戶', html_content)
        if match:
            permit_data['floorInfo'] = match.group(0)
            
            floor_match = re.search(r'地上(\d+)層', match.group(0))
            if floor_match:
                permit_data['floorsAbove'] = int(floor_match.group(1))
                permit_data['floors'] = int(floor_match.group(1))
            
            building_match = re.search(r'(\d+)棟', match.group(0))
            if building_match:
                permit_data['buildingCount'] = int(building_match.group(1))
                permit_data['buildings'] = int(building_match.group(1))
            
            unit_match = re.search(r'(\d+)戶', match.group(0))
            if unit_match:
                permit_data['unitCount'] = int(unit_match.group(1))
                permit_data['units'] = int(unit_match.group(1))
        
        # 總樓地板面積
        match = re.search(r'總樓地板面積.*?<span[^>]*>([0-9.,]+)', html_content)
        if match:
            permit_data['totalFloorArea'] = float(match.group(1).replace(',', ''))
        
        # 發照日期
        match = re.search(r'發照日期.*?(\d{3})/(\d{2})/(\d{2})', html_content)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            permit_data['issueDate'] = f"{year + 1911}-{month:02d}-{day:02d}"
            permit_data['issueDateROC'] = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
        
        return permit_data
        
    except Exception as e:
        logger.error(f'解析錯誤: {str(e)}')
        return None

if __name__ == "__main__":
    result = fetch_permit_1137()
    if result:
        print(f"\n成功爬取建照資料:")
        print(f"建照號碼: {result.get('permitNumber', '')}")
        print(f"申請人: {result.get('applicantName', '')}")
        print(f"地址: {result.get('siteAddress', '')}")
        print(f"樓層: {result.get('floorInfo', '')}")
    else:
        print("\n爬取失敗")