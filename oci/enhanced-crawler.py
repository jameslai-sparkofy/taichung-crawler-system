#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台中市建照爬蟲 - 具備即時寶佳機構篩選功能
"""

# 載入原始爬蟲
exec(open('optimized-crawler-stable.py').read().split('if __name__ == "__main__":')[0])

# 載入即時篩選器
from baojia_realtime_filter import BaojiaRealtimeFilter

class EnhancedCrawler(OptimizedCrawler):
    def __init__(self):
        super().__init__()
        self.baojia_filter = BaojiaRealtimeFilter()
    
    def crawl_single_permit(self, index_key):
        """爬取單筆建照並即時標記是否為寶佳機構"""
        result = super().crawl_single_permit(index_key)
        
        if result and isinstance(result, dict):
            # 即時判斷是否為寶佳機構
            applicant = result.get('applicantName', '')
            if applicant:
                result['isBaojia'] = self.baojia_filter.is_baojia_company(applicant)
                if result['isBaojia']:
                    print(f"  🏢 寶佳機構建案: {applicant}")
        
        return result
    
    def upload_batch_data(self, batch_data):
        """上傳資料並同時更新寶佳篩選結果"""
        # 先執行原本的上傳
        success = super().upload_batch_data(batch_data)
        
        if success:
            # 即時更新寶佳篩選結果
            self._update_baojia_filter_results()
        
        return success
    
    def _update_baojia_filter_results(self):
        """更新寶佳篩選結果到OCI"""
        try:
            # 下載最新建照資料
            subprocess.run([
                'oci', 'os', 'object', 'get',
                '--namespace', self.namespace,
                '--bucket-name', self.bucket_name,
                '--name', 'data/permits.json',
                '--file', '/tmp/permits_for_filter.json'
            ], capture_output=True)
            
            with open('/tmp/permits_for_filter.json', 'r') as f:
                data = json.load(f)
            
            # 即時篩選
            filter_result = self.baojia_filter.filter_permits_realtime(data.get('permits', []))
            
            # 儲存篩選結果
            with open('/tmp/baojia_realtime_results.json', 'w') as f:
                json.dump(filter_result, f, ensure_ascii=False, indent=2)
            
            # 上傳到OCI
            subprocess.run([
                'oci', 'os', 'object', 'put',
                '--namespace', self.namespace,
                '--bucket-name', self.bucket_name,
                '--name', 'data/baojia_realtime_results.json',
                '--file', '/tmp/baojia_realtime_results.json',
                '--force'
            ], capture_output=True)
            
            print(f"  📊 寶佳篩選結果已更新: {filter_result['totalCount']} 筆")
            
        except Exception as e:
            print(f"  ⚠️ 更新寶佳篩選結果失敗: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("使用方式: python enhanced-crawler.py <年份> <起始序號> [結束序號]")
        sys.exit(1)
    
    year = int(sys.argv[1])
    start_seq = int(sys.argv[2])
    end_seq = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    crawler = EnhancedCrawler()
    
    if end_seq:
        print(f"開始爬取 {year} 年建照資料，序號 {start_seq} 到 {end_seq}")
        crawler.crawl_year_range(year, start_seq, end_seq)
    else:
        print(f"開始爬取 {year} 年建照資料，從序號 {start_seq} 開始")
        crawler.crawl_year_continuous(year, start_seq)
