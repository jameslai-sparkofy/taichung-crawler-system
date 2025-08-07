#!/usr/bin/env python3
"""
更新執行記錄 - 記錄最新抓取的5筆資料
"""

import json
import subprocess
import re
from datetime import datetime

def get_latest_permits():
    """取得最新的建照資料"""
    try:
        cmd = ["oci", "os", "object", "get",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "permits.json",
               "--file", "/tmp/permits.json"]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            with open('/tmp/permits.json', 'r', encoding='utf-8') as f:
                permits = json.load(f)
            
            # 按 indexKey 排序，取最新的5筆
            if permits:
                permits_sorted = sorted(permits, key=lambda x: x.get('indexKey', ''), reverse=True)
                return permits_sorted[:5]
    except:
        pass
    return []

def get_current_progress():
    """從日誌檔案分析當前進度"""
    progress = {
        "113": {"current": "未知", "total": 2201},
        "112": {"current": "未知", "total": 2039}
    }
    
    try:
        # 分析113年進度
        with open('/tmp/crawler-logs/crawler-113-20250727-160219.log', 'r', encoding='utf-8') as f:
            log_113 = f.read()
        
        # 找最後一個爬取序號
        matches_113 = re.findall(r'爬取 (113\d{8})', log_113)
        if matches_113:
            last_seq = matches_113[-1]
            seq_num = int(last_seq[3:8])  # 提取序號
            progress["113"]["current"] = f"{seq_num}/2201 ({seq_num/2201*100:.1f}%)"
    except:
        pass
    
    try:
        # 分析112年進度
        with open('/tmp/crawler-logs/crawler-112-20250727-160429.log', 'r', encoding='utf-8') as f:
            log_112 = f.read()
        
        # 找最後一個爬取序號
        matches_112 = re.findall(r'爬取 (112\d{8})', log_112)
        if matches_112:
            last_seq = matches_112[-1]
            seq_num = int(last_seq[3:8])
            progress["112"]["current"] = f"{seq_num}/2039 ({seq_num/2039*100:.1f}%)"
    except:
        pass
    
    return progress

def main():
    print("📊 更新執行記錄...")
    
    # 取得最新抓取的資料
    latest_permits = get_latest_permits()
    print(f"📄 找到最新 {len(latest_permits)} 筆資料")
    
    # 取得當前進度
    progress = get_current_progress()
    
    # 建立執行記錄
    execution_record = {
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "progress": progress,
        "latest_permits": [
            {
                "indexKey": permit.get('indexKey', ''),
                "permitNumber": permit.get('permitNumber', ''),
                "applicant": permit.get('applicant', '')[:20] + "..." if len(permit.get('applicant', '')) > 20 else permit.get('applicant', ''),
                "crawlTime": permit.get('crawlTime', '')
            }
            for permit in latest_permits
        ],
        "total_permits": len(latest_permits) if latest_permits else 0
    }
    
    print("📋 最新抓取的5筆資料:")
    for i, permit in enumerate(latest_permits, 1):
        print(f"  {i}. {permit.get('indexKey', '')} - {permit.get('permitNumber', '')} - {permit.get('applicant', '')[:30]}")
    
    print(f"📈 爬蟲進度:")
    print(f"  113年: {progress['113']['current']}")
    print(f"  112年: {progress['112']['current']}")
    
    # 儲存記錄
    with open('/tmp/latest-execution-record.json', 'w', encoding='utf-8') as f:
        json.dump(execution_record, f, ensure_ascii=False, indent=2)
    
    # 上傳到OCI
    cmd = ["oci", "os", "object", "put",
           "--namespace", "nrsdi1rz5vl8",
           "--bucket-name", "taichung-building-permits",
           "--name", "logs/latest-execution-record.json",
           "--file", "/tmp/latest-execution-record.json",
           "--content-type", "application/json",
           "--force"]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print("✅ 執行記錄已更新")
    else:
        print("❌ 上傳失敗")

if __name__ == "__main__":
    main()