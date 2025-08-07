#!/usr/bin/env python3
"""
每日更新爬蟲 - 專門用於自動執行
只爬取最新的建照資料，避免重複
"""

import subprocess
import json
import re
from datetime import datetime
import time
import sys

def log(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    log("開始執行每日建照更新爬蟲")
    
    # 基本設定
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    namespace = "nrsdi1rz5vl8"
    bucket_name = "taichung-building-permits"
    
    # 載入現有資料
    log("載入現有資料...")
    permits = []
    try:
        cmd = ["oci", "os", "object", "get", "--namespace", namespace,
               "--bucket-name", bucket_name, "--name", "data/permits.json",
               "--file", "/tmp/existing.json"]
        subprocess.run(cmd, capture_output=True)
        
        with open('/tmp/existing.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            permits = data.get('permits', [])
            log(f"載入 {len(permits)} 筆現有資料")
    except Exception as e:
        log(f"載入資料失敗: {e}")
        return
    
    # 取得當前年份（民國年）
    current_year = datetime.now().year - 1911
    
    # 設定爬取參數
    new_count = 0
    max_crawl = 100  # 每次最多爬取100筆
    permit_type = 1
    
    log(f"開始爬取 {current_year} 年最新資料（最多 {max_crawl} 筆）")
    
    # 從大序號往回爬，確保爬到最新的
    for seq in range(9999, 0, -1):
        if new_count >= max_crawl:
            break
            
        index_key = f"{current_year}{permit_type}{seq:05d}00"
        
        # 檢查是否已存在
        if any(p.get('indexKey') == index_key for p in permits):
            continue
        
        # 爬取單筆
        try:
            # 清除 cookies
            subprocess.run(["rm", "-f", "/tmp/cookies.txt"], capture_output=True)
            
            # 第一次訪問
            cmd1 = ["wget", "-q", "--save-cookies=/tmp/cookies.txt", "--keep-session-cookies",
                    "--user-agent=Mozilla/5.0", "--timeout=20", "-O", "/tmp/first.html",
                    f"{base_url}?INDEX_KEY={index_key}"]
            subprocess.run(cmd1, capture_output=True)
            
            time.sleep(3)
            
            # 第二次訪問
            cmd2 = ["wget", "-q", "--load-cookies=/tmp/cookies.txt", "--save-cookies=/tmp/cookies.txt",
                    "--keep-session-cookies", "--user-agent=Mozilla/5.0", "--timeout=20",
                    "-O", f"/tmp/page_{index_key}.html", f"{base_url}?INDEX_KEY={index_key}"]
            result = subprocess.run(cmd2, capture_output=True)
            
            if result.returncode == 0:
                with open(f"/tmp/page_{index_key}.html", "rb") as f:
                    content = f.read()
                
                if len(content) > 1000:
                    # 解碼
                    try:
                        html = content.decode('big5')
                    except:
                        html = content.decode('utf-8', errors='ignore')
                    
                    # 檢查是否有建照資料
                    if "建造執照號碼" in html:
                        # 解析資料
                        permit_data = {
                            'indexKey': index_key,
                            'permitYear': current_year,
                            'permitType': permit_type,
                            'sequenceNumber': seq,
                            'versionNumber': 0,
                            'crawledAt': datetime.now().isoformat()
                        }
                        
                        # 建照號碼
                        m = re.search(r'<span class="conlist w20 tc">([1-9]\d{0,2}中[都市建]?建字第\d+號)</span>', html)
                        if m:
                            permit_data['permitNumber'] = m.group(1).strip()
                            
                            # 起造人
                            m = re.search(r'起造人.*?姓名.*?<span class="conlist w30">([^<]+)</span>', html, re.DOTALL)
                            if m:
                                permit_data['applicantName'] = m.group(1).strip()
                            
                            # 保存HTML
                            save_html(index_key, html, namespace, bucket_name)
                            
                            permits.append(permit_data)
                            new_count += 1
                            log(f"✅ 新增: {permit_data['permitNumber']} - {permit_data.get('applicantName', 'N/A')}")
                        
        except Exception as e:
            log(f"爬取失敗 {index_key}: {e}")
        
        time.sleep(2)
    
    # 儲存更新後的資料
    if new_count > 0:
        log(f"儲存 {new_count} 筆新資料...")
        
        # 排序
        sorted_permits = sorted(permits, key=lambda x: (
            -x.get('permitYear', 0),
            -x.get('sequenceNumber', 0)
        ))
        
        data = {
            "lastUpdate": datetime.now().isoformat(),
            "totalCount": len(sorted_permits),
            "yearCounts": {},
            "permits": sorted_permits
        }
        
        # 統計各年份
        for permit in sorted_permits:
            year = permit.get('permitYear', 0)
            if year not in data['yearCounts']:
                data['yearCounts'][year] = 0
            data['yearCounts'][year] += 1
        
        # 寫入檔案
        with open('/tmp/permits_updated.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 上傳到OCI
        cmd = ["oci", "os", "object", "put", "--namespace", namespace,
               "--bucket-name", bucket_name, "--name", "data/permits.json",
               "--file", "/tmp/permits_updated.json", "--content-type", "application/json",
               "--force"]
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            log(f"✅ 資料更新完成！總計 {len(sorted_permits)} 筆")
        else:
            log("❌ 資料上傳失敗")
    else:
        log("沒有發現新資料")
    
    # 記錄執行日誌
    save_log(new_count, namespace, bucket_name)
    
    log("每日更新爬蟲執行完成")

def save_html(index_key, html_content, namespace, bucket_name):
    """保存HTML到OCI"""
    try:
        temp_file = f"/tmp/html_{index_key}.html"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        cmd = ["oci", "os", "object", "put", "--namespace", namespace,
               "--bucket-name", bucket_name, "--name", f"html/{index_key}.html",
               "--file", temp_file, "--content-type", "text/html; charset=utf-8",
               "--force"]
        subprocess.run(cmd, capture_output=True)
        subprocess.run(["rm", temp_file], capture_output=True)
    except:
        pass

def save_log(new_count, namespace, bucket_name):
    """保存執行日誌"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "new_permits": new_count,
            "status": "success"
        }
        
        # 載入現有日誌
        logs = []
        cmd = ["oci", "os", "object", "get", "--namespace", namespace,
               "--bucket-name", bucket_name, "--name", "logs/daily-crawler.json",
               "--file", "/tmp/logs.json"]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            with open('/tmp/logs.json', 'r') as f:
                logs = json.load(f)
        
        # 添加新日誌
        logs.append(log_entry)
        
        # 只保留最近30筆
        if len(logs) > 30:
            logs = logs[-30:]
        
        # 保存日誌
        with open('/tmp/logs_updated.json', 'w') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        cmd = ["oci", "os", "object", "put", "--namespace", namespace,
               "--bucket-name", bucket_name, "--name", "logs/daily-crawler.json",
               "--file", "/tmp/logs_updated.json", "--content-type", "application/json",
               "--force"]
        subprocess.run(cmd, capture_output=True)
    except:
        pass

if __name__ == "__main__":
    main()