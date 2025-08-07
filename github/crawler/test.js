const TaichungBuildingCrawler = require('./index.js');

async function testCrawler() {
  console.log('🧪 開始測試台中市建照爬蟲');
  console.log('===============================');

  const crawler = new TaichungBuildingCrawler();

  try {
    // 測試 INDEX_KEY 生成和解析
    console.log('\n📋 測試 INDEX_KEY 功能');
    const testKey = crawler.generateIndexKey(114, 1, 1, 0);
    console.log(`生成的 INDEX_KEY: ${testKey}`);
    
    const parsed = crawler.parseIndexKey(testKey);
    console.log(`解析結果:`, parsed);
    
    if (testKey === '11410000100' && 
        parsed.year === 114 && 
        parsed.permitType === 1 && 
        parsed.sequence === 1 && 
        parsed.version === 0) {
      console.log('✅ INDEX_KEY 功能測試通過');
    } else {
      console.log('❌ INDEX_KEY 功能測試失敗');
      return;
    }

    // 測試網頁獲取
    console.log('\n🌐 測試網頁獲取功能');
    const html = await crawler.fetchPageWithRetry('11410000100');
    
    if (html && (html.includes('建築執照號碼') || html.includes('○○○代表遺失個資'))) {
      console.log('✅ 網頁獲取測試通過');
      
      // 測試資料解析
      console.log('\n📄 測試資料解析功能');
      const permitData = crawler.parsePermitData(html, '11410000100');
      
      if (permitData) {
        console.log('✅ 資料解析測試通過');
        console.log('解析到的資料:');
        console.log(`  建照號碼: ${permitData.permitNumber}`);
        console.log(`  年份: ${permitData.permitYear}`);
        console.log(`  起造人: ${permitData.applicantName}`);
        console.log(`  基地地址: ${permitData.siteAddress}`);
      } else {
        console.log('⚠️  資料解析測試：可能是遺失個資的資料');
      }
    } else {
      console.log('❌ 網頁獲取測試失敗');
      return;
    }

    // 測試檔案操作
    console.log('\n💾 測試檔案操作功能');
    const testPermits = [
      {
        indexKey: '11410000100',
        permitNumber: '測試建照號碼',
        permitYear: 114,
        permitType: 1,
        sequenceNumber: 1,
        versionNumber: 0,
        crawledAt: new Date().toISOString()
      }
    ];

    await crawler.saveData(testPermits);
    console.log('✅ 檔案儲存測試通過');

    const loadedData = await crawler.loadExistingData();
    if (loadedData.length > 0) {
      console.log('✅ 檔案載入測試通過');
    } else {
      console.log('❌ 檔案載入測試失敗');
    }

    console.log('\n🎉 所有測試完成');
    console.log('系統準備就緒，可以開始正式爬取');

  } catch (error) {
    console.error('💥 測試過程發生錯誤:', error.message);
  }
}

// 執行測試
if (require.main === module) {
  testCrawler().then(() => {
    console.log('\n✅ 測試程序執行完畢');
    process.exit(0);
  }).catch(error => {
    console.error('\n💥 測試程序執行失敗:', error);
    process.exit(1);
  });
}

module.exports = testCrawler;