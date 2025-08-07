#!/usr/bin/env python3
"""
改進版每日更新爬蟲
1. 記錄最後成功的ID
2. 從上次位置繼續
3. 遇到連續空白時停止
"""

import subprocess
import json
import re
from datetime import datetime
import time
import sys
import tempfile
import os

def log(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_last_update_info():
    """取得最後更新資訊"""
    try:
        cmd = ["oci", "os", "object", "get", 
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "logs/last-update-info.json",
               "--file", "/tmp/last-update-info.json"]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            with open('/tmp/last-update-info.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # 預設值
    current_year = datetime.now().year - 1911
    return {
        "last_successful_id": f"{current_year}1{9999:05d}00",
        "last_update_time": datetime.now().isoformat(),
        "year": current_year,
        "sequence": 9999
    }

def save_update_info(info):
    """儲存更新資訊"""
    try:
        with open('/tmp/update-info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        cmd = ["oci", "os", "object", "put",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "logs/last-update-info.json",
               "--file", "/tmp/update-info.json",
               "--content-type", "application/json",
               "--force"]
        subprocess.run(cmd, capture_output=True)
        log(f"✅ 已更新最後成功ID: {info['last_successful_id']}")
    except Exception as e:
        log(f"❌ 儲存更新資訊失敗: {e}")

def download_permits():
    """下載現有的permits.json"""
    try:
        cmd = ["oci", "os", "object", "get",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "permits.json",
               "--file", "/tmp/permits.json"]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            with open('/tmp/permits.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def upload_permits(permits):
    """上傳permits.json到OCI"""
    try:
        with open('/tmp/permits.json', 'w', encoding='utf-8') as f:
            json.dump(permits, f, ensure_ascii=False, indent=2)
        
        cmd = ["oci", "os", "object", "put",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "permits.json",
               "--file", "/tmp/permits.json",
               "--content-type", "application/json",
               "--force"]
        subprocess.run(cmd, capture_output=True)
        return True
    except:
        return False

def save_html_to_oci(index_key, html_content):
    """儲存HTML到OCI"""
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.html', delete=False) as f:
        f.write(html_content)
        temp_file = f.name
    
    try:
        cmd = ["oci", "os", "object", "put",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", f"html/{index_key}.html",
               "--file", temp_file,
               "--content-type", "text/html; charset=utf-8",
               "--force"]
        subprocess.run(cmd, capture_output=True)
    finally:
        os.unlink(temp_file)

def crawl_permit(index_key):
    """爬取單一建照資料"""
    url = f"https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do?INDEX_KEY={index_key}"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        temp_file = f.name
    
    try:
        # 兩次訪問策略
        cmd1 = ["curl", "-s", "-c", "/tmp/cookie.txt", url, "-o", temp_file]
        subprocess.run(cmd1, capture_output=True)
        time.sleep(3)
        
        cmd2 = ["curl", "-s", "-b", "/tmp/cookie.txt", url, "-o", temp_file]
        result = subprocess.run(cmd2, capture_output=True)
        
        with open(temp_file, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # 儲存HTML
        save_html_to_oci(index_key, html)
        
        # 檢查是否有建照資料
        permit_patterns = [
            r'<span class="conlist w20 tc">([1-9]\d{0,2}中[都市建]?建字第\d+號)</span>',
        ]
        
        permit_match = None
        for pattern in permit_patterns:
            permit_match = re.search(pattern, html)
            if permit_match:
                break
        
        if permit_match:
            # 解析其他欄位
            applicant_match = re.search(r'<td class="conlisT_td1" style="width:30%">\s*<span class="conlist wAUTO tl">(.*?)</span>', html)
            
            permit_data = {
                "indexKey": index_key,
                "permitNumber": permit_match.group(1),
                "applicant": applicant_match.group(1).strip() if applicant_match else "",
                "crawlTime": datetime.now().isoformat()
            }
            
            # 解析其他欄位（行政區、戶數、樓層等）
            area_match = re.search(r'<td class="conlisT_td1" style="width:15%">\s*<span class="conlist wAUTO tl">\s*([\u4e00-\u9fa5]+區)', html)
            if area_match:
                permit_data["administrativeArea"] = area_match.group(1)
            
            return permit_data
        else:
            # 檢查是否為真正的空資料
            if "查無資料" in html or len(html) < 1000:
                return None
            # 如果有內容但沒匹配到，可能是解析問題
            return False
    
    except Exception as e:
        log(f"爬取錯誤 {index_key}: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def save_execution_log(start_time, end_time, new_count, last_id):
    """儲存執行記錄"""
    try:
        # 下載現有記錄
        existing_logs = []
        try:
            cmd = ["oci", "os", "object", "get",
                   "--namespace", "nrsdi1rz5vl8",
                   "--bucket-name", "taichung-building-permits",
                   "--name", "logs/execution-history.json",
                   "--file", "/tmp/exec-history.json"]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                with open('/tmp/exec-history.json', 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
        except:
            pass
        
        # 新增記錄
        new_log = {
            "timestamp": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "new_permits_count": new_count,
            "last_successful_id": last_id,
            "status": "completed"
        }
        
        existing_logs.append(new_log)
        
        # 只保留最新50筆記錄
        existing_logs = existing_logs[-50:]
        
        # 上傳記錄
        with open('/tmp/exec-history.json', 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, ensure_ascii=False, indent=2)
        
        cmd = ["oci", "os", "object", "put",
               "--namespace", "nrsdi1rz5vl8",
               "--bucket-name", "taichung-building-permits",
               "--name", "logs/execution-history.json",
               "--file", "/tmp/exec-history.json",
               "--content-type", "application/json",
               "--force"]
        subprocess.run(cmd, capture_output=True)
        
        log(f"✅ 執行記錄已儲存")
    except Exception as e:
        log(f"❌ 儲存執行記錄失敗: {e}")

def main():
    start_time = datetime.now()
    log("🚀 開始執行改進版每日建照更新")
    
    # 取得最後更新資訊
    last_info = get_last_update_info()
    log(f"📍 從上次位置繼續: {last_info['last_successful_id']}")
    
    # 載入現有資料
    permits = download_permits()
    log(f"📂 載入 {len(permits)} 筆現有資料")
    
    # 建立已存在的索引集合
    existing_keys = {p.get('indexKey') for p in permits if isinstance(p, dict)}
    
    # 解析起始位置
    year = last_info['year']
    start_seq = last_info['sequence'] + 1  # 從下一個序號開始
    permit_type = 1
    
    new_count = 0
    consecutive_empty = 0  # 連續空白計數
    max_consecutive_empty = 10  # 連續10個空白就停止
    max_crawl = 200  # 每次最多爬200筆
    last_successful_id = last_info['last_successful_id']
    
    log(f"🎯 開始從 {year}{permit_type}{start_seq:05d}00 爬取")
    
    for seq in range(start_seq, start_seq + max_crawl):
        if new_count >= max_crawl:
            break
            
        index_key = f"{year}{permit_type}{seq:05d}00"
        
        # 檢查是否已存在
        if index_key in existing_keys:
            log(f"⏩ 跳過已存在: {index_key}")
            consecutive_empty = 0  # 重設空白計數
            continue
        
        log(f"🔍 爬取 {index_key}...", end=" ")
        
        permit_data = crawl_permit(index_key)
        
        if permit_data:
            permits.append(permit_data)
            new_count += 1
            consecutive_empty = 0  # 重設空白計數
            last_successful_id = index_key
            print(f"✅ {permit_data['permitNumber']}")
            
            # 每10筆儲存一次
            if new_count % 10 == 0:
                upload_permits(permits)
                save_update_info({
                    "last_successful_id": last_successful_id,
                    "last_update_time": datetime.now().isoformat(),
                    "year": year,
                    "sequence": seq
                })
                log(f"💾 已儲存 {new_count} 筆新資料")
        
        elif permit_data is None:
            # 空資料
            consecutive_empty += 1
            print(f"❌ 空資料 (連續{consecutive_empty}個)")
            
            if consecutive_empty >= max_consecutive_empty:
                log(f"🛑 連續 {consecutive_empty} 個空資料，停止爬取")
                break
        else:
            # 爬取失敗
            print("❌ 失敗")
        
        time.sleep(1)  # 短暫延遲
    
    # 最終儲存
    if new_count > 0:
        upload_permits(permits)
        save_update_info({
            "last_successful_id": last_successful_id,
            "last_update_time": datetime.now().isoformat(),
            "year": year,
            "sequence": seq
        })
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 儲存執行記錄
    save_execution_log(start_time, end_time, new_count, last_successful_id)
    
    log(f"✅ 更新完成！")
    log(f"📊 新增 {new_count} 筆資料")
    log(f"⏱️  執行時間: {duration.total_seconds():.1f} 秒")
    log(f"📍 最後成功ID: {last_successful_id}")

if __name__ == "__main__":
    main()