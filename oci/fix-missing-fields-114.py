#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復114年缺少必要欄位的資料
"""

import json
import subprocess
import time

# 載入爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 下載最新資料
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

# 找出114年缺少必要欄位的資料
missing_field_permits = []
permits_114 = [p for p in data['permits'] if p.get('permitYear') == 114]

for permit in permits_114:
    # 跳過完全空白的資料
    if not permit.get('applicantName', '').strip():
        continue
    
    # 檢查必要欄位
    missing = []
    for field in required_fields:
        if not permit.get(field):
            missing.append(field)
    
    if missing:
        missing_field_permits.append({
            'permitNumber': permit.get('permitNumber'),
            'sequenceNumber': permit.get('sequenceNumber', 0),
            'indexKey': permit.get('indexKey'),
            'missing': missing
        })

print(f"🔍 找到 {len(missing_field_permits)} 筆缺少必要欄位的資料")

if missing_field_permits:
    # 顯示前10筆範例
    print("\n範例:")
    for i, item in enumerate(missing_field_permits[:10]):
        print(f"  {item['permitNumber']}: 缺少 {', '.join(item['missing'])}")
    if len(missing_field_permits) > 10:
        print(f"  ... 還有 {len(missing_field_permits) - 10} 筆")
    
    # 啟動爬蟲
    crawler = OptimizedCrawler()
    crawler.request_delay = 1.0
    crawler.batch_size = 30
    
    print(f"\n🚀 開始修復缺少欄位的資料...")
    print("=" * 70)
    
    batch = []
    success_count = 0
    still_missing_count = 0
    
    for i, item in enumerate(missing_field_permits):
        print(f"\n[{i+1}/{len(missing_field_permits)}] {item['permitNumber']}")
        print(f"  缺少: {', '.join(item['missing'])}")
        
        try:
            result = crawler.crawl_single_permit(item['indexKey'])
            
            if result and isinstance(result, dict):
                # 檢查是否成功獲得所有必要欄位
                still_missing = []
                for field in item['missing']:
                    if not result.get(field):
                        still_missing.append(field)
                
                if not still_missing:
                    batch.append(result)
                    success_count += 1
                    print(f"  ✅ 成功補齊所有欄位")
                    # 顯示補齊的資料
                    for field in item['missing']:
                        print(f"     {field}: {result.get(field)}")
                else:
                    still_missing_count += 1
                    print(f"  ⚠️ 仍缺少: {', '.join(still_missing)}")
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
    
    print(f"\n✅ 完成！")
    print(f"成功補齊: {success_count} 筆")
    print(f"仍有缺失: {still_missing_count} 筆")
    print(f"總處理: {len(missing_field_permits)} 筆")
    
else:
    print("✅ 所有114年資料都有完整的必要欄位！")