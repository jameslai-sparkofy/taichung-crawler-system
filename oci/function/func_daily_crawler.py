import io
import json
import logging
import subprocess
import re
from datetime import datetime
import time
from fdk import response

# OCI Functions 每日定時爬蟲
def handler(ctx, data: io.BytesIO = None):
    """OCI Functions 處理函數 - 每日定時爬蟲"""
    logging.getLogger().info("開始執行每日建照爬蟲任務")
    
    try:
        # 設定參數
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
        
        # 載入進度檔案
        progress = load_progress(namespace, bucket_name)
        
        # 設定爬取參數
        year = progress.get('year', 114)
        start_seq = progress.get('currentSequence', 1100)
        permit_type = 1
        max_crawl = 50  # 每次最多爬取50筆
        consecutive_empty = progress.get('consecutiveEmpty', 0)
        
        # 載入現有資料
        permits = load_existing_data(namespace, bucket_name)
        
        # 開始爬取
        new_permits = []
        crawled = 0
        success_count = 0
        error_count = 0
        empty_count = 0
        
        for seq in range(start_seq, start_seq + max_crawl):
            index_key = f"{year}{permit_type}{seq:05d}00"
            
            # 檢查是否已存在
            exists = any(p.get('indexKey') == index_key for p in permits)
            if exists:
                logging.info(f"跳過已存在: {index_key}")
                continue
            
            # 爬取單筆資料
            permit_data = crawl_single_permit(index_key, base_url)
            crawled += 1
            
            if permit_data == "NO_DATA":
                # 無資料
                empty_count += 1
                consecutive_empty += 1
                logging.info(f"無資料: {index_key} (連續{consecutive_empty}個)")
                
                if consecutive_empty >= 3:
                    # 連續3個無資料，停止爬取
                    logging.info(f"連續{consecutive_empty}個序號無資料，停止爬取")
                    break
                    
            elif permit_data:
                # 成功爬取
                new_permits.append(permit_data)
                success_count += 1
                consecutive_empty = 0  # 重置計數
                logging.info(f"成功爬取: {permit_data.get('permitNumber')}")
                
            else:
                # 爬取失敗
                error_count += 1
                logging.warning(f"爬取失敗: {index_key}")
            
            # 避免過快請求
            time.sleep(1.5)
        
        # 更新進度
        progress['currentSequence'] = start_seq + crawled
        progress['consecutiveEmpty'] = consecutive_empty
        progress['lastCrawledAt'] = datetime.now().isoformat()
        save_progress(progress, namespace, bucket_name)
        
        # 合併資料並儲存
        if new_permits:
            permits.extend(new_permits)
            save_data(permits, namespace, bucket_name)
        
        # 更新執行記錄
        update_crawl_logs(namespace, bucket_name, {
            'crawled': crawled,
            'success': success_count,
            'empty': empty_count,
            'error': error_count,
            'lastSequence': start_seq + crawled - 1
        })
        
        message = f"爬取完成: 總計{crawled}筆, 成功{success_count}筆, 空白{empty_count}筆, 錯誤{error_count}筆"
        logging.info(message)
        
        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": "success",
                "message": message,
                "crawled": crawled,
                "newRecords": success_count
            }),
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logging.error(f"執行失敗: {str(e)}")
        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": "error",
                "message": str(e)
            }),
            headers={"Content-Type": "application/json"}
        )

def load_progress(namespace, bucket_name):
    """載入爬蟲進度"""
    try:
        cmd = [
            "oci", "os", "object", "get",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/crawler_progress.json",
            "--file", "/tmp/progress.json"
        ]
        subprocess.run(cmd, capture_output=True)
        
        with open('/tmp/progress.json', 'r') as f:
            return json.load(f)
    except:
        # 預設進度
        return {
            "year": 114,
            "currentSequence": 1100,
            "consecutiveEmpty": 0,
            "lastCrawledAt": None
        }

def save_progress(progress, namespace, bucket_name):
    """儲存爬蟲進度"""
    try:
        with open('/tmp/progress_new.json', 'w') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/crawler_progress.json",
            "--file", "/tmp/progress_new.json",
            "--content-type", "application/json",
            "--force"
        ]
        subprocess.run(cmd, capture_output=True)
    except Exception as e:
        logging.error(f"儲存進度失敗: {e}")

