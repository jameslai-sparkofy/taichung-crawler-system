# 部署 GPT API 搜尋功能

## 步驟 1：取得 OpenAI API Key

1. 前往 https://platform.openai.com/
2. 登入或註冊帳號
3. 點擊右上角頭像 → "View API keys"
4. 點擊 "Create new secret key"
5. 複製 API Key（格式類似：`sk-xxxxx`）

## 步驟 2：快速測試方案（直接在前端使用）

如果你想先快速測試，可以直接在前端使用 GPT API：

### 更新 index.html

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
        // 直接呼叫 OpenAI API（僅限測試）
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer YOUR_OPENAI_API_KEY', // 替換成你的 API Key
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: "gpt-3.5-turbo",
                messages: [
                    {
                        role: "system",
                        content: `你是一個台中市建照查詢系統的解析器。請將自然語言查詢解析成 JSON 格式。

可用欄位：year（民國年）、month_from、month_to、area（行政區）、floors_min、floors_max、unit_count_min、unit_count_max、building_count_min、building_count_max、total_area_min、total_area_max

只返回 JSON，不要其他說明。今年是民國113年。`
                    },
                    {
                        role: "user",
                        content: query
                    }
                ],
                temperature: 0.3,
                max_tokens: 200
            })
        });
        
        const data = await response.json();
        
        if (data.choices && data.choices[0]) {
            const content = data.choices[0].message.content;
            try {
                const conditions = JSON.parse(content);
                aiSearchConditions = conditions;
                applyAISearchFilters();
                showSearchConditions(conditions);
                console.log('GPT 解析結果:', conditions);
            } catch (e) {
                console.error('JSON 解析失敗:', content);
                // Fallback 到本地解析
                const localConditions = parseNaturalLanguageQuery(query);
                if (localConditions) {
                    aiSearchConditions = localConditions;
                    applyAISearchFilters();
                    showSearchConditions(localConditions);
                }
            }
        }
    } catch (error) {
        console.error('GPT API 錯誤:', error);
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

## 步驟 3：正式部署方案（使用 OCI Function）

### 在 OCI Cloud Shell 執行：

```bash
# 1. 下載 Function 程式碼
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/gpt-search-function.tar.gz \
    --file gpt-search-function.tar.gz

# 2. 解壓縮
tar -xzf gpt-search-function.tar.gz
cd gpt-search-function

# 3. 建立 Function Application（如果還沒有）
fn create app gpt-search-app --annotation oracle.com/oci/subnetIds='["<你的subnet-id>"]'

# 4. 設定 OpenAI API Key
fn config app gpt-search-app OPENAI_API_KEY "<你的OpenAI API Key>"

# 5. 部署 Function
fn -v deploy --app gpt-search-app

# 6. 取得 Function endpoint
fn inspect function gpt-search-app gpt-search
```

## GPT vs Claude 比較

### GPT-3.5-turbo：
- ✅ 設定簡單，文件豐富
- ✅ 價格便宜（$0.002/1K tokens）
- ✅ 速度快
- ⚠️ 中文理解稍弱於 Claude

### GPT-4：
- ✅ 最聰明，理解力最強
- ❌ 較貴（$0.03/1K tokens）
- ❌ 速度較慢

### 建議：
- 一般查詢用 GPT-3.5-turbo 就足夠
- 複雜查詢可以考慮 GPT-4

## 測試查詢

試試這些查詢：
1. "113年在大里區230戶以上的建案"
2. "今年北屯區7到15樓的中型社區"
3. "西屯區總樓地板面積超過一萬平方公尺的商辦"

## 費用預估

- GPT-3.5-turbo: $0.002 / 1K tokens
- 每次查詢約 200-300 tokens
- 每月 10,000 次查詢：約 $4-6 美元