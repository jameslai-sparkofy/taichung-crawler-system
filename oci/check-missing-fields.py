#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查並重新爬取缺少必要欄位的資料
"""

import json
import subprocess
import time
from datetime import datetime

# 載入爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

def check_missing_fields():
    """檢查缺少必要欄位的資料"""
    print("📥 下載最新資料...")
    subprocess.run([
        'oci', 'os', 'object', 'get',
        '--namespace', 'nrsdi1rz5vl8',
        '--bucket-name', 'taichung-building-permits',
        '--name', 'data/permits.json',
        '--file', '/tmp/check_fields.json'
    ], capture_output=True)
    
    with open('/tmp/check_fields.json', 'r') as f:
        data = json.load(f)
    
    # 必要欄位
    required_fields = ['floors', 'buildings', 'units', 'totalFloorArea', 'issueDate']
    
    # 統計各年份的問題資料
    missing_data = {}
    total_issues = 0
    
    for permit in data['permits']:
        year = permit.get('permitYear', 0)
        if year not in missing_data:
            missing_data[year] = []
        
        # 檢查是否有申請人資料
        if not permit.get('applicantName', '').strip():
            continue  # 跳過完全空白的資料
        
        # 檢查必要欄位
        missing_fields = []
        for field in required_fields:
            if not permit.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            total_issues += 1
            missing_data[year].append({
                'permitNumber': permit.get('permitNumber'),
                'sequenceNumber': permit.get('sequenceNumber', 0),
                'indexKey': permit.get('indexKey'),
                'missing': missing_fields
            })
    
    # 顯示統計
    print(f"\n📊 必要欄位缺失統計:")
    print(f"總計有 {total_issues} 筆資料缺少必要欄位\n")
    
    for year in sorted(missing_data.keys(), reverse=True):
        if missing_data[year]:
            print(f"{year}年: {len(missing_data[year])} 筆")
            # 顯示前5筆範例
            for i, item in enumerate(missing_data[year][:5]):
                print(f"  - {item['permitNumber']}: 缺少 {', '.join(item['missing'])}")
            if len(missing_data[year]) > 5:
                print(f"  ... 還有 {len(missing_data[year]) - 5} 筆")
            print()
    
    return missing_data

def recrawl_missing_fields(missing_data):
    """重新爬取缺少欄位的資料"""
    crawler = OptimizedCrawler()
    crawler.request_delay = 1.0
    crawler.batch_size = 30
    
    total_to_crawl = sum(len(items) for items in missing_data.values())
    print(f"\n🔧 開始重新爬取 {total_to_crawl} 筆缺少欄位的資料")
    print("=" * 70)
    
    count = 0
    batch = []
    
    for year in sorted(missing_data.keys(), reverse=True):
        if not missing_data[year]:
            continue
            
        print(f"\n📅 處理 {year}年資料 ({len(missing_data[year])} 筆)")
        
        for item in missing_data[year]:
            count += 1
            index_key = item['indexKey']
            
            print(f"\n[{count}/{total_to_crawl}] {item['permitNumber']}")
            print(f"  缺少: {', '.join(item['missing'])}")
            
            try:
                result = crawler.crawl_single_permit(index_key)
                
                if result and isinstance(result, dict):
                    # 檢查是否成功獲得所有必要欄位
                    still_missing = []
                    for field in item['missing']:
                        if not result.get(field):
                            still_missing.append(field)
                    
                    if not still_missing:
                        batch.append(result)
                        print(f"  ✅ 成功補齊所有欄位")
                    else:
                        print(f"  ⚠️ 仍缺少: {', '.join(still_missing)}")
                elif result == "NO_DATA":
                    print(f"  ⚠️ 無資料")
                else:
                    print(f"  ❌ 爬取失敗")
                
                # 批次上傳
                if len(batch) >= crawler.batch_size:
                    print(f"\n💾 上傳 {len(batch)} 筆資料...")
                    if crawler.upload_batch_data(batch):
                        print("  ✅ 上傳成功")
                        batch = []
                    else:
                        print("  ❌ 上傳失敗")
                
                time.sleep(crawler.request_delay)
                
            except Exception as e:
                print(f"  ❌ 錯誤: {e}")
    
    # 上傳剩餘資料
    if batch:
        print(f"\n💾 上傳最後 {len(batch)} 筆資料...")
        crawler.upload_batch_data(batch)
    
    print(f"\n✅ 重新爬取完成")

if __name__ == "__main__":
    # 檢查缺失欄位
    missing_data = check_missing_fields()
    
    # 詢問是否要重新爬取
    if missing_data and any(missing_data.values()):
        print("\n是否要重新爬取這些資料? (y/n): ", end='')
        # 自動執行
        print("y")
        recrawl_missing_fields(missing_data)
    else:
        print("\n✅ 所有資料都有完整的必要欄位！")