#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
備份爬蟲資料到GitHub
"""

import subprocess
import json
import os
from datetime import datetime

def backup_to_github():
    """備份資料到GitHub"""
    
    # 1. 下載最新資料
    print("📥 下載最新資料...")
    subprocess.run([
        'oci', 'os', 'object', 'get',
        '--namespace', 'nrsdi1rz5vl8',
        '--bucket-name', 'taichung-building-permits',
        '--name', 'data/permits.json',
        '--file', '/tmp/latest_permits.json'
    ], capture_output=True)
    
    # 2. 檢查資料
    with open('/tmp/latest_permits.json', 'r') as f:
        data = json.load(f)
    
    print(f"📊 資料統計:")
    print(f"   總計: {data['totalCount']} 筆")
    for year, count in sorted(data['yearCounts'].items(), key=lambda x: x[0], reverse=True):
        print(f"   {year}年: {count} 筆")
    
    # 3. 創建備份檔案名稱
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"permits_backup_{timestamp}.json"
    
    # 4. 複製到備份目錄
    backup_dir = '/mnt/c/claude code/建照爬蟲/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, backup_filename)
    subprocess.run(['cp', '/tmp/latest_permits.json', backup_path])
    print(f"\n💾 已備份到: {backup_path}")
    
    # 5. 也保存一份latest.json
    latest_path = os.path.join(backup_dir, 'latest.json')
    subprocess.run(['cp', '/tmp/latest_permits.json', latest_path])
    
    # 6. 創建README
    readme_content = f"""# 台中市建照資料備份

最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 資料統計

- 總計: {data['totalCount']} 筆
"""
    
    for year, count in sorted(data['yearCounts'].items(), key=lambda x: x[0], reverse=True):
        readme_content += f"- {year}年: {count} 筆\n"
    
    readme_content += f"\n## 備份檔案\n\n- 最新資料: `latest.json`\n- 此次備份: `{backup_filename}`\n"
    
    with open(os.path.join(backup_dir, 'README.md'), 'w') as f:
        f.write(readme_content)
    
    print("\n📝 已更新README.md")
    
    # 7. Git操作
    print("\n🔧 執行Git操作...")
    os.chdir('/mnt/c/claude code/建照爬蟲')
    
    # 添加檔案
    subprocess.run(['git', 'add', 'backups/'], capture_output=True)
    
    # 提交
    commit_msg = f"備份建照資料 - {timestamp} (共{data['totalCount']}筆)"
    result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Git commit 成功")
        print(f"   訊息: {commit_msg}")
    else:
        print("⚠️  沒有變更需要提交")
    
    return data['totalCount']

def check_missing_sequences():
    """檢查114年的跳號"""
    print("\n🔍 檢查114年跳號情況...")
    
    with open('/tmp/latest_permits.json', 'r') as f:
        data = json.load(f)
    
    permits_114 = [p for p in data['permits'] if p.get('permitYear') == 114]
    sequences = sorted([p.get('sequenceNumber', 0) for p in permits_114])
    
    if not sequences:
        print("   沒有114年資料")
        return []
    
    # 找出缺失的序號
    min_seq = sequences[0]
    max_seq = sequences[-1]
    full_range = set(range(min_seq, max_seq + 1))
    existing = set(sequences)
    missing = sorted(full_range - existing)
    
    print(f"   序號範圍: {min_seq} - {max_seq}")
    print(f"   應有數量: {max_seq - min_seq + 1}")
    print(f"   實際數量: {len(sequences)}")
    print(f"   缺失數量: {len(missing)}")
    
    if missing:
        print(f"\n   缺失序號範例 (前20個):")
        for seq in missing[:20]:
            print(f"     {seq}")
        if len(missing) > 20:
            print(f"     ... 還有 {len(missing) - 20} 個")
    
    # 保存缺失清單
    missing_file = '/mnt/c/claude code/建照爬蟲/backups/missing_114.txt'
    with open(missing_file, 'w') as f:
        f.write(f"114年缺失序號清單\n")
        f.write(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"缺失數量: {len(missing)}\n\n")
        for seq in missing:
            f.write(f"{seq}\n")
    
    print(f"\n   缺失清單已保存到: missing_114.txt")
    
    return missing

if __name__ == "__main__":
    # 執行備份
    total = backup_to_github()
    
    # 檢查跳號
    missing = check_missing_sequences()
    
    print("\n✅ 備份完成！")