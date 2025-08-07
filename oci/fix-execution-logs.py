#!/usr/bin/env python3
"""
修正執行記錄 - 從爬蟲日誌重建執行歷史
"""

import json
import subprocess
import re
from datetime import datetime

def main():
    print("🔧 修正執行記錄...")
    
    # 分析113年爬蟲進度
    try:
        # 讀取113年爬蟲日誌
        with open('/tmp/crawler-logs/crawler-113-20250727-160219.log', 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 提取關鍵資訊
        start_time = "2025-07-27T16:02:24"
        
        # 找出所有已儲存記錄
        saves = re.findall(r'✅ 已儲存 (\d+) 筆資料 - 各年份: {.*?113: (\d+)', log_content)
        
        if saves:
            last_save = saves[-1]
            total_count = int(last_save[0])
            year_113_count = int(last_save[1])
            
            # 找出最後成功的序號
            last_success = re.findall(r'爬取 (113\d{8})... ✅', log_content)
            last_id = last_success[-1] if last_success else "11310000100"
            
            # 建立執行記錄
            execution_log = {
                "timestamp": start_time,
                "end_time": datetime.now().isoformat(),
                "duration_seconds": 14000,  # 約4小時
                "new_permits_count": year_113_count,
                "last_successful_id": last_id,
                "status": "in_progress",
                "description": "113年建照大量爬取",
                "total_permits": total_count
            }
            
            print(f"📊 分析結果:")
            print(f"   總資料數: {total_count}")
            print(f"   113年資料: {year_113_count}")
            print(f"   最後ID: {last_id}")
            
            # 儲存執行記錄
            with open('/tmp/fixed-execution-log.json', 'w', encoding='utf-8') as f:
                json.dump([execution_log], f, ensure_ascii=False, indent=2)
            
            # 上傳到OCI
            cmd = ["oci", "os", "object", "put",
                   "--namespace", "nrsdi1rz5vl8",
                   "--bucket-name", "taichung-building-permits",
                   "--name", "logs/execution-history.json",
                   "--file", "/tmp/fixed-execution-log.json",
                   "--content-type", "application/json",
                   "--force"]
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                print("✅ 執行記錄已修正並上傳")
            else:
                print("❌ 上傳失敗")
        
        # 同時建立最後更新資訊
        last_update_info = {
            "last_successful_id": last_id,
            "last_update_time": datetime.now().isoformat(),
            "year": 113,
            "sequence": int(last_id[3:8]) if len(last_id) > 8 else 1800
        }
        
        with open('/tmp/last-update-info.json', 'w', encoding='utf-8') as f:
            json.dump(last_update_info, f, ensure_ascii=False, indent=2)
        
        cmd = ["oci", "os", "object", "put",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "logs/last-update-info.json",
               "--file", "/tmp/last-update-info.json",
               "--content-type", "application/json",
               "--force"]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print("✅ 最後更新資訊已儲存")
        else:
            print("❌ 儲存最後更新資訊失敗")
            
    except Exception as e:
        print(f"❌ 處理失敗: {e}")

if __name__ == "__main__":
    main()