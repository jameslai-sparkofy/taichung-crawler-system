#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寶佳機構公司管理與建照篩選系統
"""

import json
import os
import subprocess
from typing import List, Dict, Set
import re

class BaojiaManager:
    def __init__(self, db_file='baojia_companies.json', oci_namespace='nrsdi1rz5vl8', bucket_name='taichung-building-permits'):
        self.db_file = db_file
        self.oci_namespace = oci_namespace
        self.bucket_name = bucket_name
        self.companies = self._load_companies()
    
    def _load_companies(self) -> Set[str]:
        """載入寶佳機構公司清單"""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('companies', []))
        return set()
    
    def _save_companies(self):
        """儲存公司清單"""
        data = {
            "companies": sorted(list(self.companies)),
            "lastUpdated": subprocess.run(['date', '+%Y-%m-%d'], capture_output=True, text=True).stdout.strip(),
            "description": "寶佳機構體系公司清單"
        }
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 同步到OCI
        self._upload_to_oci()
    
    def _upload_to_oci(self):
        """上傳到OCI物件儲存"""
        print("📤 上傳寶佳公司資料庫到OCI...")
        result = subprocess.run([
            'oci', 'os', 'object', 'put',
            '--namespace', self.oci_namespace,
            '--bucket-name', self.bucket_name,
            '--name', 'data/baojia_companies.json',
            '--file', self.db_file,
            '--force'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 上傳成功")
        else:
            print(f"❌ 上傳失敗: {result.stderr}")
    
    def add_company(self, company_name: str) -> bool:
        """新增公司"""
        if company_name and company_name not in self.companies:
            self.companies.add(company_name)
            self._save_companies()
            print(f"✅ 已新增: {company_name}")
            return True
        else:
            print(f"⚠️ 公司已存在或名稱無效: {company_name}")
            return False
    
    def remove_company(self, company_name: str) -> bool:
        """刪除公司"""
        if company_name in self.companies:
            self.companies.remove(company_name)
            self._save_companies()
            print(f"✅ 已刪除: {company_name}")
            return True
        else:
            print(f"⚠️ 公司不存在: {company_name}")
            return False
    
    def list_companies(self) -> List[str]:
        """列出所有公司"""
        return sorted(list(self.companies))
    
    def search_companies(self, keyword: str) -> List[str]:
        """搜尋公司名稱"""
        keyword = keyword.lower()
        return sorted([c for c in self.companies if keyword in c.lower()])
    
    def filter_baojia_permits(self, permits_file='/tmp/permits.json', output_file='/tmp/baojia_permits.json') -> Dict:
        """篩選寶佳機構的建照"""
        # 下載最新建照資料
        print("📥 下載最新建照資料...")
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', self.oci_namespace,
            '--bucket-name', self.bucket_name,
            '--name', 'data/permits.json',
            '--file', permits_file
        ], capture_output=True)
        
        with open(permits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 智慧篩選
        baojia_permits = []
        company_stats = {}
        
        for permit in data.get('permits', []):
            applicant = permit.get('applicantName', '').strip()
            
            # 完全匹配
            if applicant in self.companies:
                baojia_permits.append(permit)
                company_stats[applicant] = company_stats.get(applicant, 0) + 1
                continue
            
            # 智慧匹配 (包含公司名稱的一部分)
            for company in self.companies:
                # 檢查是否包含主要關鍵字
                if self._smart_match(applicant, company):
                    baojia_permits.append(permit)
                    company_stats[company] = company_stats.get(company, 0) + 1
                    break
        
        # 儲存結果
        result = {
            "totalCount": len(baojia_permits),
            "permits": baojia_permits,
            "companyStats": company_stats,
            "lastUpdated": subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'], capture_output=True, text=True).stdout.strip()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 上傳結果到OCI
        print(f"\n📤 上傳篩選結果到OCI...")
        subprocess.run([
            'oci', 'os', 'object', 'put',
            '--namespace', self.oci_namespace,
            '--bucket-name', self.bucket_name,
            '--name', 'data/baojia_permits.json',
            '--file', output_file,
            '--force'
        ], capture_output=True)
        
        return result
    
    def _smart_match(self, applicant: str, company: str) -> bool:
        """智慧匹配公司名稱"""
        # 移除常見的公司後綴
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
        
        # 包含匹配
        if clean_company in clean_applicant or clean_applicant in clean_company:
            return True
        
        # 特殊情況：寶佳相關變體
        if '寶佳' in company and '寶佳' in applicant:
            return True
        
        return False
    
    def generate_report(self):
        """生成統計報告"""
        result = self.filter_baojia_permits()
        
        print("\n" + "="*60)
        print("📊 寶佳機構建照統計報告")
        print("="*60)
        print(f"🏢 寶佳機構公司數量: {len(self.companies)}")
        print(f"📋 寶佳機構建照總數: {result['totalCount']}")
        print(f"📅 最後更新時間: {result['lastUpdated']}")
        
        if result['companyStats']:
            print("\n🏗️ 各公司建照數量:")
            print("-"*40)
            sorted_stats = sorted(result['companyStats'].items(), key=lambda x: x[1], reverse=True)
            for company, count in sorted_stats[:20]:  # 顯示前20名
                print(f"  {company}: {count} 件")
            
            if len(sorted_stats) > 20:
                print(f"  ... 還有 {len(sorted_stats) - 20} 家公司")
        
        print("\n✅ 報告生成完成！")
        print(f"📁 詳細資料已儲存至: /tmp/baojia_permits.json")


def main():
    """主程式"""
    manager = BaojiaManager()
    
    while True:
        print("\n" + "="*50)
        print("🏢 寶佳機構建照管理系統")
        print("="*50)
        print("1. 列出所有寶佳機構公司")
        print("2. 搜尋公司")
        print("3. 新增公司")
        print("4. 刪除公司")
        print("5. 篩選寶佳機構建照")
        print("6. 生成統計報告")
        print("0. 結束")
        print("-"*50)
        
        choice = input("請選擇功能 (0-6): ").strip()
        
        if choice == '0':
            print("👋 再見！")
            break
        
        elif choice == '1':
            companies = manager.list_companies()
            print(f"\n📋 寶佳機構公司清單 (共 {len(companies)} 家):")
            print("-"*40)
            for i, company in enumerate(companies, 1):
                print(f"{i:3d}. {company}")
        
        elif choice == '2':
            keyword = input("\n請輸入搜尋關鍵字: ").strip()
            if keyword:
                results = manager.search_companies(keyword)
                if results:
                    print(f"\n🔍 找到 {len(results)} 家公司:")
                    for company in results:
                        print(f"  - {company}")
                else:
                    print("❌ 沒有找到符合的公司")
        
        elif choice == '3':
            company_name = input("\n請輸入要新增的公司名稱: ").strip()
            manager.add_company(company_name)
        
        elif choice == '4':
            company_name = input("\n請輸入要刪除的公司名稱: ").strip()
            manager.remove_company(company_name)
        
        elif choice == '5':
            print("\n🔄 開始篩選寶佳機構建照...")
            result = manager.filter_baojia_permits()
            print(f"\n✅ 篩選完成！")
            print(f"📊 找到 {result['totalCount']} 筆寶佳機構建照")
            print(f"📁 結果已儲存至: /tmp/baojia_permits.json")
        
        elif choice == '6':
            manager.generate_report()
        
        else:
            print("❌ 無效的選擇，請重試")


if __name__ == "__main__":
    main()