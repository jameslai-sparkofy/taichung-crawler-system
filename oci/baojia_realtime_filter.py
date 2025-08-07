#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寶佳機構建照即時篩選系統
"""

import json
import subprocess
from typing import List, Dict, Set
import os
from datetime import datetime

class BaojiaRealtimeFilter:
    def __init__(self, db_file='baojia_companies.json'):
        self.db_file = db_file
        self.companies = self._load_companies()
        self.oci_namespace = 'nrsdi1rz5vl8'
        self.bucket_name = 'taichung-building-permits'
    
    def _load_companies(self) -> Set[str]:
        """從OCI載入最新的寶佳公司清單"""
        # 先嘗試從OCI下載最新版本
        try:
            subprocess.run([
                'oci', 'os', 'object', 'get',
                '--namespace', 'nrsdi1rz5vl8',
                '--bucket-name', 'taichung-building-permits',
                '--name', 'data/baojia_companies.json',
                '--file', '/tmp/baojia_companies_latest.json'
            ], capture_output=True, check=True)
            
            with open('/tmp/baojia_companies_latest.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('companies', []))
        except:
            # 如果OCI下載失敗，使用本地檔案
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('companies', []))
            return set()
    
    def is_baojia_company(self, applicant_name: str) -> bool:
        """即時判斷是否為寶佳機構公司"""
        if not applicant_name:
            return False
        
        # 重新載入最新公司清單（確保即時性）
        if not self.companies:  # 只在沒有公司資料時才重新載入
            self.companies = self._load_companies()
        
        # 完全匹配
        if applicant_name in self.companies:
            return True
        
        # 智慧匹配
        for company in self.companies:
            if self._smart_match(applicant_name, company):
                return True
        
        return False
    
    def _smart_match(self, applicant: str, company: str) -> bool:
        """智慧匹配公司名稱"""
        suffixes = ['股份有限公司', '有限公司', '建設股份有限公司', '營造股份有限公司', '營造有限公司']
        
        clean_applicant = applicant
        clean_company = company
        
        for suffix in suffixes:
            clean_applicant = clean_applicant.replace(suffix, '')
            clean_company = clean_company.replace(suffix, '')
        
        clean_applicant = clean_applicant.strip()
        clean_company = clean_company.strip()
        
        # 完全匹配（忽略後綴）
        if clean_applicant == clean_company:
            return True
        
        # 特殊情況：寶佳相關變體 (但不包含"非"字)
        if '寶佳' in company and '寶佳' in applicant and '非' not in applicant:
            return True
        
        return False
    
    def filter_permits_realtime(self, permits: List[Dict]) -> Dict:
        """即時篩選建照資料"""
        # 重新載入最新公司清單
        self.companies = self._load_companies()
        
        baojia_permits = []
        company_stats = {}
        
        for permit in permits:
            applicant = permit.get('applicantName', '').strip()
            
            if self.is_baojia_company(applicant):
                baojia_permits.append(permit)
                
                # 找出匹配的公司名稱用於統計
                matched_company = applicant
                for company in self.companies:
                    if self._smart_match(applicant, company):
                        matched_company = company
                        break
                
                company_stats[matched_company] = company_stats.get(matched_company, 0) + 1
        
        return {
            "totalCount": len(baojia_permits),
            "permits": baojia_permits,
            "companyStats": company_stats,
            "lastUpdated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "companiesCount": len(self.companies)
        }
    
    def add_company_realtime(self, company_name: str) -> bool:
        """即時新增公司並同步到OCI"""
        # 載入最新資料
        self.companies = self._load_companies()
        
        if company_name and company_name not in self.companies:
            self.companies.add(company_name)
            
            # 儲存到本地和OCI
            data = {
                "companies": sorted(list(self.companies)),
                "lastUpdated": datetime.now().strftime('%Y-%m-%d'),
                "description": "寶佳機構體系公司清單"
            }
            
            # 儲存本地
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 上傳到OCI
            subprocess.run([
                'oci', 'os', 'object', 'put',
                '--namespace', self.oci_namespace,
                '--bucket-name', self.bucket_name,
                '--name', 'data/baojia_companies.json',
                '--file', self.db_file,
                '--force'
            ], capture_output=True)
            
            print(f"✅ 已新增並同步: {company_name}")
            return True
        
        return False
    
    def remove_company_realtime(self, company_name: str) -> bool:
        """即時刪除公司並同步到OCI"""
        # 載入最新資料
        self.companies = self._load_companies()
        
        if company_name in self.companies:
            self.companies.remove(company_name)
            
            # 儲存到本地和OCI
            data = {
                "companies": sorted(list(self.companies)),
                "lastUpdated": datetime.now().strftime('%Y-%m-%d'),
                "description": "寶佳機構體系公司清單"
            }
            
            # 儲存本地
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 上傳到OCI
            subprocess.run([
                'oci', 'os', 'object', 'put',
                '--namespace', self.oci_namespace,
                '--bucket-name', self.bucket_name,
                '--name', 'data/baojia_companies.json',
                '--file', self.db_file,
                '--force'
            ], capture_output=True)
            
            print(f"✅ 已刪除並同步: {company_name}")
            return True
        
        return False


# 修改爬蟲程式，加入即時篩選功能
def create_enhanced_crawler():
    """建立具有即時寶佳篩選功能的爬蟲"""
    code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台中市建照爬蟲 - 具備即時寶佳機構篩選功能
"""

