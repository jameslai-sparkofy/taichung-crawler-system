import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime, date
import re
import os
from dotenv import load_dotenv
from database_manager import DatabaseManager

load_dotenv()

class BuildingPermitCrawler:
    def __init__(self):
        self.base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
        self.db_manager = DatabaseManager()
        self.session = requests.Session()
        
        # 設定瀏覽器標頭
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 爬蟲設定
        self.start_year = int(os.getenv('START_YEAR', 114))
        self.crawl_type = int(os.getenv('CRAWL_TYPE', 1))
        self.delay_min = int(os.getenv('DELAY_MIN', 1))
        self.delay_max = int(os.getenv('DELAY_MAX', 3))
        
        # 統計資料
        self.total_crawled = 0
        self.new_records = 0
        self.error_records = 0
        
    def generate_index_key(self, year, permit_type, sequence, version=0):
        """生成INDEX_KEY"""
        return f"{year}{permit_type}{sequence:05d}{version:02d}"
    
    def parse_index_key(self, index_key):
        """解析INDEX_KEY"""
        if len(index_key) != 11:
            return None
        
        year = int(index_key[:3])
        permit_type = int(index_key[3])
        sequence = int(index_key[4:9])
        version = int(index_key[9:11])
        
        return {
            'year': year,
            'permit_type': permit_type,
            'sequence': sequence,
            'version': version
        }
    
    def fetch_page_with_retry(self, index_key, max_retries=3):
        """獲取頁面內容，包含重試機制"""
        url = f"{self.base_url}?INDEX_KEY={index_key}"
        
        for attempt in range(max_retries):
            try:
                # 根據用戶提到的需要重新整理兩次的情況
                for refresh_count in range(2):
                    response = self.session.get(url, timeout=30)
                    time.sleep(random.uniform(0.5, 1.5))
                
                if response.status_code == 200:
                    # 檢查是否為正常頁面
                    if '建築執照號碼' in response.text or '○○○代表遺失個資歡迎' in response.text:
                        return response
                    else:
                        logging.warning(f"頁面內容異常，INDEX_KEY: {index_key}")
                        
            except Exception as e:
                logging.error(f"獲取頁面時發生錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
                
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
        
        return None
    
    def parse_permit_data(self, html_content, index_key):
        """解析建照資料"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 檢查是否為有效的建照頁面
            if '○○○代表遺失個資歡迎' in html_content:
                logging.info(f"INDEX_KEY {index_key}: 包含遺失個資訊息，跳過")
                return None
            
            # 解析INDEX_KEY
            key_info = self.parse_index_key(index_key)
            if not key_info:
                return None
            
            permit_data = {
                'permit_number': None,
                'permit_year': key_info['year'],
                'permit_type': key_info['permit_type'],
                'sequence_number': key_info['sequence'],
                'version_number': key_info['version'],
                'applicant_name': None,
                'designer_name': None,
                'designer_company': None,
                'supervisor_name': None,
                'supervisor_company': None,
                'contractor_name': None,
                'contractor_company': None,
                'engineer_name': None,
                'site_address': None,
                'site_city': None,
                'site_zone': None,
                'site_area': None,
                'crawled_at': datetime.now()
            }
            
            # 尋找表格資料
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        
                        if '建造執照號碼' in label:
                            permit_data['permit_number'] = cells[1].get_text(strip=True)
                        
                        elif '起造人' in label and len(cells) >= 3:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data['applicant_name'] = cells[2].get_text(strip=True)
                        
                        elif '設計人' in label and len(cells) >= 4:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data['designer_name'] = cells[2].get_text(strip=True)
                            if '事務所' in cells[3].get_text(strip=True) and len(cells) >= 5:
                                permit_data['designer_company'] = cells[4].get_text(strip=True)
                        
                        elif '監造人' in label and len(cells) >= 4:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data['supervisor_name'] = cells[2].get_text(strip=True)
                            if '事務所' in cells[3].get_text(strip=True) and len(cells) >= 5:
                                permit_data['supervisor_company'] = cells[4].get_text(strip=True)
                        
                        elif '承造人' in label and len(cells) >= 4:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data['contractor_name'] = cells[2].get_text(strip=True)
                            if len(cells) >= 5:
                                permit_data['contractor_company'] = cells[4].get_text(strip=True)
                        
                        elif '專任工程人員' in label:
                            permit_data['engineer_name'] = cells[1].get_text(strip=True)
                        
                        elif '地號' in label:
                            permit_data['site_address'] = cells[1].get_text(strip=True)
                        
                        elif '地址' in label:
                            permit_data['site_city'] = cells[1].get_text(strip=True)
                        
                        elif '使用分區' in label:
                            permit_data['site_zone'] = cells[1].get_text(strip=True)
                        
                        elif '基地面積' in label and len(cells) >= 4:
                            area_text = cells[3].get_text(strip=True)
                            # 提取數字部分
                            area_match = re.search(r'([\d.]+)', area_text)
                            if area_match:
                                try:
                                    permit_data['site_area'] = float(area_match.group(1))
                                except ValueError:
                                    pass
            
            # 檢查是否有必要資料
            if not permit_data['permit_number']:
                logging.warning(f"INDEX_KEY {index_key}: 未找到建照號碼")
                return None
            
            return permit_data
            
        except Exception as e:
            logging.error(f"解析建照資料時發生錯誤: {e}")
            return None
    
    def crawl_single_permit(self, index_key):
        """爬取單一建照資料"""
        try:
            # 獲取頁面
            response = self.fetch_page_with_retry(index_key)
            if not response:
                logging.error(f"無法獲取頁面: INDEX_KEY {index_key}")
                self.error_records += 1
                return False
            
            # 解析資料
            permit_data = self.parse_permit_data(response.text, index_key)
            if not permit_data:
                logging.info(f"INDEX_KEY {index_key}: 無有效資料或已遺失個資")
                return False
            
            # 儲存到資料庫
            result = self.db_manager.insert_permit(permit_data)
            
            if result == 'new':
                self.new_records += 1
                logging.info(f"新增建照: {permit_data['permit_number']}")
            elif result == 'updated':
                logging.info(f"更新建照: {permit_data['permit_number']}")
            elif result == 'error':
                self.error_records += 1
                return False
            
            self.total_crawled += 1
            return True
            
        except Exception as e:
            logging.error(f"爬取建照時發生錯誤: {e}")
            self.error_records += 1
            return False
    
    def crawl_year_permits(self, year, permit_type=1, start_sequence=1, max_consecutive_failures=50):
        """爬取指定年份的建照資料"""
        logging.info(f"開始爬取 {year} 年類型 {permit_type} 的建照資料，從編號 {start_sequence} 開始")
        
        consecutive_failures = 0
        current_sequence = start_sequence
        
        while consecutive_failures < max_consecutive_failures:
            index_key = self.generate_index_key(year, permit_type, current_sequence)
            
            logging.info(f"爬取 INDEX_KEY: {index_key}")
            
            success = self.crawl_single_permit(index_key)
            
            if success:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                logging.info(f"連續失敗次數: {consecutive_failures}/{max_consecutive_failures}")
            
            current_sequence += 1
            
            # 隨機延遲
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)
        
        logging.info(f"完成爬取 {year} 年資料，連續失敗 {max_consecutive_failures} 次後停止")
    
    def daily_crawl(self):
        """每日爬蟲執行"""
        crawl_date = date.today()
        logging.info(f"開始執行每日爬蟲任務: {crawl_date}")
        
        try:
            # 連接資料庫
            if not self.db_manager.connect():
                logging.error("無法連接資料庫，取消爬蟲任務")
                return
            
            # 開始爬蟲記錄
            log_id = self.db_manager.start_crawl_log(crawl_date)
            
            # 重置統計
            self.total_crawled = 0
            self.new_records = 0
            self.error_records = 0
            
            # 獲取當前年份的最大編號
            current_year = self.start_year
            max_sequence = self.db_manager.get_max_sequence_number(current_year, self.crawl_type)
            start_sequence = max(max_sequence, 1)
            
            # 開始爬取
            self.crawl_year_permits(current_year, self.crawl_type, start_sequence)
            
            # 更新爬蟲記錄
            self.db_manager.update_crawl_log(
                crawl_date, 'completed', 
                self.total_crawled, self.new_records, self.error_records
            )
            
            logging.info(f"每日爬蟲任務完成: 總計 {self.total_crawled} 筆，新增 {self.new_records} 筆，錯誤 {self.error_records} 筆")
            
        except Exception as e:
            error_msg = f"每日爬蟲任務執行失敗: {e}"
            logging.error(error_msg)
            
            # 更新失敗記錄
            self.db_manager.update_crawl_log(
                crawl_date, 'failed',
                self.total_crawled, self.new_records, self.error_records, 
                error_msg
            )
        
        finally:
            self.db_manager.disconnect()

if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.getenv('LOG_FILE', 'crawler.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    crawler = BuildingPermitCrawler()
    crawler.daily_crawl()