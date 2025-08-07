#!/usr/bin/env python3
"""
8:30 測試腳本 - 爬取序號 1138 並寫入網頁
"""
import json
import logging
import subprocess
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
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        self.object_storage = ObjectStorageClient(config={}, signer=signer)
        logger.info("使用 Instance Principal 認證")
    
    def get_json_object(self, object_name):
        """從 OCI 讀取 JSON 物件"""
        try:
            response = self.object_storage.get_object(NAMESPACE, BUCKET_NAME, object_name)
            return json.loads(response.data.content.decode('utf-8'))
        except Exception as e:
            logger.error(f"讀取物件失敗 {object_name}: {str(e)}")
            return None
    
    def put_json_object(self, object_name, data):
        """寫入 JSON 物件到 OCI"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.object_storage.put_object(
                NAMESPACE, 
                BUCKET_NAME, 
                object_name,
                json_data.encode('utf-8')
            )
            logger.info(f"成功寫入 {object_name}")
            return True
        except Exception as e:
            logger.error(f"寫入物件失敗 {object_name}: {str(e)}")
            return False
    
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

def crawl_1138():
    """爬取序號 1138"""
    index_key = "11410113800"
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    logger.info(f"開始爬取建照 {index_key}")
    
    try:
        # 使用本地的 Python 爬蟲
        import sys
        sys.path.append('/home/ubuntu/crawler')
        from crawler_compute import BuildingPermitCrawler, OCIStorage as CrawlerStorage
        
        storage = CrawlerStorage()
        crawler = BuildingPermitCrawler(storage)
        
        # 爬取單一建照
        result = crawler.crawl_year_range(114, 1138, max_crawl=1)
        
        if result['successful'] > 0:
            logger.info("✅ 成功爬取序號 1138")
            return True
        else:
            logger.error("❌ 爬取失敗")
            return False
            
    except Exception as e:
        logger.error(f"爬取錯誤: {str(e)}")
        return False

def create_result_page():
    """建立結果頁面"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 取得最新的建照資料
    storage = OCIStorage()
    permits_data = storage.get_json_object('data/permits.json')
    
    # 找出序號 1138
    permit_1138 = None
    if permits_data and 'permits' in permits_data:
        for permit in permits_data['permits']:
            if isinstance(permit, dict) and permit.get('sequenceNumber') == 1138:
                permit_1138 = permit
                break
    
    if permit_1138:
        result_html = f"""
        <div class="details success-box">
            <h2>✅ 成功爬取序號 1138</h2>
            <table>
                <tr><td>建照號碼：</td><td>{permit_1138.get('permitNumber', '')}</td></tr>
                <tr><td>申請人：</td><td>{permit_1138.get('applicantName', '')}</td></tr>
                <tr><td>地址：</td><td>{permit_1138.get('siteAddress', '')}</td></tr>
                <tr><td>行政區：</td><td>{permit_1138.get('district', '')}</td></tr>
                <tr><td>樓層資訊：</td><td>{permit_1138.get('floorInfo', '')}</td></tr>
                <tr><td>總樓地板面積：</td><td>{permit_1138.get('totalFloorArea', '')} ㎡</td></tr>
                <tr><td>發照日期：</td><td>{permit_1138.get('issueDate', '')}</td></tr>
            </table>
        </div>"""
        success = True
    else:
        result_html = """
        <div class="details error-box">
            <h2>❌ 未找到序號 1138</h2>
            <p>Cron Job 執行了，但未能成功爬取資料</p>
        </div>"""
        success = False
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>8:30 Cron Job 測試結果</title>
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
        .details {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .success-box {{
            background: #e8f5e9;
            border: 1px solid #4caf50;
        }}
        .error-box {{
            background: #ffebee;
            border: 1px solid #f44336;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        td:first-child {{
            font-weight: bold;
            width: 150px;
        }}
        .success {{
            color: #2e7d32;
            font-weight: bold;
        }}
        .error {{
            color: #f44336;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 8:30 Cron Job 測試結果</h1>
        
        <div class="info">
            <div class="time">執行時間: {current_time}</div>
            <p style="text-align: center;">Cron Job 已在預定時間成功執行</p>
        </div>
        
        {result_html}
        
        <div class="details">
            <h2>執行詳情</h2>
            <ul>
                <li>腳本名稱: test_830.py</li>
                <li>執行環境: OCI Compute Instance (Ubuntu 22.04)</li>
                <li>Instance IP: 158.101.158.202</li>
                <li>執行方式: Cron Job (30 8 * * *)</li>
                <li>目標序號: 1138 (114中都建字第01138號)</li>
            </ul>
        </div>
        
        <div class="details">
            <h2>系統狀態</h2>
            <p class="success">✅ Instance Principal 認證正常</p>
            <p class="success">✅ OCI Object Storage 連線正常</p>
            <p class="{'success' if success else 'error'}">{'✅' if success else '❌'} 爬蟲執行{'成功' if success else '失敗'}</p>
        </div>
    </div>
</body>
</html>"""
    
    # 寫入結果頁面
    if storage.put_object('test/830-result.html', html_content):
        logger.info("✅ 結果頁面已寫入 OCI")
        print(f"\n✅ 測試執行完成！")
        print(f"執行時間: {current_time}")
        print(f"結果頁面: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/{NAMESPACE}/b/{BUCKET_NAME}/o/test/830-result.html")
        return success
    else:
        logger.error("結果頁面寫入失敗")
        return False

def main():
    """主程式"""
    logger.info("開始執行 8:30 測試")
    
    # 先嘗試爬取
    crawl_success = crawl_1138()
    
    # 等待一下讓資料寫入
    import time
    time.sleep(2)
    
    # 建立結果頁面
    page_success = create_result_page()
    
    if crawl_success and page_success:
        logger.info("✅ 所有任務成功完成")
    else:
        logger.error("❌ 有任務執行失敗")

if __name__ == "__main__":
    main()