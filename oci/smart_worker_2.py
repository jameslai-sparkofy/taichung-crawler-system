#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('.')

# 載入爬蟲類別
exec(open('optimized-crawler.py').read().split('if __name__ == "__main__":')[0])

# 建立爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 1.2  # 並發時增加延遲
crawler.batch_size = 20

print(f"🔧 Worker 2 啟動")
print("=" * 70)

# 任務列表
tasks = [(114, 1041, 1080)]

for task in tasks:
    year, start_seq, end_seq = task
    print(f"
📍 爬取 {year}年 {start_seq:05d}-{end_seq:05d}...")
    try:
        crawler.crawl_year_range(year, start_seq, end_seq, False)
        print(f"✅ 完成 {year}年 {start_seq:05d}-{end_seq:05d}")
    except Exception as e:
        print(f"❌ 失敗 {year}年 {start_seq:05d}-{end_seq:05d}: {e}")
        crawler.save_progress()

print(f"
🎉 Worker 2 所有任務完成")