def crawl_single_permit(index_key, base_url):
    """爬取單筆建照資料"""
    try:
        # 發送請求
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/x-www-form-urlencoded",
            "-d", f"INDEX_KEY={index_key}",
            base_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        html_content = result.stdout
        
        # 檢查是否有資料
        if "查無任何資訊" in html_content:
            return "NO_DATA"
        
        if "建造執照號碼" not in html_content:
            return None
        
        # 解析資料
        permit_data = parse_permit_data(html_content, index_key)
        return permit_data
        
    except Exception as e:
        logging.error(f"爬取失敗 {index_key}: {e}")
        return None

def parse_permit_data(html_content, index_key):
    """解析建照資料"""
    try:
        permit_data = {}
        
        # 基本資訊
        permit_data['indexKey'] = index_key
        permit_data['permitYear'] = int(index_key[:3])
        permit_data['sequenceNumber'] = int(index_key[4:9])
        
        # 建照號碼
        m = re.search(r'建造執照號碼.*?<span class="conlist w40">([^<]+)</span>', html_content, re.DOTALL)
        if m:
            permit_data['permitNumber'] = m.group(1).strip()
        
        # 申請人
        m = re.search(r'起造人\(申請人\).*?<span class="conlist">([^<]+)</span>', html_content, re.DOTALL)
        if m:
            permit_data['applicantName'] = m.group(1).strip()
        
        # 建築地址
        m = re.search(r'建築地點.*?<span class="conlist wd-m">([^<]+)</span>', html_content, re.DOTALL)
        if m:
            permit_data['address'] = m.group(1).strip()
        
        # 樓層資訊
        floor_match = re.search(r'([地下上]+[0-9]+層.*?戶)', html_content)
        if floor_match:
            floor_info = floor_match.group(1)
            
            floor_m = re.search(r'地上(\d+)層', floor_info)
            if floor_m:
                permit_data['floors'] = int(floor_m.group(1))
                
            building_m = re.search(r'(\d+)棟', floor_info)
            if building_m:
                permit_data['buildings'] = int(building_m.group(1))
                permit_data['buildingCount'] = int(building_m.group(1))
                
            unit_m = re.search(r'(\d+)戶', floor_info)
            if unit_m:
                permit_data['units'] = int(unit_m.group(1))
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

def load_existing_data(namespace, bucket_name):
    """載入現有資料"""
    try:
        cmd = [
            "oci", "os", "object", "get",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/permits.json",
            "--file", "/tmp/existing_permits.json"
        ]
        subprocess.run(cmd, capture_output=True)
        
        with open('/tmp/existing_permits.json', 'r') as f:
            data = json.load(f)
            return data.get('permits', [])
    except:
        return []

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
        logging.error(f"儲存資料失敗: {e}")

def update_crawl_logs(namespace, bucket_name, stats):
    """更新執行記錄"""
    try:
        # 載入現有記錄
        try:
            cmd = [
                "oci", "os", "object", "get",
                "--namespace", namespace,
                "--bucket-name", bucket_name,
                "--name", "data/crawl-logs.json",
                "--file", "/tmp/crawl_logs.json"
            ]
            subprocess.run(cmd, capture_output=True)
            
            with open('/tmp/crawl_logs.json', 'r') as f:
                log_data = json.load(f)
        except:
            log_data = {"logs": []}
        
        # 建立新記錄
        now = datetime.now()
        new_log = {
            "date": now.strftime("%Y-%m-%d"),
            "startTime": now.replace(second=0, microsecond=0).isoformat(),
            "endTime": now.isoformat(),
            "totalCrawled": stats['crawled'],
            "newRecords": stats['success'],
            "errorRecords": stats['error'],
            "status": "completed" if stats['success'] > 0 else "partial",
            "message": f"OCI定時爬蟲 - 爬取序號至{stats['lastSequence']}，成功{stats['success']}筆"
        }
        
        # 插入到最前面
        log_data['logs'].insert(0, new_log)
        
        # 只保留最近100筆
        log_data['logs'] = log_data['logs'][:100]
        
        # 儲存
        with open('/tmp/crawl_logs_new.json', 'w') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", "data/crawl-logs.json",
            "--file", "/tmp/crawl_logs_new.json",
            "--content-type", "application/json",
            "--force"
        ]
        subprocess.run(cmd, capture_output=True)
        
    except Exception as e:
        logging.error(f"更新執行記錄失敗: {e}")