#!/usr/bin/env python3
"""手動更新序號1091-1097的資料"""

import sys
sys.path.append('.')
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 創建爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 0.8

# 爬取1091-1097
new_permits = []
for seq in range(1091, 1098):
    index_key = f'11410{seq:04d}00'
    print(f'爬取序號{seq}: {index_key}')
    result = crawler.crawl_single_permit(index_key)
    if result and result != 'NO_DATA':
        new_permits.append(result)
        print(f'  ✅ 成功: {result.get("applicantName")}')
    else:
        print(f'  ❌ 失敗或無資料')

# 手動上傳
if new_permits:
    print(f'\n準備上傳 {len(new_permits)} 筆資料...')
    success = crawler.upload_batch_data(new_permits)
    if success:
        print('✅ 上傳成功!')
    else:
        print('❌ 上傳失敗!')