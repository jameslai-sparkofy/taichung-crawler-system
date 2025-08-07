import { BuildingPermitCrawler } from './crawler-oci.js';
import { OCISimpleStorage } from './oci-simple.js';

export default {
  // 定時觸發
  async scheduled(event, env, ctx) {
    console.log('⏰ Cron 觸發: 開始每日爬蟲任務');
    
    const storage = new OCISimpleStorage(env);
    const crawler = new BuildingPermitCrawler(env, storage);
    
    // 執行爬蟲
    ctx.waitUntil(crawler.dailyCrawl());
  },

  // HTTP 請求處理
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS 標頭
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // 處理 OPTIONS 請求
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      const storage = new OCISimpleStorage(env);

      // API 路由
      switch (path) {
        case '/':
          return new Response(getIndexHTML(), {
            headers: { 'Content-Type': 'text/html; charset=utf-8', ...corsHeaders }
          });

        case '/api/status':
          const progress = await storage.getCrawlProgress();
          return new Response(JSON.stringify({
            status: 'running',
            progress: progress,
            lastUpdate: new Date().toISOString()
          }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });

        case '/api/trigger':
          // 手動觸發爬蟲
          if (request.method === 'POST') {
            const crawler = new BuildingPermitCrawler(env, storage);
            ctx.waitUntil(crawler.dailyCrawl());
            return new Response(JSON.stringify({ 
              message: '爬蟲已觸發，請稍後查看結果' 
            }), {
              headers: { 'Content-Type': 'application/json', ...corsHeaders }
            });
          }
          return new Response('Method not allowed', { status: 405 });

        case '/api/logs':
          const logsData = await storage.getPublicObject('data/crawl-logs.json');
          const logs = logsData?.logs || [];
          return new Response(JSON.stringify(logs), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });

        case '/api/test':
          // 測試爬取單一資料
          const testYear = parseInt(url.searchParams.get('year') || '114');
          const testSeq = parseInt(url.searchParams.get('seq') || '1');
          
          const crawler = new BuildingPermitCrawler(env, storage);
          const indexKey = crawler.generateIndexKey(testYear, 1, testSeq);
          const result = await crawler.crawlSinglePermit(indexKey);
          
          return new Response(JSON.stringify({
            indexKey: indexKey,
            result: result
          }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });

        default:
          return new Response('Not found', { status: 404 });
      }
    } catch (error) {
      console.error('請求處理錯誤:', error);
      return new Response(JSON.stringify({ 
        error: error.message 
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
  }
};

// 簡單的監控頁面
function getIndexHTML() {
  return `<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台中市建照爬蟲 - Cloudflare Worker</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-top: 0;
        }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
        }
        .status.running {
            background: #4CAF50;
            color: white;
        }
        .progress {
            margin: 20px 0;
        }
        .progress-item {
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .logs {
            max-height: 400px;
            overflow-y: auto;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
        }
        .log-item {
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .log-item:last-child {
            border-bottom: none;
        }
        .error {
            color: #dc3545;
        }
        .success {
            color: #28a745;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>台中市建照爬蟲監控</h1>
            <p>Cloudflare Worker + OCI Object Storage</p>
            <div>
                狀態: <span class="status running">運行中</span>
            </div>
        </div>

        <div class="card">
            <h2>爬蟲進度</h2>
            <div id="progress" class="progress">
                載入中...
            </div>
            <button onclick="triggerCrawl()" id="triggerBtn">手動觸發爬蟲</button>
        </div>

        <div class="card">
            <h2>最近執行記錄</h2>
            <div id="logs" class="logs">
                載入中...
            </div>
        </div>
    </div>

    <script>
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const progressDiv = document.getElementById('progress');
                progressDiv.innerHTML = \`
                    <div class="progress-item">
                        <strong>114年:</strong> \${data.progress.year114.count} 筆，最大序號: \${data.progress.year114.max}
                    </div>
                    <div class="progress-item">
                        <strong>113年:</strong> \${data.progress.year113.count} 筆，最大序號: \${data.progress.year113.max}
                    </div>
                    <div class="progress-item">
                        <strong>112年:</strong> \${data.progress.year112.count} 筆，最大序號: \${data.progress.year112.max}
                    </div>
                \`;
            } catch (error) {
                console.error('載入狀態失敗:', error);
            }
        }

        async function loadLogs() {
            try {
                const response = await fetch('/api/logs');
                const logs = await response.json();
                
                const logsDiv = document.getElementById('logs');
                if (logs.length === 0) {
                    logsDiv.innerHTML = '尚無執行記錄';
                    return;
                }
                
                logsDiv.innerHTML = logs.slice(0, 10).map(log => \`
                    <div class="log-item">
                        <div><strong>\${log.date}</strong> \${log.startTime ? log.startTime.split('T')[1].split('.')[0] : ''}</div>
                        <div class="\${log.status === 'completed' ? 'success' : 'error'}">
                            狀態: \${log.status === 'completed' ? '成功' : '失敗'}
                            \${log.stats ? \`- 成功: \${log.stats.successful} 筆\` : ''}
                            \${log.duration ? \`(\${log.duration}秒)\` : ''}
                        </div>
                        \${log.error ? \`<div class="error">錯誤: \${log.error}</div>\` : ''}
                    </div>
                \`).join('');
            } catch (error) {
                console.error('載入記錄失敗:', error);
            }
        }

        async function triggerCrawl() {
            const btn = document.getElementById('triggerBtn');
            btn.disabled = true;
            btn.textContent = '觸發中...';
            
            try {
                const response = await fetch('/api/trigger', { method: 'POST' });
                const data = await response.json();
                alert(data.message);
                
                // 重新載入狀態
                setTimeout(() => {
                    loadStatus();
                    loadLogs();
                }, 5000);
            } catch (error) {
                alert('觸發失敗: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = '手動觸發爬蟲';
            }
        }

        // 初始載入
        loadStatus();
        loadLogs();

        // 每30秒更新一次
        setInterval(() => {
            loadStatus();
            loadLogs();
        }, 30000);
    </script>
</body>
</html>`;
}