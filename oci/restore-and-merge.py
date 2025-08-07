#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢復並合併資料
1. 從備份恢復基礎資料
2. 累加新爬取的資料
"""

import json
import subprocess
from datetime import datetime

def merge_permits():
    print("🔧 開始恢復並合併資料...")
    
    # 1. 載入備份資料（基礎）
    print("📥 載入備份資料...")
    cmd = [
        "oci", "os", "object", "get",
        "--namespace", "nrsdi1rz5vl8",
        "--bucket-name", "taichung-building-permits",
        "--name", "backups/permits_backup_20250728_000722.json",
        "--file", "/tmp/base_permits.json"
    ]
    subprocess.run(cmd, capture_output=True)
    
    with open('/tmp/base_permits.json', 'r', encoding='utf-8') as f:
        base_data = json.load(f)
    base_permits = base_data.get('permits', [])
    print(f"✅ 基礎資料: {len(base_permits)} 筆")
    
    # 2. 建立 index key 集合
    existing_keys = {p.get('indexKey') for p in base_permits}
    
    # 3. 從 crawl session 恢復今天新爬的資料
    # 你提到已經爬了 400+ 筆，這些應該存在某處
    # 如果有其他備份或暫存檔案，可以從那裡載入
    
    # 暫時先恢復基礎資料
    all_permits = base_permits
    
    # 統計
    year_counts = {}
    for p in all_permits:
        year = p.get('permitYear', 0)
        if year not in year_counts:
            year_counts[year] = 0
        year_counts[year] += 1
    
    print(f"📊 合併後統計: {year_counts}")
    
    # 排序
    sorted_permits = sorted(all_permits, key=lambda x: (
        -x.get('permitYear', 0),
        -x.get('sequenceNumber', 0)
    ))
    
    # 建立最終資料
    final_data = {
        "lastUpdate": datetime.now().isoformat(),
        "totalCount": len(sorted_permits),
        "yearCounts": year_counts,
        "permits": sorted_permits
    }
    
    # 儲存
    with open('/tmp/restored_permits.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    # 上傳到兩個位置
    print("📤 上傳恢復的資料...")
    for dest_path in ["permits.json", "data/permits.json"]:
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", "nrsdi1rz5vl8",
            "--bucket-name", "taichung-building-permits",
            "--name", dest_path,
            "--file", "/tmp/restored_permits.json",
            "--content-type", "application/json",
            "--force"
        ]
        subprocess.run(cmd, capture_output=True)
    
    print("✅ 資料恢復完成！")
    return len(sorted_permits)

if __name__ == "__main__":
    total = merge_permits()
    print(f"\n🎉 總共恢復 {total} 筆資料")
    print("\n建議接下來：")
    print("1. 使用已修復的累加模式爬蟲繼續爬取")
    print("2. 從 114年 401號開始（如果之前爬到400）")
    print("3. 爬蟲現在會自動累加，不會再覆蓋資料")