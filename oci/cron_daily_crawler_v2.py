#!/usr/bin/env python3
"""
每日自動爬蟲 V2 - 持續爬取直到遇到空白
"""

import sys
import os
import json
import time
from datetime import datetime

# 切換到正確的工作目錄
os.chdir('/mnt/c/claude code/建照爬蟲/oci')

# 添加路徑
sys.path.append('/mnt/c/claude code/建照爬蟲/oci')

# 載入爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 進度檔案
PROGRESS_FILE = 'cron_progress.json'

def load_progress():
    """載入爬蟲進度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    else:
        # 預設從114年序號1099開始（因為1098已經爬過了）
        return {
            "year": 114,
            "currentSequence": 1099,
            "lastCrawledAt": None,
            "consecutiveEmpty": 0
        }

def save_progress(progress):
    """儲存爬蟲進度"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def daily_crawl():
    """每日爬蟲任務 - 持續爬取直到遇到空白"""
    
    print(f"🕐 每日爬蟲 V2 開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 載入進度
    progress = load_progress()
    year = progress['year']
    current_seq = progress['currentSequence']
    consecutive_empty = progress['consecutiveEmpty']
    
    print(f"📊 當前進度: {year}年 序號{current_seq}")
    print(f"   連續空白: {consecutive_empty}次")
    
    # 創建爬蟲實例
    crawler = OptimizedCrawler()
    crawler.request_delay = 0.8
    
    # 記錄本次執行的統計
    crawled_count = 0
    success_count = 0
    empty_count = 0
    error_count = 0
    batch_data = []
    
    # 持續爬取直到遇到空白
    while True:
        index_key = f'{year}10{current_seq:04d}00'
        print(f'\n🔍 [{crawled_count + 1}] 爬取: {index_key}')
        
        result = crawler.crawl_single_permit(index_key)
        crawled_count += 1
        
        if result and result != 'NO_DATA':
            # 爬取成功
            print(f'✅ 爬取成功!')
            print(f'   建照號碼: {result.get("permitNumber")}')
            print(f'   申請人: {result.get("applicantName")}')
            print(f'   總樓地板面積: {result.get("totalFloorArea")}')
            
            success_count += 1
            batch_data.append(result)
            
            # 更新進度
            progress['currentSequence'] = current_seq + 1
            progress['lastCrawledAt'] = datetime.now().isoformat()
            progress['consecutiveEmpty'] = 0  # 重置連續空白計數
            consecutive_empty = 0
            
            # 每20筆上傳一次
            if len(batch_data) >= 20:
                print(f'\n💾 批次上傳 {len(batch_data)} 筆資料...')
                success = crawler.upload_batch_data(batch_data)
                if success:
                    print('✅ 批次上傳成功!')
                else:
                    print('❌ 批次上傳失敗!')
                batch_data = []
            
            # 繼續下一個序號
            current_seq += 1
            
        elif result == 'NO_DATA':
            # 此序號無資料（建照尚未發出）
            print('⚠️ 此序號查無資料（建照尚未發出）')
            empty_count += 1
            consecutive_empty += 1
            progress['consecutiveEmpty'] = consecutive_empty
            
            # 更新進度
            progress['currentSequence'] = current_seq + 1
            progress['lastCrawledAt'] = datetime.now().isoformat()
            
            if consecutive_empty >= 3:
                # 連續3個序號都無資料，停止爬取
                print(f'\n🏁 連續{consecutive_empty}個序號無資料，停止爬取')
                print(f'📌 最後有效序號: {current_seq - consecutive_empty}')
                break
            else:
                # 繼續嘗試下一個序號
                current_seq += 1
                
        else:
            # 爬取失敗（可能是網路問題或格式錯誤）
            print(f'❌ 爬取失敗')
            print(f'   返回值: {result}')
            print(f'   可能原因: 網路問題、網站暫時無法訪問、或序號格式錯誤')
            error_count += 1
            
            # 嘗試跳過這個序號
            progress['currentSequence'] = current_seq + 1
            progress['lastCrawledAt'] = datetime.now().isoformat()
            current_seq += 1
            
            # 如果錯誤太多，停止
            if error_count >= 5:
                print('\n❌ 錯誤次數過多，停止爬取')
                break
        
        # 儲存進度
        save_progress(progress)
        
        # 延遲避免被封鎖
        time.sleep(crawler.request_delay)
        
        # 如果已爬取超過50筆，先停止（避免執行太久）
        if crawled_count >= 50:
            print('\n⏸️ 已爬取50筆，暫停執行')
            break
    
    # 上傳剩餘的資料
    if batch_data:
        print(f'\n💾 上傳剩餘 {len(batch_data)} 筆資料...')
        success = crawler.upload_batch_data(batch_data)
        if success:
            print('✅ 上傳成功!')
        else:
            print('❌ 上傳失敗!')
    
    # 顯示統計
    print(f"\n📊 本次執行統計:")
    print(f"   總爬取: {crawled_count} 筆")
    print(f"   成功: {success_count} 筆")
    print(f"   空白: {empty_count} 筆")
    print(f"   錯誤: {error_count} 筆")
    print(f"   最新序號: {progress['currentSequence']}")
    
    print(f"\n🕐 每日爬蟲 V2 結束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    daily_crawl()