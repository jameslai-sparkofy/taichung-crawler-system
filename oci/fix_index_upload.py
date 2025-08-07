#!/usr/bin/env python3
"""
修復 index.html 上傳設定，確保可以在瀏覽器中直接訪問
"""

import oci
import os

def fix_index_upload():
    """重新上傳 index.html 並設置正確的 Content-Type"""
    try:
        # 初始化OCI客戶端
        client = oci.object_storage.ObjectStorageClient({})
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        # 讀取本地 index.html
        index_path = "/mnt/c/claude code/建照爬蟲/oci/index.html"
        if not os.path.exists(index_path):
            print(f"❌ 找不到檔案: {index_path}")
            return
            
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📤 重新上傳 index.html ({len(content)} 字元)")
        
        # 重新上傳，設置正確的 Content-Type
        put_object_response = client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name="index.html",
            put_object_body=content.encode('utf-8'),
            content_type="text/html; charset=utf-8",
            content_disposition="inline"  # 確保在瀏覽器中顯示，不是下載
        )
        
        print("✅ index.html 重新上傳成功")
        print(f"🌐 訪問網址: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/{namespace}/b/{bucket_name}/o/index.html")
        
        # 確認檔案已上傳
        try:
            head_response = client.head_object(namespace, bucket_name, "index.html")
            print(f"📋 檔案資訊:")
            print(f"   - 大小: {head_response.headers.get('content-length')} bytes")
            print(f"   - Content-Type: {head_response.headers.get('content-type')}")
            print(f"   - 最後修改: {head_response.headers.get('last-modified')}")
        except Exception as e:
            print(f"⚠️ 無法獲取檔案資訊: {e}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    print("🔧 修復 index.html 上傳設定")
    print("=" * 50)
    fix_index_upload()