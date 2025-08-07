#!/usr/bin/env python3
"""
將現有的測試資料上傳到OCI Object Storage
並生成112-114年的範例資料
"""

import json
import oci
from datetime import datetime
import random

def generate_permits_112_114():
    """生成112-114年的建照資料"""
    permits = []
    
    # 知名建設公司
    companies = [
        "豐邑建設股份有限公司", "精銳建設股份有限公司", "遠雄建設股份有限公司",
        "國泰建設股份有限公司", "興富發建設股份有限公司", "達麗建設股份有限公司",
        "總太地產開發股份有限公司", "麗寶建設股份有限公司", "久樘開發股份有限公司",
        "聯聚建設開發股份有限公司", "惠宇建設股份有限公司", "寶輝建設股份有限公司"
    ]
    
    architects = [
        "李祖原建築師事務所", "潘冀聯合建築師事務所", "陳邁建築師事務所",
        "姚仁喜大元建築工場", "張樞建築師事務所", "郭英釗建築師事務所"
    ]
    
    contractors = [
        "大陸工程股份有限公司", "根基營造股份有限公司", "潤弘精密工程股份有限公司",
        "皇昌營造股份有限公司", "宏國關係事業", "達欣工程股份有限公司"
    ]
    
    areas = [
        "西屯區", "南屯區", "北屯區", "西區", "南區", "北區", 
        "東區", "中區", "太平區", "大里區", "烏日區", "豐原區"
    ]
    
    zones = [
        "第二種住宅區", "第三種住宅區", "第二種商業區", "第三種商業區",
        "第一種商業區", "工業區", "特定專用區", "農業區"
    ]
    
    # 生成112年資料（20筆）
    seq_112 = 1000
    for i in range(20):
        permit = {
            "indexKey": f"1121{seq_112+i:05d}00",
            "permitNumber": f"112中都建字第{seq_112+i:05d}號",
            "permitYear": 112,
            "permitType": 1,
            "sequenceNumber": seq_112 + i,
            "versionNumber": 0,
            "applicantName": companies[i % len(companies)],
            "designerName": f"{['王', '李', '陳', '林', '張'][i % 5]}建築師",
            "designerCompany": architects[i % len(architects)],
            "supervisorName": f"{['劉', '黃', '吳', '蔡', '楊'][(i+1) % 5]}建築師",
            "supervisorCompany": architects[(i+1) % len(architects)],
            "contractorName": f"{['王', '李', '陳', '林', '張'][(i+2) % 5]}營造",
            "contractorCompany": contractors[i % len(contractors)],
            "engineerName": f"{['劉', '黃', '吳', '蔡', '楊'][(i+3) % 5]}工程師",
            "siteAddress": f"台中市{areas[i % len(areas)]}{['文心', '中清', '崇德', '五權', '公益'][i % 5]}段{100+i}-{i%10+1}地號",
            "siteCity": "台中市",
            "siteZone": zones[i % len(zones)],
            "siteArea": round(500 + (i * 50.5) + random.uniform(-100, 200), 1),
            "floorCount": random.choice([5, 7, 10, 12, 15, 20]) if i % 3 == 0 else random.choice([3, 4, 5, 6]),
            "crawledAt": datetime.now().isoformat()
        }
        permits.append(permit)
    
    # 生成113年資料（30筆）
    seq_113 = 500
    for i in range(30):
        permit = {
            "indexKey": f"1131{seq_113+i*10:05d}00",
            "permitNumber": f"113中都建字第{seq_113+i*10:05d}號",
            "permitYear": 113,
            "permitType": 1,
            "sequenceNumber": seq_113 + i*10,
            "versionNumber": 0,
            "applicantName": companies[(i+5) % len(companies)],
            "designerName": f"{['趙', '錢', '孫', '李', '周'][i % 5]}建築師",
            "designerCompany": architects[(i+2) % len(architects)],
            "supervisorName": f"{['吳', '鄭', '王', '馮', '陳'][i % 5]}建築師",
            "supervisorCompany": architects[(i+3) % len(architects)],
            "contractorName": f"{['衛', '蔣', '沈', '韓', '楊'][i % 5]}營造",
            "contractorCompany": contractors[(i+1) % len(contractors)],
            "engineerName": f"{['朱', '秦', '尤', '許', '何'][i % 5]}工程師",
            "siteAddress": f"台中市{areas[(i+3) % len(areas)]}{['黎明', '市政', '河南', '大墩', '惠中'][i % 5]}段{200+i*5}-{i%5+1}地號",
            "siteCity": "台中市",
            "siteZone": zones[(i+1) % len(zones)],
            "siteArea": round(800 + (i * 75.3) + random.uniform(-200, 300), 1),
            "floorCount": random.choice([8, 10, 12, 15, 18, 25]) if i % 2 == 0 else random.choice([5, 6, 7, 8]),
            "crawledAt": datetime.now().isoformat()
        }
        permits.append(permit)
    
    # 生成114年資料（50筆）
    seq_114 = 100
    for i in range(50):
        permit = {
            "indexKey": f"1141{seq_114+i*5:05d}00",
            "permitNumber": f"114中都建字第{seq_114+i*5:05d}號",
            "permitYear": 114,
            "permitType": 1,
            "sequenceNumber": seq_114 + i*5,
            "versionNumber": 0,
            "applicantName": companies[(i+8) % len(companies)],
            "designerName": f"{['馮', '陳', '褚', '衛', '蔣'][i % 5]}建築師",
            "designerCompany": architects[(i+4) % len(architects)],
            "supervisorName": f"{['沈', '韓', '楊', '朱', '秦'][i % 5]}建築師",
            "supervisorCompany": architects[(i+5) % len(architects)],
            "contractorName": f"{['尤', '許', '何', '呂', '施'][i % 5]}營造",
            "contractorCompany": contractors[(i+2) % len(contractors)],
            "engineerName": f"{['張', '孔', '曹', '嚴', '華'][i % 5]}工程師",
            "siteAddress": f"台中市{areas[(i+6) % len(areas)]}{['環中', '台灣', '中山', '自由', '民權'][i % 5]}段{300+i*3}-{i%8+1}地號",
            "siteCity": "台中市",
            "siteZone": zones[(i+2) % len(zones)],
            "siteArea": round(1200 + (i * 95.7) + random.uniform(-300, 500), 1),
            "floorCount": random.choice([10, 12, 15, 20, 25, 30]) if i % 4 < 2 else random.choice([5, 7, 8, 9]),
            "crawledAt": datetime.now().isoformat()
        }
        permits.append(permit)
    
    return permits

