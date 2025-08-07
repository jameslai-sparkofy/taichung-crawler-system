#!/usr/bin/env python3
"""
修正版爬蟲 - 解決 session 問題
"""
import json
import logging
import subprocess
import time
from datetime import datetime
import os
from pathlib import Path

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

def fetch_permit_with_session(index_key):
    """使用 session 抓取建照資料"""
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    logger.info(f"開始爬取建照 {index_key}")
    
    try:
        # 建立暫存檔案
        temp_file = f"/tmp/permit_{index_key}.html"
        cookie_file = f"/tmp/cookies_{index_key}.txt"
        
        # 清理舊檔案
        for f in [temp_file, cookie_file]:
            if os.path.exists(f):
                os.unlink(f)
        
        # 第一次請求 - 建立 session
        cmd1 = [
            'wget', '-q', '-O', '/tmp/first.html',
            '--save-cookies', cookie_file,
            '--timeout=30',
            '--tries=2',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do'
        ]
        
        result1 = subprocess.run(cmd1, capture_output=True, text=True)
        logger.info(f"第一次請求狀態: {result1.returncode}")
        
        # 等待
        time.sleep(1)
        
        # 第二次請求 - 使用 cookies
        cmd2 = [
            'wget', '-q', '-O', temp_file,
            '--load-cookies', cookie_file,
            '--timeout=30',
            '--tries=2',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ]
        
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        logger.info(f"第二次請求狀態: {result2.returncode}")
        
        if result2.returncode == 0 and os.path.exists(temp_file):
            # 嘗試用 BIG5 讀取
            with open(temp_file, 'r', encoding='big5', errors='ignore') as f:
                content = f.read()
            
            # 檢查是否成功取得建照資料
            if '建築執照存根查詢系統' in content and 'queryInfoAction.do' in content:
                logger.warning("取得的是查詢首頁，嘗試第三次請求")
                
                # 等待更久
                time.sleep(2)
                
                # 第三次請求
                cmd3 = [
                    'wget', '-q', '-O', temp_file,
                    '--load-cookies', cookie_file,
                    '--referer', 'https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do',
                    '--timeout=30',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    url
                ]
                
                result3 = subprocess.run(cmd3, capture_output=True, text=True)
                
                if result3.returncode == 0:
                    with open(temp_file, 'r', encoding='big5', errors='ignore') as f:
                        content = f.read()
            
            # 清理檔案
            for f in [temp_file, cookie_file, '/tmp/first.html']:
                if os.path.exists(f):
                    os.unlink(f)
            
            return content
        else:
            logger.error(f"wget 失敗: {result2.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"抓取錯誤 {index_key}: {str(e)}")
        return None

def parse_permit_data(html_content, index_key):
    """解析建照資料"""
    try:
        import re
        
        # 檢查是否是查詢首頁
        if '建築執照存根查詢系統' in html_content and 'queryInfoAction.do' in html_content:
            logger.warning("這是查詢首頁，不是建照資料")
            return None
        
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
            logger.info(f"找到建照號碼: {permit_data['permitNumber']}")
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

def test_crawl_1138():
    """測試爬取序號 1138"""
    index_key = "11410113800"
    
    # 爬取資料
    html_content = fetch_permit_with_session(index_key)
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

def upload_to_oci(permit_data):
    """上傳到 OCI"""
    try:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        client = ObjectStorageClient(config={}, signer=signer)
        
        # 讀取現有資料
        response = client.get_object(NAMESPACE, BUCKET_NAME, 'data/permits.json')
        data = json.loads(response.data.content.decode('utf-8'))
        
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
        
        logger.info("✅ 成功上傳到 OCI")
        return True
        
    except Exception as e:
        logger.error(f"上傳失敗: {str(e)}")
        return False

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