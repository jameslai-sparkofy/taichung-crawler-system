#!/usr/bin/env python3
"""
7:50 測試腳本 - 寫入測試資料到網頁
"""
import json
import logging
from datetime import datetime

import oci
from oci.object_storage import ObjectStorageClient

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OCI 設定
NAMESPACE = "nrsdi1rz5vl8"
BUCKET_NAME = "taichung-building-permits"

class OCIStorage:
    def __init__(self):
        # 使用 Instance Principal 認證
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        self.object_storage = ObjectStorageClient(config={}, signer=signer)
        logger.info("使用 Instance Principal 認證")
    
    def put_object(self, object_name, content):
        """寫入物件到 OCI"""
        try:
            self.object_storage.put_object(
                NAMESPACE, 
                BUCKET_NAME, 
                object_name,
                content.encode('utf-8')
            )
            logger.info(f"成功寫入 {object_name}")
            return True
        except Exception as e:
            logger.error(f"寫入物件失敗 {object_name}: {str(e)}")
            return False

def create_test_page():
    """建立測試頁面"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>7:50 測試執行</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .info {{
            background: #e8f5e9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .time {{
            font-size: 24px;
            color: #2e7d32;
            text-align: center;
            margin: 20px 0;
        }}
        .message {{
            text-align: center;
            color: #666;
            margin: 20px 0;
        }}
        .details {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .success {{
            color: #2e7d32;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 7:50 測試執行成功！</h1>
        
        <div class="info">
            <div class="time">執行時間: {current_time}</div>
            <p class="message">Cron job 已在預定時間成功執行</p>
        </div>
        
        <div class="details">
            <h2>執行詳情</h2>
            <ul>
                <li>腳本名稱: test_750.py</li>
                <li>執行環境: OCI Compute Instance (Ubuntu 22.04)</li>
                <li>Instance IP: 158.101.158.202</li>
                <li>執行方式: Cron Job (50 7 * * *)</li>
            </ul>
        </div>
        
        <div class="details">
            <h2>測試結果</h2>
            <p class="success">✅ 成功連接到 OCI Object Storage</p>
            <p class="success">✅ 成功寫入測試頁面</p>
            <p class="success">✅ Instance Principal 認證正常</p>
        </div>
        
        <div class="message">
            <p>這個頁面證明了定時爬蟲系統運作正常</p>
            <p>序號 1137 的建照資料將在後續爬取中處理</p>
        </div>
    </div>
</body>
</html>"""
    
    storage = OCIStorage()
    
    # 寫入測試頁面
    if storage.put_object('test/750-test.html', html_content):
        logger.info("✅ 測試頁面已成功寫入 OCI")
        
        # 同時更新 index.html 加入連結
        index_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>測試執行記錄</title>
</head>
<body>
    <h1>測試執行記錄</h1>
    <ul>
        <li><a href="test/750-test.html">7:50 測試執行 - {current_time}</a></li>
    </ul>
</body>
</html>"""
        
        storage.put_object('test-index.html', index_html)
        
        print(f"\n✅ 測試執行成功！")
        print(f"執行時間: {current_time}")
        print(f"測試頁面已寫入: test/750-test.html")
        print(f"可以透過以下網址查看:")
        print(f"https://objectstorage.ap-tokyo-1.oraclecloud.com/n/{NAMESPACE}/b/{BUCKET_NAME}/o/test/750-test.html")
    else:
        logger.error("測試頁面寫入失敗")

if __name__ == "__main__":
    create_test_page()