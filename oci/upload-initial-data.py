#!/usr/bin/env python3
"""
上傳初始資料到OCI Object Storage
"""

import oci
import json
import sys
from datetime import datetime

def upload_to_oci():
    """上傳資料到OCI"""
    try:
        # 初始化OCI客戶端
        config = {}
        object_storage_client = oci.object_storage.ObjectStorageClient(config)
        
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        print("🚀 開始上傳資料到OCI Object Storage")
        print(f"Namespace: {namespace}")
        print(f"Bucket: {bucket_name}")
        print("=" * 50)
        
        # 讀取建照資料
        with open('permits-initial.json', 'r', encoding='utf-8') as f:
            permits_data = json.load(f)
        
        print(f"📊 建照資料: {permits_data['totalCount']} 筆")
        
        # 上傳建照資料
        print("  上傳 permits.json...", end='')
        object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name="data/permits.json",
            put_object_body=json.dumps(permits_data, ensure_ascii=False, indent=2).encode('utf-8'),
            content_type="application/json"
        )
        print(" ✅")
        
        # 讀取執行記錄
        with open('crawl-logs-initial.json', 'r', encoding='utf-8') as f:
            logs_data = json.load(f)
        
        print(f"📋 執行記錄: {len(logs_data['logs'])} 筆")
        
        # 上傳執行記錄
        print("  上傳 crawl-logs.json...", end='')
        object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name="data/crawl-logs.json",
            put_object_body=json.dumps(logs_data, ensure_ascii=False, indent=2).encode('utf-8'),
            content_type="application/json"
        )
        print(" ✅")
        
        print("\n✅ 資料上傳成功！")
        print("\n🌐 監控網頁:")
        print("https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 上傳失敗: {e}")
        return False

if __name__ == "__main__":
    success = upload_to_oci()
    sys.exit(0 if success else 1)