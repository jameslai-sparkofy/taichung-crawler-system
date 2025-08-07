#!/usr/bin/env python3
"""
備份現有資料並檢查所有年份的空白欄位
"""

import json
import requests
import oci
from datetime import datetime
from collections import defaultdict

def backup_current_data():
    """備份當前資料到GitHub"""
    try:
        # 初始化OCI客戶端
        client = oci.object_storage.ObjectStorageClient({})
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        print("📥 下載當前資料...")
        # 下載現有資料
        obj = client.get_object(namespace, bucket_name, "data/permits.json")
        current_data = json.loads(obj.data.content.decode('utf-8'))
        
        # 創建備份檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"permits_backup_{timestamp}.json"
        
        print(f"💾 備份資料到: backups/{backup_filename}")
        
        # 上傳備份
        client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=f"backups/{backup_filename}",
            put_object_body=json.dumps(current_data, ensure_ascii=False, indent=2).encode('utf-8'),
            content_type="application/json"
        )
        
        print(f"✅ 備份完成: {len(current_data['permits'])} 筆資料")
        return current_data
        
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return None

def check_all_years_empty_fields(data):
    """檢查所有年份的空白欄位"""
    
    permits = data['permits']
    
    # 按年份分組
    by_year = defaultdict(list)
    for permit in permits:
        year = permit.get('permitYear', 0)
        by_year[year].append(permit)
    
    # 必要欄位
    required_fields = [
        'floors', 'buildings', 'units', 'totalFloorArea', 'issueDate',
        'applicantName', 'designerName', 'supervisorName', 'contractorName',
        'siteAddress', 'siteArea'
    ]
    
    print("\n📊 所有年份空白欄位檢查:")
    print("=" * 80)
    
    summary = {}
    
    for year in sorted(by_year.keys()):
        year_permits = by_year[year]
        print(f"\n🗓️ {year}年 - 總計 {len(year_permits)} 筆")
        print("-" * 60)
        
        # 統計空白欄位
        empty_stats = defaultdict(int)
        empty_records = defaultdict(list)
        
        for permit in year_permits:
            permit_number = permit.get('permitNumber', 'Unknown')
            
            for field in required_fields:
                value = permit.get(field)
                if value is None or value == "" or value == 0:
                    empty_stats[field] += 1
                    empty_records[field].append(permit_number)
        
        # 顯示統計
        total_records = len(year_permits)
        year_summary = {}
        
        for field in required_fields:
            count = empty_stats[field]
            percentage = (count / total_records) * 100 if total_records > 0 else 0
            year_summary[field] = {'count': count, 'percentage': percentage}
            print(f"  {field:20} | {count:4d}筆 ({percentage:5.1f}%)")
        
        # 計算整體完整度
        total_fields = total_records * len(required_fields)
        total_empty = sum(empty_stats.values())
        completeness = ((total_fields - total_empty) / total_fields) * 100 if total_fields > 0 else 0
        
        print(f"\n  📈 整體完整度: {completeness:.1f}%")
        
        # 檢查完全空白的記錄
        completely_empty = []
        for permit in year_permits:
            empty_count = sum(1 for field in required_fields 
                             if permit.get(field) is None or permit.get(field) == "" or permit.get(field) == 0)
            if empty_count >= len(required_fields) - 2:  # 除了建照號碼和年份外都空白
                completely_empty.append(permit.get('permitNumber', 'Unknown'))
        
        if completely_empty:
            print(f"  💀 幾乎完全空白: {len(completely_empty)} 筆")
            if len(completely_empty) <= 5:
                print(f"     範例: {completely_empty}")
            else:
                print(f"     範例: {completely_empty[:5]} ...")
        
        summary[year] = {
            'total': total_records,
            'completeness': completeness,
            'completely_empty': len(completely_empty),
            'fields': year_summary
        }
    
    # 總結報告
    print("\n🏆 年份比較總結:")
    print("=" * 60)
    for year in sorted(summary.keys()):
        s = summary[year]
        print(f"{year}年: {s['total']:4d}筆 | 完整度{s['completeness']:5.1f}% | 空白{s['completely_empty']:3d}筆")
    
    # 找出需要重新爬取的年份
    print("\n🔧 建議重新爬取的年份:")
    print("-" * 40)
    
    for year in sorted(summary.keys()):
        s = summary[year]
        if s['completeness'] < 80 or s['completely_empty'] > 50:
            print(f"⚠️ {year}年: 完整度{s['completeness']:.1f}%, 空白{s['completely_empty']}筆 - 建議重新爬取")
        else:
            print(f"✅ {year}年: 完整度{s['completeness']:.1f}%, 空白{s['completely_empty']}筆 - 資料良好")
    
    return summary

def main():
    print("🛡️ 資料備份與全面檢查")
    print("=" * 50)
    
    # 1. 備份當前資料
    print("\n📦 步驟1: 備份當前資料")
    current_data = backup_current_data()
    
    if not current_data:
        print("❌ 無法備份資料，停止檢查")
        return
    
    # 2. 檢查所有年份
    print("\n🔍 步驟2: 檢查所有年份空白欄位")
    summary = check_all_years_empty_fields(current_data)
    
    print(f"\n✅ 檢查完成！當前總計: {len(current_data['permits'])} 筆資料")

if __name__ == "__main__":
    main()