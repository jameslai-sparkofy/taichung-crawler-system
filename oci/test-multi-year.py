#!/usr/bin/env python3
"""
測試多年份爬蟲 - 簡化版本
"""

import requests
import json
from datetime import datetime
import time

def test_crawl_years():
    """測試爬取112-114年資料"""
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    results = {}
    
    # 測試各年份的第1筆資料
    years = [112, 113, 114]
    
    for year in years:
        print(f"\n📅 測試 {year} 年...")
        
        # 測試前3筆
        year_results = []
        for seq in range(1, 4):
            index_key = f"{year}1{seq:05d}00"
            url = f"{base_url}?INDEX_KEY={index_key}"
            
            try:
                print(f"  🔍 測試 {index_key}...", end='')
                
                # 第一次請求
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }, timeout=15)
                
                if response.status_code == 200:
                    time.sleep(1)
                    
                    # 第二次請求
                    response = requests.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }, timeout=15)
                    
                    html = response.text
                    
                    # 檢查是否有建照資料
                    if '建築執照號碼' in html:
                        # 簡單解析建照號碼
                        import re
                        permit_match = re.search(r'建造執照號碼[：:\s]*([^\s<\n]+)', html)
                        if permit_match:
                            permit_no = permit_match.group(1).strip()
                            print(f" ✅ {permit_no}")
                            year_results.append({
                                "indexKey": index_key,
                                "permitNumber": permit_no,
                                "status": "success"
                            })
                        else:
                            print(" ⚠️  找到頁面但無法解析號碼")
                            year_results.append({
                                "indexKey": index_key,
                                "status": "no_number"
                            })
                    elif '○○○代表遺失個資' in html:
                        print(" ℹ️  遺失個資")
                        year_results.append({
                            "indexKey": index_key,
                            "status": "lost_data"
                        })
                    else:
                        print(" ❌ 無資料")
                        year_results.append({
                            "indexKey": index_key,
                            "status": "no_data"
                        })
                else:
                    print(f" ❌ HTTP {response.status_code}")
                    year_results.append({
                        "indexKey": index_key,
                        "status": f"http_{response.status_code}"
                    })
                    
            except Exception as e:
                print(f" ❌ 錯誤: {str(e)[:30]}")
                year_results.append({
                    "indexKey": index_key,
                    "status": "error",
                    "error": str(e)[:50]
                })
            
            time.sleep(2)  # 避免過度請求
        
        results[year] = year_results
    
    return results

def save_test_results(results):
    """儲存測試結果"""
    test_data = {
        "testTime": datetime.now().isoformat(),
        "results": results,
        "summary": {}
    }
    
    # 統計各年份結果
    for year, year_results in results.items():
        success_count = len([r for r in year_results if r.get("status") == "success"])
        test_data["summary"][year] = {
            "total": len(year_results),
            "success": success_count,
            "hasData": success_count > 0
        }
    
    # 儲存到檔案
    with open('multi-year-test-results.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    return test_data

if __name__ == "__main__":
    print("🔧 台中市建照爬蟲 - 多年份測試")
    print("=" * 50)
    
    # 執行測試
    results = test_crawl_years()
    
    # 儲存結果
    test_data = save_test_results(results)
    
    # 顯示摘要
    print("\n📊 測試摘要:")
    print("=" * 50)
    
    for year, summary in test_data["summary"].items():
        status = "✅ 有資料" if summary["hasData"] else "❌ 無資料"
        print(f"{year}年: {status} (成功 {summary['success']}/{summary['total']} 筆)")
    
    print("\n💾 測試結果已儲存至 multi-year-test-results.json")
    
    # 建議
    print("\n💡 建議:")
    available_years = [year for year, summary in test_data["summary"].items() if summary["hasData"]]
    if available_years:
        print(f"可爬取年份: {', '.join(map(str, available_years))}")
    else:
        print("未發現可爬取的年份資料")