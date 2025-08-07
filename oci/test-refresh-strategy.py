#!/usr/bin/env python3
"""
測試重新整理策略 - 需要多次刷新才能獲得正確格式
"""

import requests
import json
from datetime import datetime
import time
import re

def fetch_with_multiple_refresh(index_key, max_refresh=5):
    """多次重新整理直到獲得正確格式"""
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    url = f"{base_url}?INDEX_KEY={index_key}"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
    })
    
    print(f"\n🔍 測試 INDEX_KEY: {index_key}")
    
    # 第一次點擊
    print("  第1次點擊...", end='')
    response = session.get(url, timeout=30)
    print(f" 狀態: {response.status_code}")
    time.sleep(1)
    
    # 第二次點擊
    print("  第2次點擊...", end='')
    response = session.get(url, timeout=30)
    print(f" 狀態: {response.status_code}")
    time.sleep(1)
    
    # 多次重新整理直到獲得正確格式
    for i in range(max_refresh):
        print(f"  重新整理 {i+1}/{max_refresh}...", end='')
        response = session.get(url, timeout=30)
        
        if response.status_code == 200:
            html = response.text
            
            # 檢查是否有正確格式的建照資料
            if '建造執照號碼' in html or '建築執照號碼' in html:
                # 嘗試提取建照號碼
                permit_patterns = [
                    r'建造執照號碼[：:\s]*([^<\s\n]+)',
                    r'建築執照號碼[：:\s]*([^<\s\n]+)',
                    r'(\d{3}中建字第\d+號)',
                    r'執照號碼[：:\s]*(\d{3}中建字第\d+號)'
                ]
                
                for pattern in permit_patterns:
                    match = re.search(pattern, html)
                    if match:
                        permit_no = match.group(1).strip()
                        print(f" ✅ 找到建照: {permit_no}")
                        return {
                            "success": True,
                            "permitNumber": permit_no,
                            "refreshCount": i + 1,
                            "hasTable": '<table' in html,
                            "hasApplicant": '起造人' in html,
                            "hasArea": '基地面積' in html
                        }
                
                # 有關鍵字但沒找到號碼
                print(" ⚠️  有資料但格式不完整")
            elif '○○○代表遺失個資' in html:
                print(" ℹ️  遺失個資")
                return {
                    "success": False,
                    "status": "lost_data",
                    "refreshCount": i + 1
                }
            else:
                # 檢查其他可能的關鍵字
                keywords_found = []
                check_keywords = ['執照', '起造人', '基地', '建築', '台中市']
                for kw in check_keywords:
                    if kw in html:
                        keywords_found.append(kw)
                
                if keywords_found:
                    print(f" 🔍 找到關鍵字: {', '.join(keywords_found)}")
                else:
                    print(" ❌ 無相關內容")
        else:
            print(f" ❌ HTTP {response.status_code}")
        
        # 等待後再重新整理
        time.sleep(2)
    
    return {
        "success": False,
        "status": "no_valid_format",
        "refreshCount": max_refresh
    }

def test_years_with_refresh():
    """測試各年份的資料（使用重新整理策略）"""
    results = {}
    
    # 測試不同年份和序號
    test_cases = [
        # 114年（最新）
        {"year": 114, "sequences": [1, 10, 100, 500, 1000, 2000]},
        # 113年
        {"year": 113, "sequences": [1, 10, 100, 500, 1000, 5000]},
        # 112年
        {"year": 112, "sequences": [1, 10, 100, 500, 1000, 5000]},
    ]
    
    for case in test_cases:
        year = case["year"]
        print(f"\n{'='*50}")
        print(f"📅 測試 {year} 年建照資料")
        print(f"{'='*50}")
        
        year_results = []
        
        for seq in case["sequences"]:
            index_key = f"{year}1{seq:05d}00"
            result = fetch_with_multiple_refresh(index_key)
            result["indexKey"] = index_key
            result["sequence"] = seq
            year_results.append(result)
            
            # 如果找到有效資料，測試附近的序號
            if result.get("success"):
                print(f"\n  🎯 在序號 {seq} 找到資料，測試附近序號...")
                for offset in [-1, 1, 2]:
                    nearby_seq = seq + offset
                    if nearby_seq > 0:
                        nearby_key = f"{year}1{nearby_seq:05d}00"
                        nearby_result = fetch_with_multiple_refresh(nearby_key)
                        nearby_result["indexKey"] = nearby_key
                        nearby_result["sequence"] = nearby_seq
                        year_results.append(nearby_result)
            
            time.sleep(3)  # 避免過度請求
        
        results[year] = year_results
    
    return results

def save_refresh_test_results(results):
    """儲存測試結果"""
    summary = {}
    
    for year, year_results in results.items():
        successful = [r for r in year_results if r.get("success")]
        summary[year] = {
            "totalTested": len(year_results),
            "successful": len(successful),
            "hasData": len(successful) > 0,
            "validSequences": [r["sequence"] for r in successful],
            "avgRefreshNeeded": sum(r.get("refreshCount", 0) for r in successful) / len(successful) if successful else 0
        }
    
    report = {
        "testTime": datetime.now().isoformat(),
        "results": results,
        "summary": summary,
        "recommendations": []
    }
    
    # 產生建議
    for year, stats in summary.items():
        if stats["hasData"]:
            min_seq = min(stats["validSequences"])
            max_seq = max(stats["validSequences"])
            report["recommendations"].append({
                "year": year,
                "suggestedRange": f"{min_seq} - {max_seq + 100}",
                "avgRefreshNeeded": round(stats["avgRefreshNeeded"], 1)
            })
    
    # 儲存結果
    with open('refresh-test-results.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

if __name__ == "__main__":
    print("🔧 台中市建照爬蟲 - 重新整理策略測試")
    print("測試多次點擊和重新整理以獲得正確格式")
    print("=" * 60)
    
    # 執行測試
    results = test_years_with_refresh()
    
    # 儲存並顯示結果
    report = save_refresh_test_results(results)
    
    print(f"\n{'='*60}")
    print("📊 測試結果摘要")
    print(f"{'='*60}")
    
    for year, summary in report["summary"].items():
        print(f"\n{year}年:")
        print(f"  測試數量: {summary['totalTested']}")
        print(f"  成功數量: {summary['successful']}")
        if summary["hasData"]:
            print(f"  有效序號: {summary['validSequences']}")
            print(f"  平均需要重新整理次數: {summary['avgRefreshNeeded']:.1f}")
        else:
            print("  ❌ 未找到有效資料")
    
    print(f"\n💡 爬取建議:")
    if report["recommendations"]:
        for rec in report["recommendations"]:
            print(f"  {rec['year']}年: 序號範圍 {rec['suggestedRange']}，平均需重新整理 {rec['avgRefreshNeeded']} 次")
    else:
        print("  未找到可爬取的資料")
    
    print(f"\n💾 詳細結果已儲存至 refresh-test-results.json")