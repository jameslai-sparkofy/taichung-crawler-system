#!/usr/bin/env python3
"""
更新 index.html 加入寶佳篩選功能
"""

import os

# 讀取現有的 index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 找到 filter-grid 的位置，在那裡插入寶佳篩選
filter_section = '''
        <!-- 寶佳機構篩選 -->
        <div class="filter-group" style="display: flex; align-items: center; gap: 10px;">
            <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                <input type="checkbox" id="baojiFilter" onchange="toggleBaojiFilter()">
                <span>🏗️ 只看寶佳機構</span>
            </label>
            <button class="btn btn-sm" onclick="openBaojiaManager()" style="padding: 5px 10px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
                📝 管理名單
            </button>
        </div>
'''

# 在 </style> 標籤前加入寶佳管理的樣式
baojia_styles = '''
        /* 寶佳管理彈窗樣式 */
        .baojia-modal {
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .baojia-modal-content {
            background-color: white;
            margin: 50px auto;
            padding: 20px;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        
        .baojia-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .baojia-close {
            font-size: 28px;
            cursor: pointer;
            color: #aaa;
            line-height: 20px;
        }
        
        .baojia-close:hover {
            color: #000;
        }
        
        .baojia-add-form {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .baojia-add-form input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .baojia-add-form button {
            padding: 8px 16px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .baojia-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .baojia-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            margin-bottom: 5px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .baojia-item:hover {
            background: #e9ecef;
        }
        
        .baojia-delete {
            color: #dc3545;
            cursor: pointer;
            padding: 2px 8px;
        }
'''

