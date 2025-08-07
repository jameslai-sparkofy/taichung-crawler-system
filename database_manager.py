import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '3306')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME', 'taichung_building_permits')
        self.connection = None
        
    def connect(self):
        """連接資料庫"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            if self.connection.is_connected():
                logging.info("成功連接到MySQL資料庫")
                return True
        except Error as e:
            logging.error(f"連接資料庫時發生錯誤: {e}")
            return False
    
    def disconnect(self):
        """斷開資料庫連接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("資料庫連接已關閉")
    
    def insert_permit(self, permit_data):
        """插入建照資料"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
            INSERT INTO building_permits (
                permit_number, permit_year, permit_type, sequence_number, version_number,
                applicant_name, designer_name, designer_company, supervisor_name, supervisor_company,
                contractor_name, contractor_company, engineer_name, site_address, site_city,
                site_zone, site_area, crawled_at
            ) VALUES (
                %(permit_number)s, %(permit_year)s, %(permit_type)s, %(sequence_number)s, %(version_number)s,
                %(applicant_name)s, %(designer_name)s, %(designer_company)s, %(supervisor_name)s, %(supervisor_company)s,
                %(contractor_name)s, %(contractor_company)s, %(engineer_name)s, %(site_address)s, %(site_city)s,
                %(site_zone)s, %(site_area)s, %(crawled_at)s
            ) ON DUPLICATE KEY UPDATE
                applicant_name = VALUES(applicant_name),
                designer_name = VALUES(designer_name),
                designer_company = VALUES(designer_company),
                supervisor_name = VALUES(supervisor_name),
                supervisor_company = VALUES(supervisor_company),
                contractor_name = VALUES(contractor_name),
                contractor_company = VALUES(contractor_company),
                engineer_name = VALUES(engineer_name),
                site_address = VALUES(site_address),
                site_city = VALUES(site_city),
                site_zone = VALUES(site_zone),
                site_area = VALUES(site_area),
                updated_at = CURRENT_TIMESTAMP,
                crawled_at = VALUES(crawled_at)
            """
            
            cursor.execute(insert_query, permit_data)
            self.connection.commit()
            
            if cursor.rowcount == 1:
                logging.info(f"成功新增建照資料: {permit_data['permit_number']}")
                return 'new'
            elif cursor.rowcount == 2:
                logging.info(f"成功更新建照資料: {permit_data['permit_number']}")
                return 'updated'
            else:
                logging.info(f"建照資料無變更: {permit_data['permit_number']}")
                return 'no_change'
                
        except Error as e:
            logging.error(f"插入建照資料時發生錯誤: {e}")
            self.connection.rollback()
            return 'error'
        finally:
            if cursor:
                cursor.close()
    
    def start_crawl_log(self, crawl_date):
        """開始爬蟲記錄"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
            INSERT INTO crawl_logs (crawl_date, start_time, status)
            VALUES (%s, %s, 'running')
            ON DUPLICATE KEY UPDATE
                start_time = VALUES(start_time),
                status = 'running',
                end_time = NULL,
                error_message = NULL
            """
            
            cursor.execute(insert_query, (crawl_date, datetime.now()))
            self.connection.commit()
            
            return cursor.lastrowid if cursor.rowcount == 1 else self.get_crawl_log_id(crawl_date)
            
        except Error as e:
            logging.error(f"建立爬蟲記錄時發生錯誤: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def update_crawl_log(self, crawl_date, status, total_records=0, new_records=0, error_records=0, error_message=None):
        """更新爬蟲記錄"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            update_query = """
            UPDATE crawl_logs 
            SET end_time = %s, status = %s, total_records = %s, 
                new_records = %s, error_records = %s, error_message = %s
            WHERE crawl_date = %s
            """
            
            cursor.execute(update_query, (
                datetime.now(), status, total_records, new_records, error_records, error_message, crawl_date
            ))
            self.connection.commit()
            
        except Error as e:
            logging.error(f"更新爬蟲記錄時發生錯誤: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_crawl_log_id(self, crawl_date):
        """取得爬蟲記錄ID"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM crawl_logs WHERE crawl_date = %s", (crawl_date,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            logging.error(f"查詢爬蟲記錄ID時發生錯誤: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def get_max_sequence_number(self, year, permit_type):
        """取得指定年份和類型的最大編號"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT MAX(sequence_number) 
            FROM building_permits 
            WHERE permit_year = %s AND permit_type = %s
            """
            cursor.execute(query, (year, permit_type))
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        except Error as e:
            logging.error(f"查詢最大編號時發生錯誤: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
    
    def check_permit_exists(self, permit_number):
        """檢查建照是否已存在"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM building_permits WHERE permit_number = %s", (permit_number,))
            result = cursor.fetchone()
            return result is not None
        except Error as e:
            logging.error(f"檢查建照是否存在時發生錯誤: {e}")
            return False
        finally:
            if cursor:
                cursor.close()