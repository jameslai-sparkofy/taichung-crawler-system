#!/usr/bin/env python3
"""
分析114年缺失資料的分布和原因
"""

import json
import requests

def analyze_missing_data():
    """分析缺失資料的分布"""
    
    # 從OCI下載資料
    url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
    
    print("📥 下載資料...")
    response = requests.get(url)
    data = response.json()
    
    # 篩選114年資料
    permits_114 = [p for p in data['permits'] if p.get('permitYear') == 114]
    
    print(f"🔍 114年總計: {len(permits_114)} 筆資料")
    
    # 分析序號分布
    sequences = []
    for permit in permits_114:
        seq = permit.get('sequenceNumber')
        if seq:
            sequences.append(seq)
    
    sequences.sort()
    print(f"\n📊 序號範圍: {min(sequences)} - {max(sequences)}")
    
    # 檢查缺失的序號段
    missing_ranges = []
    for i in range(1, max(sequences) + 1):
        if i not in sequences:
            missing_ranges.append(i)
    
    print(f"📊 爬取序號: {len(sequences)} 筆")
    print(f"📊 缺失序號: {len(missing_ranges)} 筆")
    
    # 分析空白資料的序號分布
    empty_records = []
    partial_records = []
    complete_records = []
    
    required_fields = ['floors', 'buildings', 'units', 'totalFloorArea', 'issueDate']
    
    for permit in permits_114:
        seq = permit.get('sequenceNumber', 0)
        empty_count = sum(1 for field in required_fields 
                         if permit.get(field) is None or permit.get(field) == "" or permit.get(field) == 0)
        
        if empty_count >= 4:  # 幾乎全空
            empty_records.append(seq)
        elif empty_count > 0:  # 部分空白
            partial_records.append(seq)
        else:  # 完整資料
            complete_records.append(seq)
    
    print(f"\n📋 資料品質分析:")
    print(f"   完整資料: {len(complete_records)} 筆")
    print(f"   部分缺失: {len(partial_records)} 筆") 
    print(f"   幾乎空白: {len(empty_records)} 筆")
    
    # 檢查序號分布模式
    empty_records.sort()
    complete_records.sort()
    
    if empty_records:
        print(f"\n🔴 空白資料序號範圍:")
        print(f"   最小: {min(empty_records)}")
        print(f"   最大: {max(empty_records)}")
        print(f"   範例: {empty_records[:10]}")
    
    if complete_records:
        print(f"\n✅ 完整資料序號範圍:")
        print(f"   最小: {min(complete_records)}")
        print(f"   最大: {max(complete_records)}")
        print(f"   範例: {complete_records[:10]}")
    
    # 找出需要重新爬取的範圍
    if empty_records and complete_records:
        gap_start = min(empty_records)
        gap_end = max(empty_records)
        
        print(f"\n🔧 建議重新爬取範圍:")
        print(f"   序號 {gap_start} - {gap_end} ({gap_end - gap_start + 1} 筆)")
        
        # 生成重新爬取指令
        print(f"\n💻 重新爬取指令:")
        print(f"nohup python3 simple-crawl.py 114 {gap_start} {gap_end} > recrawl_114_{gap_start}_{gap_end}.log 2>&1 &")

if __name__ == "__main__":
    print("🔍 分析114年缺失資料")
    print("=" * 50)
    
    try:
        analyze_missing_data()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")