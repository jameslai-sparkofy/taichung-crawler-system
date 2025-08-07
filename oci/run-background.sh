#!/bin/bash
# 背景執行爬蟲腳本

echo "🚀 啟動背景爬蟲..."
echo "======================================="
echo "選擇執行方式："
echo "1. nohup (簡單，關閉終端後繼續執行)"
echo "2. screen (可以重新連接查看進度)"
echo "3. tmux (類似 screen，功能更強)"
echo "======================================="

# 方式1: 使用 nohup (最簡單)
echo "方式1: nohup 背景執行"
echo "執行指令："
echo "nohup python3 optimized-crawler.py > crawler.log 2>&1 &"
echo ""

# 方式2: 使用 screen
echo "方式2: screen 執行"
echo "安裝: sudo apt-get install screen"
echo "執行指令："
echo "screen -S crawler"
echo "python3 optimized-crawler.py"
echo "# 按 Ctrl+A+D 離開"
echo "# screen -r crawler 重新連接"
echo ""

# 方式3: 使用 tmux  
echo "方式3: tmux 執行"
echo "安裝: sudo apt-get install tmux"
echo "執行指令："
echo "tmux new -s crawler"
echo "python3 optimized-crawler.py"
echo "# 按 Ctrl+B+D 離開"
echo "# tmux attach -t crawler 重新連接"
echo ""

# 實際執行 nohup 方式
echo "======================================="
echo "現在使用 nohup 方式執行..."
cd /mnt/c/claude\ code/建照爬蟲/oci

# 修改起始點從 581 開始
cat > continue-crawler.py << 'EOF'
import sys
sys.path.append('.')
from optimized_crawler import OptimizedCrawler

crawler = OptimizedCrawler()
print("🔄 背景爬蟲啟動 - 從 114年 581號繼續")

# 先備份
crawler.backup_existing_data()

# 繼續爬取
try:
    # 114年從581開始到空白
    crawler.crawl_year_range(114, 581, None, True)
    
    # 113年全部
    crawler.crawl_year_range(113, 1, 2201, False)
    
    # 112年全部  
    crawler.crawl_year_range(112, 1, 2039, False)
    
except Exception as e:
    print(f"爬蟲異常: {e}")
    crawler.save_progress()

print("✅ 爬蟲任務完成")
EOF

# 使用 nohup 執行
nohup python3 continue-crawler.py > crawler_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 取得 PID
PID=$!
echo "✅ 爬蟲已在背景啟動"
echo "   PID: $PID"
echo "   日誌: crawler_$(date +%Y%m%d_%H%M%S).log"
echo ""
echo "查看進度："
echo "  tail -f crawler_*.log"
echo ""
echo "查看爬蟲狀態："
echo "  ps -p $PID"
echo ""
echo "停止爬蟲："
echo "  kill $PID"
echo ""
echo "監控網頁："
echo "  https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/index.html"