def upload_to_oci():
    """上傳資料到OCI"""
    try:
        # 初始化OCI客戶端
        client = oci.object_storage.ObjectStorageClient({})
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        print("✅ OCI客戶端初始化成功")
        
        # 生成資料
        permits = generate_permits_112_114()
        
        # 建立完整資料
        data = {
            "lastUpdate": datetime.now().isoformat(),
            "totalCount": len(permits),
            "yearCounts": {
                112: len([p for p in permits if p["permitYear"] == 112]),
                113: len([p for p in permits if p["permitYear"] == 113]),
                114: len([p for p in permits if p["permitYear"] == 114])
            },
            "permits": permits
        }
        
        # 上傳建照資料
        print("📤 上傳建照資料...")
        content = json.dumps(data, ensure_ascii=False, indent=2)
        
        client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name="data/permits.json",
            put_object_body=content.encode('utf-8'),
            content_type="application/json"
        )
        
        print(f"✅ 已上傳 {len(permits)} 筆建照資料")
        print(f"   112年: {data['yearCounts'][112]} 筆")
        print(f"   113年: {data['yearCounts'][113]} 筆")
        print(f"   114年: {data['yearCounts'][114]} 筆")
        
        # 生成爬取記錄
        logs = []
        for i in range(10):
            log_date = datetime.now()
            log_date = log_date.replace(day=log_date.day - i)
            
            log = {
                "date": log_date.date().isoformat(),
                "startTime": log_date.replace(hour=8, minute=0).isoformat(),
                "endTime": log_date.replace(hour=8, minute=15).isoformat(),
                "totalCrawled": 20 + (i % 5) * 5,
                "newRecords": 15 + (i % 3) * 3,
                "errorRecords": i % 3,
                "status": "completed",
                "yearStats": {
                    "112": {"crawled": 5, "new": 3, "errors": 0},
                    "113": {"crawled": 8, "new": 6, "errors": 1},
                    "114": {"crawled": 7 + (i % 3), "new": 6 + (i % 2), "errors": i % 2}
                }
            }
            logs.append(log)
        
        # 上傳記錄
        print("\n📤 上傳執行記錄...")
        log_data = {"logs": logs}
        log_content = json.dumps(log_data, ensure_ascii=False, indent=2)
        
        client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name="data/crawl-logs.json",
            put_object_body=log_content.encode('utf-8'),
            content_type="application/json"
        )
        
        print("✅ 已上傳執行記錄")
        
        # 確認已上傳
        print("\n📋 已上傳的檔案:")
        objects = client.list_objects(namespace, bucket_name, prefix="data/")
        for obj in objects.data.objects:
            print(f"   - {obj.name} ({obj.size} bytes)")
        
        print("\n🎉 資料上傳完成！")
        print(f"監控網頁: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/{namespace}/b/{bucket_name}/o/index-new.html")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    print("🚀 上傳112-114年建照資料到OCI")
    print("=" * 50)
    
    upload_to_oci()