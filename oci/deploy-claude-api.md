# 部署 Claude API 搜尋功能

## 步驟 1：取得 Claude API Key

1. 前往 https://console.anthropic.com/
2. 登入或註冊帳號
3. 點擊「API Keys」
4. 點擊「Create Key」
5. 複製 API Key（格式類似：`sk-ant-api03-xxxxx`）

## 步驟 2：在 OCI 設定 Function

### 方法 A：使用 OCI Cloud Shell（推薦）

```bash
# 1. 開啟 OCI Cloud Shell

# 2. 下載 Function 程式碼
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/claude-search-function.tar.gz \
    --file claude-search-function.tar.gz

# 3. 解壓縮
tar -xzf claude-search-function.tar.gz
cd claude-search-function

# 4. 建立 Function Application（如果還沒有）
fn create context claude-search --provider oracle
fn use context claude-search
fn update context oracle.compartment-id <你的compartment-id>
fn update context registry <你的registry>

# 建立 Application
fn create app claude-search-app --annotation oracle.com/oci/subnetIds='["<你的subnet-id>"]'

# 5. 設定 Claude API Key
fn config app claude-search-app CLAUDE_API_KEY "<你的Claude API Key>"

# 6. 部署 Function
fn -v deploy --app claude-search-app

# 7. 取得 Function 的 invoke endpoint
fn inspect function claude-search-app claude-search | grep "invoke_endpoint"
```

### 方法 B：簡易測試方案（使用 OCI API Gateway）

如果你覺得 Function 太複雜，我可以建立一個簡單的代理服務：

```python
# 建立一個簡單的 Flask 應用
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    
    # Claude API 請求
    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': os.environ['CLAUDE_API_KEY'],
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": f"將以下查詢解析成JSON搜尋條件：{query}"
            }]
        }
    )
    
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## 步驟 3：更新前端連接 API

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
        // 呼叫 Claude API Function
        const response = await fetch('<你的Function Endpoint>/search', {
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
            
            console.log('Claude 解析結果:', result.conditions);
        } else {
            // 如果 API 失敗，fallback 到本地解析
            console.log('API 失敗，使用本地解析');
            const conditions = parseNaturalLanguageQuery(query);
            if (conditions) {
                aiSearchConditions = conditions;
                applyAISearchFilters();
                showSearchConditions(conditions);
            }
        }
    } catch (error) {
        console.error('搜尋錯誤:', error);
        // Fallback 到本地解析
        const conditions = parseNaturalLanguageQuery(query);
        if (conditions) {
            aiSearchConditions = conditions;
            applyAISearchFilters();
            showSearchConditions(conditions);
        }
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🤖</span><span>智慧搜尋</span>';
    }
}
```

## 測試查詢範例

Claude API 能理解的複雜查詢：

1. **複雜組合**：
   - "113年在大里區230戶以上的建案"
   - "今年上半年北屯區7樓以上100戶以上的大樓"
   - "找出西屯區總樓地板面積超過1萬平方公尺的商業大樓"

2. **自然語言**：
   - "最近的大型住宅建案"
   - "適合投資的中型社區"
   - "豪宅等級的建案"

3. **模糊查詢**：
   - "台積電附近的建案"（會解析成特定區域）
   - "捷運沿線的大樓"（會解析成相關區域）

## 預估費用

- Claude 3 Haiku: $0.25 / 百萬輸入tokens
- 每次查詢約 300-500 tokens
- 每月 10,000 次查詢：約 $1-2 美元

## 需要協助嗎？

如果你提供：
1. OCI Compartment ID
2. Subnet ID
3. Container Registry

我可以幫你產生完整的部署腳本！