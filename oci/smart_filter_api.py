#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台中市建照智慧篩選API (含寶佳機構篩選)
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import os
import subprocess
from baojia_realtime_filter import BaojiaRealtimeFilter

app = Flask(__name__)
CORS(app)

# 初始化寶佳篩選器
baojia_filter = BaojiaRealtimeFilter()

@app.route('/')
def index():
    """首頁 - 返回前端介面"""
    return send_file('smart_filter_with_baojia.html')

@app.route('/api/permits/all', methods=['GET'])
def get_all_permits():
    """取得所有建照資料"""
    try:
        # 下載最新資料
        permits_file = '/tmp/all_permits.json'
        
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits',
            '--name', 'data/permits.json',
            '--file', permits_file
        ], capture_output=True, check=True)
        
        with open(permits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 為每筆資料添加寶佳標記
        permits = data.get('permits', [])
        for permit in permits:
            applicant = permit.get('applicantName', '')
            permit['isBaojia'] = baojia_filter.is_baojia_company(applicant)
        
        return jsonify({
            'permits': permits,
            'totalCount': len(permits),
            'lastUpdated': data.get('lastUpdated', ''),
            'baojiCompaniesCount': len(baojia_filter.companies)
        })
        
    except Exception as e:
        return jsonify({'error': f'載入建照資料失敗: {str(e)}'}), 500

@app.route('/api/permits/search', methods=['POST'])
def search_permits():
    """智慧搜尋建照"""
    try:
        data = request.get_json()
        search_term = data.get('search', '').lower().strip()
        baojia_only = data.get('baojiOnly', False)
        
        # 取得所有建照
        permits_file = '/tmp/search_permits.json'
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits',
            '--name', 'data/permits.json',
            '--file', permits_file
        ], capture_output=True, check=True)
        
        with open(permits_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        permits = all_data.get('permits', [])
        filtered_permits = []
        
        for permit in permits:
            # 寶佳篩選
            applicant = permit.get('applicantName', '')
            is_baojia = baojia_filter.is_baojia_company(applicant)
            permit['isBaojia'] = is_baojia
            
            if baojia_only and not is_baojia:
                continue
            
            # 智慧搜尋
            if search_term:
                searchable_text = ' '.join([
                    permit.get('permitNumber', ''),
                    permit.get('applicantName', ''),
                    permit.get('constructionAddress', ''),
                    permit.get('projectName', '')
                ]).lower()
                
                if search_term not in searchable_text:
                    continue
            
            filtered_permits.append(permit)
        
        return jsonify({
            'permits': filtered_permits,
            'totalCount': len(filtered_permits),
            'searchTerm': search_term,
            'baojiOnly': baojia_only,
            'lastUpdated': all_data.get('lastUpdated', '')
        })
        
    except Exception as e:
        return jsonify({'error': f'搜尋失敗: {str(e)}'}), 500

@app.route('/api/baojia/companies', methods=['GET'])
def get_baojia_companies():
    """取得寶佳機構公司清單"""
    return jsonify({
        'companies': sorted(list(baojia_filter.companies)),
        'count': len(baojia_filter.companies)
    })

@app.route('/api/baojia/companies', methods=['POST'])
def manage_baojia_company():
    """管理寶佳機構公司"""
    try:
        data = request.get_json()
        action = data.get('action')
        company_name = data.get('company', '').strip()
        
        if not company_name:
            return jsonify({'error': '公司名稱不能為空'}), 400
        
        if action == 'add':
            success = baojia_filter.add_company_realtime(company_name)
            if success:
                return jsonify({
                    'message': f'已新增: {company_name}',
                    'companies': sorted(list(baojia_filter.companies))
                })
            else:
                return jsonify({'error': '公司已存在或名稱無效'}), 400
        
        elif action == 'remove':
            success = baojia_filter.remove_company_realtime(company_name)
            if success:
                return jsonify({
                    'message': f'已刪除: {company_name}',
                    'companies': sorted(list(baojia_filter.companies))
                })
            else:
                return jsonify({'error': '公司不存在'}), 404
        
        else:
            return jsonify({'error': '無效的操作'}), 400
    
    except Exception as e:
        return jsonify({'error': f'操作失敗: {str(e)}'}), 500

@app.route('/api/baojia/stats', methods=['GET'])
def get_baojia_stats():
    """取得寶佳機構統計資料"""
    try:
        # 下載最新資料
        permits_file = '/tmp/baojia_stats.json'
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits',
            '--name', 'data/permits.json',
            '--file', permits_file
        ], capture_output=True, check=True)
        
        with open(permits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        permits = data.get('permits', [])
        baojia_permits = []
        company_stats = {}
        
        for permit in permits:
            applicant = permit.get('applicantName', '')
            if baojia_filter.is_baojia_company(applicant):
                baojia_permits.append(permit)
                
                # 統計各公司建案數
                matched_company = applicant
                for company in baojia_filter.companies:
                    if baojia_filter._smart_match(applicant, company):
                        matched_company = company
                        break
                
                company_stats[matched_company] = company_stats.get(matched_company, 0) + 1
        
        return jsonify({
            'totalCompanies': len(baojia_filter.companies),
            'totalBaojiPermits': len(baojia_permits),
            'totalPermits': len(permits),
            'companyStats': company_stats,
            'topCompanies': sorted(company_stats.items(), key=lambda x: x[1], reverse=True)[:10],
            'lastUpdated': data.get('lastUpdated', '')
        })
        
    except Exception as e:
        return jsonify({'error': f'取得統計資料失敗: {str(e)}'}), 500

@app.route('/api/permits/check/<permit_number>', methods=['GET'])
def check_permit(permit_number):
    """檢查單筆建照是否為寶佳機構"""
    try:
        # 下載最新資料
        permits_file = '/tmp/check_permit.json'
        subprocess.run([
            'oci', 'os', 'object', 'get',
            '--namespace', 'nrsdi1rz5vl8',
            '--bucket-name', 'taichung-building-permits',
            '--name', 'data/permits.json',
            '--file', permits_file
        ], capture_output=True, check=True)
        
        with open(permits_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 尋找指定建照
        for permit in data.get('permits', []):
            if permit.get('permitNumber') == permit_number:
                applicant = permit.get('applicantName', '')
                is_baojia = baojia_filter.is_baojia_company(applicant)
                
                return jsonify({
                    'permitNumber': permit_number,
                    'applicantName': applicant,
                    'isBaojia': is_baojia,
                    'permitData': permit
                })
        
        return jsonify({'error': '找不到指定建照'}), 404
        
    except Exception as e:
        return jsonify({'error': f'檢查失敗: {str(e)}'}), 500

@app.route('/api/export/baojia', methods=['GET'])
def export_baojia_permits():
    """匯出寶佳機構建照資料"""
    try:
        format_type = request.args.get('format', 'json')
        
        # 篩選寶佳建照
        result = baojia_filter.filter_permits_realtime([])
        
        if format_type == 'csv':
            import csv
            csv_file = '/tmp/baojia_permits_export.csv'
            
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '建照號碼', '申請人', '建築地址', '樓層', 
                    '棟數', '戶數', '總樓地板面積', '發照日期'
                ])
                
                for permit in result.get('permits', []):
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
            json_file = '/tmp/baojia_permits_export.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            return send_file(json_file, as_attachment=True, download_name='baojia_permits.json')
    
    except Exception as e:
        return jsonify({'error': f'匯出失敗: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 啟動台中市建照智慧篩選API...")
    print("📌 請訪問 http://localhost:5000 使用系統")
    print("📋 功能包含:")
    print("   - 智慧搜尋建照資料")
    print("   - 寶佳機構即時篩選")
    print("   - 寶佳公司名單管理")
    print("   - 統計報表生成")
    app.run(debug=True, host='0.0.0.0', port=5000)