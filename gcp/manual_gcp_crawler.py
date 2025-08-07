#!/usr/bin/env python3
"""
Google Cloud 手動爬蟲程式
可在本地執行，資料會儲存到 Google Cloud Storage
"""
import os
import json
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import subprocess
import re

# 設定
BUCKET_NAME = "taichung-crawler-permits"
LOCAL_DATA_FILE = "permits.json"

def check_taiwan_ip():
    """檢查是否為台灣 IP"""
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        data = response.json()
        country = data.get('country', 'Unknown')
        ip = data.get('ip', 'Unknown')
        print(f"📍 目前 IP: {ip} ({country})")
        return country == 'TW'
    except:
        return False

def upload_to_gcs(file_path, gcs_path):
    """上傳檔案到 Google Cloud Storage"""
    try:
        cmd = f"gsutil cp {file_path} gs://{BUCKET_NAME}/{gcs_path}"
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ 已上傳到 GCS: {gcs_path}")
        return True
    except Exception as e:
        print(f"❌ 上傳失敗: {e}")
        print("   請確認已安裝 gsutil 並登入 Google Cloud")
        return False

def download_from_gcs(gcs_path, local_path):
    """從 Google Cloud Storage 下載檔案"""
    try:
        cmd = f"gsutil cp gs://{BUCKET_NAME}/{gcs_path} {local_path}"
        subprocess.run(cmd, shell=True, check=True)
        return True
    except:
        print(f"⚠️  無法下載 {gcs_path}，將使用新檔案")
        return False

def crawl_single_permit(year, seq):
    """爬取單筆建照資料"""
    index_key = f"{year}10{seq:05d}00"
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 檢查是否為空白頁面
        if "查無此案件編號資料" in response.text or len(response.text) < 1000:
            return "BLANK"
        
        # 解析建照資料
        permit_data = {
            'indexKey': index_key,
            'year': year,
            'sequence': seq,
            'crawlTime': datetime.now().isoformat()
        }
        
        # 解析各欄位
        fields = soup.find_all('td', class_='tit_intd2 w15')
        for field in fields:
            label = field.text.strip()
            value_elem = field.find_next_sibling('td')
            if value_elem:
                value = value_elem.text.strip()
                
                if '建照號碼' in label:
                    permit_data['permitNumber'] = value
                elif '申請人' in label:
                    permit_data['applicant'] = value
                elif '地址' in label:
                    permit_data['address'] = value
                elif '建築物概要' in label:
                    # 解析樓層、棟數、戶數
                    floor_info = value
                    permit_data['buildingSummary'] = floor_info
                    
                    floor_match = re.search(r'地上(\d+)層', floor_info)
                    if floor_match:
                        permit_data['floors'] = int(floor_match.group(1))
                    
                    building_match = re.search(r'(\d+)棟', floor_info)
                    if building_match:
                        permit_data['buildings'] = int(building_match.group(1))
                    
                    unit_match = re.search(r'(\d+)戶', floor_info)
                    if unit_match:
                        permit_data['units'] = int(unit_match.group(1))
        
        # 解析總樓地板面積
        area_match = re.search(r'總樓地板面積.*?<span class="conlist w50">([0-9.,]+)', response.text)
        if area_match:
            permit_data['totalFloorArea'] = float(area_match.group(1).replace(',', ''))
        
        # 解析發照日期
        date_match = re.search(r'發照日期.*?(\d{4})/(\d{2})/(\d{2})', response.text)
        if date_match:
            year_date = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            permit_data['issueDate'] = f"{year_date}-{month:02d}-{day:02d}"
        
        return permit_data
        
    except Exception as e:
        print(f"❌ 爬取失敗 {index_key}: {e}")
        return None

