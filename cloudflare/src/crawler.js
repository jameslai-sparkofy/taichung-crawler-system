// 建照爬蟲類別
export class BuildingPermitCrawler {
  constructor(db) {
    this.db = db;
    this.baseUrl = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do";
    this.startYear = 114;
    this.crawlType = 1;
    this.delayMs = 2000; // 2秒延遲
    
    // 統計資料
    this.totalCrawled = 0;
    this.newRecords = 0;
    this.errorRecords = 0;
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

  // 獲取頁面內容
  async fetchPageWithRetry(indexKey, maxRetries = 3) {
    const url = `${this.baseUrl}?INDEX_KEY=${indexKey}`;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        // 第一次請求
        let response = await fetch(url, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
          }
        });

        if (response.ok) {
          await this.delay(1000); // 等待1秒
          
          // 第二次請求（重新整理）
          response = await fetch(url, {
            headers: {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
              'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
            }
          });

          if (response.ok) {
            const text = await response.text();
            if (text.includes('建築執照號碼') || text.includes('○○○代表遺失個資歡迎')) {
              return text;
            }
          }
        }
      } catch (error) {
        console.error(`獲取頁面錯誤 (嘗試 ${attempt + 1}/${maxRetries}):`, error);
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
        console.log(`INDEX_KEY ${indexKey}: 包含遺失個資訊息，跳過`);
        return null;
      }

      const keyInfo = this.parseIndexKey(indexKey);
      if (!keyInfo) return null;

      const permitData = {
        permit_number: null,
        permit_year: keyInfo.year,
        permit_type: keyInfo.permitType,
        sequence_number: keyInfo.sequence,
        version_number: keyInfo.version,
        applicant_name: null,
        designer_name: null,
        designer_company: null,
        supervisor_name: null,
        supervisor_company: null,
        contractor_name: null,
        contractor_company: null,
        engineer_name: null,
        site_address: null,
        site_city: null,
        site_zone: null,
        site_area: null,
        crawled_at: new Date().toISOString()
      };

      // 簡化的資料解析 - 使用正則表達式
      const patterns = {
        permit_number: /建造執照號碼[：:]\s*([^\s<]+)/,
        applicant_name: /起造人[^>]*姓名[^>]*>([^<]+)/,
        designer_name: /設計人[^>]*姓名[^>]*>([^<]+)/,
        designer_company: /設計人[^>]*事務所[^>]*>([^<]+)/,
        supervisor_name: /監造人[^>]*姓名[^>]*>([^<]+)/,
        supervisor_company: /監造人[^>]*事務所[^>]*>([^<]+)/,
        contractor_name: /承造人[^>]*姓名[^>]*>([^<]+)/,
        contractor_company: /承造廠商[^>]*>([^<]+)/,
        engineer_name: /專任工程人員[^>]*>([^<]+)/,
        site_address: /地號[^>]*>([^<]+)/,
        site_city: /地址[^>]*>([^<]+)/,
        site_zone: /使用分區[^>]*>([^<]+)/,
        site_area: /基地面積[^>]*>[\s\S]*?(\d+\.?\d*)/
      };

      for (const [key, pattern] of Object.entries(patterns)) {
        const match = htmlContent.match(pattern);
        if (match) {
          permitData[key] = match[1].trim();
          if (key === 'site_area') {
            permitData[key] = parseFloat(match[1]);
          }
        }
      }

      // 檢查是否有建照號碼
      if (!permitData.permit_number) {
        console.log(`INDEX_KEY ${indexKey}: 未找到建照號碼`);
        return null;
      }

      return permitData;
    } catch (error) {
      console.error('解析建照資料錯誤:', error);
      return null;
    }
  }

  // 儲存建照資料到資料庫
  async savePermitData(permitData) {
    try {
      const result = await this.db.prepare(`
        INSERT OR REPLACE INTO building_permits (
          permit_number, permit_year, permit_type, sequence_number, version_number,
          applicant_name, designer_name, designer_company, supervisor_name, supervisor_company,
          contractor_name, contractor_company, engineer_name, site_address, site_city,
          site_zone, site_area, crawled_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      `).bind(
        permitData.permit_number,
        permitData.permit_year,
        permitData.permit_type,
        permitData.sequence_number,
        permitData.version_number,
        permitData.applicant_name,
        permitData.designer_name,
        permitData.designer_company,
        permitData.supervisor_name,
        permitData.supervisor_company,
        permitData.contractor_name,
        permitData.contractor_company,
        permitData.engineer_name,
        permitData.site_address,
        permitData.site_city,
        permitData.site_zone,
        permitData.site_area,
        permitData.crawled_at
      ).run();

      if (result.changes > 0) {
        console.log(`儲存建照資料: ${permitData.permit_number}`);
        return 'saved';
      }
      return 'no_change';
    } catch (error) {
      console.error('儲存建照資料錯誤:', error);
      throw error;
    }
  }

  // 爬取單一建照
  async crawlSinglePermit(indexKey) {
    try {
      console.log(`爬取 INDEX_KEY: ${indexKey}`);
      
      const htmlContent = await this.fetchPageWithRetry(indexKey);
      if (!htmlContent) {
        console.error(`無法獲取頁面: ${indexKey}`);
        this.errorRecords++;
        return false;
      }

      const permitData = this.parsePermitData(htmlContent, indexKey);
      if (!permitData) {
        return false;
      }

      await this.savePermitData(permitData);
      this.newRecords++;
      this.totalCrawled++;
      
      return true;
    } catch (error) {
      console.error(`爬取建照錯誤: ${error}`);
      this.errorRecords++;
      return false;
    }
  }

  // 獲取最大序號
  async getMaxSequenceNumber(year, permitType) {
    try {
      const result = await this.db.prepare(`
        SELECT MAX(sequence_number) as max_seq 
        FROM building_permits 
        WHERE permit_year = ? AND permit_type = ?
      `).bind(year, permitType).first();
      
      return result?.max_seq || 0;
    } catch (error) {
      console.error('查詢最大序號錯誤:', error);
      return 0;
    }
  }

  // 開始爬蟲記錄
  async startCrawlLog(crawlDate) {
    try {
      await this.db.prepare(`
        INSERT OR REPLACE INTO crawl_logs (crawl_date, start_time, status)
        VALUES (?, CURRENT_TIMESTAMP, 'running')
      `).bind(crawlDate).run();
    } catch (error) {
      console.error('建立爬蟲記錄錯誤:', error);
    }
  }

  // 更新爬蟲記錄
  async updateCrawlLog(crawlDate, status, errorMessage = null) {
    try {
      await this.db.prepare(`
        UPDATE crawl_logs 
        SET end_time = CURRENT_TIMESTAMP, status = ?, total_records = ?, 
            new_records = ?, error_records = ?, error_message = ?
        WHERE crawl_date = ?
      `).bind(status, this.totalCrawled, this.newRecords, this.errorRecords, errorMessage, crawlDate).run();
    } catch (error) {
      console.error('更新爬蟲記錄錯誤:', error);
    }
  }

  // 每日爬蟲執行
  async dailyCrawl() {
    const crawlDate = new Date().toISOString().split('T')[0];
    console.log(`開始每日爬蟲任務: ${crawlDate}`);

    try {
      await this.startCrawlLog(crawlDate);
      
      // 重置統計
      this.totalCrawled = 0;
      this.newRecords = 0;
      this.errorRecords = 0;

      // 獲取最大序號
      const maxSequence = await this.getMaxSequenceNumber(this.startYear, this.crawlType);
      let currentSequence = Math.max(maxSequence, 1);
      let consecutiveFailures = 0;
      const maxConsecutiveFailures = 50;

      console.log(`從序號 ${currentSequence} 開始爬取`);

      while (consecutiveFailures < maxConsecutiveFailures) {
        const indexKey = this.generateIndexKey(this.startYear, this.crawlType, currentSequence);
        const success = await this.crawlSinglePermit(indexKey);

        if (success) {
          consecutiveFailures = 0;
        } else {
          consecutiveFailures++;
        }

        currentSequence++;
        
        // 延遲避免過度請求
        await this.delay(this.delayMs);
        
        // Cloudflare Workers有執行時間限制，所以限制最大爬取數量
        if (this.totalCrawled >= 100) {
          console.log('達到單次執行最大爬取數量限制');
          break;
        }
      }

      await this.updateCrawlLog(crawlDate, 'completed');
      console.log(`爬蟲任務完成: 總計 ${this.totalCrawled} 筆，新增 ${this.newRecords} 筆，錯誤 ${this.errorRecords} 筆`);
      
      return {
        success: true,
        total: this.totalCrawled,
        new: this.newRecords,
        errors: this.errorRecords
      };

    } catch (error) {
      const errorMsg = `爬蟲任務失敗: ${error.message}`;
      console.error(errorMsg);
      await this.updateCrawlLog(crawlDate, 'failed', errorMsg);
      
      return {
        success: false,
        error: errorMsg,
        total: this.totalCrawled,
        new: this.newRecords,
        errors: this.errorRecords
      };
    }
  }

  // 延遲函數
  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}