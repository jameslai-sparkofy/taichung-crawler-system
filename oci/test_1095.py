#!/usr/bin/env python3
import sys
sys.path.append('.')
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 創建爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 0.8

# 測試爬取序號1095
index_key = '11410109500'
print(f'測試爬取序號1095: {index_key}')
result = crawler.crawl_single_permit(index_key)

if result and result != 'NO_DATA':
    import json
    print('爬取成功！資料內容:')
    print(json.dumps(result, ensure_ascii=False, indent=2))
elif result == 'NO_DATA':
    print('網站回應：查無任何資訊')
else:
    print('爬取失敗')