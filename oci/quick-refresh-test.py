#!/usr/bin/env python3
"""
快速測試重新整理策略
"""

import requests
import time
import re

def quick_test():
    """快速測試一個建照"""
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    index_key = "11410100000"  # 114年第100號
    url = f"{base_url}?INDEX_KEY={index_key}"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    })
    
    print(f"🔍 測試 INDEX_KEY: {index_key}")
    print(f"URL: {url}")
    print("=" * 50)
    
    # 記錄每次請求的結果
    for i in range(5):
        print(f"\n第 {i+1} 次請求:")
        
        try:
            response = session.get(url, timeout=30)
            print(f"  狀態碼: {response.status_code}")
            print(f"  內容長度: {len(response.text)} 字元")
            
            html = response.text
            
            # 檢查關鍵內容
            checks = {
                "建造執照號碼": "建造執照號碼" in html,
                "建築執照號碼": "建築執照號碼" in html,
                "起造人": "起造人" in html,
                "基地面積": "基地面積" in html,
                "遺失個資": "○○○代表遺失個資" in html,
                "表格": "<table" in html
            }
            
            print("  內容檢查:")
            for key, found in checks.items():
                print(f"    {key}: {'✅' if found else '❌'}")
            
            # 嘗試提取建照號碼
            patterns = [
                r'建造執照號碼[：:\s]*([^<\s\n]+)',
                r'(\d{3}中建字第\d+號)',
                r'執照號碼[：:\s]*([^<\s\n]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    print(f"  🎯 找到建照號碼: {match.group(1).strip()}")
                    break
            
            # 顯示部分內容
            if '建' in html:
                # 找出包含"建"字的片段
                idx = html.find('建')
                if idx != -1:
                    snippet = html[max(0, idx-50):idx+100]
                    print(f"  內容片段: ...{snippet}...")
            
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
        
        # 等待2秒後再試
        if i < 4:
            print("  等待2秒後重新整理...")
            time.sleep(2)

if __name__ == "__main__":
    print("🔧 快速測試重新整理策略")
    print("=" * 50)
    quick_test()