#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復114年空白資料
"""

import json
import subprocess
import time
from datetime import datetime

# 載入爬蟲
exec(open('optimized-crawler.py').read().split('if __name__ == "__main__":')[0])

def find_empty_data_sequences():
    """找出空白資料的序號"""
    print("📥 載入現有資料...")
    
    # 下載最新資料
    subprocess.run([
        'oci', 'os', 'object', 'get',
        '--namespace', 'nrsdi1rz5vl8',
        '--bucket-name', 'taichung-building-permits',
        '--name', 'data/permits.json',
        '--file', '/tmp/check_permits.json'
    ], capture_output=True)
    
    with open('/tmp/check_permits.json', 'r') as f:
        data = json.load(f)
    
    # 找出114年空白資料
    empty_sequences = []
    for p in data['permits']:
        if p.get('permitYear') == 114:
            seq = p.get('sequenceNumber', 0)
            # 檢查是否為空白資料
            if not p.get('applicantName', '').strip() or not p.get('siteAddress', '').strip():
                empty_sequences.append(seq)
    
    print(f"找到 {len(empty_sequences)} 筆空白資料")
    return sorted(empty_sequences)

def crawl_specific_sequences(sequences):
    """爬取特定序號"""
    crawler = OptimizedCrawler()
    crawler.request_delay = 1.0
    crawler.batch_size = 20
    
    print(f"\n🔧 開始修復 {len(sequences)} 筆空白資料")
    
    # 分批處理
    batch = []
    success_count = 0
    
    for i, seq in enumerate(sequences):
        print(f"\n[{i+1}/{len(sequences)}] 爬取序號 {seq:05d}...")
        
        try:
            # 使用原始爬蟲的crawl_single_permit方法
            permit_data = crawler.crawl_single_permit(114, seq)
            
            if permit_data and permit_data.get('applicantName'):
                batch.append(permit_data)
                success_count += 1
                print(f"   ✅ 成功: {permit_data['permitNumber']}")
                print(f"   申請人: {permit_data['applicantName']}")
                print(f"   地址: {permit_data['siteAddress'][:30]}...")
            else:
                print(f"   ⚠️ 無資料")
            
            # 每20筆上傳一次
            if len(batch) >= 20:
                print(f"\n💾 上傳 {len(batch)} 筆資料...")
                if crawler.upload_batch_data(batch):
                    print("   ✅ 上傳成功")
                    batch = []
                else:
                    print("   ❌ 上傳失敗")
            
            time.sleep(crawler.request_delay)
            
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
    
    # 上傳剩餘資料
    if batch:
        print(f"\n💾 上傳最後 {len(batch)} 筆資料...")
        crawler.upload_batch_data(batch)
    
    print(f"\n✅ 完成！成功修復 {success_count}/{len(sequences)} 筆資料")

if __name__ == "__main__":
    # 找出空白資料
    empty_seqs = find_empty_data_sequences()
    
    if empty_seqs:
        # 顯示前20個
        print("\n空白資料序號範例:")
        for seq in empty_seqs[:20]:
            print(f"  {seq}")
        if len(empty_seqs) > 20:
            print(f"  ... 還有 {len(empty_seqs) - 20} 個")
        
        # 開始爬取
        crawl_specific_sequences(empty_seqs)
    else:
        print("✅ 沒有找到空白資料！")