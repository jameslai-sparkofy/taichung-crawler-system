// 簡化版 OCI Storage（使用公開讀取桶或預簽名 URL）
export class OCISimpleStorage {
  constructor(env) {
    this.namespace = env.OCI_NAMESPACE;
    this.bucket = env.OCI_BUCKET;
    this.region = env.OCI_REGION;
    this.preauthKey = env.OCI_PREAUTH_KEY; // 預驗證請求金鑰
    
    this.baseUrl = `https://objectstorage.${this.region}.oraclecloud.com`;
  }

  // 使用預驗證請求上傳
  async uploadWithPreauthRequest(objectName, data) {
    const url = `${this.baseUrl}/p/${this.preauthKey}/n/${this.namespace}/b/${this.bucket}/o/${encodeURIComponent(objectName)}`;
    
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data, null, 2)
    });

    if (!response.ok) {
      throw new Error(`上傳失敗: ${response.status} ${response.statusText}`);
    }

    return true;
  }

  // 公開讀取
  async getPublicObject(objectName) {
    const url = `${this.baseUrl}/n/${this.namespace}/b/${this.bucket}/o/${encodeURIComponent(objectName)}`;
    
    const response = await fetch(url);
    
    if (response.ok) {
      return await response.json();
    }
    
    if (response.status === 404) {
      return null;
    }
    
    throw new Error(`下載失敗: ${response.status}`);
  }

  // 更新 permits.json
  async updatePermits(newPermits) {
    try {
      // 下載現有資料
      let existingData = await this.getPublicObject('permits.json');
      if (!existingData) {
        existingData = {
          lastUpdate: new Date().toISOString(),
          totalCount: 0,
          yearCounts: {},
          permits: []
        };
      }

      // 建立索引字典
      const existingDict = {};
      for (const permit of existingData.permits) {
        existingDict[permit.indexKey] = permit;
      }

      // 更新資料
      let addedCount = 0;
      let updatedCount = 0;

      for (const permit of newPermits) {
        const indexKey = permit.indexKey;
        if (existingDict[indexKey]) {
          // 更新現有資料
          if (permit.crawledAt > existingDict[indexKey].crawledAt) {
            existingDict[indexKey] = permit;
            updatedCount++;
          }
        } else {
          // 新增資料
          existingDict[indexKey] = permit;
          addedCount++;
        }
      }

      // 轉回陣列並排序
      const allPermits = Object.values(existingDict);
      allPermits.sort((a, b) => {
        if (a.permitYear !== b.permitYear) {
          return b.permitYear - a.permitYear;
        }
        return b.sequenceNumber - a.sequenceNumber;
      });

      // 統計各年份數量
      const yearCounts = {};
      for (const permit of allPermits) {
        const year = permit.permitYear;
        yearCounts[year] = (yearCounts[year] || 0) + 1;
      }

      // 更新資料
      existingData.permits = allPermits;
      existingData.totalCount = allPermits.length;
      existingData.yearCounts = yearCounts;
      existingData.lastUpdate = new Date().toISOString();

      // 使用預驗證請求上傳
      await this.uploadWithPreauthRequest('permits.json', existingData);
      await this.uploadWithPreauthRequest('data/permits.json', existingData);
      await this.uploadWithPreauthRequest('all_permits.json', existingData);

      console.log(`✅ 更新成功: 新增 ${addedCount} 筆, 更新 ${updatedCount} 筆, 總計 ${allPermits.length} 筆`);

      return {
        success: true,
        added: addedCount,
        updated: updatedCount,
        total: allPermits.length
      };
    } catch (error) {
      console.error('更新 permits 失敗:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 儲存爬蟲記錄
  async saveCrawlLog(log) {
    try {
      // 下載現有記錄
      let existingData = await this.getPublicObject('data/crawl-logs.json');
      let logs = [];
      
      if (existingData && existingData.logs) {
        logs = existingData.logs;
      } else if (Array.isArray(existingData)) {
        logs = existingData;
      }

      // 轉換格式以兼容原有系統
      const formattedLog = {
        date: log.date,
        startTime: log.startTime,
        endTime: log.endTime,
        duration: log.duration,
        results: {
          success: log.stats?.successful || 0,
          failed: log.stats?.failed || 0,
          empty: log.stats?.noData || 0,
          total: log.stats?.totalAttempted || 0
        },
        yearStats: {},
        status: log.status,
        error: log.error
      };

      // 添加年份統計
      if (log.targetYear) {
        formattedLog.yearStats[log.targetYear] = {
          crawled: log.stats?.successful || 0,
          start: log.startSequence,
          end: log.startSequence + (log.stats?.totalAttempted || 0) - 1
        };
      }

      // 新增記錄
      logs.unshift(formattedLog); // 最新的在前

      // 只保留最近 30 天的記錄
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      logs = logs.filter(l => new Date(l.date) > thirtyDaysAgo);

      // 建立兼容格式
      const dataToSave = {
        logs: logs,
        lastUpdate: new Date().toISOString()
      };

      // 上傳
      await this.uploadWithPreauthRequest('crawl-logs.json', logs);
      await this.uploadWithPreauthRequest('data/crawl-logs.json', dataToSave);

      return true;
    } catch (error) {
      console.error('儲存爬蟲記錄失敗:', error);
      return false;
    }
  }

  // 取得爬蟲進度
  async getCrawlProgress() {
    try {
      const data = await this.getPublicObject('permits.json');
      if (!data || !data.permits || data.permits.length === 0) {
        return {
          year114: { max: 0, count: 0 },
          year113: { max: 0, count: 0 },
          year112: { max: 0, count: 0 }
        };
      }

      const progress = {
        year114: { max: 0, count: 0 },
        year113: { max: 0, count: 0 },
        year112: { max: 0, count: 0 }
      };

      for (const permit of data.permits) {
        const year = permit.permitYear;
        const seq = permit.sequenceNumber;
        
        if (year === 114) {
          progress.year114.count++;
          if (seq > progress.year114.max) progress.year114.max = seq;
        } else if (year === 113) {
          progress.year113.count++;
          if (seq > progress.year113.max) progress.year113.max = seq;
        } else if (year === 112) {
          progress.year112.count++;
          if (seq > progress.year112.max) progress.year112.max = seq;
        }
      }

      return progress;
    } catch (error) {
      console.error('取得爬蟲進度失敗:', error);
      return {
        year114: { max: 0, count: 0 },
        year113: { max: 0, count: 0 },
        year112: { max: 0, count: 0 }
      };
    }
  }
}