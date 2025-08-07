#!/usr/bin/env python3
"""
台中市建照爬蟲 - OCI Compute Instance 版本
每日自動爬取新的建照資料並上傳到 OCI Object Storage
"""
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import oci
from oci.object_storage import ObjectStorageClient

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# OCI 設定
NAMESPACE = "nrsdi1rz5vl8"
BUCKET_NAME = "taichung-building-permits"

class OCIStorage:
    def __init__(self):
        # 使用 Instance Principal 認證
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            self.object_storage = ObjectStorageClient(config={}, signer=signer)
            logger.info("使用 Instance Principal 認證")
        except Exception:
            # 如果 Instance Principal 失敗，使用預設設定檔
            config = oci.config.from_file()
            self.object_storage = ObjectStorageClient(config)
            logger.info("使用設定檔認證")
    
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
            logger.info(f"成功寫入 {object_name}")
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
            'year112': {'count': 0, 'max': 0},
            'total': len(permits)
        }
        
        if isinstance(permits, list):
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
        self.max_consecutive_no_data = 20
        self.batch_size = 30
        self.request_delay = 0.8
        self.max_crawl_per_run = 50
        
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
            # 建立暫存檔案
            temp_file = f"/tmp/permit_{index_key}.html"
            
            # 使用 wget 下載
            cmd = [
                'wget', '-q', '-O', temp_file,
                '--timeout=30',
                '--tries=3',
                '--wait-retry=2',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and Path(temp_file).exists():
                with open(temp_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 清理暫存檔案
                os.unlink(temp_file)
                return content
            else:
                if Path(temp_file).exists():
                    os.unlink(temp_file)
                logger.error(f"wget 失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"抓取錯誤 {index_key}: {str(e)}")
            return None
    
    def parse_permit_data(self, html_content, index_key):
        """解析建照資料"""
        try:
            import re
            
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
            match = re.search(r'建造執照號碼[：:]\s*([^\s<]+)', html_content)
            if not match:
                match = re.search(r'建築執照號碼[：:]\s*([^\s<]+)', html_content)
            if match:
                permit_data['permitNumber'] = match.group(1).strip()
            else:
                return None
            
            # 申請人
            match = re.search(r'起造人[^>]*姓名[^>]*>([^<]+)', html_content)
            if match:
                permit_data['applicantName'] = match.group(1).strip()
            
            # 地址
            match = re.search(r'地號[^>]*>([^<]+)', html_content)
            if not match:
                match = re.search(r'地址[^>]*>([^<]+)', html_content)
            if match:
                permit_data['siteAddress'] = match.group(1).strip()
            
            # 行政區
            if permit_data.get('siteAddress'):
                district_match = re.search(r'臺中市([^區]+區)', permit_data['siteAddress'])
                if district_match:
                    permit_data['district'] = district_match.group(1)
            
            # 樓層資訊
            match = re.search(r'地上.*?層.*?棟.*?戶|地上.*?層.*?幢.*?棟.*?戶', html_content)
            if match:
                permit_data['floorInfo'] = match.group(0)
                
                floor_match = re.search(r'地上(\d+)層', match.group(0))
                if floor_match:
                    permit_data['floorsAbove'] = int(floor_match.group(1))
                    permit_data['floors'] = int(floor_match.group(1))
                
                building_match = re.search(r'(\d+)棟', match.group(0))
                if building_match:
                    permit_data['buildingCount'] = int(building_match.group(1))
                    permit_data['buildings'] = int(building_match.group(1))
                
                unit_match = re.search(r'(\d+)戶', match.group(0))
                if unit_match:
                    permit_data['unitCount'] = int(unit_match.group(1))
                    permit_data['units'] = int(unit_match.group(1))
            
            # 總樓地板面積
            match = re.search(r'總樓地板面積.*?<span[^>]*>([0-9.,]+)', html_content)
            if match:
                permit_data['totalFloorArea'] = float(match.group(1).replace(',', ''))
            
            # 發照日期
            match = re.search(r'發照日期.*?(\d{3})/(\d{2})/(\d{2})', html_content)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                permit_data['issueDate'] = f"{year + 1911}-{month:02d}-{day:02d}"
                permit_data['issueDateROC'] = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
            
            return permit_data
            
        except Exception as e:
            logger.error(f'解析錯誤: {str(e)}')
            return None
    
    def crawl_year_range(self, year, start_seq, max_crawl=None):
        """爬取年份範圍"""
        if max_crawl is None:
            max_crawl = self.max_crawl_per_run
            
        logger.info(f"開始爬取 {year} 年，從序號 {start_seq:05d} 開始")
        logger.info(f"參數: 延遲={self.request_delay}s, 批次={self.batch_size}, 上限={max_crawl}")
        
        consecutive_failed = 0
        consecutive_no_data = 0
        seq = start_seq
        
        while consecutive_failed < self.max_consecutive_failures and self.stats['totalAttempted'] < max_crawl:
            index_key = self.generate_index_key(year, 1, seq)
            self.stats['totalAttempted'] += 1
            
            logger.info(f"[{seq:05d}] 爬取 {index_key}...")
            
            html_content = self.fetch_permit(index_key)
            if not html_content:
                consecutive_failed += 1
                consecutive_no_data = 0
                self.stats['failed'] += 1
                logger.info(f"❌ {index_key} 失敗 (連續 {consecutive_failed})")
            else:
                result = self.parse_permit_data(html_content, index_key)
                if result == "NO_DATA":
                    consecutive_no_data += 1
                    consecutive_failed = 0
                    self.stats['noData'] += 1
                    logger.info(f"⏭️ {index_key} 無資料 (連續 {consecutive_no_data})")
                    
                    if consecutive_no_data >= self.max_consecutive_no_data:
                        logger.info(f"連續 {self.max_consecutive_no_data} 筆無資料，停止爬取")
                        break
                elif result:
                    consecutive_failed = 0
                    consecutive_no_data = 0
                    self.stats['successful'] += 1
                    self.results.append(result)
                    logger.info(f"✅ {index_key} {result.get('permitNumber', '')}")
                else:
                    consecutive_failed += 1
                    consecutive_no_data = 0
                    self.stats['failed'] += 1
                    logger.info(f"❌ {index_key} 解析失敗 (連續 {consecutive_failed})")
            
            # 批次儲存
            if len(self.results) >= self.batch_size:
                logger.info(f"批次儲存 {len(self.results)} 筆資料...")
                self.save_results()
            
            # 延遲避免過快
            time.sleep(self.request_delay)
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
            logger.info(f"✅ 儲存 {new_count} 筆新資料（總計 {len(permits)} 筆）")
        
        self.results = []
    
    def run_daily_crawl(self):
        """執行每日爬蟲"""
        start_time = datetime.now()
        logger.info("="*70)
        logger.info(f"🚀 開始每日爬蟲: {start_time}")
        logger.info("="*70)
        
        try:
            # 取得目前進度
            progress = self.storage.get_current_progress()
            logger.info('📊 目前進度:')
            logger.info(f"  114年: {progress['year114']['count']} 筆, 最大序號: {progress['year114']['max']}")
            logger.info(f"  113年: {progress['year113']['count']} 筆, 最大序號: {progress['year113']['max']}")
            logger.info(f"  112年: {progress['year112']['count']} 筆, 最大序號: {progress['year112']['max']}")
            logger.info(f"  總計: {progress['total']} 筆")
            
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
            
            logger.info(f"\n📊 開始爬取: {target_year}年 序號{start_seq}")
            
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
                'results': {
                    'success': stats['successful'],
                    'failed': stats['failed'],
                    'empty': stats['noData'],
                    'total': stats['totalAttempted']
                },
                'yearStats': {
                    str(target_year): {
                        'crawled': stats['successful'],
                        'start': start_seq,
                        'end': start_seq + stats['totalAttempted'] - 1
                    }
                },
                'status': 'completed' if stats['successful'] > 0 else 'partial'
            }
            
            # 更新日誌
            logs_data = self.storage.get_json_object('data/crawl-logs.json') or {'logs': []}
            logs_data['logs'].insert(0, log_entry)
            logs_data['logs'] = logs_data['logs'][:100]  # 保留最近 100 筆
            logs_data['lastUpdate'] = datetime.now().isoformat()
            self.storage.put_json_object('data/crawl-logs.json', logs_data)
            
            logger.info("="*70)
            logger.info(f"🏁 爬蟲完成")
            logger.info(f"📊 統計: 總嘗試 {stats['totalAttempted']} 筆")
            logger.info(f"   ✅ 成功: {stats['successful']} 筆")
            logger.info(f"   ❌ 失敗: {stats['failed']} 筆")
            logger.info(f"   ⏭️ 無資料: {stats['noData']} 筆")
            logger.info(f"⏱️ 耗時: {duration:.0f} 秒")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"爬蟲執行錯誤: {str(e)}", exc_info=True)
            
            # 記錄錯誤
            log_entry = {
                'date': start_time.strftime('%Y-%m-%d'),
                'startTime': start_time.isoformat(),
                'endTime': datetime.now().isoformat(),
                'error': str(e),
                'status': 'failed'
            }
            
            logs_data = self.storage.get_json_object('data/crawl-logs.json') or {'logs': []}
            logs_data['logs'].insert(0, log_entry)
            logs_data['lastUpdate'] = datetime.now().isoformat()
            self.storage.put_json_object('data/crawl-logs.json', logs_data)

def main():
    """主程式"""
    storage = OCIStorage()
    crawler = BuildingPermitCrawler(storage)
    crawler.run_daily_crawl()

if __name__ == "__main__":
    main()