#!/bin/bash
# 啟動5個並行爬蟲爭取113年資料

echo "🚀 啟動5個並行爬蟲爭取113年"
echo "======================================"

# 停止所有現有的爬蟲
echo "⏹️  停止所有現有爬蟲..."
pkill -f 'worker.*py'
pkill -f 'worker.*sh'
sleep 2

# 113年分成500筆一份，分給5個worker
echo "📋 113年任務分配 (1-2201):" 

# Worker 1: 1-440
echo "#!/bin/bash
cd '/mnt/c/claude code/建照爬蟲/oci'
exec python3 -c \"
exec(open('optimized-crawler.py').read().split('if __name__ == \\\"__main__\\\":')[0])
crawler = OptimizedCrawler()
crawler.request_delay = 1.0
print('🔧 Worker 1: 爬取 113年 1-440')
crawler.crawl_year_range(113, 1, 440, False)
print('✅ Worker 1 完成')
\"" > w113_1.sh
chmod +x w113_1.sh
nohup ./w113_1.sh > w113_1_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "   Worker 1: 113年 00001-00440 (PID: $!)"
sleep 2

# Worker 2: 441-880
echo "#!/bin/bash
cd '/mnt/c/claude code/建照爬蟲/oci'
exec python3 -c \"
exec(open('optimized-crawler.py').read().split('if __name__ == \\\"__main__\\\":')[0])
crawler = OptimizedCrawler()
crawler.request_delay = 1.0
print('🔧 Worker 2: 爬取 113年 441-880')
crawler.crawl_year_range(113, 441, 880, False)
print('✅ Worker 2 完成')
\"" > w113_2.sh
chmod +x w113_2.sh
nohup ./w113_2.sh > w113_2_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "   Worker 2: 113年 00441-00880 (PID: $!)"
sleep 2

# Worker 3: 881-1320
echo "#!/bin/bash
cd '/mnt/c/claude code/建照爬蟲/oci'
exec python3 -c \"
exec(open('optimized-crawler.py').read().split('if __name__ == \\\"__main__\\\":')[0])
crawler = OptimizedCrawler()
crawler.request_delay = 1.0
print('🔧 Worker 3: 爬取 113年 881-1320')
crawler.crawl_year_range(113, 881, 1320, False)
print('✅ Worker 3 完成')
\"" > w113_3.sh
chmod +x w113_3.sh
nohup ./w113_3.sh > w113_3_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "   Worker 3: 113年 00881-01320 (PID: $!)"
sleep 2

# Worker 4: 1321-1760
echo "#!/bin/bash
cd '/mnt/c/claude code/建照爬蟲/oci'
exec python3 -c \"
exec(open('optimized-crawler.py').read().split('if __name__ == \\\"__main__\\\":')[0])
crawler = OptimizedCrawler()
crawler.request_delay = 1.0
print('🔧 Worker 4: 爬取 113年 1321-1760')
crawler.crawl_year_range(113, 1321, 1760, False)
print('✅ Worker 4 完成')
\"" > w113_4.sh
chmod +x w113_4.sh
nohup ./w113_4.sh > w113_4_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "   Worker 4: 113年 01321-01760 (PID: $!)"
sleep 2

# Worker 5: 1761-2201
echo "#!/bin/bash
cd '/mnt/c/claude code/建照爬蟲/oci'
exec python3 -c \"
exec(open('optimized-crawler.py').read().split('if __name__ == \\\"__main__\\\":')[0])
crawler = OptimizedCrawler()
crawler.request_delay = 1.0
print('🔧 Worker 5: 爬取 113年 1761-2201')
crawler.crawl_year_range(113, 1761, 2201, False)
print('✅ Worker 5 完成')
\"" > w113_5.sh
chmod +x w113_5.sh
nohup ./w113_5.sh > w113_5_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "   Worker 5: 113年 01761-02201 (PID: $!)"

echo ""
echo "💡 監控指令:"
echo "   查看工作進程: ps aux | grep 'w113_[0-9].sh' | grep -v grep"
echo "   查看日誌: tail -f w113_1_*.log"
echo "   停止所有: pkill -f 'w113_[0-9].sh'"
echo ""
echo "✅ 5個並行爬蟲已啟動爭取113年！"