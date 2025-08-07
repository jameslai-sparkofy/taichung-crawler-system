#!/usr/bin/env python3
"""
測試格式建立機制
"""

import requests
import time
import re

def test_format_establishment():
    """測試建立正確格式的流程"""
    base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
    })
    
    print("🔧 測試格式建立流程")
    print("=" * 50)
    
    # 測試序號（從較大的序號開始）
    test_index = "11410100000"  # 114年第1000號
    url = f"{base_url}?INDEX_KEY={test_index}"
    
    print(f"測試 INDEX_KEY: {test_index}")
    print(f"URL: {url}")
    print()
    
    # 第一次點擊
    print("第1次點擊...")
    response1 = session.get(url, timeout=30)
    print(f"  狀態碼: {response1.status_code}")
    print(f"  內容長度: {len(response1.text)}")
    check_content(response1.text, "  ")
    time.sleep(1)
    
    # 第二次點擊
    print("\n第2次點擊...")
    response2 = session.get(url, timeout=30)
    print(f"  狀態碼: {response2.status_code}")
    print(f"  內容長度: {len(response2.text)}")
    check_content(response2.text, "  ")
    time.sleep(1)
    
    # 多次重新整理
    format_established = False
    for i in range(5):
        print(f"\n重新整理 {i+1}/5...")
        response = session.get(url, timeout=30)
        print(f"  狀態碼: {response.status_code}")
        print(f"  內容長度: {len(response.text)}")
        
        if check_content(response.text, "  "):
            format_established = True
            print(f"\n✅ 在第 {i+1} 次重新整理後建立正確格式！")
            
            # 測試格式是否持續
            print("\n測試格式持續性...")
            test_other_keys = ["11410099900", "11410100100", "11410100200"]
            
            for other_key in test_other_keys:
                other_url = f"{base_url}?INDEX_KEY={other_key}"
                print(f"\n測試 {other_key}...")
                response = session.get(other_url, timeout=30)
                if check_content(response.text, "  "):
                    print("  ✅ 格式保持正確！")
                else:
                    print("  ❌ 格式丟失")
                time.sleep(1)
            
            break
        
        time.sleep(2)
    
    if not format_established:
        print("\n❌ 無法建立正確格式")
    
    session.close()
    return format_established

def check_content(html, prefix=""):
    """檢查內容並返回是否為正確格式"""
    has_correct_format = False
    
    if '建造執照號碼' in html or '建築執照號碼' in html:
        print(f"{prefix}✅ 找到建照關鍵字")
        
        # 嘗試提取建照號碼
        patterns = [
            r'建造執照號碼[：:\s]*([^<\s\n]+)',
            r'建築執照號碼[：:\s]*([^<\s\n]+)',
            r'執照號碼[：:\s]*(\d{3}中建字第\d+號)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                permit_no = match.group(1).strip()
                print(f"{prefix}📋 建照號碼: {permit_no}")
                has_correct_format = True
                break
        
        # 檢查其他關鍵資訊
        if '<table' in html:
            print(f"{prefix}📊 包含表格")
        if '起造人' in html:
            print(f"{prefix}👷 包含起造人資訊")
        if '基地面積' in html:
            print(f"{prefix}📏 包含基地面積資訊")
            
    elif '○○○代表遺失個資' in html:
        print(f"{prefix}ℹ️  遺失個資")
    elif '查無資料' in html:
        print(f"{prefix}❌ 查無資料")
    else:
        # 檢查是否有部分關鍵字
        keywords = ['執照', '起造人', '基地', '建築', '台中市']
        found = [kw for kw in keywords if kw in html]
        if found:
            print(f"{prefix}🔍 找到部分關鍵字: {', '.join(found)}")
        else:
            print(f"{prefix}❓ 無相關內容")
    
    return has_correct_format

if __name__ == "__main__":
    test_format_establishment()