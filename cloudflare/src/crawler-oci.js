// 建照爬蟲 - OCI 版本
export class BuildingPermitCrawler {
  constructor(env, storage) {
    this.env = env;
    this.storage = storage;
    this.baseUrl = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do";
    
    // 從環境變數讀取設定
    this.startYear = parseInt(env.START_YEAR) || 114;
    this.crawlType = parseInt(env.CRAWL_TYPE) || 1;
    this.maxConsecutiveFailures = parseInt(env.MAX_CONSECUTIVE_FAILURES) || 5;
    this.maxConsecutiveNoData = parseInt(env.MAX_CONSECUTIVE_NO_DATA) || 20;
    this.batchSize = parseInt(env.BATCH_SIZE) || 30;
    this.requestDelayMs = parseInt(env.REQUEST_DELAY_MS) || 800;
    this.maxCrawlPerRun = parseInt(env.MAX_CRAWL_PER_RUN) || 50;
    
    // 統計資料
    this.stats = {
      totalAttempted: 0,
      successful: 0,
      failed: 0,
      skipped: 0,
      noData: 0
    };
    
    this.results = [];
  }

  // 生成 INDEX_KEY
  generateIndexKey(year, permitType, sequence, version = 0) {
    return `${year}${permitType}${sequence.toString().padStart(5, '0')}${version.toString().padStart(2, '0')}`;
  }

  // 延遲函數
  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 獲取頁面內容 - 改進版本
  async fetchPageWithRetry(indexKey, maxRetries = 3) {
    const url = `${this.baseUrl}?INDEX_KEY=${indexKey}`;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        // 建立一個持久的 headers 物件
        const baseHeaders = {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
          'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
          'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none',
          'Sec-Fetch-User': '?1',
          'Cache-Control': 'max-age=0'
        };

        // 第一次請求 - 建立 session
        let response = await fetch(url, {
          method: 'GET',
          headers: baseHeaders,
          redirect: 'follow'
        });

        // 收集所有 cookies
        let cookieJar = new Map();
        const setCookieHeaders = response.headers.getAll('set-cookie');
        for (const cookie of setCookieHeaders) {
          const [nameValue] = cookie.split(';');
          const [name, value] = nameValue.split('=');
          if (name && value) {
            cookieJar.set(name.trim(), value.trim());
          }
        }

        // 檢查是否有重定向
        if (response.status === 302 || response.status === 303) {
          const location = response.headers.get('location');
          if (location) {
            response = await fetch(location.startsWith('http') ? location : `https://mcgbm.taichung.gov.tw${location}`, {
              headers: {
                ...baseHeaders,
                'Cookie': Array.from(cookieJar.entries()).map(([k, v]) => `${k}=${v}`).join('; ')
              }
            });
          }
        }

        if (response.ok) {
          let text = await response.text();
          
          // 檢查是否需要 JavaScript 執行
          if (text.includes('document.location.reload()') || text.includes('window.location.reload()')) {
            await this.delay(2000);
            
            // 模擬 JavaScript 重新載入
            response = await fetch(url, {
              headers: {
                ...baseHeaders,
                'Cookie': Array.from(cookieJar.entries()).map(([k, v]) => `${k}=${v}`).join('; '),
                'Referer': url
              }
            });
            
            text = await response.text();
          }
          
          // 如果還是沒有內容，再試一次帶完整 cookie
          if (!text.includes('建築執照號碼') && !text.includes('建造執照號碼')) {
            await this.delay(1500);
            
            // 最後一次嘗試
            response = await fetch(url, {
              headers: {
                ...baseHeaders,
                'Cookie': Array.from(cookieJar.entries()).map(([k, v]) => `${k}=${v}`).join('; '),
                'Referer': url,
                'X-Requested-With': 'XMLHttpRequest'
              }
            });
            
            if (response.ok) {
              const finalText = await response.text();
              if (finalText.includes('建築執照號碼') || finalText.includes('建造執照號碼')) {
                return finalText;
              }
            }
          } else {
            return text;
          }
        }
      } catch (error) {
        console.error(`獲取頁面錯誤 (嘗試 ${attempt + 1}/${maxRetries}):`, error.message);
      }
      
