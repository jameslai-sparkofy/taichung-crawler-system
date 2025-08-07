// 測試記錄功能
import { OCISimpleStorage } from './src/oci-simple.js';

const env = {
  OCI_NAMESPACE: 'nrsdi1rz5vl8',
  OCI_BUCKET: 'taichung-building-permits',
  OCI_REGION: 'ap-tokyo-1',
  OCI_PREAUTH_KEY: 'P4-4FVql_6vPAHVqX7JZxDbS15B34gCaGE-ta0BgOjAVPxkUrre9ZpYbtUZHneKO'
};

async function testLog() {
  const storage = new OCISimpleStorage(env);
  
  const testLog = {
    date: new Date().toISOString().split('T')[0],
    startTime: new Date().toISOString(),
    endTime: new Date().toISOString(),
    duration: 5,
    targetYear: 114,
    startSequence: 1139,
    stats: {
      totalAttempted: 5,
      successful: 3,
      failed: 2,
      noData: 0
    },
    status: 'completed'
  };

  console.log('測試儲存記錄...');
  const result = await storage.saveCrawlLog(testLog);
  console.log('結果:', result ? '成功' : '失敗');
}

testLog().catch(console.error);