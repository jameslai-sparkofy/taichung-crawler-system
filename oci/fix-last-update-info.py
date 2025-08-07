#!/usr/bin/env python3
"""
修正最後更新資訊 - 設定正確的起始位置
"""

import json
import subprocess
from datetime import datetime

def main():
    print("🔧 修正最後更新資訊...")
    
    # 設定正確的最後更新資訊
    # 114年目前發到1098號，所以下次從1099開始
    last_update_info = {
        "last_successful_id": "11410109800",  # 114年最後一筆
        "last_update_time": datetime.now().isoformat(),
        "year": 114,  # 當前年份114年
        "sequence": 1098,  # 最後序號
        "note": "114年當前發照進度，每日自動從下一號開始爬取"
    }
    
    print(f"📍 設定起始位置:")
    print(f"   最後成功ID: {last_update_info['last_successful_id']}")
    print(f"   下次開始: 11410109900")
    print(f"   當前年份: 114年")
    
    # 儲存到檔案
    with open('/tmp/last-update-info.json', 'w', encoding='utf-8') as f:
        json.dump(last_update_info, f, ensure_ascii=False, indent=2)
    
    # 上傳到OCI
    cmd = ["oci", "os", "object", "put",
           "--namespace", "nrsdi1rz5vl8",
           "--bucket-name", "taichung-building-permits",
           "--name", "logs/last-update-info.json",
           "--file", "/tmp/last-update-info.json",
           "--content-type", "application/json",
           "--force"]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print("✅ 最後更新資訊已修正")
        print("")
        print("🕒 明天凌晨3:00自動爬蟲將會:")
        print("   1. 從 11410109900 開始爬取114年新建照")
        print("   2. 遇到空白（還沒發照）就停止")
        print("   3. 記錄詳細執行過程")
    else:
        print("❌ 上傳失敗")

if __name__ == "__main__":
    main()