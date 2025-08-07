#!/usr/bin/env python3
"""
除錯HTML解析
"""

import requests
import time
import re

def debug_parse():
    """除錯解析邏輯"""
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
    })
    
    # 建立格式
    test_key = "11410100000"
    url = f"{base_url}?INDEX_KEY={test_key}"
    
    print("建立格式...")
    session.get(url, timeout=30)
    time.sleep(1)
    response = session.get(url, timeout=30)
    
    if '建造執照號碼' not in response.text:
        print("需要重新整理...")
        time.sleep(1)
        response = session.get(url, timeout=30)
    
    print(f"\n分析 INDEX_KEY: {test_key}")
    print("=" * 50)
    
    html = response.text
    
    # 儲存HTML供分析
    with open('debug-output.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML已儲存到 debug-output.html")
    
    # 查找建照號碼相關的HTML片段
    print("\n查找建照號碼...")
    
    # 找出包含"建造執照號碼"的部分
    permit_index = html.find('建造執照號碼')
    if permit_index > 0:
        # 取前後各200字元
        start = max(0, permit_index - 100)
        end = min(len(html), permit_index + 200)
        snippet = html[start:end]
        
        print("HTML片段:")
        print("-" * 50)
        print(snippet)
        print("-" * 50)
        
        # 嘗試各種模式
        patterns = [
            r'建造執照號碼[：:]\s*</[^>]+>\s*<[^>]+>([^<]+)',
            r'建造執照號碼[：:][^<]*<[^>]+>([^<]+)',
            r'建造執照號碼[：:]\s*([^<\s]+)',
            r'建造執照號碼</[^>]+>\s*<[^>]+>[：:]\s*</[^>]+>\s*<[^>]+>([^<]+)'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, html)
            if match:
                print(f"\n模式{i+1}匹配: {match.group(1)}")
            else:
                print(f"\n模式{i+1}: 無匹配")
    
    # 查找起造人
    print("\n\n查找起造人...")
    applicant_index = html.find('起造人')
    if applicant_index > 0:
        start = max(0, applicant_index - 50)
        end = min(len(html), applicant_index + 300)
        snippet = html[start:end]
        
        print("HTML片段:")
        print("-" * 50)
        print(snippet)
        print("-" * 50)
    
    # 測試其他序號
    print("\n\n測試其他序號...")
    other_keys = ["11410099900", "11410100100", "11310100000"]
    
    for key in other_keys:
        url = f"{base_url}?INDEX_KEY={key}"
        response = session.get(url, timeout=30)
        
        print(f"\n{key}:")
        if '建造執照號碼' in response.text:
            # 使用更靈活的正則表達式
            match = re.search(r'建造執照號碼[^<]*<[^>]*>[^<]*<[^>]*>([^<]+)', response.text)
            if match:
                content = match.group(1).strip()
                print(f"  建照號碼: {content}")
            else:
                print("  有建照關鍵字但無法解析")
        elif '查無資料' in response.text:
            print("  查無資料")
        else:
            print("  其他狀態")
        
        time.sleep(1)
    
    session.close()

if __name__ == "__main__":
    debug_parse()