#!/usr/bin/env python3
"""
全面資料分析工具
1. 檢查所有年份的資料完整性
2. 找出空白欄位的資料
3. 找出缺失的序號
4. 生成修復清單
"""

import json
import re
from collections import defaultdict

def load_data():
    """載入 all_permits.json 資料"""
    try:
        with open('all_permits.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 檢查資料結構
            if isinstance(data, dict) and 'permits' in data:
                return data['permits']
            elif isinstance(data, list):
                return data
            else:
                print(f"未知的資料格式: {type(data)}")
                return []
    except Exception as e:
        print(f"載入資料失敗: {e}")
        return []

def extract_sequence_from_permit_number(permit_number):
    """從建照號碼提取序號"""
    if not permit_number:
        return None
    
    # 格式: 114中都建字第01099號
    match = re.search(r'第(\d+)號', permit_number)
    if match:
        return int(match.group(1))
    return None

def check_empty_fields(permits):
    """檢查空白或缺失必要欄位的資料"""
    print("=" * 60)
    print("檢查空白欄位")
    print("=" * 60)
    
    # 必要欄位定義
    required_fields = ['floors', 'buildings', 'units', 'totalFloorArea', 'issueDate']
    
    empty_records = defaultdict(list)
    
    for permit in permits:
        year = permit.get('permitYear')
        if not year:
            continue
            
        # 檢查必要欄位
        missing_fields = []
        for field in required_fields:
            value = permit.get(field)
            if value is None or value == '' or value == 0:
                missing_fields.append(field)
        
        if missing_fields:
            seq = extract_sequence_from_permit_number(permit.get('permitNumber'))
            empty_records[year].append({
                'sequence': seq,
                'permitNumber': permit.get('permitNumber'),
                'missing_fields': missing_fields,
                'applicantName': permit.get('applicantName', '未知')
            })
    
    # 輸出結果
    for year in sorted(empty_records.keys()):
        records = empty_records[year]
        print(f"\n{year}年空白欄位資料: {len(records)} 筆")
        
        for record in sorted(records, key=lambda x: x['sequence'] or 0):
            seq = record['sequence'] or '無序號'
            missing = ', '.join(record['missing_fields'])
            print(f"  序號 {seq:>4}: {record['permitNumber']} - 缺失: {missing}")
    
    return empty_records

def check_missing_sequences(permits):
    """檢查缺失的序號"""
    print("\n" + "=" * 60)
    print("檢查缺失序號")
    print("=" * 60)
    
    year_sequences = defaultdict(set)
    
    # 收集現有序號
    for permit in permits:
        year = permit.get('permitYear')
        if not year:
            continue
            
        seq = extract_sequence_from_permit_number(permit.get('permitNumber'))
        if seq:
            year_sequences[year].add(seq)
    
    # 定義各年份總數
    year_totals = {
        '112': 2039,
        '113': 2201,
        '114': 1098  # 根據之前的記錄
    }
    
    missing_sequences = {}
    
    for year, total in year_totals.items():
        if year not in year_sequences:
            print(f"\n{year}年: 完全無資料")
            missing_sequences[year] = list(range(1, total + 1))
            continue
            
        existing = year_sequences[year]
        expected = set(range(1, total + 1))
        missing = sorted(expected - existing)
        
        print(f"\n{year}年統計:")
        print(f"  預期總數: {total}")
        print(f"  現有數量: {len(existing)}")
        print(f"  缺失數量: {len(missing)}")
        
        if missing:
            missing_sequences[year] = missing
            # 顯示前20個缺失序號
            if len(missing) <= 50:
                print(f"  缺失序號: {missing}")
            else:
                print(f"  缺失序號(前20個): {missing[:20]}")
                print(f"  ... 還有 {len(missing)-20} 個")
    
    return missing_sequences

def analyze_data_quality(permits):
    """分析資料品質"""
    print("\n" + "=" * 60)
    print("資料品質分析")
    print("=" * 60)
    
    year_stats = defaultdict(lambda: {
        'total': 0,
        'complete': 0,
        'partial': 0,
        'empty': 0
    })
    
    required_fields = ['floors', 'buildings', 'units', 'totalFloorArea', 'issueDate']
    
    for permit in permits:
        year = permit.get('permitYear')
        if not year:
            continue
            
        year_stats[year]['total'] += 1
        
        # 計算完整度
        filled_fields = 0
        for field in required_fields:
            value = permit.get(field)
            if value is not None and value != '' and value != 0:
                filled_fields += 1
        
        if filled_fields == len(required_fields):
            year_stats[year]['complete'] += 1
        elif filled_fields > 0:
            year_stats[year]['partial'] += 1
        else:
            year_stats[year]['empty'] += 1
    
    print("\n資料完整性統計:")
    print("年份   總數   完整   部分   空白   完整率")
    print("-" * 45)
    
    for year in sorted(year_stats.keys()):
        stats = year_stats[year]
        complete_rate = (stats['complete'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{year}年  {stats['total']:4d}  {stats['complete']:4d}  {stats['partial']:4d}  {stats['empty']:4d}  {complete_rate:6.1f}%")

def generate_fix_lists(empty_records, missing_sequences):
    """生成修復清單"""
    print("\n" + "=" * 60)
    print("生成修復清單")
    print("=" * 60)
    
    # 生成空白資料修復清單
    for year in sorted(empty_records.keys()):
        records = empty_records[year]
        if records:
            filename = f"fix_empty_{year}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {year}年空白欄位修復清單\n")
                f.write(f"# 總計 {len(records)} 筆\n\n")
                
                for record in sorted(records, key=lambda x: x['sequence'] or 0):
                    seq = record['sequence']
                    if seq:
                        f.write(f"{year} {seq}\n")
            
            print(f"已生成 {filename}: {len(records)} 筆空白資料")
    
    # 生成缺失序號修復清單
    for year, missing in missing_sequences.items():
        if missing:
            filename = f"fix_missing_{year}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {year}年缺失序號修復清單\n")
                f.write(f"# 總計 {len(missing)} 筆\n\n")
                
                for seq in missing:
                    f.write(f"{year} {seq}\n")
            
            print(f"已生成 {filename}: {len(missing)} 筆缺失序號")

def main():
    print("開始全面資料分析...")
    
    # 載入資料
    permits = load_data()
    if not permits:
        print("無法載入資料，程式結束")
        return
    
    print(f"總計載入 {len(permits)} 筆資料")
    
    # 1. 檢查空白欄位
    empty_records = check_empty_fields(permits)
    
    # 2. 檢查缺失序號
    missing_sequences = check_missing_sequences(permits)
    
    # 3. 分析資料品質
    analyze_data_quality(permits)
    
    # 4. 生成修復清單
    generate_fix_lists(empty_records, missing_sequences)
    
    print("\n分析完成！")

if __name__ == "__main__":
    main()