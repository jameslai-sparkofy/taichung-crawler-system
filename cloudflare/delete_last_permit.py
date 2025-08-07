#!/usr/bin/env python3
import json
import subprocess
import sys

# OCI 設定
namespace = "nrsdi1rz5vl8"
bucket = "taichung-building-permits"

# 1. 下載現有資料
print("下載現有資料...")
cmd = [
    "/home/laija/bin/oci", "os", "object", "get",
    "--namespace", namespace,
    "--bucket-name", bucket,
    "--name", "permits.json",
    "--file", "/tmp/permits_current.json"
]
result = subprocess.run(cmd, capture_output=True)
if result.returncode != 0:
    print(f"下載失敗: {result.stderr.decode()}")
    sys.exit(1)

# 2. 讀取並處理資料
with open('/tmp/permits_current.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"原始資料: {data['totalCount']} 筆")

# 找出並刪除序號 1138 的資料
permits = data['permits']
original_count = len(permits)

# 過濾掉序號 1138
filtered_permits = [p for p in permits if p.get('sequenceNumber') != 1138 or p.get('permitYear') != 114]
removed_count = original_count - len(filtered_permits)

if removed_count > 0:
    print(f"找到並刪除 {removed_count} 筆序號 1138 的資料")
    
    # 更新資料
    data['permits'] = filtered_permits
    data['totalCount'] = len(filtered_permits)
    
    # 重新計算年份統計
    year_counts = {}
    for permit in filtered_permits:
        year = permit.get('permitYear', 0)
        year_counts[str(year)] = year_counts.get(str(year), 0) + 1
    data['yearCounts'] = year_counts
    
    # 3. 寫入暫存檔
    with open('/tmp/permits_updated.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 4. 上傳回 OCI (三個位置)
    for object_name in ['permits.json', 'data/permits.json', 'all_permits.json']:
        print(f"上傳到 {object_name}...")
        cmd = [
            "/home/laija/bin/oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket,
            "--name", object_name,
            "--file", "/tmp/permits_updated.json",
            "--force"
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"✓ {object_name} 上傳成功")
        else:
            print(f"✗ {object_name} 上傳失敗: {result.stderr.decode()}")
    
    print(f"\n完成！新資料總數: {len(filtered_permits)} 筆")
else:
    print("未找到序號 1138 的資料")