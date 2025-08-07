#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速篩選寶佳機構建照
"""

from baojia_manager import BaojiaManager
import sys

def main():
    manager = BaojiaManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'list':
            # 列出所有公司
            companies = manager.list_companies()
            print(f"\n📋 寶佳機構公司清單 (共 {len(companies)} 家):")
            print("-" * 50)
            for i, company in enumerate(companies, 1):
                print(f"{i:3d}. {company}")
        
        elif command == 'add' and len(sys.argv) > 2:
            # 新增公司
            company_name = ' '.join(sys.argv[2:])
            manager.add_company(company_name)
        
        elif command == 'remove' and len(sys.argv) > 2:
            # 刪除公司
            company_name = ' '.join(sys.argv[2:])
            manager.remove_company(company_name)
        
        elif command == 'search' and len(sys.argv) > 2:
            # 搜尋公司
            keyword = ' '.join(sys.argv[2:])
            results = manager.search_companies(keyword)
            if results:
                print(f"\n🔍 找到 {len(results)} 家公司:")
                for company in results:
                    print(f"  - {company}")
            else:
                print("❌ 沒有找到符合的公司")
        
        elif command == 'filter':
            # 篩選建照
            print("\n🔄 開始篩選寶佳機構建照...")
            result = manager.filter_baojia_permits()
            print(f"\n✅ 篩選完成！")
            print(f"📊 找到 {result['totalCount']} 筆寶佳機構建照")
            print(f"📁 結果已儲存至: /tmp/baojia_permits.json")
            
            # 顯示前10筆
            if result['permits']:
                print("\n📋 前10筆建照:")
                print("-" * 80)
                for i, permit in enumerate(result['permits'][:10], 1):
                    print(f"{i}. {permit.get('permitNumber')} - {permit.get('applicantName')} - {permit.get('constructionAddress', 'N/A')}")
        
        elif command == 'report':
            # 生成報告
            manager.generate_report()
        
        else:
            print_usage()
    
    else:
        # 互動模式
        print("\n🔄 開始篩選寶佳機構建照...")
        manager.generate_report()

def print_usage():
    print("""
使用方式:
  python filter_baojia.py [指令] [參數]

指令:
  list              列出所有寶佳機構公司
  add <公司名稱>    新增公司
  remove <公司名稱> 刪除公司
  search <關鍵字>   搜尋公司
  filter            篩選寶佳機構建照
  report            生成統計報告

範例:
  python filter_baojia.py list
  python filter_baojia.py add 新寶佳建設
  python filter_baojia.py search 佳
  python filter_baojia.py filter
    """)

if __name__ == "__main__":
    main()