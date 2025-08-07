#!/bin/bash
cd "/mnt/c/claude code/建照爬蟲/oci"
python3 -c "
import sys
sys.path.append('.')
# 載入爬蟲類別
exec(open('optimized-crawler.py').read().split('if __name__ == \"__main__\":')[0])

# 建立爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 1.5  # 增加延遲避免並發問題
crawler.batch_size = 20

print(f'🔧 Worker 2: 爬取 114年 1111-1310')
print('=' * 70)

try:
    crawler.crawl_year_range(114, 1111, 1310, False)
    print(f'\n✅ Worker 2 完成任務')
except Exception as e:
    print(f'\n❌ Worker 2 錯誤: {e}')
    crawler.save_progress()
"
