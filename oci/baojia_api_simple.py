#!/usr/bin/env python3
"""
簡單的寶佳公司名單 API 服務
可以用 Python 內建的 http.server 運行
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os

class BaojiaAPIHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """處理 CORS preflight 請求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """取得寶佳公司名單"""
        if self.path == '/api/baojia/companies':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                # 從 OCI 下載最新的公司名單
                cmd = [
                    "oci", "os", "object", "get",
                    "--namespace", "nrsdi1rz5vl8",
                    "--bucket-name", "taichung-building-permits",
                    "--name", "baojia_companies.json",
                    "--file", "/tmp/baojia_companies_temp.json"
                ]
                subprocess.run(cmd, capture_output=True)
                
                with open('/tmp/baojia_companies_temp.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.wfile.write(json.dumps(data).encode('utf-8'))
                
            except Exception as e:
                error_data = {"error": str(e)}
                self.wfile.write(json.dumps(error_data).encode('utf-8'))
        else:
            self.send_error(404)
    
    def do_POST(self):
        """更新寶佳公司名單"""
        if self.path == '/api/baojia/companies':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # 解析請求資料
                data = json.loads(post_data.decode('utf-8'))
                
                # 儲存到臨時檔案
                temp_file = '/tmp/baojia_companies_update.json'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 上傳到 OCI
                cmd = [
                    "oci", "os", "object", "put",
                    "--namespace", "nrsdi1rz5vl8",
                    "--bucket-name", "taichung-building-permits",
                    "--name", "baojia_companies.json",
                    "--file", temp_file,
                    "--content-type", "application/json",
                    "--force"
                ]
                result = subprocess.run(cmd, capture_output=True)
                
                if result.returncode == 0:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {"success": True, "message": "寶佳公司名單已更新"}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                else:
                    raise Exception("上傳失敗")
                    
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                error_data = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(error_data).encode('utf-8'))
        else:
            self.send_error(404)

def run_server(port=8080):
    """啟動 API 服務"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, BaojiaAPIHandler)
    print(f'🚀 寶佳 API 服務已啟動在 port {port}')
    print(f'📍 API 端點:')
    print(f'   GET  http://localhost:{port}/api/baojia/companies - 取得公司名單')
    print(f'   POST http://localhost:{port}/api/baojia/companies - 更新公司名單')
    print(f'\n按 Ctrl+C 停止服務...')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n🛑 服務已停止')

if __name__ == '__main__':
    run_server()