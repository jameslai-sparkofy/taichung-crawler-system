import io
import json
import logging
from fdk import response
import requests

def handler(ctx, data: io.BytesIO = None):
    """
    OCI Function 作為 Claude API 代理
    解析自然語言查詢並返回結構化搜尋條件
    """
    logging.getLogger().info("Claude search function called")
    
    try:
        body = json.loads(data.getvalue())
        query = body.get("query", "")
        
        if not query:
            return response.Response(
                ctx, 
                response_data=json.dumps({"error": "查詢不能為空"}, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
        
        # Claude API 金鑰（需要在 OCI 設定環境變數）
        api_key = ctx.Config().get("CLAUDE_API_KEY", "")
        if not api_key:
            return response.Response(
                ctx,
                response_data=json.dumps({"error": "未設定 API 金鑰"}, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
        
        # 呼叫 Claude API
        claude_response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": f"""你是一個建照查詢系統的解析器。請將以下自然語言查詢解析成 JSON 格式的搜尋條件。

查詢: {query}

請返回 JSON 格式，可能包含以下欄位：
- year: 年份（民國年，如 113）
- month_from: 起始月份（1-12）
- month_to: 結束月份（1-12）
- area: 行政區（如"北屯區"、"西區"等）
- floors_min: 最少樓層數
- floors_max: 最多樓層數
- applicant_keyword: 起造人關鍵字
- building_count_min: 最少棟數
- unit_count_min: 最少戶數
- total_area_min: 最少總樓地板面積（平方公尺）

範例輸入："找出113年三月以後北屯區7樓以上的建案"
範例輸出：{{"year": 113, "month_from": 3, "area": "北屯區", "floors_min": 7}}

只返回 JSON，不要其他說明。"""
                }]
            }
        )
        
        if claude_response.status_code != 200:
            return response.Response(
                ctx,
                response_data=json.dumps({"error": "Claude API 錯誤"}, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
        
        # 解析 Claude 的回應
        claude_data = claude_response.json()
        content = claude_data["content"][0]["text"]
        
        try:
            # 嘗試解析 JSON
            search_conditions = json.loads(content)
            
            return response.Response(
                ctx,
                response_data=json.dumps({
                    "success": True,
                    "conditions": search_conditions,
                    "original_query": query
                }, ensure_ascii=False),
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except json.JSONDecodeError:
            return response.Response(
                ctx,
                response_data=json.dumps({
                    "error": "無法解析搜尋條件",
                    "raw_response": content
                }, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
            
    except Exception as e:
        logging.getLogger().error(f"Error: {str(e)}")
        return response.Response(
            ctx,
            response_data=json.dumps({"error": str(e)}, ensure_ascii=False),
            headers={"Content-Type": "application/json"}
        )