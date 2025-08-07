#!/usr/bin/env python3
"""
檢查114年資料中的空白欄位
"""

import json
import requests
from collections import defaultdict

def check_empty_fields():
    """檢查114年資料的空白欄位"""
    
    # 從OCI下載資料
    url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
    
    print("📥 下載資料...")
    response = requests.get(url)
    data = response.json()
    
    # 篩選114年資料
    permits_114 = [p for p in data['permits'] if p.get('permitYear') == 114]
    
    print(f"🔍 114年總計: {len(permits_114)} 筆資料")
    
    # 檢查必要欄位
    required_fields = [
        'floors', 'buildings', 'units', 'totalFloorArea', 'issueDate',
        'applicantName', 'designerName', 'supervisorName', 'contractorName',
        'siteAddress', 'siteArea'
    ]
    
    # 統計空白欄位
    empty_stats = defaultdict(int)
    empty_records = defaultdict(list)
    
    for permit in permits_114:
        permit_number = permit.get('permitNumber', 'Unknown')
        
        for field in required_fields:
            value = permit.get(field)
            if value is None or value == "" or value == 0:
                empty_stats[field] += 1
                empty_records[field].append(permit_number)
    
    # 顯示統計結果
    print("\n📊 空白欄位統計:")
    print("=" * 60)
    
    for field in required_fields:
        count = empty_stats[field]
        percentage = (count / len(permits_114)) * 100
        print(f"{field:20} | {count:4d}筆 ({percentage:5.1f}%)")
    
    # 顯示最嚴重的空白欄位
    print("\n⚠️ 空白欄位最多的前5個:")
    sorted_fields = sorted(empty_stats.items(), key=lambda x: x[1], reverse=True)
    
    for field, count in sorted_fields[:5]:
        print(f"\n🔍 {field} - 共{count}筆空白:")
        # 顯示前10個範例
        examples = empty_records[field][:10]
        for example in examples:
            print(f"   - {example}")
        if len(empty_records[field]) > 10:
            print(f"   ... 還有 {len(empty_records[field]) - 10} 筆")
    
    # 檢查完全空白的記錄
    completely_empty = []
    for permit in permits_114:
        empty_count = sum(1 for field in required_fields 
                         if permit.get(field) is None or permit.get(field) == "" or permit.get(field) == 0)
        if empty_count >= len(required_fields) - 2:  # 除了建照號碼和年份外都空白
            completely_empty.append(permit.get('permitNumber', 'Unknown'))
    
    if completely_empty:
        print(f"\n💀 幾乎完全空白的記錄 ({len(completely_empty)}筆):")
        for record in completely_empty[:20]:
            print(f"   - {record}")
        if len(completely_empty) > 20:
            print(f"   ... 還有 {len(completely_empty) - 20} 筆")
    
    return empty_stats, permits_114

if __name__ == "__main__":
    print("🔍 檢查114年資料空白欄位")
    print("=" * 50)
    
    try:
        empty_stats, permits_114 = check_empty_fields()
        
        # 計算整體完整度
        total_fields = len(permits_114) * 11  # 11個必要欄位
        total_empty = sum(empty_stats.values())
        completeness = ((total_fields - total_empty) / total_fields) * 100
        
        print(f"\n📈 整體資料完整度: {completeness:.1f}%")
        print(f"   - 總欄位數: {total_fields:,}")
        print(f"   - 空白欄位: {total_empty:,}")
        print(f"   - 有效欄位: {total_fields - total_empty:,}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")