#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動5個並行爬蟲爭取113年
"""

import subprocess
import time
import os
from datetime import datetime

# 載入爬蟲類別
exec(open('optimized-crawler.py').read().split('if __name__ == "__main__":')[0])

def start_worker(worker_id, year, start_seq, end_seq):
    """啟動單個工作進程"""
    log_file = f"worker_113_{worker_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 創建工作腳本
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append('.')

# 載入爬蟲類別
exec(open('optimized-crawler.py').read().split('if __name__ == "__main__":')[0])

# 建立爬蟲實例
crawler = OptimizedCrawler()
crawler.request_delay = 1.0  # 並發時稍微增加延遲
crawler.batch_size = 20

print(f"🔧 Worker {worker_id}: 爬取 {year}年 {start_seq:05d}-{end_seq:05d}")
print("=" * 70)

try:
    crawler.crawl_year_range({year}, {start_seq}, {end_seq}, False)
    print(f"\n✅ Worker {worker_id} 完成任務")
except Exception as e:
    print(f"\n❌ Worker {worker_id} 錯誤: {{e}}")
    crawler.save_progress()
'''
    
    worker_script = f"worker_113_{worker_id}.py"
    with open(worker_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    os.chmod(worker_script, 0o755)
    
    # 啟動工作進程
    cmd = f"nohup python3 {worker_script} > {log_file} 2>&1 &"
    subprocess.run(cmd, shell=True)
    
    # 取得PID
    time.sleep(0.5)
    pid_cmd = f"ps aux | grep 'python3 {worker_script}' | grep -v grep | awk '{{print $2}}' | head -1"
    pid_result = subprocess.run(pid_cmd, shell=True, capture_output=True, text=True)
    pid = pid_result.stdout.strip()
    
    return pid, log_file

def main():
    print("🚀 啟動5個並行爬蟲爭取113年")
    print("=" * 70)
    
    # 113年分成440筆一份，分給5個worker
    tasks = [
        (1, 113, 1, 440),
        (2, 113, 441, 880),
        (3, 113, 881, 1320),
        (4, 113, 1321, 1760),
        (5, 113, 1761, 2201)
    ]
    
    print("📋 113年任務分配 (1-2201):")
    worker_info = []
    
    for worker_id, year, start, end in tasks:
        print(f"\n🔧 啟動 Worker {worker_id}: {year}年 {start:05d}-{end:05d} ({end-start+1} 筆)")
        pid, log_file = start_worker(worker_id, year, start, end)
        
        if pid:
            print(f"   ✅ PID: {pid}, Log: {log_file}")
            worker_info.append({
                'worker_id': worker_id,
                'pid': pid,
                'log_file': log_file,
                'year': year,
                'start': start,
                'end': end
            })
        else:
            print(f"   ❌ 啟動失敗")
        
        time.sleep(2)  # 避免同時啟動造成問題
    
    print("\n📊 工作進程摘要:")
    print(f"{'Worker':<10} {'PID':<10} {'年份':<6} {'範圍':<20} {'日誌檔案'}")
    print("=" * 80)
    for info in worker_info:
        range_str = f"{info['start']:05d}-{info['end']:05d}"
        print(f"Worker {info['worker_id']:<4} {info['pid']:<10} {info['year']:<6} {range_str:<20} {info['log_file']}")
    
    print("\n💡 監控指令:")
    print("   查看所有工作進程: ps aux | grep 'worker_113_[0-9].py' | grep -v grep")
    print("   查看工作日誌: tail -f worker_113_1_*.log")
    print("   停止所有工作進程: pkill -f 'worker_113_[0-9].py'")
    
    # 保存工作進程資訊
    import json
    with open('workers_113_info.json', 'w', encoding='utf-8') as f:
        json.dump({
            'start_time': datetime.now().isoformat(),
            'workers': worker_info
        }, f, indent=2)
    
    print("\n✅ 5個並行爬蟲已啟動爭取113年！")

if __name__ == "__main__":
    main()