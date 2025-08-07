#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單爬蟲執行腳本 - 基於成功的版本
"""

import sys

# 載入穩定版爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python3 simple-crawl.py <年份> <起始序號> [結束序號]")
        print("範例:")
        print("  python3 simple-crawl.py 114 1 100")
        print("  python3 simple-crawl.py 113 1")
        sys.exit(1)
    
    year = int(sys.argv[1])
    start_seq = int(sys.argv[2])
    end_seq = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # 創建爬蟲實例
    crawler = OptimizedCrawler()
    crawler.request_delay = 0.8  # 可調整延遲
    crawler.batch_size = 30       # 可調整批次大小
    
    # 開始爬取
    if end_seq:
        print(f"🚀 爬取 {year}年 序號 {start_seq}-{end_seq}")
    else:
        print(f"🚀 爬取 {year}年 從序號 {start_seq} 開始")
    
    # 執行爬取
    crawler.crawl_year_range(year, start_seq, end_seq, end_seq is None)