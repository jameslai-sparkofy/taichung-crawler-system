#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動台中市建照智慧篩選系統
"""

import subprocess
import sys
import os

def main():
    print("🚀 啟動台中市建照智慧篩選系統")
    print("=" * 50)
    
    # 檢查依賴
    try:
        from flask import Flask
        from flask_cors import CORS
        from baojia_realtime_filter import BaojiaRealtimeFilter
        print("✅ 系統依賴檢查通過")
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("請安裝: pip install flask flask-cors")
        return
    
    # 檢查檔案
    required_files = [
        'smart_filter_with_baojia.html',
        'smart_filter_api.py', 
        'baojia_realtime_filter.py',
        'baojia_companies.json'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少檔案: {file}")
            return
    
    print("✅ 系統檔案檢查通過")
    
    # 測試寶佳篩選器
    try:
        filter_test = BaojiaRealtimeFilter()
        print(f"✅ 寶佳篩選器載入成功 ({len(filter_test.companies)} 家公司)")
    except Exception as e:
        print(f"❌ 寶佳篩選器載入失敗: {e}")
        return
    
    print("\n📌 系統功能:")
    print("   🔍 智慧搜尋建照資料")
    print("   🏗️ 寶佳機構即時篩選")
    print("   📝 寶佳公司名單管理")
    print("   📊 統計報表生成")
    
    print("\n🌐 啟動Web伺服器...")
    print("📍 訪問地址: http://localhost:5000")
    print("📍 API文檔: http://localhost:5000/api/")
    print("\n⚠️  按 Ctrl+C 停止伺服器")
    print("=" * 50)
    
    # 啟動API伺服器
    try:
        subprocess.run([sys.executable, 'smart_filter_api.py'])
    except KeyboardInterrupt:
        print("\n👋 系統已停止")

if __name__ == "__main__":
    main()