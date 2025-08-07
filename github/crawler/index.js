const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');

class TaichungBuildingCrawler {
  constructor() {
    this.baseUrl = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do";
    this.dataDir = path.join(__dirname, '../data');
    this.docsDir = path.join(__dirname, '../docs');
    this.startYear = 114;
    this.crawlType = 1;
    this.delayMs = 2000;
    
    // 統計資料
    this.stats = {
      totalCrawled: 0,
      newRecords: 0,
      errorRecords: 0,
      startTime: new Date(),
      endTime: null
    };

    // 確保目錄存在
    fs.ensureDirSync(this.dataDir);
    fs.ensureDirSync(this.docsDir);
  }

  // 生成INDEX_KEY
  generateIndexKey(year, permitType, sequence, version = 0) {
    return `${year}${permitType}${sequence.toString().padStart(5, '0')}${version.toString().padStart(2, '0')}`;
  }

  // 解析INDEX_KEY
  parseIndexKey(indexKey) {
    if (indexKey.length !== 11) return null;
    
    return {
      year: parseInt(indexKey.substr(0, 3)),
      permitType: parseInt(indexKey.substr(3, 1)),
      sequence: parseInt(indexKey.substr(4, 5)),
      version: parseInt(indexKey.substr(9, 2))
    };
  }

