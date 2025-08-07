import schedule
import time
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from building_permit_crawler import BuildingPermitCrawler

load_dotenv()

def setup_logging():
    """設定日誌"""
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.getenv('LOG_FILE', 'scheduler.log'), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def run_daily_crawl():
    """執行每日爬蟲任務"""
    try:
        logging.info("=" * 50)
        logging.info("開始執行排程爬蟲任務")
        
        crawler = BuildingPermitCrawler()
        crawler.daily_crawl()
        
        logging.info("排程爬蟲任務執行完成")
        logging.info("=" * 50)
        
    except Exception as e:
        logging.error(f"排程爬蟲任務執行失敗: {e}")

def main():
    """主程序"""
    setup_logging()
    
    logging.info("建照爬蟲排程器啟動")
    
    # 設定每日執行時間 (預設早上8點)
    schedule_time = os.getenv('DAILY_SCHEDULE_TIME', '08:00')
    schedule.every().day.at(schedule_time).do(run_daily_crawl)
    
    logging.info(f"已設定每日 {schedule_time} 執行爬蟲任務")
    
    # 可選：立即執行一次 (用於測試)
    if os.getenv('RUN_IMMEDIATELY', 'false').lower() == 'true':
        logging.info("立即執行一次爬蟲任務")
        run_daily_crawl()
    
    # 持續運行排程器
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
    except KeyboardInterrupt:
        logging.info("排程器已停止")

if __name__ == "__main__":
    main()