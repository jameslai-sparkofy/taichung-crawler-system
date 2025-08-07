#!/usr/bin/env python3
"""
刪除114年序號1098並準備CRON測試
"""

import json
import requests
import subprocess
from datetime import datetime

def delete_1098():
    """刪除114年序號1098"""
    
    # 下載現有資料
    print("📥 下載現有資料...")
    url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
    response = requests.get(url)
    data = response.json()
    
    original_count = len(data['permits'])
    print(f"原始資料: {original_count} 筆")
    
    # 找出並刪除114年序號1098
    new_permits = []
    deleted_count = 0
    
    for permit in data['permits']:
        if permit.get('permitYear') == 114 and permit.get('sequenceNumber') == 1098:
            deleted_count += 1
            print(f"🗑️ 刪除: {permit.get('permitNumber')} - {permit.get('applicantName', '無申請人')}")
        else:
            new_permits.append(permit)
    
    print(f"\n刪除了 {deleted_count} 筆114年序號1098的資料")
    
    # 統計各年份
    from collections import defaultdict
    year_stats = defaultdict(int)
    for permit in new_permits:
        year = permit.get('permitYear')
        year_stats[year] += 1
    
    # 準備上傳資料
    data['permits'] = new_permits
    data['totalCount'] = len(new_permits)
    data['yearCounts'] = dict(year_stats)
    data['lastUpdate'] = datetime.now().isoformat()
    
    # 保存到臨時檔案
    temp_file = "/tmp/permits_without_1098.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 上傳到OCI
    print("\n📤 上傳更新後的資料...")
    namespace = "nrsdi1rz5vl8"
    bucket_name = "taichung-building-permits"
    
    for dest_path in ["permits.json", "data/permits.json"]:
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", dest_path,
            "--file", temp_file,
            "--content-type", "application/json",
            "--force"
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"✅ 上傳成功: {dest_path}")
        else:
            print(f"❌ 上傳失敗: {dest_path}")
    
    print(f"\n📊 更新後統計:")
    print(f"總資料: {len(new_permits)} 筆")
    for year in sorted(year_stats.keys(), reverse=True):
        print(f"  {year}年: {year_stats[year]} 筆")

if __name__ == "__main__":
    print("🧹 刪除114年序號1098...")
    print("=" * 50)
    
    try:
        delete_1098()
        print("\n✅ 完成!")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")