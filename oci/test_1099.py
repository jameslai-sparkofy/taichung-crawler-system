#!/usr/bin/env python3
import sys
import os

os.chdir('/mnt/c/claude code/建照爬蟲/oci')
sys.path.append('.')
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 測試爬取序號1099
crawler = OptimizedCrawler()
crawler.request_delay = 0.8

index_key = '11410109900'
print(f'測試爬取序號1099: {index_key}')
result = crawler.crawl_single_permit(index_key)

if result == 'NO_DATA':
    print('⚠️ 網站回應：查無任何資訊（此建照號碼尚未發出）')
elif result:
    import json
    print('✅ 爬取成功！資料內容:')
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print('❌ 爬取失敗（網路錯誤或其他問題）')