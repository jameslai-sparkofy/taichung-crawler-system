import io
import json
import logging
import os
import subprocess
import time
from datetime import datetime

from fdk import response
import oci
from oci.object_storage import ObjectStorageClient

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OCI 設定
NAMESPACE = "nrsdi1rz5vl8"
BUCKET_NAME = "taichung-building-permits"
COMPARTMENT_ID = os.environ.get('OCI_COMPARTMENT_ID', '')

class OCIStorage:
    def __init__(self):
        # 使用 Instance Principal 認證（在 Functions 中自動可用）
        signer = oci.auth.signers.get_resource_principals_signer()
        self.object_storage = ObjectStorageClient(config={}, signer=signer)
        
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
            return True
        except Exception as e:
            logger.error(f"寫入物件失敗 {object_name}: {str(e)}")
            return False
    
    def get_current_progress(self):
        """取得目前爬取進度"""
        permits = self.get_json_object('data/permits.json') or []
        
        progress = {
            'year114': {'count': 0, 'max': 0},
            'year113': {'count': 0, 'max': 0},
            'year112': {'count': 0, 'max': 0}
        }
        
        for permit in permits:
            year = permit.get('permitYear', 0)
            seq = permit.get('sequenceNumber', 0)
            
            if year == 114:
                progress['year114']['count'] += 1
                progress['year114']['max'] = max(progress['year114']['max'], seq)
            elif year == 113:
                progress['year113']['count'] += 1
                progress['year113']['max'] = max(progress['year113']['max'], seq)
            elif year == 112:
                progress['year112']['count'] += 1
                progress['year112']['max'] = max(progress['year112']['max'], seq)
        
        return progress