  // 獲取頁面內容（含重新整理機制）
  async fetchPageWithRetry(indexKey, maxRetries = 3) {
    const url = `${this.baseUrl}?INDEX_KEY=${indexKey}`;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        console.log(`🔍 爬取 INDEX_KEY: ${indexKey} (嘗試 ${attempt + 1}/${maxRetries})`);
        
        // 第一次請求
        let response = await axios.get(url, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
          },
          timeout: 30000
        });

        if (response.status === 200) {
          await this.delay(1000); // 等待1秒
          
          // 第二次請求（重新整理）
          response = await axios.get(url, {
            headers: {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
              'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
            },
            timeout: 30000
          });

          if (response.status === 200) {
            const text = response.data;
            if (text.includes('建築執照號碼') || text.includes('○○○代表遺失個資歡迎')) {
              return text;
            }
          }
        }
      } catch (error) {
        console.error(`❌ 獲取頁面錯誤 (嘗試 ${attempt + 1}/${maxRetries}):`, error.message);
      }
      
      if (attempt < maxRetries - 1) {
        await this.delay(2000);
      }
    }
    
    return null;
  }

  // 解析建照資料
  parsePermitData(htmlContent, indexKey) {
    try {
      // 檢查是否包含遺失個資
      if (htmlContent.includes('○○○代表遺失個資歡迎')) {
        console.log(`ℹ️  INDEX_KEY ${indexKey}: 包含遺失個資訊息，跳過`);
        return null;
      }

      const keyInfo = this.parseIndexKey(indexKey);
      if (!keyInfo) return null;

      const $ = cheerio.load(htmlContent);
      
      const permitData = {
        indexKey: indexKey,
        permitNumber: null,
        permitYear: keyInfo.year,
        permitType: keyInfo.permitType,
        sequenceNumber: keyInfo.sequence,
        versionNumber: keyInfo.version,
        applicantName: null,
        designerName: null,
        designerCompany: null,
        supervisorName: null,
        supervisorCompany: null,
        contractorName: null,
        contractorCompany: null,
        engineerName: null,
        siteAddress: null,
        siteCity: null,
        siteZone: null,
        siteArea: null,
        crawledAt: new Date().toISOString(),
        rawHtml: htmlContent // 保存原始HTML以備後用
      };

      // 簡化的資料解析
      const text = $.text();
      
      // 建照號碼
      const permitNumberMatch = htmlContent.match(/建造執照號碼[：:\s]*([^\s<\n]+)/);
      if (permitNumberMatch) {
        permitData.permitNumber = permitNumberMatch[1].trim();
      }

      // 表格資料解析
      $('table tr').each((i, row) => {
        const cells = $(row).find('td, th');
        if (cells.length >= 2) {
          const label = $(cells[0]).text().trim();
          
          if (label.includes('起造人') && cells.length >= 3) {
            const nextLabel = $(cells[1]).text().trim();
            if (nextLabel.includes('姓名')) {
              permitData.applicantName = $(cells[2]).text().trim();
            }
          }
          
          if (label.includes('設計人') && cells.length >= 4) {
            if ($(cells[1]).text().includes('姓名')) {
              permitData.designerName = $(cells[2]).text().trim();
            }
            if ($(cells[3]).text().includes('事務所') && cells.length >= 5) {
              permitData.designerCompany = $(cells[4]).text().trim();
            }
          }
          
          if (label.includes('監造人') && cells.length >= 4) {
            if ($(cells[1]).text().includes('姓名')) {
              permitData.supervisorName = $(cells[2]).text().trim();
            }
            if ($(cells[3]).text().includes('事務所') && cells.length >= 5) {
              permitData.supervisorCompany = $(cells[4]).text().trim();
            }
          }
          
          if (label.includes('承造人') && cells.length >= 4) {
            if ($(cells[1]).text().includes('姓名')) {
              permitData.contractorName = $(cells[2]).text().trim();
            }
            if (cells.length >= 5) {
              permitData.contractorCompany = $(cells[4]).text().trim();
            }
          }
          
          if (label.includes('專任工程人員')) {
            permitData.engineerName = $(cells[1]).text().trim();
          }
          
          if (label.includes('地號')) {
            permitData.siteAddress = $(cells[1]).text().trim();
          }
          
          if (label.includes('地址')) {
            permitData.siteCity = $(cells[1]).text().trim();
          }
          
          if (label.includes('使用分區')) {
            permitData.siteZone = $(cells[1]).text().trim();
          }
          
          if (label.includes('基地面積') && cells.length >= 4) {
            const areaText = $(cells[3]).text().trim();
            const areaMatch = areaText.match(/([\d.]+)/);
            if (areaMatch) {
              permitData.siteArea = parseFloat(areaMatch[1]);
            }
          }
        }
      });

      // 檢查是否有必要資料
      if (!permitData.permitNumber) {
        console.log(`⚠️  INDEX_KEY ${indexKey}: 未找到建照號碼`);
        return null;
      }

      // 清理rawHtml以節省空間
      delete permitData.rawHtml;

      return permitData;
    } catch (error) {
      console.error(`❌ 解析建照資料錯誤:`, error.message);
      return null;
    }
  }

  // 載入現有資料
  async loadExistingData() {
    try {
      const dataFile = path.join(this.dataDir, 'permits.json');
      if (await fs.pathExists(dataFile)) {
        const data = await fs.readJson(dataFile);
        return data.permits || [];
      }
    } catch (error) {
      console.error('載入現有資料錯誤:', error.message);
    }
    return [];
  }

  // 儲存資料
  async saveData(permits) {
    try {
      const dataFile = path.join(this.dataDir, 'permits.json');
      const data = {
        lastUpdate: new Date().toISOString(),
        totalCount: permits.length,
        permits: permits
      };
      
      await fs.writeJson(dataFile, data, { spaces: 2 });
      console.log(`💾 已儲存 ${permits.length} 筆建照資料`);
    } catch (error) {
      console.error('儲存資料錯誤:', error.message);
    }
  }

  // 儲存執行記錄
  async saveLog() {
    try {
      const logFile = path.join(this.dataDir, 'crawl-logs.json');
      let logs = [];
      
      if (await fs.pathExists(logFile)) {
        const data = await fs.readJson(logFile);
        logs = data.logs || [];
      }

      const logEntry = {
        date: new Date().toISOString().split('T')[0],
        startTime: this.stats.startTime.toISOString(),
        endTime: this.stats.endTime.toISOString(),
        totalCrawled: this.stats.totalCrawled,
        newRecords: this.stats.newRecords,
        errorRecords: this.stats.errorRecords,
        status: this.stats.errorRecords > this.stats.newRecords ? 'failed' : 'completed'
      };

      // 移除今日舊記錄
      logs = logs.filter(log => log.date !== logEntry.date);
      logs.unshift(logEntry);

      // 只保留最近30天記錄
      logs = logs.slice(0, 30);

      await fs.writeJson(logFile, { logs }, { spaces: 2 });
      console.log(`📋 已儲存執行記錄`);
    } catch (error) {
      console.error('儲存記錄錯誤:', error.message);
    }
  }

  // 獲取最大序號
  getMaxSequenceNumber(permits, year, permitType) {
    const filtered = permits.filter(p => p.permitYear === year && p.permitType === permitType);
    if (filtered.length === 0) return 0;
    return Math.max(...filtered.map(p => p.sequenceNumber));
  }

  // 爬取單一建照
  async crawlSinglePermit(indexKey) {
    try {
      const htmlContent = await this.fetchPageWithRetry(indexKey);
      if (!htmlContent) {
        console.error(`❌ 無法獲取頁面: ${indexKey}`);
        this.stats.errorRecords++;
        return null;
      }

      const permitData = this.parsePermitData(htmlContent, indexKey);
      if (!permitData) {
        return null;
      }

      console.log(`✅ 成功解析建照: ${permitData.permitNumber}`);
      this.stats.newRecords++;
      this.stats.totalCrawled++;
      
      return permitData;
    } catch (error) {
      console.error(`❌ 爬取建照錯誤:`, error.message);
      this.stats.errorRecords++;
      return null;
    }
  }

  // 主要爬蟲執行
  async crawl() {
    console.log('🚀 開始台中市建照資料爬取');
    console.log(`📅 執行時間: ${this.stats.startTime.toLocaleString('zh-TW')}`);

    try {
      // 載入現有資料
      const existingPermits = await this.loadExistingData();
      console.log(`📊 現有資料: ${existingPermits.length} 筆`);

      // 獲取最大序號
      const maxSequence = this.getMaxSequenceNumber(existingPermits, this.startYear, this.crawlType);
      let currentSequence = Math.max(maxSequence, 1);
      let consecutiveFailures = 0;
      const maxConsecutiveFailures = 50;

      console.log(`🔢 從序號 ${currentSequence} 開始爬取`);

      const newPermits = [];

      while (consecutiveFailures < maxConsecutiveFailures && newPermits.length < 100) {
        const indexKey = this.generateIndexKey(this.startYear, this.crawlType, currentSequence);
        const permitData = await this.crawlSinglePermit(indexKey);

        if (permitData) {
          // 檢查是否已存在
          const exists = existingPermits.some(p => p.indexKey === indexKey);
          if (!exists) {
            newPermits.push(permitData);
            consecutiveFailures = 0;
          }
        } else {
          consecutiveFailures++;
        }

        currentSequence++;
        
        // 延遲避免過度請求
        await this.delay(this.delayMs);
      }

      // 合併新舊資料
      const allPermits = [...existingPermits, ...newPermits];
      
      // 依序號排序
      allPermits.sort((a, b) => {
        if (a.permitYear !== b.permitYear) return b.permitYear - a.permitYear;
        if (a.permitType !== b.permitType) return a.permitType - b.permitType;
        return b.sequenceNumber - a.sequenceNumber;
      });

      // 儲存資料
      await this.saveData(allPermits);

      this.stats.endTime = new Date();
      await this.saveLog();

      console.log('✅ 爬蟲任務完成');
      console.log(`📊 統計: 總計 ${this.stats.totalCrawled} 筆，新增 ${this.stats.newRecords} 筆，錯誤 ${this.stats.errorRecords} 筆`);
      console.log(`⏱️  執行時間: ${((this.stats.endTime - this.stats.startTime) / 1000).toFixed(1)} 秒`);

    } catch (error) {
      console.error('❌ 爬蟲執行失敗:', error.message);
      this.stats.endTime = new Date();
      await this.saveLog();
    }
  }

  // 延遲函數
  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// 執行爬蟲
if (require.main === module) {
  const crawler = new TaichungBuildingCrawler();
  crawler.crawl().then(() => {
    console.log('🎉 爬蟲程序執行完畢');
    process.exit(0);
  }).catch(error => {
    console.error('💥 爬蟲程序執行失敗:', error);
    process.exit(1);
  });
}

module.exports = TaichungBuildingCrawler;