def main():
    """主程式"""
    print(f"🚀 Google Cloud 手動爬蟲開始: {datetime.now()}")
    
    # 檢查 IP
    if not check_taiwan_ip():
        print("⚠️  警告：目前不是台灣 IP，可能無法正常爬取")
        print("   建議使用 Google Cloud 台灣區域的實例執行")
    
    # 載入現有資料
    permits_data = []
    
    # 嘗試從 GCS 下載
    if download_from_gcs("permits.json", LOCAL_DATA_FILE):
        with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
            permits_data = json.load(f)
        print(f"📊 從 GCS 載入資料: {len(permits_data)} 筆")
    elif os.path.exists(LOCAL_DATA_FILE):
        # 使用本地檔案
        with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
            permits_data = json.load(f)
        print(f"📊 使用本地資料: {len(permits_data)} 筆")
    
    # 取得最新序號
    latest_seq = 0
    year_114_count = 0
    for permit in permits_data:
        if permit.get('year') == 114:
            year_114_count += 1
            seq = permit.get('sequence', 0)
            if seq > latest_seq:
                latest_seq = seq
    
    print(f"📊 114年資料: {year_114_count} 筆")
    print(f"📊 最新序號: {latest_seq}")
    
    # 詢問爬取範圍
    print("\n請選擇爬取模式:")
    print("1. 從最新序號開始爬取")
    print("2. 指定序號範圍")
    print("3. 只測試一筆")
    
    choice = input("請輸入選項 (1/2/3): ").strip()
    
    if choice == "1":
        start_seq = latest_seq + 1
        end_seq = start_seq + 50  # 預設爬50筆
    elif choice == "2":
        start_seq = int(input("起始序號: "))
        end_seq = int(input("結束序號: "))
    else:
        start_seq = latest_seq + 1
        end_seq = start_seq + 1
    
    # 開始爬取
    new_count = 0
    blank_count = 0
    error_count = 0
    
    print(f"\n開始爬取: {start_seq} ~ {end_seq}")
    
    for seq in range(start_seq, end_seq):
        print(f"\n🔍 [{seq - start_seq + 1}/{end_seq - start_seq}] 爬取: 114年 序號{seq}")
        
        result = crawl_single_permit(114, seq)
        
        if result == "BLANK":
            print("   ⚪ 空白資料")
            blank_count += 1
            if blank_count >= 5:  # 連續5筆空白就停止
                print("\n❌ 連續5筆空白資料，停止爬取")
                break
        elif result:
            # 檢查是否重複
            exists = any(p.get('indexKey') == result.get('indexKey') for p in permits_data)
            if not exists:
                permits_data.append(result)
                print(f"   ✅ 成功: {result.get('permitNumber', 'N/A')} - {result.get('applicant', 'N/A')}")
                new_count += 1
            else:
                print(f"   ⚠️  已存在: {result.get('permitNumber', 'N/A')}")
            blank_count = 0  # 重設空白計數
        else:
            print("   ❌ 失敗")
            error_count += 1
            if error_count >= 3:  # 連續3次錯誤就停止
                print("\n❌ 連續3次錯誤，停止爬取")
                break
        
        time.sleep(1.5)  # 延遲1.5秒
    
    # 儲存資料
    if new_count > 0:
        print(f"\n💾 儲存資料...")
        with open(LOCAL_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(permits_data, f, ensure_ascii=False, indent=2)
        
        # 上傳到 GCS
        upload_to_gcs(LOCAL_DATA_FILE, "permits.json")
        
        # 建立並上傳執行記錄
        log_data = {
            'executionTime': datetime.now().isoformat(),
            'newRecords': new_count,
            'totalRecords': len(permits_data),
            'latestSequence': latest_seq + new_count,
            'year114Count': sum(1 for p in permits_data if p.get('year') == 114)
        }
        
        log_file = f"logs/crawl_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open("crawl_log.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        upload_to_gcs("crawl_log.json", log_file)
    
    print(f"\n📊 執行統計:")
    print(f"   新增: {new_count} 筆")
    print(f"   總計: {len(permits_data)} 筆")
    print(f"   114年: {sum(1 for p in permits_data if p.get('year') == 114)} 筆")
    print(f"\n🚀 爬蟲執行完成: {datetime.now()}")

if __name__ == "__main__":
    main()