class BuildingPermitCrawler:
    def __init__(self, storage):
        self.storage = storage
        self.base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
        self.max_consecutive_failures = 5
        self.stats = {
            'totalAttempted': 0,
            'successful': 0,
            'failed': 0,
            'noData': 0
        }
        self.results = []
    
    def generate_index_key(self, year, permit_type, sequence, version=0):
        """生成 INDEX_KEY"""
        return f"{year}{permit_type}{sequence:05d}{version:02d}"
    
    def fetch_permit(self, index_key):
        """使用 wget 抓取建照資料"""
        url = f"{self.base_url}?INDEX_KEY={index_key}"
        
        try:
            # 使用 wget 命令（OCI Functions 環境有 wget）
            result = subprocess.run([
                'wget', '-q', '-O', '-',
                '--timeout=30',
                '--tries=3',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                url
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"wget 失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"抓取錯誤 {index_key}: {str(e)}")
            return None
    
    def parse_permit_data(self, html_content, index_key):
        """解析建照資料"""
        try:
            # 檢查是否包含遺失個資
            if '○○○代表遺失個資' in html_content:
                return "NO_DATA"
            
            permit_data = {
                'indexKey': index_key,
                'permitYear': int(index_key[0:3]),
                'permitType': int(index_key[3:4]),
                'sequenceNumber': int(index_key[4:9]),
                'versionNumber': int(index_key[9:11]),
                'crawledAt': datetime.now().isoformat()
            }
            
            # 建照號碼
            import re
            match = re.search(r'建造執照號碼[：:]\s*([^\s<]+)', html_content)
            if not match:
                match = re.search(r'建築執照號碼[：:]\s*([^\s<]+)', html_content)
            if match:
                permit_data['permitNumber'] = match.group(1).strip()
            else:
                return None
            
            # 其他欄位解析...
            # (保持原有的解析邏輯)
            
            return permit_data
            
        except Exception as e:
            logger.error(f'解析錯誤: {str(e)}')
            return None
    
    def crawl_year_range(self, year, start_seq, max_crawl=50):
        """爬取年份範圍"""
        logger.info(f"開始爬取 {year} 年，從序號 {start_seq} 開始")
        
        consecutive_failed = 0
        seq = start_seq
        
        while consecutive_failed < self.max_consecutive_failures and self.stats['totalAttempted'] < max_crawl:
            index_key = self.generate_index_key(year, 1, seq)
            self.stats['totalAttempted'] += 1
            
            html_content = self.fetch_permit(index_key)
            if not html_content:
                consecutive_failed += 1
                self.stats['failed'] += 1
                logger.info(f"❌ {index_key} 失敗 (連續 {consecutive_failed})")
            else:
                result = self.parse_permit_data(html_content, index_key)
                if result == "NO_DATA":
                    consecutive_failed += 1
                    self.stats['noData'] += 1
                    logger.info(f"⏭️ {index_key} 無資料 (連續 {consecutive_failed})")
                elif result:
                    consecutive_failed = 0
                    self.stats['successful'] += 1
                    self.results.append(result)
                    logger.info(f"✅ {index_key} {result.get('permitNumber', '')}")
                else:
                    consecutive_failed += 1
                    self.stats['failed'] += 1
                    logger.info(f"❌ {index_key} 解析失敗 (連續 {consecutive_failed})")
            
            # 批次儲存
            if len(self.results) >= 10:
                self.save_results()
            
            # 延遲避免過快
            time.sleep(0.8)
            seq += 1
        
        # 儲存剩餘結果
        if self.results:
            self.save_results()
        
        return self.stats
    
    def save_results(self):
        """儲存爬取結果到 OCI"""
        if not self.results:
            return
        
        # 讀取現有資料
        permits = self.storage.get_json_object('data/permits.json') or []
        
        # 建立索引字典以快速查找
        existing_keys = {p['indexKey'] for p in permits}
        
        # 新增不重複的資料
        new_count = 0
        for result in self.results:
            if result['indexKey'] not in existing_keys:
                permits.append(result)
                new_count += 1
        
        # 重新排序
        permits.sort(key=lambda x: x['indexKey'])
        
        # 儲存回 OCI
        if self.storage.put_json_object('data/permits.json', permits):
            logger.info(f"✅ 儲存 {new_count} 筆新資料")
        
        self.results = []
    
    def run_daily_crawl(self):
        """執行每日爬蟲"""
        start_time = datetime.now()
        logger.info(f"🚀 開始每日爬蟲: {start_time}")
        
        try:
            # 取得目前進度
            progress = self.storage.get_current_progress()
            
            # 決定要爬取的年份和起始序號
            if progress['year114']['max'] < 2000:  # 假設 114 年最多到 2000
                target_year = 114
                start_seq = progress['year114']['max'] + 1
            elif progress['year113']['max'] < 2500:  # 假設 113 年最多到 2500
                target_year = 113
                start_seq = progress['year113']['max'] + 1
            elif progress['year112']['max'] < 2500:  # 假設 112 年最多到 2500
                target_year = 112
                start_seq = progress['year112']['max'] + 1
            else:
                logger.info("✅ 所有年份都已爬取完成")
                return
            
            # 執行爬取
            stats = self.crawl_year_range(target_year, start_seq)
            
            # 記錄日誌
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            log_entry = {
                'date': start_time.strftime('%Y-%m-%d'),
                'startTime': start_time.isoformat(),
                'endTime': end_time.isoformat(),
                'duration': int(duration),
                'targetYear': target_year,
                'startSequence': start_seq,
                'stats': stats,
                'status': 'completed' if stats['successful'] > 0 else 'partial'
            }
            
            # 更新日誌
            logs = self.storage.get_json_object('data/crawl-logs.json') or {'logs': []}
            logs['logs'].insert(0, log_entry)
            logs['logs'] = logs['logs'][:100]  # 保留最近 100 筆
            logs['lastUpdate'] = datetime.now().isoformat()
            self.storage.put_json_object('data/crawl-logs.json', logs)
            
            logger.info(f"🏁 爬蟲完成: 成功 {stats['successful']} 筆，耗時 {duration:.0f} 秒")
            
        except Exception as e:
            logger.error(f"爬蟲執行錯誤: {str(e)}")

def handler(ctx, data: io.BytesIO = None):
    """OCI Functions 處理函數"""
    try:
        # 建立儲存物件
        storage = OCIStorage()
        
        # 建立爬蟲
        crawler = BuildingPermitCrawler(storage)
        
        # 執行每日爬蟲
        crawler.run_daily_crawl()
        
        return response.Response(
            ctx, 
            response_data=json.dumps({
                "status": "success",
                "message": "爬蟲執行完成",
                "stats": crawler.stats
            }),
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logger.error(f"函數執行錯誤: {str(e)}")
        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": "error",
                "message": str(e)
            }),
            headers={"Content-Type": "application/json"}
        )