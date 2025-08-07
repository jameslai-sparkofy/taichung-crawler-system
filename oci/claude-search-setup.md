# Claude API 智慧搜尋設定指南

## 功能說明

新增了自然語言搜尋功能，可以用中文直接查詢，例如：
- "找出113年三月以後北屯區7樓以上的建案"
- "查詢西屯區10戶以上的大樓"
- "顯示今年總樓地板面積超過5000的建案"

## 目前實作

1. **本地測試版本**（已完成）
   - 使用簡單的規則解析
   - 支援基本的年份、月份、行政區、樓層篩選
   - 可以立即在網頁上測試

2. **Claude API 版本**（待部署）
   - 使用 Claude AI 進行更智慧的解析
   - 支援更複雜的查詢
   - 需要設定 API Key

## 部署 Claude API Function 到 OCI

### 1. 取得 Claude API Key

```bash
# 前往 https://console.anthropic.com/
# 建立 API Key
# 複製 API Key 備用
```

### 2. 部署 OCI Function

```bash
# 在 OCI Cloud Shell 執行

# 1. 建立 Function Application（如果還沒有）
fn create app claude-search --annotation oracle.com/oci/subnetIds='["你的subnet-id"]'

# 2. 設定環境變數
fn config app claude-search CLAUDE_API_KEY "你的Claude API Key"

# 3. 部署 Function
cd claude-search-function
fn -v deploy --app claude-search

# 4. 取得 Function 的 invoke endpoint
fn list functions claude-search
```

### 3. 更新前端程式碼

修改 index.html 中的 `performAISearch` 函數：

```javascript
async function performAISearch() {
    const input = document.getElementById('aiSearchInput');
    const btn = document.getElementById('aiSearchBtn');
    const query = input.value.trim();
    
    if (!query) {
        alert('請輸入搜尋內容');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span>🔄</span><span>搜尋中...</span>';
    
    try {
        // 呼叫 OCI Function
        const response = await fetch('你的Function Invoke Endpoint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        
        if (result.success) {
            aiSearchConditions = result.conditions;
            applyAISearchFilters();
            showSearchConditions(result.conditions);
        } else {
            alert('搜尋失敗：' + (result.error || '未知錯誤'));
        }
    } catch (error) {
        console.error('搜尋錯誤:', error);
        alert('搜尋失敗，請稍後再試');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🤖</span><span>智慧搜尋</span>';
    }
}
```

## 使用方式

1. **直接使用（本地解析）**
   - 已經可以使用，支援基本查詢
   - 在搜尋框輸入自然語言查詢
   - 按 Enter 或點擊「智慧搜尋」按鈕

2. **使用 Claude API（更智慧）**
   - 需要先完成上述部署步驟
   - 支援更複雜的查詢理解
   - 可以處理更多樣的表達方式

## 支援的查詢範例

### 基本查詢
- "113年的建案"
- "北屯區的建照"
- "7樓以上的大樓"

### 組合查詢
- "113年3月後北屯區7樓以上"
- "西屯區10戶以上的建案"
- "今年豐原區的透天厝"

### 進階查詢（需要 Claude API）
- "找出最近三個月的大型建案"
- "查詢總價可能超過1億的建案"
- "顯示適合小家庭的新建案"

## 費用說明

### Claude API 定價（2024年）
- Claude 3 Haiku: $0.25 / 百萬輸入tokens
- 預估每次查詢：約 200 tokens
- 每月 10,000 次查詢：約 $0.50 美元

### OCI Functions
- 每月前 200萬次請求免費
- 之後每百萬次請求 $0.20 美元

## 故障排除

1. **搜尋沒有反應**
   - 檢查瀏覽器控制台錯誤
   - 確認 Function endpoint 正確

2. **API Key 錯誤**
   - 檢查環境變數設定
   - 確認 API Key 有效

3. **搜尋結果不準確**
   - 嘗試更明確的描述
   - 使用標準術語（如"北屯區"而非"北屯"）