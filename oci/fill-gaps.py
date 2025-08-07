#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
補爬中間漏掉的資料
"""

import sys
sys.path.append('.')
from optimized_crawler import OptimizedCrawler

def main():
    crawler = OptimizedCrawler()
    
    print("🔧 補爬漏掉的資料")
    print("=" * 70)
    
    # 需要補爬的區間
    gaps = [
        (114, 1, 99),      # 114年 1-99
        (114, 346, 360),   # 114年 346-360  
        (114, 391, 400),   # 114年 391-400
    ]
    
    print("📋 補爬計畫:")
    total_to_fill = 0
    for year, start, end in gaps:
        count = end - start + 1
        total_to_fill += count
        print(f"   {year}年: {start:05d}-{end:05d} ({count} 筆)")
    
    print(f"📊 總計需補爬: {total_to_fill} 筆")
    print("=" * 70)
    
    # 依序補爬各區間
    for year, start_seq, end_seq in gaps:
        try:
            print(f"\n🔍 補爬 {year}年 {start_seq:05d}-{end_seq:05d}...")
            crawler.crawl_year_range(year, start_seq, end_seq, False)
            print(f"✅ 區間 {start_seq:05d}-{end_seq:05d} 完成")
        except KeyboardInterrupt:
            print(f"\n🛑 用戶中斷")
            break
        except Exception as e:
            print(f"❌ 補爬失敗: {e}")
            crawler.save_progress()
            continue
    
    print("\n🎉 補爬任務完成！")
    print("\n接下來可以從 114年 401號繼續往後爬取")

if __name__ == "__main__":
    main()