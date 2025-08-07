#!/usr/bin/env python3
"""
清理重複的建照資料
保留欄位最完整的版本
"""

import json
import requests
import subprocess
from collections import defaultdict
from datetime import datetime

def clean_duplicates():
    """清理重複資料"""
    
    # 下載現有資料
    print("📥 下載現有資料...")
    url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
    response = requests.get(url)
    data = response.json()
    
    permits = data['permits']
    print(f"原始資料: {len(permits)} 筆")
    
    # 找出重複的資料
    duplicates = defaultdict(list)
    for permit in permits:
        # 使用年份+序號作為唯一鍵
        year = permit.get('permitYear')
        seq = permit.get('sequenceNumber')
        
        # 如果沒有這些欄位，嘗試從indexKey解析
        if not year or not seq:
            index_key = permit.get('indexKey', '')
            if len(index_key) >= 9:
                try:
                    year = int(index_key[:3])
                    seq = int(index_key[4:9])
                except:
                    pass
        
        key = f"{year}_{seq}"
        duplicates[key].append(permit)
    
    # 統計重複數量
    dup_count = sum(1 for v in duplicates.values() if len(v) > 1)
    print(f"\n發現 {dup_count} 組重複資料")
    
    # 處理重複資料 - 保留欄位最多且最新的
    cleaned_permits = []
    removed_count = 0
    
    for key, dup_list in duplicates.items():
        if len(dup_list) > 1:
            # 先按欄位數排序，再按爬取時間排序
            sorted_list = sorted(dup_list, 
                               key=lambda x: (len(x), x.get('crawledAt', '')), 
                               reverse=True)
            # 保留最好的版本
            best = sorted_list[0]
            cleaned_permits.append(best)
            removed_count += len(dup_list) - 1
        else:
            cleaned_permits.append(dup_list[0])
    
    print(f"\n清理後: {len(cleaned_permits)} 筆")
    print(f"刪除了 {removed_count} 筆重複資料")
    
    # 排序所有資料
    sorted_permits = sorted(cleaned_permits, key=lambda x: (
        -x.get('permitYear', 0),
        -x.get('sequenceNumber', 0)
    ))
    
    # 統計各年份數量
    year_counts = {}
    for permit in sorted_permits:
        year = permit.get('permitYear', 0)
        if year not in year_counts:
            year_counts[year] = 0
        year_counts[year] += 1
    
    # 準備上傳資料
    clean_data = {
        "lastUpdate": datetime.now().isoformat(),
        "totalCount": len(sorted_permits),
        "yearCounts": year_counts,
        "permits": sorted_permits
    }
    
    # 保存到臨時檔案
    temp_file = "/tmp/permits_cleaned.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
    
    print("\n📤 上傳清理後的資料...")
    
    # 上傳到OCI
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
    
    # 顯示統計
    print("\n📊 各年份資料統計:")
    for year in sorted(year_counts.keys(), reverse=True):
        print(f"  {year}年: {year_counts[year]} 筆")
    
    return len(cleaned_permits), removed_count

if __name__ == "__main__":
    print("🧹 開始清理重複資料...")
    print("=" * 50)
    
    try:
        total, removed = clean_duplicates()
        print("\n✅ 清理完成!")
        print(f"最終資料: {total} 筆")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")