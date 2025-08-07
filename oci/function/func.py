import io
import json
import logging
import subprocess
import re
from datetime import datetime
import time
from fdk import response

# OCI Functions 專用爬蟲
def handler(ctx, data: io.BytesIO = None):
    """OCI Functions 處理函數"""
    logging.getLogger().info("開始執行每日建照爬蟲任務")
    
    try:
        # 設定參數
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
        
        # 載入現有資料
        permits = load_existing_data(namespace, bucket_name)
        
        # 取得今天的日期（民國年）
        today = datetime.now()
        current_year = today.year - 1911  # 轉換為民國年
        
        # 爬取112年資料（1564-2039）
        new_permits = []
        permit_type = 1
        year = 112  # 指定爬取112年
        start_seq = 1564
        end_seq = 2039
        max_crawl = 50  # 每次最多爬取50筆
        
        crawled = 0
        for seq in range(start_seq, min(end_seq + 1, start_seq + max_crawl)):
            index_key = f"{year}{permit_type}{seq:05d}00"
            
            # 檢查是否已存在
            exists = any(p.get('indexKey') == index_key for p in permits)
            if exists:
                logging.info(f"跳過已存在: {index_key}")
                continue
            
            # 爬取單筆資料
            permit_data = crawl_single_permit(index_key, base_url)
            
            if permit_data:
                new_permits.append(permit_data)
                crawled += 1
                logging.info(f"成功爬取: {permit_data.get('permitNumber')}")
            else:
                logging.warning(f"爬取失敗: {index_key}")
            
            # 避免過快請求
            time.sleep(2)
        
        # 合併資料並儲存
        if new_permits:
            permits.extend(new_permits)
            save_data(permits, namespace, bucket_name)
            message = f"成功爬取 {len(new_permits)} 筆新資料"
        else:
            message = "沒有發現新資料"
        
        # 記錄執行日誌
        log_execution(namespace, bucket_name, len(new_permits))
        
        return response.Response(
            ctx, response_data=json.dumps(
                {"message": message, "new_count": len(new_permits)},
                ensure_ascii=False
            ),
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logging.error(f"爬蟲執行失敗: {str(e)}")
        return response.Response(
            ctx, response_data=json.dumps(
                {"error": str(e)},
                ensure_ascii=False
            ),
            headers={"Content-Type": "application/json"}
        )

def load_existing_data(namespace, bucket_name):
    """載入現有資料"""
    try:
        # 使用 OCI CLI 下載資料
        cmd = [
            "oci", "os", "object", "get",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/permits.json",
            "--file", "/tmp/permits.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open('/tmp/permits.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('permits', [])
        else:
            return []
    except:
        return []

def crawl_single_permit(index_key, base_url):
    """爬取單一建照"""
    try:
        # 清除 cookies
        subprocess.run(["rm", "-f", "/tmp/cookies.txt"], capture_output=True)
        
        # 第一次訪問
        cmd1 = [
            "wget", "-q", "--save-cookies=/tmp/cookies.txt", "--keep-session-cookies",
            "--user-agent=Mozilla/5.0", "--timeout=20", "-O", "/tmp/first.html",
            f"{base_url}?INDEX_KEY={index_key}"
        ]
        subprocess.run(cmd1, capture_output=True)
        
        # 等待
        time.sleep(3)
        
        # 第二次訪問
        cmd2 = [
            "wget", "-q", "--load-cookies=/tmp/cookies.txt", "--save-cookies=/tmp/cookies.txt",
            "--keep-session-cookies", "--user-agent=Mozilla/5.0", "--timeout=20",
            "-O", f"/tmp/page_{index_key}.html", f"{base_url}?INDEX_KEY={index_key}"
        ]
        result = subprocess.run(cmd2, capture_output=True)
        
        if result.returncode != 0:
            return None
        
        # 讀取並解析內容
        with open(f"/tmp/page_{index_key}.html", "rb") as f:
            content = f.read()
        
        if len(content) < 1000:
            return None
        
        # 解碼
        try:
            html = content.decode('big5')
        except:
            html = content.decode('utf-8', errors='ignore')
        
        # 解析資料
        return parse_permit_data(html, index_key)
        
    except Exception as e:
        logging.error(f"爬取失敗 {index_key}: {e}")
        return None

def parse_permit_data(html_content, index_key):
    """解析建照資料"""
    try:
        if "查無任何資訊" in html_content or "建造執照號碼" not in html_content:
            return None
        
        permit_data = {
            'indexKey': index_key,
            'permitYear': int(index_key[:3]),
            'permitType': int(index_key[3]),
            'sequenceNumber': int(index_key[4:9]),
            'versionNumber': int(index_key[9:11]),
            'crawledAt': datetime.now().isoformat()
        }
        
        # 建照號碼
        m = re.search(r'<span class="conlist w20 tc">([1-9]\d{0,2}中[都市建]?建字第\d+號)</span>', html_content)
        if m:
            permit_data['permitNumber'] = m.group(1).strip()
        else:
            return None
        
        # 起造人
        m = re.search(r'起造人.*?姓名.*?<span class="conlist w30">([^<]+)</span>', html_content, re.DOTALL)
        if m:
            permit_data['applicantName'] = m.group(1).strip()
        
        # 地號和行政區
        m = re.search(r'地號.*?<span class="conlist w30">([^<]+)</span>', html_content, re.DOTALL)
        if m:
            land_text = m.group(1).strip()
            permit_data['siteAddress'] = land_text
            district_match = re.search(r'臺中市([^區]+區)', land_text)
            if district_match:
                permit_data['district'] = district_match.group(1)
        
        # 層棟戶數
        m = re.search(r'層棟戶數.*?<span class="conlist w50">([^<]+)</span>', html_content, re.DOTALL)
        if m:
            floor_info = m.group(1).strip()
            permit_data['floorInfo'] = floor_info
            
            floor_m = re.search(r'地上(\d+)層', floor_info)
            if floor_m:
                permit_data['floors'] = int(floor_m.group(1))
                
            building_m = re.search(r'(\d+)棟', floor_info)
            if building_m:
                permit_data['buildingCount'] = int(building_m.group(1))
                
            unit_m = re.search(r'(\d+)戶', floor_info)
            if unit_m:
                permit_data['unitCount'] = int(unit_m.group(1))
        
        # 總樓地板面積
        m = re.search(r'總樓地板面積.*?<span class="conlist w50">([0-9.,]+)', html_content, re.DOTALL)
        if m:
            try:
                area_str = m.group(1).replace(',', '')
                permit_data['totalFloorArea'] = float(area_str)
            except:
                pass
        
        # 發照日期
        m = re.search(r'發照日期.*?<span class="conlist w30">(\d+年\d+月\d+日)</span>', html_content, re.DOTALL)
        if m:
            date_text = m.group(1).strip()
            date_m = re.search(r'(\d+)年(\d+)月(\d+)日', date_text)
            if date_m:
                year = int(date_m.group(1)) + 1911
                month = int(date_m.group(2))
                day = int(date_m.group(3))
                permit_data['issueDate'] = f"{year:04d}-{month:02d}-{day:02d}"
        
        # 保存HTML
        save_html_to_oci(index_key, html_content, "nrsdi1rz5vl8", "taichung-building-permits")
        
        return permit_data
        
    except Exception as e:
        logging.error(f"解析失敗 {index_key}: {e}")
        return None

def save_html_to_oci(index_key, html_content, namespace, bucket_name):
    """保存HTML到OCI"""
    try:
        temp_file = f"/tmp/html_{index_key}.html"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", f"html/{index_key}.html",
            "--file", temp_file,
            "--content-type", "text/html; charset=utf-8",
            "--force"
        ]
        
        subprocess.run(cmd, capture_output=True)
        subprocess.run(["rm", temp_file], capture_output=True)
        
    except Exception as e:
        logging.error(f"保存HTML失敗: {e}")

def save_data(permits, namespace, bucket_name):
    """保存資料到OCI"""
    try:
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
        
        # 計算各年份數量
        for permit in sorted_permits:
            year = permit['permitYear']
            if year not in data['yearCounts']:
                data['yearCounts'][year] = 0
            data['yearCounts'][year] += 1
        
        # 寫入檔案
        with open('/tmp/permits_updated.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 上傳到OCI
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/permits.json",
            "--file", "/tmp/permits_updated.json",
            "--content-type", "application/json",
            "--force"
        ]
        
        subprocess.run(cmd, capture_output=True)
        
    except Exception as e:
        logging.error(f"保存資料失敗: {e}")
        raise

def log_execution(namespace, bucket_name, new_count):
    """記錄執行日誌"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "new_permits": new_count,
            "status": "success"
        }
        
        # 載入現有日誌
        logs = []
        cmd = [
            "oci", "os", "object", "get",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "logs/crawler-logs.json",
            "--file", "/tmp/logs.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            with open('/tmp/logs.json', 'r') as f:
                logs = json.load(f)
        
        # 添加新日誌
        logs.append(log_entry)
        
        # 只保留最近30天的日誌
        if len(logs) > 30:
            logs = logs[-30:]
        
        # 保存日誌
        with open('/tmp/logs_updated.json', 'w') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "logs/crawler-logs.json",
            "--file", "/tmp/logs_updated.json",
            "--content-type", "application/json",
            "--force"
        ]
        
        subprocess.run(cmd, capture_output=True)
        
    except Exception as e:
        logging.error(f"記錄日誌失敗: {e}")