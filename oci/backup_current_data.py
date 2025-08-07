#!/usr/bin/env python3
"""
備份當前所有資料
"""

import json
import requests
import subprocess
from datetime import datetime

def backup_current_data():
    """備份當前資料到本地和OCI"""
    
    # 下載現有資料
    print("📥 下載現有資料...")
    url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
    response = requests.get(url)
    data = response.json()
    
    permits = data['permits']
    print(f"現有資料: {len(permits)} 筆")
    
    # 創建備份檔名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.json"
    
    # 保存到本地
    print(f"\n💾 保存本地備份: {backup_filename}")
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 上傳到OCI backups目錄
    print(f"\n📤 上傳到OCI backups/...")
    namespace = "nrsdi1rz5vl8"
    bucket_name = "taichung-building-permits"
    
    cmd = [
        "oci", "os", "object", "put",
        "--namespace", namespace,
        "--bucket-name", bucket_name,
        "--name", f"backups/{backup_filename}",
        "--file", backup_filename,
        "--content-type", "application/json",
        "--force"
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print(f"✅ 備份成功上傳到OCI")
    else:
        print(f"❌ 上傳失敗: {result.stderr.decode()}")
    
    # 統計各年份
    from collections import defaultdict
    year_stats = defaultdict(int)
    for permit in permits:
        year = permit.get('permitYear')
        year_stats[year] += 1
    
    print("\n📊 備份資料統計:")
    for year in sorted(year_stats.keys(), reverse=True):
        print(f"  {year}年: {year_stats[year]} 筆")
    
    return backup_filename

if __name__ == "__main__":
    print("🛡️ 開始備份當前資料...")
    print("=" * 50)
    
    try:
        filename = backup_current_data()
        print(f"\n✅ 備份完成: {filename}")
    except Exception as e:
        print(f"\n❌ 備份失敗: {e}")