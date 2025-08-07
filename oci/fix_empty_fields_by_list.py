#!/usr/bin/env python3
"""
根據修復清單修復空白欄位
使用 fix_empty_[year].txt 清單進行修復
"""

import sys
import json
import time
from datetime import datetime

# 載入爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

def load_fix_list(year):
    """載入指定年份的修復清單"""
    filename = f"fix_empty_{year}.txt"
    sequences = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        seq_year, seq_num = parts[0], int(parts[1])
                        if seq_year == str(year):
                            sequences.append(seq_num)
        
        return sorted(sequences)
    except FileNotFoundError:
        print(f"❌ 修復清單檔案不存在: {filename}")
        return []

def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 fix_empty_fields_by_list.py <年份>")
        print("例如: python3 fix_empty_fields_by_list.py 112")
        sys.exit(1)
    
    year = int(sys.argv[1])
    print(f"🔧 開始修復 {year}年 空白欄位資料")
    
    # 載入修復清單
    sequences = load_fix_list(year)
    if not sequences:
        print(f"❌ 沒有找到 {year}年 的修復清單")
        return
    
    print(f"📋 載入修復清單: {len(sequences)} 筆")
    print(f"📊 序號範圍: {min(sequences)} - {max(sequences)}")
    
    # 初始化爬蟲
    crawler = OptimizedCrawler()
    crawler.request_delay = 0.8
    crawler.batch_size = 30
    
    print(f"\n🚀 開始修復空白欄位...")
    print("=" * 70)
    
    success_count = 0
    failed_count = 0
    
    for i, seq in enumerate(sequences):
        try:
            print(f"🔍 [{seq:05d}] 修復中...", end=" ")
            
            # 爬取單筆資料
            index_key = f"{year}1{seq:05d}00"
            permit_data = crawler.crawl_single_permit(index_key)
            
            if permit_data:
                print("✅")
                success_count += 1
            else:
                print("❌ 無資料")
                failed_count += 1
            
            # 每30筆上傳一次
            if (i + 1) % crawler.batch_size == 0 and len(crawler.results) > 0:
                print(f"\n💾 批次上傳 ({len(crawler.results)} 筆)...")
                try:
                    crawler.upload_batch_data(crawler.results)
                    crawler.results = []  # 清空已上傳的資料
                    print("✅ 上傳成功")
                    print(f"📊 [{i+1:4d}/{len(sequences)}] 成功:{success_count} 失敗:{failed_count}")
                    print("-" * 50)
                except Exception as e:
                    print(f"❌ 上傳失敗: {e}")
            
            # 延遲避免被封鎖
            if crawler.request_delay > 0:
                time.sleep(crawler.request_delay)
                
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            failed_count += 1
    
    # 上傳剩餘資料
    if len(crawler.results) > 0:
        print(f"\n💾 上傳剩餘資料 ({len(crawler.results)} 筆)...")
        try:
            crawler.upload_batch_data(crawler.results)
            print("✅ 上傳成功")
        except Exception as e:
            print(f"❌ 上傳失敗: {e}")
    
    # 最終統計
    print("\n" + "=" * 70)
    print("🏁 修復完成！")
    print(f"📊 最終統計:")
    print(f"   總計嘗試: {len(sequences)}")
    print(f"   成功修復: {success_count}")
    print(f"   失敗: {failed_count}")
    print(f"   成功率: {success_count/len(sequences)*100:.1f}%")

if __name__ == "__main__":
    main()