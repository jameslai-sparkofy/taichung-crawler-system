#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新爬取114年空白資料
"""

import json
import subprocess
import time

# 載入爬蟲
exec(open('optimized-crawler.py').read().split('if __name__ == "__main__":')[0])

# 下載最新資料
print("📥 下載最新資料...")
subprocess.run([
    'oci', 'os', 'object', 'get',
    '--namespace', 'nrsdi1rz5vl8',
    '--bucket-name', 'taichung-building-permits',
    '--name', 'data/permits.json',
    '--file', '/tmp/current_permits.json'
], capture_output=True)

with open('/tmp/current_permits.json', 'r') as f:
    data = json.load(f)

# 找出114年空白資料序號
empty_sequences = []
for p in data['permits']:
    if p.get('permitYear') == 114:
        seq = p.get('sequenceNumber', 0)
        if not p.get('applicantName', '').strip() or not p.get('siteAddress', '').strip():
            empty_sequences.append(seq)

empty_sequences = sorted(empty_sequences)
print(f"🔍 找到 {len(empty_sequences)} 筆空白資料需要重新爬取")

if empty_sequences:
    print(f"📋 序號範圍: {min(empty_sequences)} - {max(empty_sequences)}")
    print("前10筆:", empty_sequences[:10])
    
    # 啟動爬蟲
    crawler = OptimizedCrawler()
    crawler.request_delay = 1.0
    crawler.batch_size = 30
    
    print(f"\n🚀 開始爬取空白資料...")
    print("=" * 70)
    
    # 批次爬取
    batch = []
    success_count = 0
    
    for i, seq in enumerate(empty_sequences):
        # 組成正確的 index_key
        year = 114
        permit_type = 1
        index_key = f"{year}{permit_type}{seq:05d}00"
        
        print(f"\n[{i+1}/{len(empty_sequences)}] 爬取序號 {seq:05d} (index_key: {index_key})")
        
        try:
            # 使用正確的參數爬取
            result = crawler.crawl_single_permit(index_key)
            
            if result and isinstance(result, dict):
                batch.append(result)
                success_count += 1
                print(f"  ✅ {result['permitNumber']}")
                print(f"  申請人: {result['applicantName']}")
                print(f"  地址: {result['siteAddress'][:50]}...")
                
                # 每30筆上傳一次
                if len(batch) >= crawler.batch_size:
                    print(f"\n💾 上傳 {len(batch)} 筆資料...")
                    if crawler.upload_batch_data(batch):
                        print("  ✅ 上傳成功")
                        batch = []
                    else:
                        print("  ❌ 上傳失敗")
                        
            elif result == "NO_DATA":
                print(f"  ⚠️ 無資料")
            else:
                print(f"  ❌ 爬取失敗")
                
            # 延遲避免過快
            time.sleep(crawler.request_delay)
            
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
    
    # 上傳剩餘資料
    if batch:
        print(f"\n💾 上傳最後 {len(batch)} 筆資料...")
        crawler.upload_batch_data(batch)
    
    # 顯示統計
    print(f"\n✅ 完成！成功爬取 {success_count}/{len(empty_sequences)} 筆資料")
    crawler.save_progress()
    
else:
    print("✅ 沒有空白資料需要爬取！")