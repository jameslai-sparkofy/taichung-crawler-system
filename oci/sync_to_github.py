#!/usr/bin/env python3
"""
同步備份資料到 GitHub 目錄
"""

import shutil
import os
import json
from datetime import datetime

def sync_to_github():
    """同步最新備份到 GitHub 目錄"""
    
    print("🔄 開始同步資料到 GitHub 目錄...")
    
    # 路徑設定
    backup_dir = "/mnt/c/claude code/建照爬蟲/backups"
    github_data_dir = "/mnt/c/claude code/建照爬蟲/github/data"
    
    # 確保目標目錄存在
    os.makedirs(github_data_dir, exist_ok=True)
    
    # 複製最新的 permits 資料
    latest_file = os.path.join(backup_dir, "latest.json")
    target_permits = os.path.join(github_data_dir, "permits.json")
    
    if os.path.exists(latest_file):
        print(f"📋 複製 {latest_file} → {target_permits}")
        shutil.copy2(latest_file, target_permits)
        
        # 讀取資料統計
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📊 資料統計:")
        print(f"   總計: {data['totalCount']} 筆")
        for year, count in sorted(data['yearCounts'].items(), key=lambda x: x[0], reverse=True):
            print(f"   {year}年: {count} 筆")
    else:
        print("❌ 找不到 latest.json 檔案")
        return False
    
    # 更新 crawl-logs.json
    logs_file = os.path.join(github_data_dir, "crawl-logs.json")
    
    # 讀取現有日誌
    if os.path.exists(logs_file):
        with open(logs_file, 'r', encoding='utf-8') as f:
            logs_data = json.load(f)
    else:
        logs_data = {"logs": []}
    
    # 新增此次同步記錄
    new_log = {
        "timestamp": datetime.now().isoformat(),
        "action": "sync_from_oci",
        "totalCount": data['totalCount'],
        "yearCounts": data['yearCounts'],
        "message": "從 OCI 備份同步資料"
    }
    
    logs_data['logs'].insert(0, new_log)
    
    # 只保留最近 100 筆日誌
    logs_data['logs'] = logs_data['logs'][:100]
    
    # 寫入日誌
    with open(logs_file, 'w', encoding='utf-8') as f:
        json.dump(logs_data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 已更新 crawl-logs.json")
    
    # 複製缺失清單 (如果存在)
    missing_file = os.path.join(backup_dir, "missing_114.txt")
    if os.path.exists(missing_file):
        target_missing = os.path.join(github_data_dir, "missing_114.txt")
        shutil.copy2(missing_file, target_missing)
        print(f"📋 已複製缺失清單")
    
    print("\n✅ 同步完成！")
    print(f"\n💡 下一步:")
    print(f"   1. cd '/mnt/c/claude code/建照爬蟲/github'")
    print(f"   2. git add data/")
    print(f"   3. git commit -m '更新建照資料 - {datetime.now().strftime('%Y%m%d_%H%M%S')}'")
    print(f"   4. git push")
    
    return True

if __name__ == "__main__":
    sync_to_github()