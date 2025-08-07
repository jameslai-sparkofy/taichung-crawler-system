#!/usr/bin/env python3
"""
部署並執行 OCI Functions 爬蟲
"""

import oci
import base64
import json
import time
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCIFunctionDeployer:
    def __init__(self):
        # OCI 設定
        self.config = {}
        self.compartment_id = "ocid1.compartment.oc1..aaaaaaaallw7iqx2tijiqo3uu54o6skmhukqah2jvtmqyqogwj36a5wdz5q"
        self.application_name = "taichung-building-crawler"
        self.function_name = "taichung-crawler"
        
        # 初始化 OCI 客戶端
        self.functions_client = oci.functions.FunctionsManagementClient(self.config)
        self.functions_invoke_client = oci.functions.FunctionsInvokeClient(self.config)
        
    def get_application(self):
        """取得應用程式"""
        try:
            list_apps = self.functions_client.list_applications(
                compartment_id=self.compartment_id,
                display_name=self.application_name
            )
            
            if list_apps.data:
                app = list_apps.data[0]
                logger.info(f"✅ 找到應用程式: {app.display_name} (ID: {app.id})")
                return app
            else:
                logger.error("❌ 找不到應用程式")
                return None
                
        except Exception as e:
            logger.error(f"❌ 取得應用程式失敗: {e}")
            return None
            
    def update_function_code(self, function_id):
        """更新函數程式碼"""
        try:
            # 讀取函數程式碼
            with open("taichung-crawler-function/func.py", "r", encoding="utf-8") as f:
                code = f.read()
            
            # 將程式碼轉換為 base64
            code_base64 = base64.b64encode(code.encode()).decode()
            
            # 更新函數
            update_details = oci.functions.models.UpdateFunctionDetails(
                code=code_base64
            )
            
            self.functions_client.update_function(
                function_id=function_id,
                update_function_details=update_details
            )
            
            logger.info("✅ 函數程式碼已更新")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新函數程式碼失敗: {e}")
            return False
            
    def get_function(self, app_id):
        """取得函數"""
        try:
            list_functions = self.functions_client.list_functions(
                application_id=app_id,
                display_name=self.function_name
            )
            
            if list_functions.data:
                function = list_functions.data[0]
                logger.info(f"✅ 找到函數: {function.display_name} (ID: {function.id})")
                return function
            else:
                logger.error("❌ 找不到函數")
                return None
                
        except Exception as e:
            logger.error(f"❌ 取得函數失敗: {e}")
            return None
            
    def invoke_function(self, function_id):
        """調用函數"""
        try:
            logger.info("🚀 開始調用函數...")
            
            # 設定函數端點
            endpoint = f"https://functions.ap-tokyo-1.oraclecloud.com"
            self.functions_invoke_client.base_client.set_region("ap-tokyo-1")
            
            # 調用函數
            response = self.functions_invoke_client.invoke_function(
                function_id=function_id,
                invoke_function_body=b'{}'
            )
            
            # 處理回應
            if response.status == 200:
                result = json.loads(response.data.text)
                logger.info(f"✅ 函數執行成功!")
                logger.info(f"結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                logger.error(f"❌ 函數執行失敗: HTTP {response.status}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 調用函數失敗: {e}")
            return None
            
    def run(self):
        """執行部署和調用"""
        logger.info("🏗️ 開始部署並執行台中市建照爬蟲")
        logger.info("=" * 50)
        
        # 取得應用程式
        app = self.get_application()
        if not app:
            return
            
        # 取得函數
        function = self.get_function(app.id)
        if not function:
            return
            
        # 更新函數程式碼
        # logger.info("\n📝 更新函數程式碼...")
        # if not self.update_function_code(function.id):
        #     return
            
        # 等待函數準備好
        # logger.info("⏳ 等待函數更新完成...")
        # time.sleep(10)
        
        # 調用函數
        logger.info("\n🔥 調用函數執行爬蟲...")
        result = self.invoke_function(function.id)
        
        if result and result.get("success"):
            logger.info("\n🎉 爬蟲執行完成!")
            logger.info(f"   總爬取數: {result.get('totalCrawled', 0)}")
            logger.info(f"   新增記錄: {result.get('newRecords', 0)}")
            logger.info(f"   錯誤記錄: {result.get('errorRecords', 0)}")
            logger.info(f"   執行時間: {result.get('executionTime', 0):.1f} 秒")
            logger.info("\n📊 資料已更新到 OCI Object Storage")
            logger.info("🌐 網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html")
        else:
            logger.error("\n❌ 爬蟲執行失敗")

if __name__ == "__main__":
    deployer = OCIFunctionDeployer()
    deployer.run()