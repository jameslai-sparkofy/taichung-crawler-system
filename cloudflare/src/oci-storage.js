// OCI Object Storage 整合
import { createHash, createHmac } from 'crypto';

export class OCIStorage {
  constructor(env) {
    this.namespace = env.OCI_NAMESPACE;
    this.bucket = env.OCI_BUCKET;
    this.region = env.OCI_REGION;
    this.tenancyId = env.OCI_TENANCY_ID;
    this.userId = env.OCI_USER_ID;
    this.fingerprint = env.OCI_FINGERPRINT;
    this.privateKey = env.OCI_PRIVATE_KEY;
    
    this.baseUrl = `https://objectstorage.${this.region}.oraclecloud.com`;
  }

  // 生成 OCI API 簽名
  async signRequest(method, path, headers = {}, body = null) {
    const date = new Date().toUTCString();
    const host = `objectstorage.${this.region}.oraclecloud.com`;
    
    // 建立簽名基礎字串
    const signingHeaders = '(request-target) host date';
    const requestTarget = `${method.toLowerCase()} ${path}`;
    
    let signingString = `(request-target): ${requestTarget}\n`;
    signingString += `host: ${host}\n`;
    signingString += `date: ${date}`;
    
    if (body) {
      const contentLength = new TextEncoder().encode(body).length;
      const contentType = 'application/json';
      const bodyHash = await this.sha256(body);
      
      signingString += `\ncontent-length: ${contentLength}`;
      signingString += `\ncontent-type: ${contentType}`;
      signingString += `\nx-content-sha256: ${bodyHash}`;
      
      headers['content-length'] = contentLength;
      headers['content-type'] = contentType;
      headers['x-content-sha256'] = bodyHash;
    }
    
    // 使用私鑰簽名
    const signature = await this.signWithPrivateKey(signingString);
    
    // 建立授權標頭
    const authHeader = `Signature version="1",keyId="${this.tenancyId}/${this.userId}/${this.fingerprint}",algorithm="rsa-sha256",headers="${signingHeaders}",signature="${signature}"`;
    
    headers['date'] = date;
    headers['host'] = host;
    headers['authorization'] = authHeader;
    
    return headers;
  }

  // SHA256 雜湊
  async sha256(data) {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    return btoa(String.fromCharCode(...new Uint8Array(hashBuffer)));
  }

  // 使用私鑰簽名（簡化版本，實際需要完整的 RSA-SHA256）
  async signWithPrivateKey(data) {
    // 注意：Cloudflare Workers 的 crypto API 限制，這裡需要特殊處理
    // 實際部署時可能需要使用其他方式處理私鑰簽名
    // 或者考慮使用預簽名 URL 方式
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(this.privateKey),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    
    const signature = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(data)
    );
    
    return btoa(String.fromCharCode(...new Uint8Array(signature)));
  }

  // 下載檔案
  async getObject(objectName) {
    const path = `/n/${this.namespace}/b/${this.bucket}/o/${encodeURIComponent(objectName)}`;
    const headers = await this.signRequest('GET', path);
    
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers
    });
    
    if (response.ok) {
      return await response.json();
    }
    
    if (response.status === 404) {
      return null;
    }
    
    throw new Error(`Failed to get object: ${response.status} ${response.statusText}`);
  }

  // 上傳檔案
  async putObject(objectName, data) {
    const body = JSON.stringify(data, null, 2);
    const path = `/n/${this.namespace}/b/${this.bucket}/o/${encodeURIComponent(objectName)}`;
    const headers = await this.signRequest('PUT', path, {}, body);
    
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers,
      body
    });
    
    if (!response.ok) {
      throw new Error(`Failed to put object: ${response.status} ${response.statusText}`);
    }
    
    return true;
  }

  // 更新 permits.json（累加模式）
  async updatePermits(newPermits) {
    try {
      // 下載現有資料
      let existingData = await this.getObject('permits.json');
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

      // 上傳到多個位置
      await this.putObject('permits.json', existingData);
      await this.putObject('data/permits.json', existingData);
      await this.putObject('all_permits.json', existingData);

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
      let logs = await this.getObject('crawl-logs.json');
      if (!logs) {
        logs = [];
      }

      // 新增記錄
      logs.push(log);

      // 只保留最近 30 天的記錄
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      logs = logs.filter(l => new Date(l.date) > thirtyDaysAgo);

      // 上傳
      await this.putObject('crawl-logs.json', logs);
      await this.putObject('data/crawl-logs.json', logs);

      return true;
    } catch (error) {
      console.error('儲存爬蟲記錄失敗:', error);
      return false;
    }
  }
}