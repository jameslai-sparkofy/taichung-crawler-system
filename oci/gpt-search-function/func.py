import io
import json
import logging
from fdk import response
import requests

def handler(ctx, data: io.BytesIO = None):
    """
    OCI Function 作為 OpenAI GPT API 代理
    解析自然語言查詢並返回結構化搜尋條件
    """
    logging.getLogger().info("GPT search function called")
    
    try:
        body = json.loads(data.getvalue())
        query = body.get("query", "")
        
        if not query:
            return response.Response(
                ctx, 
                response_data=json.dumps({"error": "查詢不能為空"}, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
        
        # OpenAI API 金鑰（需要在 OCI 設定環境變數）
        api_key = ctx.Config().get("OPENAI_API_KEY", "")
        if not api_key:
            return response.Response(
                ctx,
                response_data=json.dumps({"error": "未設定 API 金鑰"}, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
        
        # 呼叫 OpenAI API
        openai_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": """你是一個台中市建照查詢系統的解析器。請將自然語言查詢解析成 JSON 格式的搜尋條件。

可用欄位：
- year: 年份（民國年，如 113、112）
- month_from: 起始月份（1-12）
- month_to: 結束月份（1-12）
- area: 行政區（北屯區、西屯區、南屯區、西區、北區、南區、東區、中區、太平區、大里區、霧峰區、烏日區、豐原區、潭子區、大雅區、神岡區、后里區、東勢區、和平區、新社區、石岡區、外埔區、大安區、清水區、沙鹿區、龍井區、梧棲區、大肚區、大甲區）
- floors_min: 最少樓層數
- floors_max: 最多樓層數
- unit_count_min: 最少戶數
- unit_count_max: 最多戶數
- building_count_min: 最少棟數
- building_count_max: 最多棟數
- total_area_min: 最少總樓地板面積（平方公尺）
- total_area_max: 最多總樓地板面積（平方公尺）
- applicant_keyword: 起造人關鍵字

只返回 JSON，不要其他說明。如果提到"今年"，指的是民國113年（2024年）。"""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
        )
        
        if openai_response.status_code != 200:
            return response.Response(
                ctx,
                response_data=json.dumps({"error": "OpenAI API 錯誤"}, ensure_ascii=False),
                headers={"Content-Type": "application/json"}
            )
        
        # 解析 OpenAI 的回應
        openai_data = openai_response.json()
        content = openai_data["choices"][0]["message"]["content"]
        
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