      if (attempt < maxRetries - 1) {
        await this.delay(3000 + attempt * 1000); // 遞增延遲
      }
    }
    
    return null;
  }

  // 解析建照資料
  parsePermitData(htmlContent, indexKey) {
    try {
      // 檢查是否包含遺失個資
      if (htmlContent.includes('○○○代表遺失個資')) {
        return "NO_DATA";
      }

      const permitData = {
        indexKey: indexKey,
        permitYear: parseInt(indexKey.substr(0, 3)),
        permitType: parseInt(indexKey.substr(3, 1)),
        sequenceNumber: parseInt(indexKey.substr(4, 5)),
        versionNumber: parseInt(indexKey.substr(9, 2)),
        crawledAt: new Date().toISOString()
      };

      // 建照號碼
      let match = htmlContent.match(/建造執照號碼[：:]\s*([^\s<]+)/);
      if (!match) match = htmlContent.match(/建築執照號碼[：:]\s*([^\s<]+)/);
      if (match) {
        permitData.permitNumber = match[1].trim();
      } else {
        return null;
      }

      // 申請人
      match = htmlContent.match(/起造人[^>]*姓名[^>]*>([^<]+)/);
      if (match) permitData.applicantName = match[1].trim();

      // 地址
      match = htmlContent.match(/地號[^>]*>([^<]+)/);
      if (!match) match = htmlContent.match(/地址[^>]*>([^<]+)/);
      if (match) permitData.siteAddress = match[1].trim();

      // 行政區（從地址解析）
      if (permitData.siteAddress) {
        const districtMatch = permitData.siteAddress.match(/臺中市([^區]+區)/);
        if (districtMatch) {
          permitData.district = districtMatch[1];
        }
      }

      // 樓層資訊
      match = htmlContent.match(/地上.*?層.*?棟.*?戶|地上.*?層.*?幢.*?棟.*?戶/);
      if (match) {
        permitData.floorInfo = match[0];
        
        // 解析詳細資訊
        const floorMatch = match[0].match(/地上(\d+)層/);
        if (floorMatch) {
          permitData.floorsAbove = parseInt(floorMatch[1]);
          permitData.floors = parseInt(floorMatch[1]);
        }

        const blockMatch = match[0].match(/(\d+)幢/);
        if (blockMatch) permitData.blockCount = parseInt(blockMatch[1]);

        const buildingMatch = match[0].match(/(\d+)棟/);
        if (buildingMatch) {
          permitData.buildingCount = parseInt(buildingMatch[1]);
          permitData.buildings = parseInt(buildingMatch[1]);
        }

        const unitMatch = match[0].match(/(\d+)戶/);
        if (unitMatch) {
          permitData.unitCount = parseInt(unitMatch[1]);
          permitData.units = parseInt(unitMatch[1]);
        }
      }

      // 總樓地板面積
      match = htmlContent.match(/總樓地板面積.*?<span[^>]*>([0-9.,]+)/);
      if (match) {
        permitData.totalFloorArea = parseFloat(match[1].replace(/,/g, ''));
      }

      // 發照日期
      match = htmlContent.match(/發照日期.*?(\d{3})\/(\d{2})\/(\d{2})/);
      if (match) {
        const year = parseInt(match[1]);
        const month = parseInt(match[2]);
        const day = parseInt(match[3]);
        permitData.issueDate = `${year + 1911}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
        permitData.issueDateROC = `${match[1]}/${match[2]}/${match[3]}`;
      }

      // 設計人
      match = htmlContent.match(/設計人[^>]*姓名[^>]*>([^<]+)/);
      if (match) permitData.designerName = match[1].trim();

      match = htmlContent.match(/設計人[^>]*事務所[^>]*>([^<]+)/);
      if (match) permitData.designerCompany = match[1].trim();

      // 監造人
      match = htmlContent.match(/監造人[^>]*姓名[^>]*>([^<]+)/);
      if (match) permitData.supervisorName = match[1].trim();

      match = htmlContent.match(/監造人[^>]*事務所[^>]*>([^<]+)/);
      if (match) permitData.supervisorCompany = match[1].trim();

      // 承造人
      match = htmlContent.match(/承造人[^>]*姓名[^>]*>([^<]+)/);
      if (match) permitData.contractorName = match[1].trim();

      match = htmlContent.match(/承造廠商[^>]*>([^<]+)/);
      if (match) permitData.contractorCompany = match[1].trim();

      return permitData;
    } catch (error) {
      console.error('解析建照資料錯誤:', error);
      return null;
    }
  }

  // 爬取單一建照
  async crawlSinglePermit(indexKey) {
    try {
      const htmlContent = await this.fetchPageWithRetry(indexKey);
      if (!htmlContent) {
        return null;
      }

      const permitData = this.parsePermitData(htmlContent, indexKey);
      return permitData;
    } catch (error) {
      console.error(`爬取建照錯誤 ${indexKey}:`, error);
      return null;
    }
  }

  // 爬取年份範圍
  async crawlYearRange(year, startSeq, endSeq = null, autoStop = true) {
    console.log(`🚀 開始爬取 ${year} 年資料 (從 ${startSeq.toString().padStart(5, '0')} 開始${endSeq ? ` 到 ${endSeq.toString().padStart(5, '0')}` : '，直到空白'})`);
    console.log(`🔧 參數: 延遲=${this.requestDelayMs}ms, 批次=${this.batchSize}`);
    console.log("=" * 70);

    let consecutiveNoData = 0;
    let consecutiveFailed = 0;
    let seq = startSeq;

    while (true) {
      // 檢查是否到達結束序號
      if (endSeq && seq > endSeq) break;
      
      // 檢查是否達到單次執行上限
      if (this.stats.totalAttempted >= this.maxCrawlPerRun) {
        console.log(`\n🛑 達到單次執行上限 (${this.maxCrawlPerRun} 筆)`);
        break;
      }

      const indexKey = this.generateIndexKey(year, this.crawlType, seq);
      this.stats.totalAttempted++;

      console.log(`🔍 [${seq.toString().padStart(5, '0')}] ${indexKey}...`, '');

      const result = await this.crawlSinglePermit(indexKey);

      if (result === "NO_DATA") {
        // 無資料
        this.stats.noData++;
        consecutiveNoData++;
        consecutiveFailed = 0;
        console.log(`⏭️ 無資料 (連續 ${consecutiveNoData})`);

        if (autoStop && consecutiveNoData >= this.maxConsecutiveNoData) {
          console.log(`\n🛑 連續 ${this.maxConsecutiveNoData} 筆無資料，停止 ${year} 年爬取`);
          break;
        }
      } else if (result) {
        // 成功
        this.results.push(result);
        this.stats.successful++;
        consecutiveNoData = 0;
        consecutiveFailed = 0;
        console.log(`✅ ${result.permitNumber}`);
      } else {
        // 失敗
        this.stats.failed++;
        consecutiveNoData = 0;
        consecutiveFailed++;
        console.log(`❌ 失敗 (連續 ${consecutiveFailed})`);

        if (autoStop && consecutiveFailed >= this.maxConsecutiveFailures) {
          console.log(`\n🛑 連續 ${this.maxConsecutiveFailures} 次失敗，停止 ${year} 年爬取`);
          break;
        }
      }

      // 批次上傳
      if (this.results.length >= this.batchSize) {
        console.log(`\n💾 批次上傳 ${this.results.length} 筆資料...`);
        const uploadResult = await this.storage.updatePermits(this.results);
        if (uploadResult.success) {
          console.log(`✅ 上傳成功`);
          this.results = [];
        } else {
          console.log(`❌ 上傳失敗: ${uploadResult.error}`);
        }
      }

      // 延遲
      await this.delay(this.requestDelayMs);
      seq++;
    }

    // 上傳剩餘資料
    if (this.results.length > 0) {
      console.log(`\n💾 上傳剩餘 ${this.results.length} 筆資料...`);
      await this.storage.updatePermits(this.results);
      this.results = [];
    }

    return this.stats;
  }

  // 每日爬蟲執行
  async dailyCrawl() {
    const startTime = new Date();
    console.log(`🕐 每日爬蟲開始: ${startTime.toISOString()}`);
    console.log("=" * 60);

    try {
      // 取得目前進度
      const progress = await this.storage.getCrawlProgress();
      console.log('📊 目前進度:');
      console.log(`  114年: ${progress.year114.count} 筆, 最大序號: ${progress.year114.max}`);
      console.log(`  113年: ${progress.year113.count} 筆, 最大序號: ${progress.year113.max}`);
      console.log(`  112年: ${progress.year112.count} 筆, 最大序號: ${progress.year112.max}`);

      // 決定要爬取的年份和起始序號
      let targetYear = 114;
      let startSeq = progress.year114.max + 1;

      // 如果114年已經連續失敗，檢查其他年份
      if (progress.year114.max >= 1138) {
        // 114年可能已完成，檢查113年
        if (progress.year113.max < 2201) {
          targetYear = 113;
          startSeq = progress.year113.max + 1;
        } else if (progress.year112.max < 2039) {
          targetYear = 112;
          startSeq = progress.year112.max + 1;
        } else {
          console.log('✅ 所有年份都已爬取完成');
          return;
        }
      }

      console.log(`\n📊 開始爬取: ${targetYear}年 序號${startSeq}`);

      // 執行爬取
      const stats = await this.crawlYearRange(targetYear, startSeq, null, true);

      // 儲存爬蟲記錄
      const endTime = new Date();
      const duration = Math.round((endTime - startTime) / 1000);
      
      const log = {
        date: startTime.toISOString().split('T')[0],
        startTime: startTime.toISOString(),
        endTime: endTime.toISOString(),
        duration: duration,
        targetYear: targetYear,
        startSequence: startSeq,
        stats: stats,
        status: 'completed'
      };

      await this.storage.saveCrawlLog(log);

      console.log(`\n🏁 每日爬蟲完成`);
      console.log(`📊 統計: 總嘗試 ${stats.totalAttempted} 筆, 成功 ${stats.successful} 筆, 失敗 ${stats.failed} 筆`);
      console.log(`⏱️ 耗時: ${duration} 秒`);

    } catch (error) {
      console.error('每日爬蟲執行錯誤:', error);
      
      // 記錄錯誤
      const log = {
        date: startTime.toISOString().split('T')[0],
        startTime: startTime.toISOString(),
        endTime: new Date().toISOString(),
        error: error.message,
        status: 'failed'
      };
      
      await this.storage.saveCrawlLog(log);
    }
  }
}