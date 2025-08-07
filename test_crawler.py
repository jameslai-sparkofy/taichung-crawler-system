import logging
import os
from dotenv import load_dotenv
from building_permit_crawler import BuildingPermitCrawler
from database_manager import DatabaseManager

load_dotenv()

def setup_test_logging():
    """設定測試日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_crawler.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def test_database_connection():
    """測試資料庫連接"""
    print("測試資料庫連接...")
    db_manager = DatabaseManager()
    
    if db_manager.connect():
        print("✅ 資料庫連接成功")
        db_manager.disconnect()
        return True
    else:
        print("❌ 資料庫連接失敗")
        return False

def test_single_permit_crawl():
    """測試爬取單一建照"""
    print("測試爬取單一建照...")
    
    crawler = BuildingPermitCrawler()
    
    # 測試已知存在的建照
    test_index_key = "11410000100"
    
    try:
        if not crawler.db_manager.connect():
            print("❌ 無法連接資料庫")
            return False
        
        success = crawler.crawl_single_permit(test_index_key)
        
        if success:
            print(f"✅ 成功爬取建照: {test_index_key}")
            return True
        else:
            print(f"❌ 爬取建照失敗: {test_index_key}")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        return False
    finally:
        crawler.db_manager.disconnect()

def test_index_key_generation():
    """測試INDEX_KEY生成和解析"""
    print("測試INDEX_KEY生成和解析...")
    
    crawler = BuildingPermitCrawler()
    
    # 測試生成
    year = 114
    permit_type = 1
    sequence = 1
    version = 0
    
    index_key = crawler.generate_index_key(year, permit_type, sequence, version)
    expected = "11410000100"
    
    if index_key == expected:
        print(f"✅ INDEX_KEY生成正確: {index_key}")
    else:
        print(f"❌ INDEX_KEY生成錯誤: 期望 {expected}, 實際 {index_key}")
        return False
    
    # 測試解析
    parsed = crawler.parse_index_key(index_key)
    
    if (parsed and 
        parsed['year'] == year and 
        parsed['permit_type'] == permit_type and
        parsed['sequence'] == sequence and
        parsed['version'] == version):
        print("✅ INDEX_KEY解析正確")
        return True
    else:
        print(f"❌ INDEX_KEY解析錯誤: {parsed}")
        return False

def test_page_fetch():
    """測試頁面獲取"""
    print("測試頁面獲取...")
    
    crawler = BuildingPermitCrawler()
    test_index_key = "11410000100"
    
    try:
        response = crawler.fetch_page_with_retry(test_index_key)
        
        if response and response.status_code == 200:
            if '建築執照號碼' in response.text:
                print("✅ 頁面獲取成功且包含建照資料")
                return True
            else:
                print("❌ 頁面獲取成功但不包含建照資料")
                return False
        else:
            print("❌ 頁面獲取失敗")
            return False
            
    except Exception as e:
        print(f"❌ 頁面獲取測試發生錯誤: {e}")
        return False

def test_small_batch_crawl():
    """測試小批量爬取"""
    print("測試小批量爬取 (5筆資料)...")
    
    crawler = BuildingPermitCrawler()
    
    try:
        if not crawler.db_manager.connect():
            print("❌ 無法連接資料庫")
            return False
        
        # 重置統計
        crawler.total_crawled = 0
        crawler.new_records = 0
        crawler.error_records = 0
        
        # 測試爬取114年前5個編號
        for sequence in range(1, 6):
            index_key = crawler.generate_index_key(114, 1, sequence)
            success = crawler.crawl_single_permit(index_key)
            print(f"  編號 {sequence}: {'成功' if success else '失敗'}")
        
        print(f"✅ 小批量測試完成")
        print(f"   總爬取: {crawler.total_crawled} 筆")
        print(f"   新增: {crawler.new_records} 筆")
        print(f"   錯誤: {crawler.error_records} 筆")
        
        return True
        
    except Exception as e:
        print(f"❌ 小批量爬取測試發生錯誤: {e}")
        return False
    finally:
        crawler.db_manager.disconnect()

def main():
    """主測試程序"""
    setup_test_logging()
    
    print("🚀 開始爬蟲系統測試")
    print("=" * 50)
    
    tests = [
        ("資料庫連接", test_database_connection),
        ("INDEX_KEY生成和解析", test_index_key_generation),
        ("頁面獲取", test_page_fetch),
        ("單一建照爬取", test_single_permit_crawl),
        ("小批量爬取", test_small_batch_crawl),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 執行測試: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 測試失敗")
        except Exception as e:
            print(f"❌ {test_name} 測試發生異常: {e}")
        
        print("-" * 30)
    
    print(f"\n🏁 測試完成: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！爬蟲系統準備就緒")
    else:
        print("⚠️  部分測試失敗，請檢查配置和環境")

if __name__ == "__main__":
    main()