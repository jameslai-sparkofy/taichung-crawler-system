import io
import json
import logging
import requests
import oci
from bs4 import BeautifulSoup
from datetime import datetime, date
import time
import random
import re

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(ctx, data: io.BytesIO = None):
    """
    OCI Functions 處理器 - 台中市建照爬蟲
    """
    try:
        logger.info("🚀 開始執行台中市建照爬蟲")
        
        # 初始化爬蟲
        crawler = TaichungBuildingCrawler()
        result = crawler.crawl()
        
        logger.info(f"✅ 爬蟲執行完成: {result}")
        
        return {
            "statusCode": 200,
            "body": json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"❌ 爬蟲執行失敗: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}, ensure_ascii=False)
        }

class TaichungBuildingCrawler:
    def __init__(self):
        self.base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
        self.bucket_name = "taichung-building-permits"
        self.namespace = "nrsdi1rz5vl8"
        self.start_year = 114
        self.crawl_type = 1
        self.delay_ms = 2000
        
        # 初始化OCI Object Storage客戶端
        self.object_storage_client = oci.object_storage.ObjectStorageClient({})
        
        # 統計資料
        self.stats = {
            "totalCrawled": 0,
            "newRecords": 0,
            "errorRecords": 0,
            "startTime": datetime.now(),
            "endTime": None
        }

    def generate_index_key(self, year, permit_type, sequence, version=0):
        """生成INDEX_KEY"""
        return f"{year}{permit_type}{sequence:05d}{version:02d}"

    def parse_index_key(self, index_key):
        """解析INDEX_KEY"""
        if len(index_key) != 11:
            return None
        
        return {
            "year": int(index_key[:3]),
            "permitType": int(index_key[3]),
            "sequence": int(index_key[4:9]),
            "version": int(index_key[9:11])
        }

    def fetch_page_with_retry(self, index_key, max_retries=3):
        """獲取頁面內容（含重新整理機制）"""
        url = f"{self.base_url}?INDEX_KEY={index_key}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 爬取 INDEX_KEY: {index_key} (嘗試 {attempt + 1}/{max_retries})")
                
                # 第一次請求
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
                }, timeout=30)

                if response.status_code == 200:
                    time.sleep(1)  # 等待1秒
                    
                    # 第二次請求（重新整理）
                    response = requests.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
                    }, timeout=30)

                    if response.status_code == 200:
                        text = response.text
                        if '建築執照號碼' in text or '○○○代表遺失個資歡迎' in text:
                            return text
                        
            except Exception as e:
                logger.error(f"❌ 獲取頁面錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
                
            if attempt < max_retries - 1:
                time.sleep(2)
        
        return None

    def parse_permit_data(self, html_content, index_key):
        """解析建照資料"""
        try:
            # 檢查是否包含遺失個資
            if '○○○代表遺失個資歡迎' in html_content:
                logger.info(f"ℹ️  INDEX_KEY {index_key}: 包含遺失個資訊息，跳過")
                return None

            key_info = self.parse_index_key(index_key)
            if not key_info:
                return None

            soup = BeautifulSoup(html_content, 'html.parser')
            
            permit_data = {
                "indexKey": index_key,
                "permitNumber": None,
                "permitYear": key_info["year"],
                "permitType": key_info["permitType"],
                "sequenceNumber": key_info["sequence"],
                "versionNumber": key_info["version"],
                "applicantName": None,
                "designerName": None,
                "designerCompany": None,
                "supervisorName": None,
                "supervisorCompany": None,
                "contractorName": None,
                "contractorCompany": None,
                "engineerName": None,
                "siteAddress": None,
                "siteCity": None,
                "siteZone": None,
                "siteArea": None,
                "landNumber": None,
                "district": None,
                "buildingCount": None,
                "unitCount": None,
                "totalFloorArea": None,
                "issueDate": None,
                "floorInfo": None,
                "crawledAt": datetime.now().isoformat()
            }

            # 建照號碼
            permit_number_match = re.search(r'建造執照號碼[：:\s]*([^\s<\n]+)', html_content)
            if permit_number_match:
                permit_data["permitNumber"] = permit_number_match.group(1).strip()

            # 表格資料解析
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        
                        if '起造人' in label and len(cells) >= 3:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data["applicantName"] = cells[2].get_text(strip=True)
                        
                        elif '設計人' in label and len(cells) >= 4:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data["designerName"] = cells[2].get_text(strip=True)
                            if '事務所' in cells[3].get_text(strip=True) and len(cells) >= 5:
                                permit_data["designerCompany"] = cells[4].get_text(strip=True)
                        
                        elif '監造人' in label and len(cells) >= 4:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data["supervisorName"] = cells[2].get_text(strip=True)
                            if '事務所' in cells[3].get_text(strip=True) and len(cells) >= 5:
                                permit_data["supervisorCompany"] = cells[4].get_text(strip=True)
                        
                        elif '承造人' in label and len(cells) >= 4:
                            if '姓名' in cells[1].get_text(strip=True):
                                permit_data["contractorName"] = cells[2].get_text(strip=True)
                            if len(cells) >= 5:
                                permit_data["contractorCompany"] = cells[4].get_text(strip=True)
                        
                        elif '專任工程人員' in label:
                            permit_data["engineerName"] = cells[1].get_text(strip=True)
                        
                        elif '地號' in label:
                            land_text = cells[1].get_text(strip=True)
                            permit_data["siteAddress"] = land_text
                            permit_data["landNumber"] = self.extract_land_number(land_text)
                            permit_data["district"] = self.extract_district(land_text)
                        
                        elif '地址' in label:
                            address_text = cells[1].get_text(strip=True)
                            permit_data["siteCity"] = address_text
                            if not permit_data.get("district"):
                                permit_data["district"] = self.extract_district(address_text)
                        
                        elif '使用分區' in label:
                            permit_data["siteZone"] = cells[1].get_text(strip=True)
                        
                        elif '基地面積' in label and len(cells) >= 4:
                            area_text = cells[3].get_text(strip=True)
                            area_match = re.search(r'([\d.]+)', area_text)
                            if area_match:
                                try:
                                    permit_data["siteArea"] = float(area_match.group(1))
                                except ValueError:
                                    pass
                        
                        elif '層棟戶數' in label:
                            floor_info = cells[1].get_text(strip=True)
                            permit_data["floorInfo"] = floor_info
                            building_info = self.extract_building_info(floor_info)
                            permit_data["buildingCount"] = building_info["buildingCount"]
                            permit_data["unitCount"] = building_info["unitCount"]
                        
                        elif '總樓地板面積' in label:
                            area_text = cells[1].get_text(strip=True)
                            area_match = re.search(r'([\d.]+)', area_text)
                            if area_match:
                                try:
                                    permit_data["totalFloorArea"] = float(area_match.group(1))
                                except ValueError:
                                    pass
                        
                        elif '發照日期' in label:
                            date_text = cells[1].get_text(strip=True)
                            permit_data["issueDate"] = self.parse_issue_date(date_text)

            # 檢查是否有必要資料
            if not permit_data["permitNumber"]:
                logger.warning(f"⚠️  INDEX_KEY {index_key}: 未找到建照號碼")
                return None

            return permit_data
            
        except Exception as e:
            logger.error(f"❌ 解析建照資料錯誤: {e}")
            return None

    def load_existing_data(self):
        """載入現有資料"""
        try:
            response = self.object_storage_client.get_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name="data/permits.json"
            )
            data = json.loads(response.data.content.decode('utf-8'))
            return data.get("permits", [])
        except Exception as e:
            logger.info(f"載入現有資料失敗 (可能是首次執行): {e}")
            return []

    def save_data(self, permits):
        """儲存資料到Object Storage"""
        try:
            data = {
                "lastUpdate": datetime.now().isoformat(),
                "totalCount": len(permits),
                "permits": permits
            }
            
            content = json.dumps(data, ensure_ascii=False, indent=2)
            
            self.object_storage_client.put_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name="data/permits.json",
                put_object_body=content.encode('utf-8'),
                content_type="application/json"
            )
            
            logger.info(f"💾 已儲存 {len(permits)} 筆建照資料")
            
        except Exception as e:
            logger.error(f"儲存資料錯誤: {e}")

    def save_log(self):
        """儲存執行記錄"""
        try:
            # 載入現有記錄
            try:
                response = self.object_storage_client.get_object(
                    namespace_name=self.namespace,
                    bucket_name=self.bucket_name,
                    object_name="data/crawl-logs.json"
                )
                log_data = json.loads(response.data.content.decode('utf-8'))
                logs = log_data.get("logs", [])
            except:
                logs = []

            log_entry = {
                "date": date.today().isoformat(),
                "startTime": self.stats["startTime"].isoformat(),
                "endTime": self.stats["endTime"].isoformat(),
                "totalCrawled": self.stats["totalCrawled"],
                "newRecords": self.stats["newRecords"],
                "errorRecords": self.stats["errorRecords"],
                "status": "completed" if self.stats["errorRecords"] <= self.stats["newRecords"] else "failed"
            }

            # 移除今日舊記錄
            logs = [log for log in logs if log.get("date") != log_entry["date"]]
            logs.insert(0, log_entry)

            # 只保留最近30天記錄
            logs = logs[:30]

            content = json.dumps({"logs": logs}, ensure_ascii=False, indent=2)
            
            self.object_storage_client.put_object(
                namespace_name=self.namespace,
                bucket_name=self.bucket_name,
                object_name="data/crawl-logs.json",
                put_object_body=content.encode('utf-8'),
                content_type="application/json"
            )
            
            logger.info("📋 已儲存執行記錄")
            
        except Exception as e:
            logger.error(f"儲存記錄錯誤: {e}")

    def get_max_sequence_number(self, permits, year, permit_type):
        """取得最大序號"""
        filtered = [p for p in permits if p.get("permitYear") == year and p.get("permitType") == permit_type]
        if not filtered:
            return 0
        return max([p.get("sequenceNumber", 0) for p in filtered])

    def crawl_single_permit(self, index_key):
        """爬取單一建照"""
        try:
            html_content = self.fetch_page_with_retry(index_key)
            if not html_content:
                logger.error(f"❌ 無法獲取頁面: {index_key}")
                self.stats["errorRecords"] += 1
                return None

            permit_data = self.parse_permit_data(html_content, index_key)
            if not permit_data:
                return None

            logger.info(f"✅ 成功解析建照: {permit_data['permitNumber']}")
            self.stats["newRecords"] += 1
            self.stats["totalCrawled"] += 1
            
            return permit_data
            
        except Exception as e:
            logger.error(f"❌ 爬取建照錯誤: {e}")
            self.stats["errorRecords"] += 1
            return None

    def crawl(self):
        """主要爬蟲執行"""
        logger.info(f"📅 執行時間: {self.stats['startTime'].isoformat()}")

        try:
            # 載入現有資料
            existing_permits = self.load_existing_data()
            logger.info(f"📊 現有資料: {len(existing_permits)} 筆")

            # 獲取最大序號
            max_sequence = self.get_max_sequence_number(existing_permits, self.start_year, self.crawl_type)
            current_sequence = max(max_sequence, 1)
            consecutive_failures = 0
            max_consecutive_failures = 50

            logger.info(f"🔢 從序號 {current_sequence} 開始爬取")

            new_permits = []

            # 限制Functions執行時間，最多爬取50筆
            while consecutive_failures < max_consecutive_failures and len(new_permits) < 50:
                index_key = self.generate_index_key(self.start_year, self.crawl_type, current_sequence)
                permit_data = self.crawl_single_permit(index_key)

                if permit_data:
                    # 檢查是否已存在
                    exists = any(p.get("indexKey") == index_key for p in existing_permits)
                    if not exists:
                        new_permits.append(permit_data)
                        consecutive_failures = 0
                else:
                    consecutive_failures += 1

                current_sequence += 1
                
                # 延遲避免過度請求
                time.sleep(self.delay_ms / 1000)

            # 合併新舊資料
            all_permits = existing_permits + new_permits
            
            # 依序號排序
            all_permits.sort(key=lambda x: (
                -x.get("permitYear", 0),
                x.get("permitType", 0),
                -x.get("sequenceNumber", 0)
            ))

            # 儲存資料
            self.save_data(all_permits)

            self.stats["endTime"] = datetime.now()
            self.save_log()

            result = {
                "success": True,
                "totalCrawled": self.stats["totalCrawled"],
                "newRecords": self.stats["newRecords"],
                "errorRecords": self.stats["errorRecords"],
                "executionTime": (self.stats["endTime"] - self.stats["startTime"]).total_seconds()
            }

            logger.info(f"✅ 爬蟲任務完成: 總計 {self.stats['totalCrawled']} 筆，新增 {self.stats['newRecords']} 筆，錯誤 {self.stats['errorRecords']} 筆")
            
            return result

        except Exception as e:
            self.stats["endTime"] = datetime.now()
            self.save_log()
            logger.error(f"❌ 爬蟲執行失敗: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "totalCrawled": self.stats["totalCrawled"],
                "newRecords": self.stats["newRecords"],
                "errorRecords": self.stats["errorRecords"]
            }
    
    def extract_land_number(self, text):
        """從文字中提取地號"""
        if not text:
            return None
        # 匹配完整地號格式
        match = re.search(r'(臺中市[^區]+區[^段]+段[\d-]+地號)', text)
        if match:
            return match.group(1)
        # 匹配簡化地號格式
        match = re.search(r'([^市區]+段[\d-]+地號)', text)
        if match:
            return match.group(1)
        return text

    def extract_district(self, text):
        """從文字中提取行政區"""
        if not text:
            return None
        # 先嘗試從完整格式中提取
        match = re.search(r'臺中市([^區]+區)', text)
        if match:
            return match.group(1)
        # 匹配已知的行政區
        districts = [
            '西屯區', '南屯區', '北屯區', '西區', '南區', '北區', '東區', '中區',
            '太平區', '大里區', '烏日區', '豐原區', '霧峰區', '大雅區', '潭子區',
            '后里區', '神岡區', '梧棲區', '清水區', '大甲區', '外埔區', '大安區',
            '沙鹿區', '龍井區', '大肚區', '新社區', '石岡區', '東勢區', '和平區'
        ]
        for district in districts:
            if district in text:
                return district
        return None

    def extract_building_info(self, text):
        """從層棟戶數文字中提取棟數和戶數"""
        if not text:
            return {'buildingCount': None, 'unitCount': None}
        
        building_match = re.search(r'(\d+)棟', text)
        unit_match = re.search(r'(\d+)戶', text)
        
        return {
            'buildingCount': int(building_match.group(1)) if building_match else None,
            'unitCount': int(unit_match.group(1)) if unit_match else None
        }
    
    def parse_issue_date(self, text):
        """解析發照日期"""
        if not text:
            return None
        # 嘗試解析民國年格式
        date_match = re.search(r'(\d+)年(\d+)月(\d+)日', text)
        if date_match:
            try:
                year = int(date_match.group(1)) + 1911  # 民國年轉西元年
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                return f"{year:04d}-{month:02d}-{day:02d}"
            except:
                return text
        return text