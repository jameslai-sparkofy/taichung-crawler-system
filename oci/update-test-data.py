#!/usr/bin/env python3
"""
直接更新Object Storage中的測試資料
添加更多真實的建照資料樣本
"""

import json
from datetime import datetime, timedelta

def generate_realistic_permits():
    """生成更真實的建照資料"""
    
    base_date = datetime.now()
    permits = []
    
    # 一些知名的台中建設公司和建築師
    companies = [
        "豐邑建設股份有限公司", "精銳建設股份有限公司", "遠雄建設股份有限公司",
        "國泰建設股份有限公司", "興富發建設股份有限公司", "達麗建設股份有限公司",
        "總太地產開發股份有限公司", "麗寶建設股份有限公司", "久樘開發股份有限公司",
        "聯聚建設開發股份有限公司", "惠宇建設股份有限公司", "寶輝建設股份有限公司"
    ]
    
    architects = [
        "李祖原建築師事務所", "潘冀聯合建築師事務所", "陳邁建築師事務所",
        "姚仁喜大元建築工場", "張樞建築師事務所", "郭英釗建築師事務所",
        "呂建興建築師事務所", "林洲民建築師事務所", "劉培森建築師事務所"
    ]
    
    contractors = [
        "大陸工程股份有限公司", "根基營造股份有限公司", "潤弘精密工程股份有限公司",
        "皇昌營造股份有限公司", "宏國關係事業", "達欣工程股份有限公司",
        "互助營造股份有限公司", "中華工程股份有限公司", "新亞建設開發股份有限公司"
    ]
    
    areas = [
        "西屯區", "南屯區", "北屯區", "西區", "南區", "北區", 
        "東區", "中區", "太平區", "大里區", "烏日區", "豐原區"
    ]
    
    zones = [
        "第二種住宅區", "第三種住宅區", "第二種商業區", "第三種商業區",
        "第一種商業區", "工業區", "特定專用區", "農業區"
    ]
    
    # 生成30筆建照資料
    for i in range(1, 31):
        crawl_time = base_date - timedelta(minutes=i*5)
        
        permit = {
            "indexKey": f"1141{i:05d}00",
            "permitNumber": f"114中建字第{i:05d}號",
            "permitYear": 114,
            "permitType": 1,
            "sequenceNumber": i,
            "versionNumber": 0,
            "applicantName": companies[i % len(companies)],
            "designerName": f"{['王', '李', '陳', '林', '張', '劉', '黃', '吳', '蔡', '楊'][i % 10]}建築師",
            "designerCompany": architects[i % len(architects)],
            "supervisorName": f"{['王', '李', '陳', '林', '張', '劉', '黃', '吳', '蔡', '楊'][(i+1) % 10]}建築師",
            "supervisorCompany": architects[(i+1) % len(architects)],
            "contractorName": f"{['王', '李', '陳', '林', '張', '劉', '黃', '吳', '蔡', '楊'][(i+2) % 10]}營造",
            "contractorCompany": contractors[i % len(contractors)],
            "engineerName": f"{['王', '李', '陳', '林', '張', '劉', '黃', '吳', '蔡', '楊'][(i+3) % 10]}工程師",
            "siteAddress": f"台中市{areas[i % len(areas)]}{['福成', '逢甲', '田心', '松竹', '向上', '忠明', '健行', '東光', '成功', '頭汴'][i % 10]}段{100+i}-{i%10+1}地號",
            "siteCity": "台中市",
            "siteZone": zones[i % len(zones)],
            "siteArea": round(150 + (i * 15.7) + (i % 7) * 50, 1),
            "crawledAt": crawl_time.isoformat()
        }
        
        permits.append(permit)
    
    return permits

def generate_realistic_logs():
    """生成真實的爬取記錄"""
    
    base_date = datetime.now()
    logs = []
    
    # 生成最近10天的記錄
    for i in range(10):
        log_date = (base_date - timedelta(days=i)).date()
        start_time = datetime.combine(log_date, datetime.min.time().replace(hour=8))
        
        # 模擬不同的執行結果
        total_crawled = 15 + (i % 5) * 3
        new_records = max(0, total_crawled - (i % 3) * 2)
        error_records = total_crawled - new_records
        
        end_time = start_time + timedelta(minutes=5 + i%3, seconds=30 + i*5)
        
        log_entry = {
            "date": log_date.isoformat(),
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "totalCrawled": total_crawled,
            "newRecords": new_records,
            "errorRecords": error_records,
            "status": "completed" if error_records <= 2 else "failed" if i == 3 else "completed"
        }
        
        logs.append(log_entry)
    
    return logs

def create_updated_data():
    """建立更新的資料檔案"""
    
    print("🚀 生成真實的建照測試資料...")
    
    # 生成建照資料
    permits = generate_realistic_permits()
    permits_data = {
        "lastUpdate": datetime.now().isoformat(),
        "totalCount": len(permits),
        "permits": permits
    }
    
    # 生成執行記錄
    logs = generate_realistic_logs()
    logs_data = {
        "logs": logs
    }
    
    # 儲存到檔案
    with open('permits-updated.json', 'w', encoding='utf-8') as f:
        json.dump(permits_data, f, ensure_ascii=False, indent=2)
    
    with open('crawl-logs-updated.json', 'w', encoding='utf-8') as f:
        json.dump(logs_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已生成 {len(permits)} 筆建照資料")
    print(f"✅ 已生成 {len(logs)} 筆執行記錄")
    
    return permits_data, logs_data

if __name__ == "__main__":
    print("📊 建立真實的建照測試資料")
    print("="*50)
    
    permits_data, logs_data = create_updated_data()
    
    print("\n📋 資料摘要:")
    print(f"建照資料: {permits_data['totalCount']} 筆")
    print(f"最後更新: {permits_data['lastUpdate']}")
    print(f"執行記錄: {len(logs_data['logs'])} 天")
    
    print("\n📄 最新建照範例:")
    latest_permit = permits_data['permits'][0]
    print(f"  建照號碼: {latest_permit['permitNumber']}")
    print(f"  起造人: {latest_permit['applicantName']}")
    print(f"  基地地址: {latest_permit['siteAddress']}")
    print(f"  基地面積: {latest_permit['siteArea']} m²")
    
    print("\n🎉 測試資料準備完成！")