# 在 </body> 標籤前加入寶佳管理的 JavaScript
baojia_script = '''
    <!-- 寶佳管理彈窗 -->
    <div id="baojiaModal" class="baojia-modal">
        <div class="baojia-modal-content">
            <div class="baojia-header">
                <h2>🏗️ 寶佳機構公司名單管理</h2>
                <span class="baojia-close" onclick="closeBaojiaManager()">&times;</span>
            </div>
            
            <div class="baojia-add-form">
                <input type="text" id="newBaojiaCompany" placeholder="輸入新的寶佳公司名稱" onkeypress="if(event.key==='Enter')addBaojiaCompany()">
                <button onclick="addBaojiaCompany()">➕ 新增</button>
            </div>
            
            <div id="baojiaStats" style="margin-bottom: 15px; color: #666;">
                載入中...
            </div>
            
            <div class="baojia-list" id="baojiaList">
                載入中...
            </div>
        </div>
    </div>

    <script>
        // 寶佳公司管理
        let baojiaCompanies = [];
        let baojiFilterActive = false;
        
        // 載入寶佳公司名單
        async function loadBaojiaCompanies() {
            try {
                const response = await fetch('https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/baojia_companies.json');
                const data = await response.json();
                baojiaCompanies = data.companies || [];
            } catch (error) {
                console.error('載入寶佳公司名單失敗:', error);
                baojiaCompanies = [];
            }
        }
        
        // 開啟寶佳管理視窗
        function openBaojiaManager() {
            document.getElementById('baojiaModal').style.display = 'block';
            updateBaojiaList();
        }
        
        // 關閉寶佳管理視窗
        function closeBaojiaManager() {
            document.getElementById('baojiaModal').style.display = 'none';
        }
        
        // 更新寶佳公司列表顯示
        function updateBaojiaList() {
            const listElement = document.getElementById('baojiaList');
            const statsElement = document.getElementById('baojiaStats');
            
            statsElement.innerHTML = `共 ${baojiaCompanies.length} 家寶佳機構公司`;
            
            if (baojiaCompanies.length === 0) {
                listElement.innerHTML = '<p style="text-align: center; color: #999;">尚無公司資料</p>';
                return;
            }
            
            listElement.innerHTML = baojiaCompanies
                .sort((a, b) => a.localeCompare(b, 'zh-TW'))
                .map(company => `
                    <div class="baojia-item">
                        <span>${company}</span>
                        <span class="baojia-delete" onclick="deleteBaojiaCompany('${company}')">🗑️ 刪除</span>
                    </div>
                `).join('');
        }
        
        // 新增寶佳公司
        async function addBaojiaCompany() {
            const input = document.getElementById('newBaojiaCompany');
            const companyName = input.value.trim();
            
            if (!companyName) {
                alert('請輸入公司名稱');
                return;
            }
            
            if (baojiaCompanies.includes(companyName)) {
                alert('此公司已在名單中');
                return;
            }
            
            baojiaCompanies.push(companyName);
            await saveBaojiaCompanies();
            input.value = '';
            updateBaojiaList();
            
            // 如果篩選已開啟，重新篩選
            if (baojiFilterActive) {
                filterData();
            }
        }
        
        // 刪除寶佳公司
        async function deleteBaojiaCompany(companyName) {
            if (!confirm(`確定要刪除「${companyName}」嗎？`)) {
                return;
            }
            
            baojiaCompanies = baojiaCompanies.filter(c => c !== companyName);
            await saveBaojiaCompanies();
            updateBaojiaList();
            
            // 如果篩選已開啟，重新篩選
            if (baojiFilterActive) {
                filterData();
            }
        }
        
        // 儲存寶佳公司名單到 OCI
        async function saveBaojiaCompanies() {
            try {
                const data = {
                    companies: baojiaCompanies,
                    lastUpdated: new Date().toISOString().split('T')[0],
                    description: "寶佳機構體系公司清單"
                };
                
                // 這裡需要後端 API 支援
                // 暫時顯示提示訊息
                console.log('更新寶佳公司名單:', data);
                alert('注意：需要後端 API 才能永久保存變更。目前變更只在本次瀏覽有效。');
                
            } catch (error) {
                console.error('儲存失敗:', error);
                alert('儲存失敗，請稍後再試');
            }
        }
        
        // 切換寶佳篩選
        function toggleBaojiFilter() {
            baojiFilterActive = document.getElementById('baojiFilter').checked;
            filterData();
        }
        
        // 寶佳智慧匹配
        function isBaojiaCompany(applicantName) {
            if (!applicantName || baojiaCompanies.length === 0) return false;
            
            // 清理申請人名稱
            let cleanName = applicantName
                .replace(/負責人[：:].+$/g, '')
                .replace(/代表人[：:].+$/g, '')
                .replace(/\s+等如附表$/g, '')
                .trim();
            
            // 公司名稱後綴
            const suffixes = ['股份有限公司', '有限公司', '建設股份有限公司', '營造股份有限公司', '營造有限公司'];
            
            return baojiaCompanies.some(company => {
                // 完全匹配
                if (cleanName === company) return true;
                
                // 移除後綴比對
                let companyBase = company;
                let nameBase = cleanName;
                
                for (const suffix of suffixes) {
                    companyBase = companyBase.replace(suffix, '');
                    nameBase = nameBase.replace(suffix, '');
                }
                
                if (companyBase === nameBase) return true;
                
                // 包含關係檢查
                if (cleanName.includes(company) || company.includes(cleanName)) return true;
                
                return false;
            });
        }
        
        // 修改原有的 filterData 函數，加入寶佳篩選邏輯
        const originalFilterData = window.filterData || function() {};
        window.filterData = function() {
            originalFilterData();
            
            if (baojiFilterActive && window.currentData) {
                const tbody = document.querySelector('#dataTable tbody');
                const rows = tbody.querySelectorAll('tr');
                
                rows.forEach(row => {
                    const applicantCell = row.cells[3]; // 假設申請人在第4欄
                    if (applicantCell) {
                        const applicantName = applicantCell.textContent;
                        if (!isBaojiaCompany(applicantName)) {
                            row.style.display = 'none';
                        }
                    }
                });
                
                updateStats();
            }
        }
        
        // 頁面載入時初始化
        document.addEventListener('DOMContentLoaded', async function() {
            await loadBaojiaCompanies();
        });
        
        // 點擊 modal 外部關閉
        window.onclick = function(event) {
            const modal = document.getElementById('baojiaModal');
            if (event.target === modal) {
                closeBaojiaManager();
            }
        }
    </script>
'''

# 替換內容
# 1. 在 </style> 前加入樣式
html_content = html_content.replace('</style>', baojia_styles + '\n    </style>')

# 2. 在 filter-grid 中加入寶佳篩選（如果存在）
if 'filter-grid' in html_content:
    # 在第一個 </div> <!-- filter-group --> 後加入
    import re
    pattern = r'(<div class="filter-group">.*?</div>)'
    def replacer(match):
        return match.group(1) + '\n' + filter_section
    html_content = re.sub(pattern, replacer, html_content, count=1, flags=re.DOTALL)
else:
    # 否則在 stats-grid 後加入
    html_content = html_content.replace('</div> <!-- stats-grid -->', 
                                      '</div> <!-- stats-grid -->\n' + filter_section)

# 3. 在 </body> 前加入腳本
html_content = html_content.replace('</body>', baojia_script + '\n</body>')

# 寫入新檔案
with open('index_with_baojia.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ 已創建 index_with_baojia.html")
print("⚠️  注意：完整的持久化功能需要後端 API 支援")
print("💡 建議：使用 baojia_api_server.py 提供 API 服務")