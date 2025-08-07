#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('.')

# 載入爬蟲類別
exec(open('optimized-crawler.py').read().split('if __name__ == "__main__":')[0])

# 建立爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 1.2  # 稍微增加延遲避免並發問題
crawler.batch_size = 20  # 減少批次大小避免衝突

print(f"🔧 Worker 3: 爬取 114年 01329-01552")
print("=" * 70)

try:
    crawler.crawl_year_range(114, 1329, 1552, False)
    print(f"
✅ Worker 3 完成任務")
except Exception as e:
    print(f"
❌ Worker 3 錯誤: {e}")
    crawler.save_progress()
