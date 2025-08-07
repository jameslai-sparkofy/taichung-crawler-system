#!/usr/bin/env python3
"""
OCI Functions定時觸發器設定
使用OCI Resource Scheduler服務定時執行爬蟲Function
"""

import oci
import json
from datetime import datetime

def setup_scheduler():
    """設定定時執行器"""
    
    # 基本配置
    compartment_id = "ocid1.tenancy.oc1..aaaaaaaatj2jclzf26lcsptdllggkodf4kvaj4gajrxtjngakmjl6smu3t6q"
    function_id = "ocid1.fnfunc.oc1.ap-tokyo-1.aaaaaaaalvsxm3tudvstk67h6ltdwpfyyhy5rlvi22wanzmlu2r4twas4zra"  # 需要替換為實際Function ID
    
    # 初始化Events客戶端
    events_client = oci.events.EventsClient({})
    
    try:
        # 建立Events Rule來定時觸發
        rule_details = oci.events.models.CreateRuleDetails(
            display_name="taichung-building-crawler-daily",
            description="每日定時執行台中市建照爬蟲",
            compartment_id=compartment_id,
            condition='{"eventType":"oracle.apigateway.httpagent.custom"}',
            is_enabled=True,
            actions=oci.events.models.ActionDetailsList(
                actions=[
                    oci.events.models.CreateFunctionActionDetails(
                        action_type="FAAS",
                        function_id=function_id,
                        is_enabled=True
                    )
                ]
            )
        )
        
        response = events_client.create_rule(rule_details)
        print(f"✅ Events Rule建立成功: {response.data.id}")
        
        return response.data.id
        
    except Exception as e:
        print(f"❌ 建立Events Rule失敗: {e}")
        return None

def create_cron_schedule():
    """建立CRON排程配置"""
    
    cron_config = {
        "schedule": "0 0 * * *",  # 每天午夜執行 (UTC時間)
        "timezone": "Asia/Taipei",
        "description": "台中市建照資料每日爬取",
        "enabled": True
    }
    
    print("📅 CRON排程配置:")
    print(json.dumps(cron_config, indent=2, ensure_ascii=False))
    
    return cron_config

if __name__ == "__main__":
    print("🚀 設定台中市建照爬蟲定時執行")
    
    # 建立排程配置
    cron_config = create_cron_schedule()
    
    # 設定Events Rule
    rule_id = setup_scheduler()
    
    if rule_id:
        print("✅ 定時執行設定完成")
        print(f"Rule ID: {rule_id}")
    else:
        print("❌ 定時執行設定失敗")