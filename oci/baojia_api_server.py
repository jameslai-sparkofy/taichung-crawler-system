#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寶佳機構建照篩選 API 伺服器
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import os
from baojia_manager import BaojiaManager

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 初始化管理器
manager = BaojiaManager()

@app.route('/')
def index():
    """首頁 - 返回前端介面"""
    return send_file('baojia_filter.html')

@app.route('/api/baojia/companies', methods=['GET'])
def get_companies():
    """取得所有寶佳機構公司"""
    companies = manager.list_companies()
    return jsonify({
        'companies': companies,
        'count': len(companies)
    })

@app.route('/api/baojia/companies', methods=['POST'])
def add_company():
    """新增公司"""
    data = request.get_json()
    company_name = data.get('company', '').strip()
    
    if not company_name:
        return jsonify({'error': '公司名稱不能為空'}), 400
    
    success = manager.add_company(company_name)
    if success:
        return jsonify({
            'message': f'成功新增: {company_name}',
            'companies': manager.list_companies()
        })
    else:
        return jsonify({'error': '公司已存在或名稱無效'}), 400

@app.route('/api/baojia/companies/<company_name>', methods=['DELETE'])
def delete_company(company_name):
    """刪除公司"""
    success = manager.remove_company(company_name)
    if success:
        return jsonify({
            'message': f'成功刪除: {company_name}',
            'companies': manager.list_companies()
        })
    else:
        return jsonify({'error': '公司不存在'}), 404

@app.route('/api/baojia/search', methods=['GET'])
def search_companies():
    """搜尋公司"""
    keyword = request.args.get('q', '')
    results = manager.search_companies(keyword)
    return jsonify({
        'results': results,
        'count': len(results)
    })

@app.route('/api/baojia/filter', methods=['POST'])
def filter_permits():
    """篩選寶佳機構建照"""
    data = request.get_json()
    selected_companies = data.get('companies', [])
    
    # 暫時更新選擇的公司
    original_companies = manager.companies.copy()
    manager.companies = set(selected_companies)
    
    # 執行篩選
    result = manager.filter_baojia_permits()
    
    # 恢復原始公司清單
    manager.companies = original_companies
    
    return jsonify(result)

@app.route('/api/baojia/permits', methods=['GET'])
def get_filtered_permits():
    """取得已篩選的寶佳建照"""
    output_file = '/tmp/baojia_permits.json'
    
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        # 執行新的篩選
        result = manager.filter_baojia_permits()
        return jsonify(result)

@app.route('/api/permits', methods=['GET'])
def get_all_permits():
    """取得所有建照資料"""
    # 下載最新資料
    permits_file = '/tmp/all_permits.json'
    
    import subprocess
    subprocess.run([
        'oci', 'os', 'object', 'get',
        '--namespace', manager.oci_namespace,
        '--bucket-name', manager.bucket_name,
        '--name', 'data/permits.json',
        '--file', permits_file
    ], capture_output=True)
    
    if os.path.exists(permits_file):
        with open(permits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({'error': '無法載入建照資料'}), 500

@app.route('/api/baojia/report', methods=['GET'])
def generate_report():
    """生成統計報告"""
    result = manager.filter_baojia_permits()
    
    report = {
        'totalCompanies': len(manager.companies),
        'totalPermits': result['totalCount'],
        'lastUpdated': result['lastUpdated'],
        'companyStats': result['companyStats'],
        'topCompanies': sorted(
            result['companyStats'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:20]
    }
    
    return jsonify(report)

@app.route('/api/baojia/export', methods=['GET'])
def export_data():
    """匯出篩選結果"""
    format_type = request.args.get('format', 'json')
    
    output_file = '/tmp/baojia_permits.json'
    if not os.path.exists(output_file):
        manager.filter_baojia_permits()
    
    if format_type == 'csv':
        # 轉換為 CSV
        import csv
        csv_file = '/tmp/baojia_permits.csv'
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '建照號碼', '申請人', '建築地址', '樓層', 
                '棟數', '戶數', '總樓地板面積', '發照日期'
            ])
            
            for permit in data.get('permits', []):
                writer.writerow([
                    permit.get('permitNumber', ''),
                    permit.get('applicantName', ''),
                    permit.get('constructionAddress', ''),
                    permit.get('floors', ''),
                    permit.get('buildings', ''),
                    permit.get('units', ''),
                    permit.get('totalFloorArea', ''),
                    permit.get('issueDate', '')
                ])
        
        return send_file(csv_file, as_attachment=True, download_name='baojia_permits.csv')
    
    else:
        # JSON 格式
        return send_file(output_file, as_attachment=True, download_name='baojia_permits.json')


if __name__ == '__main__':
    print("🚀 啟動寶佳機構建照篩選 API 伺服器...")
    print("📌 請訪問 http://localhost:5000 使用系統")
    app.run(debug=True, host='0.0.0.0', port=5000)