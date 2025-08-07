#!/usr/bin/env python3
"""
檢查所有年份的空白欄位 (不需要OCI模組)
"""

import json
import requests
from collections import defaultdict
from datetime import datetime

def check_all_years_empty_fields():
    """檢查所有年份的空白欄位"""
    
    # 從OCI下載資料
    url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
    
    print("📥 下載資料...")
    response = requests.get(url)
    data = response.json()
    
    permits = data['permits']
    print(f"📊 總計: {len(permits)} 筆資料")
    
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
    
    print(f"\n📊 發現 {len(by_year)} 個年份的資料")
    print("=" * 80)
    
    summary = {}
    
    for year in sorted(by_year.keys()):
        year_permits = by_year[year]
        print(f"\n🗓️ {year}年 - 總計 {len(year_permits)} 筆")
        print("-" * 60)
        
        # 統計空白欄位
        empty_stats = defaultdict(int)
        
        for permit in year_permits:
            for field in required_fields:
                value = permit.get(field)
                if value is None or value == "" or value == 0:
                    empty_stats[field] += 1
        
        # 顯示統計
        total_records = len(year_permits)
        year_summary = {}
        
        for field in required_fields:
            count = empty_stats[field]
            percentage = (count / total_records) * 100 if total_records > 0 else 0
            year_summary[field] = {'count': count, 'percentage': percentage}
            
            # 只顯示有問題的欄位 (>5%空白)
            if percentage > 5:
                print(f"  ⚠️ {field:20} | {count:4d}筆 ({percentage:5.1f}%)")
            elif count > 0:
                print(f"     {field:20} | {count:4d}筆 ({percentage:5.1f}%)")
        
        # 計算整體完整度
        total_fields = total_records * len(required_fields)
        total_empty = sum(empty_stats.values())
        completeness = ((total_fields - total_empty) / total_fields) * 100 if total_fields > 0 else 0
        
        print(f"\n  📈 整體完整度: {completeness:.1f}%")
        
        # 檢查完全空白的記錄
        completely_empty = 0
        for permit in year_permits:
            empty_count = sum(1 for field in required_fields 
                             if permit.get(field) is None or permit.get(field) == "" or permit.get(field) == 0)
            if empty_count >= len(required_fields) - 2:  # 除了建照號碼和年份外都空白
                completely_empty += 1
        
        if completely_empty > 0:
            print(f"  💀 幾乎完全空白: {completely_empty} 筆")
        
        summary[year] = {
            'total': total_records,
            'completeness': completeness,
            'completely_empty': completely_empty,
            'major_issues': sum(1 for field, stats in year_summary.items() if stats['percentage'] > 20)
        }
    
    # 總結報告
    print("\n🏆 年份比較總結:")
    print("=" * 70)
    print("年份   | 總筆數 | 完整度 | 空白筆數 | 主要問題欄位")
    print("-" * 70)
    
    for year in sorted(summary.keys()):
        s = summary[year]
        print(f"{year:4d}年 | {s['total']:6d} | {s['completeness']:6.1f}% | {s['completely_empty']:8d} | {s['major_issues']:10d}")
    
    # 找出需要重新爬取的年份
    print("\n🔧 建議操作:")
    print("-" * 50)
    
    need_recrawl = []
    for year in sorted(summary.keys()):
        s = summary[year]
        if s['completeness'] < 80:
            need_recrawl.append(year)
            print(f"🔴 {year}年: 完整度{s['completeness']:.1f}% - 急需重新爬取")
        elif s['completeness'] < 95:
            print(f"🟡 {year}年: 完整度{s['completeness']:.1f}% - 建議部分重新爬取")
        else:
            print(f"✅ {year}年: 完整度{s['completeness']:.1f}% - 資料良好")
    
    if need_recrawl:
        print(f"\n⚠️ 需要緊急處理的年份: {need_recrawl}")
    
    return summary

def main():
    print("🔍 全年份資料品質檢查")
    print("=" * 50)
    
    try:
        summary = check_all_years_empty_fields()
        
        # 備份建議
        print(f"\n💡 建議:")
        print("1. 當前資料已自動備份到OCI backups/目錄")
        print("2. 重新爬取前請確認爬蟲程式錯誤已修復")
        print("3. 建議分批處理，避免同時爬取多個年份")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    main()