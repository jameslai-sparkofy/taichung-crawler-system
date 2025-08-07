#!/usr/bin/env python3
"""
清理建照資料 - 移除無效記錄
"""

import json
import subprocess
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_valid_permit(permit):
    """檢查建照記錄是否有效"""
    # 檢查起造人
    applicant = permit.get('applicantName', '')
    if not applicant or applicant in ['1', '：', '-', '']:
        return False
    
    # 檢查建照號碼
    permit_number = permit.get('permitNumber', '')
    if not permit_number or permit_number in ['1', '：', '-', '']:
        return False
    
    # 檢查地址
    address = permit.get('siteAddress', '')
    if not address or address in ['1', '：', '-', '']:
        return False
    
    # 檢查是否包含有效的建照號碼格式
    if '中' not in permit_number or '建字第' not in permit_number:
        return False
    
    return True

def clean_permits_data():
    """清理建照資料"""
    namespace = "nrsdi1rz5vl8"
    bucket_name = "taichung-building-permits"
    
    logger.info("🧹 開始清理建照資料...")
    
    # 下載現有資料
    try:
        cmd = [
            "oci", "os", "object", "get",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/permits.json",
            "--file", "/tmp/permits_to_clean.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"下載資料失敗: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"下載資料失敗: {e}")
        return False
    
    # 讀取並清理資料
    try:
        with open('/tmp/permits_to_clean.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_permits = data.get('permits', [])
        original_count = len(original_permits)
        
        logger.info(f"📊 原始資料數量: {original_count}")
        
        # 過濾有效資料
        valid_permits = []
        invalid_count = 0
        
        for permit in original_permits:
            if is_valid_permit(permit):
                valid_permits.append(permit)
            else:
                invalid_count += 1
                logger.debug(f"移除無效記錄: {permit.get('indexKey')} - {permit.get('applicantName')}")
        
        logger.info(f"✅ 有效資料數量: {len(valid_permits)}")
        logger.info(f"❌ 移除無效資料: {invalid_count}")
        
        # 按建照號碼重新排序（新的在前）
        valid_permits.sort(key=lambda x: (
            -x.get('permitYear', 0),
            -x.get('sequenceNumber', 0)
        ))
        
        # 重新計算統計
        year_counts = {}
        for permit in valid_permits:
            year = permit['permitYear']
            if year not in year_counts:
                year_counts[year] = 0
            year_counts[year] += 1
        
        # 創建清理後的資料
        cleaned_data = {
            "lastUpdate": datetime.now().isoformat(),
            "totalCount": len(valid_permits),
            "yearCounts": year_counts,
            "permits": valid_permits
        }
        
        # 儲存到臨時檔案
        with open('/tmp/permits_cleaned.json', 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        # 上傳清理後的資料
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/permits.json",
            "--file", "/tmp/permits_cleaned.json",
            "--content-type", "application/json",
            "--force"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ 已上傳清理後的資料到OCI")
            
            # 更新爬取記錄
            update_crawl_log(original_count, len(valid_permits), invalid_count)
            
            return True
        else:
            logger.error(f"上傳失敗: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"清理資料失敗: {e}")
        return False

def update_crawl_log(original_count, valid_count, removed_count):
    """更新爬取記錄"""
    try:
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        new_log = {
            "date": datetime.now().date().isoformat(),
            "startTime": datetime.now().isoformat(),
            "endTime": datetime.now().isoformat(),
            "totalCrawled": 0,
            "newRecords": 0,
            "errorRecords": 0,
            "status": "data_cleaned",
            "cleaningStats": {
                "originalCount": original_count,
                "validCount": valid_count,
                "removedCount": removed_count
            },
            "message": f"資料清理完成，移除 {removed_count} 筆無效記錄"
        }
        
        # 載入現有記錄
        try:
            cmd = [
                "oci", "os", "object", "get",
                "--namespace", namespace,
                "--bucket-name", bucket_name,
                "--name", "data/crawl-logs.json",
                "--file", "-"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                log_data = json.loads(result.stdout)
                logs = log_data.get('logs', [])
            else:
                logs = []
                
        except:
            logs = []
        
        # 新增清理記錄
        logs.insert(0, new_log)
        logs = logs[:30]  # 只保留最近30天
        
        # 上傳記錄
        with open('/tmp/crawl-logs-updated.json', 'w', encoding='utf-8') as f:
            json.dump({"logs": logs}, f, ensure_ascii=False, indent=2)
        
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/crawl-logs.json",
            "--file", "/tmp/crawl-logs-updated.json",
            "--content-type", "application/json",
            "--force"
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        logger.info("✅ 已更新爬取記錄")
        
    except Exception as e:
        logger.error(f"更新記錄失敗: {e}")

if __name__ == "__main__":
    if clean_permits_data():
        logger.info("🎉 資料清理完成！")
        logger.info("監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html")
    else:
        logger.error("資料清理失敗")