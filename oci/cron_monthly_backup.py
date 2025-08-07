#!/usr/bin/env python3
"""
每月自動備份 - 每月1日執行
"""

import json
import requests
import subprocess
import os
from datetime import datetime
from collections import defaultdict

# 切換到正確的工作目錄
os.chdir('/mnt/c/claude code/建照爬蟲/oci')

def monthly_backup():
    """執行每月備份"""
    
    print(f"🗓️ 每月備份開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 下載現有資料
        print("📥 下載現有資料...")
        url = "https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/data/permits.json"
        response = requests.get(url)
        data = response.json()
        
        permits = data['permits']
        print(f"現有資料: {len(permits)} 筆")
        
        # 創建備份檔名（包含年月）
        timestamp = datetime.now().strftime("%Y%m")
        backup_filename = f"monthly_backup_{timestamp}.json"
        
        # 統計各年份
        year_stats = defaultdict(int)
        for permit in permits:
            year = permit.get('permitYear')
            year_stats[year] += 1
        
        # 更新備份資訊
        data['backupInfo'] = {
            'backupDate': datetime.now().isoformat(),
            'backupType': 'monthly',
            'totalCount': len(permits),
            'yearStats': dict(year_stats)
        }
        
        # 保存到本地
        print(f"\n💾 保存本地備份: {backup_filename}")
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 獲取檔案大小
        file_size = os.path.getsize(backup_filename)
        file_size_mb = file_size / (1024 * 1024)
        print(f"   檔案大小: {file_size_mb:.2f} MB")
        
        # 上傳到OCI backups目錄
        print(f"\n📤 上傳到OCI backups/monthly/...")
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        cmd = [
            "oci", "os", "object", "put",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--name", f"backups/monthly/{backup_filename}",
            "--file", backup_filename,
            "--content-type", "application/json",
            "--force"
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"✅ 備份成功上傳到OCI")
            # 刪除本地檔案以節省空間
            os.remove(backup_filename)
            print(f"🗑️ 已刪除本地檔案")
        else:
            print(f"❌ 上傳失敗: {result.stderr.decode()}")
            print(f"⚠️ 本地備份保留在: {backup_filename}")
        
        # 顯示統計
        print("\n📊 備份資料統計:")
        for year in sorted(year_stats.keys(), reverse=True):
            print(f"  {year}年: {year_stats[year]} 筆")
        
        # 清理舊備份（保留最近6個月）
        print("\n🧹 檢查舊備份...")
        clean_old_backups()
        
        print(f"\n✅ 每月備份完成!")
        
    except Exception as e:
        print(f"\n❌ 備份失敗: {e}")
    
    print(f"\n🗓️ 每月備份結束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def clean_old_backups():
    """清理超過6個月的舊備份"""
    try:
        # 列出OCI上的月備份
        namespace = "nrsdi1rz5vl8"
        bucket_name = "taichung-building-permits"
        
        cmd = [
            "oci", "os", "object", "list",
            "--namespace", namespace,
            "--bucket-name", bucket_name,
            "--prefix", "backups/monthly/",
            "--limit", "100"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            objects = json.loads(result.stdout)
            
            # 計算6個月前的日期
            from datetime import datetime, timedelta
            six_months_ago = datetime.now() - timedelta(days=180)
            
            deleted_count = 0
            for obj in objects.get('data', []):
                obj_name = obj.get('name', '')
                # 解析檔名中的日期 (monthly_backup_YYYYMM.json)
                if 'monthly_backup_' in obj_name:
                    try:
                        date_str = obj_name.split('monthly_backup_')[1].split('.')[0]
                        backup_date = datetime.strptime(date_str, '%Y%m')
                        
                        if backup_date < six_months_ago:
                            # 刪除舊備份
                            delete_cmd = [
                                "oci", "os", "object", "delete",
                                "--namespace", namespace,
                                "--bucket-name", bucket_name,
                                "--object-name", obj_name,
                                "--force"
                            ]
                            delete_result = subprocess.run(delete_cmd, capture_output=True)
                            if delete_result.returncode == 0:
                                print(f"   🗑️ 已刪除舊備份: {obj_name}")
                                deleted_count += 1
                    except:
                        pass
            
            if deleted_count > 0:
                print(f"   ✅ 共刪除 {deleted_count} 個舊備份")
            else:
                print(f"   ✅ 無需清理舊備份")
                
    except Exception as e:
        print(f"   ⚠️ 清理舊備份時發生錯誤: {e}")

if __name__ == "__main__":
    monthly_backup()