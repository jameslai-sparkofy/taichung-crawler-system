// 使用 Cloudflare Browser Rendering API 的爬蟲
export class BrowserCrawler {
  constructor(env, storage) {
    this.env = env;
    this.storage = storage;
    this.baseUrl = "https://mcgbm.taichung.gov.tw/bupic/pages/queryInfoAction.do";
    
    // 從環境變數讀取設定
    this.startYear = parseInt(env.START_YEAR) || 114;
    this.crawlType = parseInt(env.CRAWL_TYPE) || 1;
    this.maxConsecutiveFailures = parseInt(env.MAX_CONSECUTIVE_FAILURES) || 5;
    this.batchSize = parseInt(env.BATCH_SIZE) || 30;
    this.requestDelayMs = parseInt(env.REQUEST_DELAY_MS) || 800;
    
    this.stats = {
      totalAttempted: 0,
      successful: 0,
      failed: 0,
      skipped: 0,
      noData: 0
    };
    
    this.results = [];
  }

  // 使用 Browser Rendering API
  async fetchWithBrowser(indexKey) {
    const url = `${this.baseUrl}?INDEX_KEY=${indexKey}`;
    
    // Cloudflare Browser Rendering API endpoint
    const browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
      const page = await browser.newPage();
      
      // 設定 User-Agent
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
      
      // 第一次訪問 - 建立 session
      await page.goto(url, { waitUntil: 'networkidle2' });
      await page.waitForTimeout(1500);
      
      // 第二次訪問 - 重新整理
      await page.reload({ waitUntil: 'networkidle2' });
      await page.waitForTimeout(1000);
      
      // 檢查是否有內容
      const content = await page.content();
      
      // 如果還是沒有內容，再試一次
      if (!content.includes('建築執照號碼') && !content.includes('建造執照號碼')) {
        await page.reload({ waitUntil: 'networkidle2' });
        await page.waitForTimeout(1000);
        const finalContent = await page.content();
        return finalContent;
      }
      
      return content;
    } finally {
      await browser.close();
    }
  }

  // ... 其他方法與 crawler-oci.js 相同
}