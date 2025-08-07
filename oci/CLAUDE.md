# 台中市建照爬蟲專案記錄

## 🚀 快速開始 - 重開專案時的執行步驟

### 步驟 1：檢查目前資料狀態
```bash
# 下載並檢查現有資料
/home/laija/bin/oci os object get --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --name permits.json --file /tmp/current_permits.json

# 查看目前最新序號
python3 -c "import json; data=json.load(open('/tmp/current_permits.json')); permits=data.get('permits',[]); y114=[p for p in permits if p.get('permitYear')==114]; latest=max(y114, key=lambda x: x.get('sequenceNumber',0)) if y114 else None; print(f'目前114年最新序號: {latest[\"sequenceNumber\"]} ({latest[\"permitNumber\"]})' if latest else '無資料')"
```

### 步驟 2：爬取新資料
```bash
# 假設目前最新是1142，從1143開始爬取
cd /mnt/c/claude\ code/建照爬蟲/oci

# 方法1：爬取特定範圍（例如1143-1200）
python3 simple-crawl.py 114 1143 1200

# 方法2：爬取到空白為止（自動停止）
python3 simple-crawl.py 114 1143
```

### 步驟 3：確認爬取結果
```bash
# 下載最新資料檢查
/home/laija/bin/oci os object get --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --name permits.json --file /tmp/latest_permits.json

# 顯示新增的建照
python3 -c "import json; data=json.load(open('/tmp/latest_permits.json')); permits=data.get('permits',[]); new=[p for p in permits if p.get('sequenceNumber',0) >= 1143 and p.get('permitYear')==114]; print(f'新增 {len(new)} 筆'); [print(f'  - {p[\"permitNumber\"]}: {p.get(\"applicantName\",\"\")[:20]}...') for p in new[:10]]"
```

### 步驟 4：更新執行日誌（可選）
如果需要手動更新網頁的執行記錄：
```python
# 創建更新日誌的Python腳本
cat > update_log.py << 'EOF'
import json, os
from datetime import datetime

# 下載現有日誌
os.system('/home/laija/bin/oci os object get --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --name data/crawl-logs.json --file /tmp/logs.json 2>/dev/null')

try:
    with open('/tmp/logs.json', 'r') as f:
        data = json.load(f)
        logs = data.get('logs', [])
except:
    logs = []

# 添加新記錄（請根據實際情況修改數值）
new_log = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "startTime": datetime.now().isoformat(),
    "endTime": datetime.now().isoformat(),
    "duration": 30,  # 實際耗時（秒）
    "results": {
        "success": 10,  # 成功筆數
        "failed": 0,
        "empty": 0,
        "total": 10
    },
    "yearStats": {
        "114": {
            "crawled": 10,
            "start": 1143,  # 起始序號
            "end": 1152     # 結束序號
        }
    },
    "status": "completed",
    "totalCrawled": 10,
    "newRecords": 10,
    "errorRecords": 0
}

logs.insert(0, new_log)
log_data = {"lastUpdate": datetime.now().isoformat(), "totalLogs": len(logs[:20]), "logs": logs[:20]}

with open('/tmp/new_logs.json', 'w') as f:
    json.dump(log_data, f, ensure_ascii=False, indent=2)

os.system('/home/laija/bin/oci os object put --namespace nrsdi1rz5vl8 --bucket-name taichung-building-permits --name data/crawl-logs.json --file /tmp/new_logs.json --force')
print("✅ 日誌已更新")
EOF

python3 update_log.py
```

## 📋 保留的正確爬蟲程式（共5個）

### 1. **simple-crawl.py** ⭐ 主要使用
- 簡單執行腳本，最常用
- 用法：`python3 simple-crawl.py 年份 起始序號 [結束序號]`
- 使用wget + cookie機制（關鍵成功因素）
- 自動上傳到OCI

### 2. **optimized-crawler-stable.py**
- 核心穩定版爬蟲
- simple-crawl.py的基礎
- 包含完整的錯誤處理和重試機制

### 3. **recrawl-empty-stable.py**
- 專門重新爬取空白資料
- 自動找出失敗的序號並重試

### 4. **enhanced-crawler.py**
- 增強版，包含寶佳建案識別
- 即時標記寶佳相關建照

### 5. **cron_daily_crawler_v2.py**
- 每日排程爬蟲
- 用於自動化定時執行

## ⚠️ 重要提醒

### 關鍵成功因素
1. **必須使用wget + cookie機制**
   - 第一次請求：建立session並儲存cookie
   - 第二次請求：使用cookie取得實際資料
   - Python requests庫會失敗！

2. **必須解析的欄位**（缺一不可）：
   - 樓層 (floors)
   - 棟數 (buildings)
   - 戶數 (units)
   - 總樓地板面積 (totalFloorArea)
   - 發照日期 (issueDate)

3. **參數設定**：
   - request_delay: 0.8-1.0秒（避免被封鎖）
   - batch_size: 20-30筆（平衡效能與穩定性）
   - timeout: 20-30秒

## 📊 資料統計（2025-08-07更新）

- **總計**: 4,599 筆
- **114年**: 1,142 筆（最新序號：1142，114中都建字第01142號）
- **113年**: 2,112 筆
- **112年**: 1,345 筆

### 最近爬取記錄
- 2025-08-07：成功爬取114年序號1137-1142共6筆
  - 114中都建字第01137號 - 登鴻建設
  - 114中都建字第01138號 - 李闓〇
  - 114中都建字第01139號 - 黃水〇
  - 114中都建字第01140號 - 全鑫精密工業
  - 114中都建字第01141號 - 陳志〇
  - 114中都建字第01142號 - 張登〇

## 🔧 常見問題處理

### 問題1：爬蟲沒有取得資料
**原因**：使用了錯誤的爬取方法
**解決**：確保使用`simple-crawl.py`或`optimized-crawler-stable.py`

### 問題2：網頁執行記錄不正確
**原因**：日誌格式不符合網頁期待
**解決**：使用上面的更新日誌腳本

### 問題3：資料重複或覆蓋
**原因**：沒有正確合併現有資料
**解決**：爬蟲程式已內建去重複機制

## 📁 專案結構

```
/mnt/c/claude code/建照爬蟲/oci/
├── simple-crawl.py              # 主要爬蟲腳本 ⭐
├── optimized-crawler-stable.py  # 核心穩定版
├── recrawl-empty-stable.py      # 空白資料重爬
├── enhanced-crawler.py          # 增強版（含寶佳識別）
├── cron_daily_crawler_v2.py     # 每日排程爬蟲
├── baojia_companies.json        # 寶佳體系公司清單（74家）
├── index.html                   # 網頁查詢介面
├── CLAUDE.md                    # 本文件
└── CLEANUP_SUMMARY.md           # 2025-08-07清理記錄
```

## 🌐 線上資源

- **查詢網頁**: https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html
- **建照資料**: permits.json
- **執行日誌**: data/crawl-logs.json

## 📝 Index Key 格式說明

```
{年份:3}{建照類型:2}{序號:5}{版本號:2}
例：11410114200 = 114年 + 類型1 + 序號1142 + 版本00
```

## 🎯 下次執行預估

根據目前進度（114年第1142號），預估：
- 每日新增建照：約5-10筆
- 建議爬取頻率：每週一次
- 下次爬取範圍：114年 1143-1200

---
最後更新：2025-08-07
作者：Claude