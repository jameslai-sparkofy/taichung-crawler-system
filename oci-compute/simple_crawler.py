#!/usr/bin/env python3
"""
簡單爬蟲 - 使用重新整理技巧
"""
import json
import logging
import subprocess
import time
from datetime import datetime
import os

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

def fetch_permit_simple(index_key):
    """簡單抓取 - 點上去，等一秒，重新整理"""
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    logger.info(f"開始爬取建照 {index_key}")
    
    try:
        temp_file = f"/tmp/permit_{index_key}.html"
        
        # 清理舊檔案
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        
        # 第一次請求 - 點上去
        cmd1 = [
            'wget', '-q', '-O', temp_file,
            '--timeout=30',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ]
        
        result1 = subprocess.run(cmd1, capture_output=True, text=True)
        logger.info(f"第一次請求完成: {result1.returncode}")
        
        # 等一秒
        time.sleep(1)
        
        # 檢查是否有資料
        if os.path.exists(temp_file):
            with open(temp_file, 'r', encoding='big5', errors='ignore') as f:
                content = f.read()
            
            # 如果沒有建照資料，重新整理
            if '建築執照存根查詢系統' in content and 'INDEX_KEY' not in content:
                logger.info("沒有資料，重新整理...")
                
                # 重新整理 - 再請求一次
                cmd2 = [
                    'wget', '-q', '-O', temp_file,
                    '--timeout=30',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    url
                ]
                
                result2 = subprocess.run(cmd2, capture_output=True, text=True)
                logger.info(f"重新整理完成: {result2.returncode}")
                
                if result2.returncode == 0:
                    with open(temp_file, 'r', encoding='big5', errors='ignore') as f:
                        content = f.read()
            
            # 清理檔案
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            
            return content
        else:
            logger.error("檔案不存在")
            return None
            
    except Exception as e:
        logger.error(f"抓取錯誤 {index_key}: {str(e)}")
        return None

def parse_permit_data(html_content, index_key):
    """解析建照資料"""
    try:
        import re
        
        # 檢查是否包含遺失個資
        if '○○○代表遺失個資' in html_content:
            return "NO_DATA"
        
        # 檢查是否是查詢首頁
        if '建築執照存根查詢系統' in html_content and 'queryInfoAction.do' in html_content and '建照號碼' not in html_content:
            logger.warning("還是查詢首頁")
            return None
        
        permit_data = {
            'indexKey': index_key,
            'permitYear': int(index_key[0:3]),
            'permitType': int(index_key[3:4]),
            'sequenceNumber': int(index_key[4:9]),
            'versionNumber': int(index_key[9:11]),
            'crawledAt': datetime.now().isoformat()
        }
        
        # 建照號碼 - 多種模式
        patterns = [
            r'建造執照號碼[：:]\s*([^\s<]+)',
            r'建築執照號碼[：:]\s*([^\s<]+)',
            r'(114中都建字第\d+號)',
            r'(113中都建字第\d+號)',
            r'(112中都建字第\d+號)'
        ]
        
        permit_number = None
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                permit_number = match.group(1).strip()
                break
        
        if permit_number:
            permit_data['permitNumber'] = permit_number
            logger.info(f"找到建照號碼: {permit_number}")
        else:
            logger.warning("未找到建照號碼")
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
        
        return permit_data
        
    except Exception as e:
        logger.error(f'解析錯誤: {str(e)}')
        return None

def upload_to_oci(permit_data):
    """上傳到 OCI"""
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        client = ObjectStorageClient(config={}, signer=signer)
        
        # 讀取現有資料
        response = client.get_object(NAMESPACE, BUCKET_NAME, 'data/permits.json')
        data = json.loads(response.data.content.decode('utf-8'))
        
        # 檢查是否已存在
        existing_keys = {p.get('indexKey') for p in data.get('permits', []) if isinstance(p, dict)}
        
        if permit_data['indexKey'] not in existing_keys:
            # 新增資料
            data['permits'].append(permit_data)
            
            # 重新排序
            data['permits'].sort(key=lambda x: x.get('indexKey', ''))
            
            # 更新統計
            data['totalCount'] = len(data['permits'])
            year_counts = {'114': 0, '113': 0, '112': 0}
            for permit in data['permits']:
                year = str(permit.get('permitYear', 0))
                if year in year_counts:
                    year_counts[year] += 1
            data['yearCounts'] = year_counts
            
            # 上傳回 OCI
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            client.put_object(
                NAMESPACE,
                BUCKET_NAME,
                'data/permits.json',
                json_data.encode('utf-8')
            )
            
            logger.info("✅ 成功上傳新資料到 OCI")
            return True
        else:
            logger.info("資料已存在，跳過上傳")
            return True
        
    except Exception as e:
        logger.error(f"上傳失敗: {str(e)}")
        return False

def test_crawl_1138():
    """測試爬取序號 1138"""
    index_key = "11410113800"
    
    # 爬取資料
    html_content = fetch_permit_simple(index_key)
    if not html_content:
        logger.error("無法取得 HTML 內容")
        return None
    
    # 解析資料
    result = parse_permit_data(html_content, index_key)
    
    if result and result != "NO_DATA":
        logger.info("✅ 成功爬取並解析資料")
        return result
    else:
        logger.error("❌ 解析失敗")
        return None

if __name__ == "__main__":
    result = test_crawl_1138()
    if result:
        print(f"\n✅ 成功爬取建照資料:")
        print(f"建照號碼: {result.get('permitNumber', '')}")
        print(f"申請人: {result.get('applicantName', '')}")
        print(f"地址: {result.get('siteAddress', '')}")
        
        # 上傳到 OCI
        if upload_to_oci(result):
            print("✅ 已上傳到 OCI")
        else:
            print("❌ 上傳失敗")
    else:
        print("❌ 爬取失敗")