# 寶佳公司名單持久化解決方案

## 問題描述
使用者新增的寶佳公司（如「大華建設」）在網頁重新整理後會消失，無法持久保存。

## 解決方案架構

### 1. API 後端服務 (`baojia_api_simple.py`)
- 提供 GET/POST 端點管理寶佳公司名單
- 直接與 OCI Object Storage 同步
- 支援 CORS 跨域請求

### 2. 整合版前端 (`index_with_baojia_api.html`)
- 完整的建照查詢系統
- 寶佳篩選功能
- 公司名單管理介面
- 透過 API 持久化變更

### 3. 資料存儲
- 位置：OCI Object Storage
- 檔案：`baojia_companies.json`
- 格式：JSON 包含公司陣列

## 使用方式

### 啟動 API 服務
```bash
# 方法 1：使用啟動腳本
./start_baojia_api.sh

# 方法 2：直接執行
python3 baojia_api_simple.py
```

### 開啟網頁介面
1. 確保 API 服務在 port 8080 執行中
2. 在瀏覽器開啟 `index_with_baojia_api.html`
3. 點擊「📝 管理名單」按鈕

### 管理公司名單
1. **新增公司**：
   - 在輸入框輸入公司名稱
   - 點擊「➕ 新增」或按 Enter
   - 系統會自動儲存到 OCI

2. **刪除公司**：
   - 在列表中找到要刪除的公司
   - 點擊「🗑️ 刪除」
   - 確認後即從 OCI 移除

3. **篩選寶佳建案**：
   - 勾選「🏗️ 只看寶佳機構」
   - 系統會即時篩選顯示

## 技術細節

### API 端點
- `GET /api/baojia/companies`：取得公司名單
- `POST /api/baojia/companies`：更新公司名單

### 智慧匹配邏輯
系統會自動處理以下情況：
- 「大華建設」匹配「大華建設股份有限公司」
- 「寶佳建設」匹配「寶佳建設有限公司」
- 移除常見後綴進行比對

### 錯誤處理
- API 無法連線時，會從 OCI 直接載入（唯讀模式）
- 儲存失敗時會顯示錯誤訊息
- 資料變更會即時反映在篩選結果

## 檔案說明
- `baojia_api_simple.py`：簡單的 HTTP API 服務
- `index_with_baojia_api.html`：整合 API 的完整前端
- `baojia_companies.json`：寶佳公司資料庫（在 OCI）
- `start_baojia_api.sh`：API 啟動腳本

## 注意事項
1. API 服務必須在本機 port 8080 執行
2. 需要 OCI CLI 設定正確才能讀寫資料
3. 變更會直接寫入 OCI，請謹慎操作