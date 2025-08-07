#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
補爬114年缺失的序號
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接複製需要的類別
import subprocess
import time
import json
import re
from datetime import datetime
import signal
import tempfile
import json
import subprocess

def get_missing_sequences():
    """取得缺失的序號"""
    # 下載最新資料
    subprocess.run(['oci', 'os', 'object', 'get', 
                   '--namespace', 'nrsdi1rz5vl8', 
                   '--bucket-name', 'taichung-building-permits', 
                   '--name', 'data/permits.json', 
                   '--file', '/tmp/check_gaps.json'], capture_output=True)
    
    with open('/tmp/check_gaps.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    permits = data.get('permits', [])
    
    # 取得114年的所有序號
    year_114 = [p for p in permits if p.get('permitYear') == 114]
    existing_nums = set([p.get('sequenceNumber', 0) for p in year_114])
    
    # 找出缺失的序號（1-580範圍內）
    missing = []
    for i in range(1, 581):  # 只檢查到580，因為目前最大是580
        if i not in existing_nums:
            missing.append(i)
    
    return missing

def group_sequences(sequences):
    """將序號分組為連續區間"""
    if not sequences:
        return []
    
    ranges = []
    start = sequences[0]
    end = sequences[0]
    
    for i in range(1, len(sequences)):
        if sequences[i] == end + 1:
            end = sequences[i]
        else:
            ranges.append((start, end))
            start = sequences[i]
            end = sequences[i]
    
    ranges.append((start, end))
    return ranges

def main():
    print("🔍 檢查114年缺失序號...")
    
    missing = get_missing_sequences()
    
    if not missing:
        print("✅ 沒有缺失序號！")
        return
    
    print(f"❌ 發現 {len(missing)} 個缺失序號")
    
    # 分組顯示
    ranges = group_sequences(missing)
    
    print("\n📋 缺失範圍：")
    for start, end in ranges[:10]:  # 顯示前10組
        if start == end:
            print(f"   {start:05d}")
        else:
            print(f"   {start:05d}-{end:05d} ({end-start+1}筆)")
    
    if len(ranges) > 10:
        print(f"   ... 還有 {len(ranges)-10} 組")
    
    # 確認是否補爬
    print(f"\n總計需要補爬 {len(missing)} 筆")
    print("=" * 50)
    
    # 開始補爬
    crawler = OptimizedCrawler()
    crawler.request_delay = 0.5  # 加快速度
    
    print("🚀 開始補爬缺失序號...")
    
    # 分批處理，每批30個
    batch_size = 30
    for i in range(0, len(missing), batch_size):
        batch = missing[i:i+batch_size]
        batch_ranges = group_sequences(batch)
        
        print(f"\n📦 批次 {i//batch_size + 1}:")
        
        for start, end in batch_ranges:
            try:
                print(f"🔧 補爬 114年 {start:05d}-{end:05d}...")
                crawler.crawl_year_range(114, start, end, False)
                print(f"✅ 完成 {start:05d}-{end:05d}")
            except KeyboardInterrupt:
                print("\n🛑 用戶中斷")
                return
            except Exception as e:
                print(f"❌ 失敗: {e}")
                continue
    
    print("\n🎉 補爬完成！")
    
    # 重新檢查
    print("\n🔍 重新檢查缺失...")
    new_missing = get_missing_sequences()
    if new_missing:
        print(f"⚠️ 仍有 {len(new_missing)} 個缺失序號")
    else:
        print("✅ 所有序號都已補齊！")

if __name__ == "__main__":
    main()