# 載入原始爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 載入即時篩選器
from baojia_realtime_filter import BaojiaRealtimeFilter

class EnhancedCrawler(OptimizedCrawler):
    def __init__(self):
        super().__init__()
        self.baojia_filter = BaojiaRealtimeFilter()
    
    def crawl_single_permit(self, index_key):
        """爬取單筆建照並即時標記是否為寶佳機構"""
        result = super().crawl_single_permit(index_key)
        
        if result and isinstance(result, dict):
            # 即時判斷是否為寶佳機構
            applicant = result.get('applicantName', '')
            if applicant:
                result['isBaojia'] = self.baojia_filter.is_baojia_company(applicant)
                if result['isBaojia']:
                    print(f"  🏢 寶佳機構建案: {applicant}")
        
        return result
    
    def upload_batch_data(self, batch_data):
        """上傳資料並同時更新寶佳篩選結果"""
        # 先執行原本的上傳
        success = super().upload_batch_data(batch_data)
        
        if success:
            # 即時更新寶佳篩選結果
            self._update_baojia_filter_results()
        
        return success
    
    def _update_baojia_filter_results(self):
        """更新寶佳篩選結果到OCI"""
        try:
            # 下載最新建照資料
            subprocess.run([
                'oci', 'os', 'object', 'get',
                '--namespace', self.namespace,
                '--bucket-name', self.bucket_name,
                '--name', 'data/permits.json',
                '--file', '/tmp/permits_for_filter.json'
            ], capture_output=True)
            
            with open('/tmp/permits_for_filter.json', 'r') as f:
                data = json.load(f)
            
            # 即時篩選
            filter_result = self.baojia_filter.filter_permits_realtime(data.get('permits', []))
            
            # 儲存篩選結果
            with open('/tmp/baojia_realtime_results.json', 'w') as f:
                json.dump(filter_result, f, ensure_ascii=False, indent=2)
            
            # 上傳到OCI
            subprocess.run([
                'oci', 'os', 'object', 'put',
                '--namespace', self.namespace,
                '--bucket-name', self.bucket_name,
                '--name', 'data/baojia_realtime_results.json',
                '--file', '/tmp/baojia_realtime_results.json',
                '--force'
            ], capture_output=True)
            
            print(f"  📊 寶佳篩選結果已更新: {filter_result['totalCount']} 筆")
            
        except Exception as e:
            print(f"  ⚠️ 更新寶佳篩選結果失敗: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("使用方式: python enhanced-crawler.py <年份> <起始序號> [結束序號]")
        sys.exit(1)
    
    year = int(sys.argv[1])
    start_seq = int(sys.argv[2])
    end_seq = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    crawler = EnhancedCrawler()
    
    if end_seq:
        print(f"開始爬取 {year} 年建照資料，序號 {start_seq} 到 {end_seq}")
        crawler.crawl_year_range(year, start_seq, end_seq)
    else:
        print(f"開始爬取 {year} 年建照資料，從序號 {start_seq} 開始")
        crawler.crawl_year_continuous(year, start_seq)
'''
    
    with open('/mnt/c/claude code/建照爬蟲/oci/enhanced-crawler.py', 'w', encoding='utf-8') as f:
        f.write(code)
    
    print("✅ 已建立具有即時寶佳篩選功能的爬蟲: enhanced-crawler.py")


# 建立即時查詢API
def create_realtime_api():
    """建立即時查詢API"""
    code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寶佳機構建照即時查詢API
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from baojia_realtime_filter import BaojiaRealtimeFilter
import subprocess
import json
import os

app = Flask(__name__)
CORS(app)

# 初始化篩選器
filter_instance = BaojiaRealtimeFilter()

@app.route('/api/baojia/check/<permit_number>')
def check_permit(permit_number):
    """即時檢查單筆建照是否為寶佳機構"""
    # 從OCI下載最新資料
    subprocess.run([
        'oci', 'os', 'object', 'get',
        '--namespace', 'nrsdi1rz5vl8',
        '--bucket-name', 'taichung-building-permits',
        '--name', 'data/permits.json',
        '--file', '/tmp/check_permits.json'
    ], capture_output=True)
    
    with open('/tmp/check_permits.json', 'r') as f:
        data = json.load(f)
    
    # 尋找指定建照
    for permit in data.get('permits', []):
        if permit.get('permitNumber') == permit_number:
            applicant = permit.get('applicantName', '')
            is_baojia = filter_instance.is_baojia_company(applicant)
            
            return jsonify({
                'permitNumber': permit_number,
                'applicantName': applicant,
                'isBaojia': is_baojia,
                'permitData': permit
            })
    
    return jsonify({'error': '找不到指定建照'}), 404

@app.route('/api/baojia/realtime-stats')
def realtime_stats():
    """取得即時統計資料"""
    # 檢查是否有最新的即時篩選結果
    try:
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits',
            '--name', 'data/baojia_realtime_results.json',
            '--file', '/tmp/realtime_results.json'
        ], capture_output=True, check=True)
        
        with open('/tmp/realtime_results.json', 'r') as f:
            return jsonify(json.load(f))
    
    except:
        # 如果沒有即時結果，執行即時篩選
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits',
            '--name', 'data/permits.json',
            '--file', '/tmp/all_permits.json'
        ], capture_output=True)
        
        with open('/tmp/all_permits.json', 'r') as f:
            data = json.load(f)
        
        result = filter_instance.filter_permits_realtime(data.get('permits', []))
        return jsonify(result)

@app.route('/api/baojia/companies/sync', methods=['POST'])
def sync_companies():
    """同步公司清單變更"""
    data = request.get_json()
    action = data.get('action')
    company_name = data.get('company')
    
    if action == 'add':
        success = filter_instance.add_company_realtime(company_name)
        if success:
            return jsonify({'message': f'已新增並同步: {company_name}'})
        else:
            return jsonify({'error': '公司已存在或名稱無效'}), 400
    
    elif action == 'remove':
        success = filter_instance.remove_company_realtime(company_name)
        if success:
            return jsonify({'message': f'已刪除並同步: {company_name}'})
        else:
            return jsonify({'error': '公司不存在'}), 404
    
    return jsonify({'error': '無效的操作'}), 400

if __name__ == '__main__':
    print("🚀 啟動寶佳機構即時查詢API...")
    app.run(debug=True, host='0.0.0.0', port=5001)
'''
    
    with open('/mnt/c/claude code/建照爬蟲/oci/baojia_realtime_api.py', 'w', encoding='utf-8') as f:
        f.write(code)
    
    print("✅ 已建立即時查詢API: baojia_realtime_api.py")


if __name__ == "__main__":
    # 建立增強版爬蟲
    create_enhanced_crawler()
    
    # 建立即時API
    create_realtime_api()
    
    # 測試即時篩選
    print("\n📊 測試即時篩選功能...")
    filter_test = BaojiaRealtimeFilter()
    
    # 測試一些公司名稱
    test_names = [
        "勝發建設股份有限公司",
        "寶佳建設",
        "合遠建設有限公司",
        "非寶佳公司",
        "勝華建設"
    ]
    
    for name in test_names:
        is_baojia = filter_test.is_baojia_company(name)
        print(f"  {name}: {'✅ 是寶佳機構' if is_baojia else '❌ 非寶佳機構'}")