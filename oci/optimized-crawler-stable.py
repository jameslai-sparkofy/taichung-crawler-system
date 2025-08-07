#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
優化爬蟲 - 改良版
策略：
1. 串行但快速 - 減少延遲和超時時間
2. 智能跳過 - 快速檢測無效序號
3. 批次處理 - 減少上傳頻率
4. 錯誤恢復 - 自動重試機制
5. 進度保存 - 中斷可恢復
"""

import subprocess
import time
import json
import re
import os
import signal
import sys
from datetime import datetime

class OptimizedCrawler:
    def __init__(self):
        self.base_url = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do"
        self.namespace = "nrsdi1rz5vl8"
        self.bucket_name = "taichung-building-permits"
        self.results = []
        self.failed_keys = []
        self.skipped_keys = []
        self.stats = {
            'total_attempted': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': time.time()
        }
        
        # 優化參數
        self.request_delay = 0.8  # 減少延遲
        self.timeout = 20  # 減少超時時間
        self.batch_size = 30  # 增加批次大小
        self.retry_limit = 2  # 重試次數
        
        # 設定信號處理
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """處理中斷信號"""
        print(f"\n🛑 收到中斷信號，正在保存進度...")
        self.save_progress()
        self.print_final_stats()
        sys.exit(0)

    def crawl_single_permit(self, index_key, retry_count=0):
        """爬取單一建照資料 - 優化版"""
        cookie_file = None
        temp_file = None
        
        try:
            # 使用唯一的cookie檔案避免衝突
            cookie_file = f"/tmp/cookie_{index_key}_{int(time.time())}.txt"
            
            # 第一次訪問 - 建立session
            cmd1 = [
                "wget", "-q", "--timeout=" + str(self.timeout),
                "--save-cookies=" + cookie_file, "--keep-session-cookies",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "-O", "/dev/null",  # 直接丟棄第一次回應
                f"{self.base_url}?INDEX_KEY={index_key}"
            ]
            
            result1 = subprocess.run(cmd1, capture_output=True, timeout=self.timeout)
            
            if result1.returncode != 0:
                self.cleanup_files(cookie_file)
                return None
            
            # 短暫延遲
            time.sleep(self.request_delay)
            
            # 第二次訪問 - 取得資料
            temp_file = f"/tmp/page_{index_key}_{int(time.time())}.html"
            cmd2 = [
                "wget", "-q", "--timeout=" + str(self.timeout),
                "--load-cookies=" + cookie_file,
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "-O", temp_file,
                f"{self.base_url}?INDEX_KEY={index_key}"
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, timeout=self.timeout)
            
            # 清理cookie檔案
            self.cleanup_files(cookie_file)
            
            if result2.returncode != 0:
                self.cleanup_files(temp_file)
                return None
            
            # 讀取並檢查內容
            try:
                with open(temp_file, 'rb') as f:
                    content = f.read()
                self.cleanup_files(temp_file)
            except:
                return None
            
            # 快速檢查內容大小
            if len(content) < 1000:
                return None
            
            # 解碼
            try:
                html = content.decode('big5')
            except:
                try:
                    html = content.decode('utf-8', errors='ignore')
                except:
                    return None
            
            # 快速檢查是否有資料
            if "查無任何資訊" in html:
                return "NO_DATA"  # 特殊標記表示此序號無資料
            
            if "建造執照號碼" not in html:
                return None
            
            # 解析資料
            permit_data = self.parse_permit_data(html, index_key)
            
            if permit_data:
                # 背景保存HTML
                self.save_html_background(index_key, html)
                return permit_data
                
        except subprocess.TimeoutExpired:
            print(f"⏰ 超時 {index_key}")
            # 只清理已定義的檔案
            if cookie_file:
                self.cleanup_files(cookie_file)
            if temp_file:
                self.cleanup_files(temp_file)
            return None
        except Exception as e:
            print(f"❌ 錯誤 {index_key}: {e}")
            # 只清理已定義的檔案
            if cookie_file:
                self.cleanup_files(cookie_file)
            if temp_file:
                self.cleanup_files(temp_file)
            return None
        
        return None

    def cleanup_files(self, *files):
        """清理臨時檔案"""
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass

    def save_html_background(self, index_key, html_content):
        """背景保存HTML"""
        try:
            temp_file = f"/tmp/html_{index_key}_{int(time.time())}.html"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 背景上傳命令
            cmd = f"""
            nohup oci os object put \\
                --namespace {self.namespace} \\
                --bucket-name {self.bucket_name} \\
                --name html/{index_key}.html \\
                --file {temp_file} \\
                --content-type 'text/html; charset=utf-8' \\
                --force && rm {temp_file} &
            """
            
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        except Exception as e:
            print(f"⚠️ HTML保存失敗 {index_key}: {e}")

    def parse_permit_data(self, html_content, index_key):
        """解析建照資料"""
        try:
            permit_data = {
                'indexKey': index_key,
                'permitYear': int(index_key[:3]),
                'permitType': int(index_key[3]),
                'sequenceNumber': int(index_key[4:9]),
                'versionNumber': int(index_key[9:11]),
                'crawledAt': datetime.now().isoformat()
            }
            
            # 建照號碼 (必要欄位)
            m = re.search(r'<span class="conlist w20 tc">([1-9]\d{0,2}中[都市建]?建字第\d+號)</span>', html_content)
            if m:
                permit_data['permitNumber'] = m.group(1).strip()
            else:
                return None
            
            # 起造人
            patterns = [
                r'起造人.*?姓名.*?<span class="conlist w30">([^<]+)</span>',
                r'起造人.*?<span class="conlist w30">([^<]+)</span>'
            ]
            for pattern in patterns:
                m = re.search(pattern, html_content, re.DOTALL)
                if m:
                    permit_data['applicantName'] = m.group(1).strip()
                    break
            
            # 地號
            m = re.search(r'地號.*?<span class="conlist w30">([^<]+)</span>', html_content, re.DOTALL)
            if m:
                land_text = m.group(1).strip()
                permit_data['siteAddress'] = land_text
                
                # 提取行政區
                district_match = re.search(r'臺中市([^區]+區)', land_text)
                if district_match:
                    permit_data['district'] = district_match.group(1)
            
            # 層棟戶數
            m = re.search(r'層棟戶數.*?<span class="conlist w50">([^<]+)</span>', html_content, re.DOTALL)
            if m:
                floor_info = m.group(1).strip()
                permit_data['floorInfo'] = floor_info
                
                # 解析數值 - 更完整的解析
                # 地上層數
                floor_match = re.search(r'地上(\d+)層', floor_info)
                if floor_match:
                    permit_data['floorsAbove'] = int(floor_match.group(1))
                    permit_data['floors'] = int(floor_match.group(1))  # 保留舊欄位相容性
                
                # 地下層數
                basement_match = re.search(r'地下(\d+)層', floor_info)
                if basement_match:
                    permit_data['floorsBelow'] = int(basement_match.group(1))
                
                # 幢數
                block_match = re.search(r'(\d+)幢', floor_info)
                if block_match:
                    permit_data['blockCount'] = int(block_match.group(1))
                
                # 棟數
                building_match = re.search(r'(\d+)棟', floor_info)
                if building_match:
                    permit_data['buildingCount'] = int(building_match.group(1))
                    permit_data['buildings'] = int(building_match.group(1))  # 相容舊欄位名稱
                
                # 戶數
                unit_match = re.search(r'(\d+)戶', floor_info)
                if unit_match:
                    permit_data['unitCount'] = int(unit_match.group(1))
                    permit_data['units'] = int(unit_match.group(1))  # 相容舊欄位名稱
            
            # 總樓地板面積
            m = re.search(r'總樓地板面積.*?<span class="conlist w50">([0-9.,]+)', html_content, re.DOTALL)
            if m:
                try:
                    area_str = m.group(1).replace(',', '')
                    permit_data['totalFloorArea'] = float(area_str)
                except:
                    pass
            
            # 發照日期
            m = re.search(r'發照日期.*?<span class="conlist w30">(\d+年\d+月\d+日)</span>', html_content, re.DOTALL)
            if m:
                date_text = m.group(1).strip()
                date_m = re.search(r'(\d+)年(\d+)月(\d+)日', date_text)
                if date_m:
                    year = int(date_m.group(1))  # 民國年
                    month = int(date_m.group(2))
                    day = int(date_m.group(3))
                    # 保留兩種格式
                    permit_data['issueDate'] = f"{year + 1911:04d}-{month:02d}-{day:02d}"  # 西元年格式
                    permit_data['issueDateROC'] = f"{year:03d}/{month:02d}/{day:02d}"  # 民國年格式 114/03/03
            
            return permit_data
            
        except Exception as e:
            print(f"❌ 解析失敗 {index_key}: {e}")
            return None

    def upload_batch_data(self, new_permits):
        """批次上傳資料 - 累加模式"""
        try:
            # 先下載現有資料
            existing_permits = []
            existing_data = {}
            
            print("   📥 載入現有資料...", end=' ')
            cmd = [
                "/home/laija/bin/oci", "os", "object", "get",
                "--namespace", self.namespace,
                "--bucket-name", self.bucket_name,
                "--name", "data/permits.json",
                "--file", "/tmp/existing_permits.json"
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                try:
                    with open('/tmp/existing_permits.json', 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_permits = existing_data.get('permits', [])
                    print(f"✅ ({len(existing_permits)} 筆)")
                except:
                    print("⚠️ (讀取失敗)")
            else:
                print("⚠️ (無現有資料)")
            
            # 建立已存在資料的字典（用於更新）
            existing_dict = {p.get('indexKey'): p for p in existing_permits}
            
            # 更新或新增資料
            added_count = 0
            updated_count = 0
            
            for permit in new_permits:
                index_key = permit.get('indexKey')
                if index_key in existing_dict:
                    # 檢查現有資料是否完整
                    old_permit = existing_dict[index_key]
                    # 如果新資料有更多欄位，則更新
                    if len(permit) > len(old_permit) or permit.get('crawledAt', '') > old_permit.get('crawledAt', ''):
                        existing_dict[index_key] = permit
                        updated_count += 1
                else:
                    # 全新資料
                    existing_dict[index_key] = permit
                    added_count += 1
            
            # 轉回列表
            existing_permits = list(existing_dict.values())
            
            print(f"   ➕ 新增 {added_count} 筆資料, 🔄 更新 {updated_count} 筆資料")
            
            # 排序所有資料
            sorted_permits = sorted(existing_permits, key=lambda x: (
                -x.get('permitYear', 0),
                -x.get('sequenceNumber', 0)
            ))
            
            # 統計各年份數量
            year_counts = {}
            for permit in sorted_permits:
                year = permit.get('permitYear', 0)
                if year not in year_counts:
                    year_counts[year] = 0
                year_counts[year] += 1
            
            data = {
                "lastUpdate": datetime.now().isoformat(),
                "totalCount": len(sorted_permits),
                "yearCounts": year_counts,
                "permits": sorted_permits,
                "crawlStats": self.stats
            }
            
            # 寫入臨時檔案
            temp_file = f"/tmp/permits_batch_{int(time.time())}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 上傳到三個位置（包含網頁使用的all_permits.json）
            success = True
            for dest_path in ["permits.json", "data/permits.json", "all_permits.json"]:
                cmd = [
                    "/home/laija/bin/oci", "os", "object", "put",
                    "--namespace", self.namespace,
                    "--bucket-name", self.bucket_name,
                    "--name", dest_path,
                    "--file", temp_file,
                    "--content-type", "application/json",
                    "--force"
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=60)
                if result.returncode != 0:
                    success = False
            
            os.unlink(temp_file)
            return success
            
        except Exception as e:
            print(f"❌ 批次上傳失敗: {e}")
            return False

    def save_progress(self):
        """保存進度"""
        if self.results:
            print(f"💾 保存進度：{len(self.results)} 筆資料")
            self.upload_batch_data(self.results)

    def print_stats(self):
        """打印即時統計"""
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['successful'] / elapsed if elapsed > 0 else 0
        
        print(f"📊 [{elapsed:.0f}s] 成功:{self.stats['successful']} 失敗:{self.stats['failed']} 跳過:{self.stats['skipped']} 速度:{rate:.2f}/s")

    def print_final_stats(self):
        """打印最終統計"""
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['successful'] / elapsed if elapsed > 0 else 0
        
        print(f"\n🏁 最終統計:")
        print(f"   總計嘗試: {self.stats['total_attempted']}")
        print(f"   成功: {self.stats['successful']}")
        print(f"   失敗: {self.stats['failed']}")
        print(f"   跳過(無資料): {self.stats['skipped']}")
        print(f"   總耗時: {elapsed:.1f} 秒")
        print(f"   平均速度: {rate:.2f} 筆/秒")
        
        if self.stats['successful'] > 0:
            estimated_time = (5440 - self.stats['successful']) / rate / 3600  # 預估剩餘時間
            print(f"   預估完成時間: {estimated_time:.1f} 小時")

    def crawl_year_range(self, year, start_seq, end_seq=None, auto_stop=False):
        """爬取指定年份範圍
        
        Args:
            year: 年份
            start_seq: 開始序號
            end_seq: 結束序號 (如果為None且auto_stop=True，則爬到空白為止)
            auto_stop: 是否自動停止（連續遇到多個空白後停止）
        """
        if end_seq:
            print(f"🚀 開始爬取 {year} 年資料 ({start_seq:05d}-{end_seq:05d})")
        else:
            print(f"🚀 開始爬取 {year} 年資料 (從 {start_seq:05d} 開始，直到空白)")
        
        print(f"🔧 參數: 延遲={self.request_delay}s, 超時={self.timeout}s, 批次={self.batch_size}")
        print("=" * 70)
        
        permit_type = 1
        consecutive_no_data = 0  # 連續無資料計數
        max_consecutive_no_data = 20  # 連續20個無資料就停止
        consecutive_failed = 0  # 連續失敗計數
        max_consecutive_failed = 5  # 連續5個失敗就停止
        seq = start_seq
        
        while True:
            # 如果有設定結束序號且已到達，則停止
            if end_seq and seq > end_seq:
                break
                
            index_key = f"{year}{permit_type}{seq:05d}00"
            self.stats['total_attempted'] += 1
            
            print(f"🔍 [{seq:05d}] {index_key}...", end=' ', flush=True)
            
            result = self.crawl_single_permit(index_key)
            
            if result == "NO_DATA":
                # 序號無資料，跳過
                self.skipped_keys.append(index_key)
                self.stats['skipped'] += 1
                consecutive_no_data += 1
                consecutive_failed = 0  # 無資料不算失敗，重置失敗計數
                print(f"⏭️ 無資料 (連續 {consecutive_no_data})")
                
                # 如果啟用自動停止且連續無資料超過閾值，停止爬取
                if auto_stop and consecutive_no_data >= max_consecutive_no_data:
                    print(f"\n🛑 連續 {max_consecutive_no_data} 筆無資料，停止 {year} 年爬取")
                    print(f"   最後有效序號約為: {seq - max_consecutive_no_data:05d}")
                    break
            elif result:
                # 成功爬取
                self.results.append(result)
                self.stats['successful'] += 1
                consecutive_no_data = 0  # 重置連續無資料計數
                consecutive_failed = 0  # 重置連續失敗計數
                print(f"✅ {result['permitNumber']}")
            else:
                # 爬取失敗
                self.failed_keys.append(index_key)
                self.stats['failed'] += 1
                consecutive_no_data = 0  # 失敗也重置計數（可能是網路問題）
                consecutive_failed += 1  # 增加連續失敗計數
                print(f"❌ 失敗 (連續 {consecutive_failed})")
                
                # 如果連續失敗超過閾值，停止爬取
                if auto_stop and consecutive_failed >= max_consecutive_failed:
                    print(f"\n🛑 連續 {max_consecutive_failed} 次失敗，停止 {year} 年爬取")
                    print(f"   最後成功序號約為: {seq - max_consecutive_failed:05d}")
                    break
            
            # 每10筆顯示統計
            if self.stats['total_attempted'] % 10 == 0:
                self.print_stats()
            
            # 批次上傳
            if len(self.results) >= self.batch_size:
                print(f"\n💾 批次上傳 ({len(self.results)} 筆)...", end=' ')
                if self.upload_batch_data(self.results):
                    print("✅")
                    self.results = []  # 清空已上傳的資料
                else:
                    print("❌")
            
            seq += 1
        
        # 上傳最後剩餘的資料
        if self.results:
            print(f"\n💾 上傳最終資料 ({len(self.results)} 筆)...")
            self.upload_batch_data(self.results)
        
        self.print_final_stats()

    def backup_existing_data(self):
        """備份現有資料"""
        try:
            print("📦 備份現有資料...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 下載現有資料
            cmd = [
                "/home/laija/bin/oci", "os", "object", "get",
                "--namespace", self.namespace,
                "--bucket-name", self.bucket_name,
                "--name", "data/permits.json",
                "--file", f"/tmp/permits_backup_{timestamp}.json"
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                # 上傳備份
                backup_cmd = [
                    "/home/laija/bin/oci", "os", "object", "put",
                    "--namespace", self.namespace,
                    "--bucket-name", self.bucket_name,
                    "--name", f"backups/permits_backup_{timestamp}.json",
                    "--file", f"/tmp/permits_backup_{timestamp}.json",
                    "--content-type", "application/json",
                    "--force"
                ]
                
                backup_result = subprocess.run(backup_cmd, capture_output=True)
                
                if backup_result.returncode == 0:
                    print(f"✅ 備份成功: backups/permits_backup_{timestamp}.json")
                    # 清理臨時檔案
                    os.unlink(f"/tmp/permits_backup_{timestamp}.json")
                    return True
                else:
                    print(f"❌ 備份上傳失敗")
                    return False
            else:
                print(f"⚠️ 沒有現有資料需要備份")
                return True
                
        except Exception as e:
            print(f"❌ 備份失敗: {e}")
            return False

def main():
    crawler = OptimizedCrawler()
    
    print("🚀 優化爬蟲啟動！")
    
    # 先備份現有資料
    crawler.backup_existing_data()
    
    # 設定爬取計畫 - 114年爬到空白為止，其他年份指定範圍
    crawl_plan = [
        (114, 401, None, True),   # 114年：從401開始，爬到空白為止（接續之前的進度）
        (113, 1, 2201, False),    # 113年：1-2201
        (112, 1, 2039, False),    # 112年：1-2039
    ]
    
    print(f"\n📋 爬取計畫:")
    for item in crawl_plan:
        if len(item) == 4:
            year, start, end, auto_stop = item
            if auto_stop:
                print(f"   {year}年: 從 {start:05d} 開始，直到連續空白")
            else:
                count = end - start + 1
                print(f"   {year}年: {start:05d}-{end:05d} ({count:,} 筆)")
    
    print("=" * 70)
    
    # 依序爬取各年度
    for item in crawl_plan:
        if len(item) == 4:
            year, start_seq, end_seq, auto_stop = item
        else:
            year, start_seq, end_seq = item
            auto_stop = False
            
        try:
            crawler.crawl_year_range(year, start_seq, end_seq, auto_stop)
            print(f"✅ {year} 年爬取完成\n")
        except KeyboardInterrupt:
            print(f"\n🛑 用戶中斷 {year} 年爬取")
            break
        except Exception as e:
            print(f"❌ {year} 年爬取異常: {e}")
            crawler.save_progress()
            continue
    
    print("🎉 爬取任務完成！")

if __name__ == "__main__":
    # 檢查是否為補爬模式
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "fill-gaps-114":
        # 補爬114年所有缺失序號
        crawler = OptimizedCrawler()
        crawler.request_delay = 0.5  # 加快速度
        
        print("🔧 補爬114年缺失序號")
        print("=" * 70)
        
        # 114年的所有缺失區間
        gaps_114 = []
        # 101-344的規律性缺失（每5個缺4個）
        for base in range(100, 345, 5):
            gaps_114.append((114, base+1, base+4))
        
        # 361-390的大缺口
        gaps_114.append((114, 361, 390))
        
        print(f"📋 總計 {len(gaps_114)} 組缺失區間")
        
        for idx, (year, start, end) in enumerate(gaps_114):
            try:
                print(f"\n[{idx+1}/{len(gaps_114)}] 補爬 {year}年 {start:05d}-{end:05d}...")
                crawler.crawl_year_range(year, start, end, False)
            except KeyboardInterrupt:
                print("\n🛑 用戶中斷")
                break
            except Exception as e:
                print(f"❌ 失敗: {e}")
                continue
        
        print("\n🎉 114年補爬完成！")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "fill-gaps":
        crawler = OptimizedCrawler()
        
        print("🔧 補爬漏掉的資料")
        print("=" * 70)
        
        # 需要補爬的區間
        gaps = [
            (114, 1, 99),      # 114年 1-99
            (114, 346, 360),   # 114年 346-360  
            (114, 391, 400),   # 114年 391-400
        ]
        
        print("📋 補爬計畫:")
        total_to_fill = 0
        for year, start, end in gaps:
            count = end - start + 1
            total_to_fill += count
            print(f"   {year}年: {start:05d}-{end:05d} ({count} 筆)")
        
        print(f"📊 總計需補爬: {total_to_fill} 筆")
        print("=" * 70)
        
        # 依序補爬各區間
        for year, start_seq, end_seq in gaps:
            try:
                print(f"\n🔍 補爬 {year}年 {start_seq:05d}-{end_seq:05d}...")
                crawler.crawl_year_range(year, start_seq, end_seq, False)
                print(f"✅ 區間 {start_seq:05d}-{end_seq:05d} 完成")
            except KeyboardInterrupt:
                print(f"\n🛑 用戶中斷")
                break
            except Exception as e:
                print(f"❌ 補爬失敗: {e}")
                crawler.save_progress()
                continue
        
        print("\n🎉 補爬任務完成！")
    else:
        main()