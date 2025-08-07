#!/usr/bin/env python3
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
