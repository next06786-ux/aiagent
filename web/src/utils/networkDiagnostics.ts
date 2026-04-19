/**
 * 网络诊断工具
 * 用于分析API请求延迟的原因
 */

export interface NetworkDiagnostics {
  dnsTime: number;
  tcpTime: number;
  tlsTime: number;
  requestTime: number;
  responseTime: number;
  totalTime: number;
}

export async function diagnoseNetworkLatency(url: string): Promise<NetworkDiagnostics> {
  const startTime = performance.now();
  
  // 使用 Performance API 获取详细的网络时序
  const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    entries.forEach((entry) => {
      if (entry.entryType === 'resource' && entry.name === url) {
        const resourceEntry = entry as PerformanceResourceTiming;
        console.log('[Network Diagnostics] 详细时序:', {
          DNS: `${resourceEntry.domainLookupEnd - resourceEntry.domainLookupStart}ms`,
          TCP: `${resourceEntry.connectEnd - resourceEntry.connectStart}ms`,
          TLS: resourceEntry.secureConnectionStart > 0 
            ? `${resourceEntry.connectEnd - resourceEntry.secureConnectionStart}ms` 
            : '0ms (HTTP)',
          Request: `${resourceEntry.responseStart - resourceEntry.requestStart}ms`,
          Response: `${resourceEntry.responseEnd - resourceEntry.responseStart}ms`,
          Total: `${resourceEntry.responseEnd - resourceEntry.startTime}ms`,
        });
      }
    });
  });
  
  observer.observe({ entryTypes: ['resource'] });
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Connection': 'keep-alive' }
    });
    
    const totalTime = performance.now() - startTime;
    console.log('[Network Diagnostics] Fetch完成，总耗时:', `${totalTime.toFixed(2)}ms`);
    
    return {
      dnsTime: 0,
      tcpTime: 0,
      tlsTime: 0,
      requestTime: 0,
      responseTime: 0,
      totalTime,
    };
  } finally {
    observer.disconnect();
  }
}

/**
 * 测试API连接速度
 */
export async function testApiConnection(baseUrl: string): Promise<void> {
  console.log('[Network Test] 🧪 开始API连接测试');
  console.log('[Network Test] 目标:', baseUrl);
  
  // 测试1: 健康检查端点
  const healthUrl = `${baseUrl}/health`;
  console.log('[Network Test] 测试1: 健康检查');
  const test1Start = performance.now();
  
  try {
    const response = await fetch(healthUrl, {
      method: 'GET',
      headers: { 'Connection': 'keep-alive' }
    });
    const test1Time = performance.now() - test1Start;
    console.log('[Network Test] ✅ 健康检查完成:', {
      耗时: `${test1Time.toFixed(2)}ms`,
      状态: response.status,
      OK: response.ok
    });
  } catch (error) {
    console.error('[Network Test] ❌ 健康检查失败:', error);
  }
  
  // 测试2: 第二次请求（测试连接复用）
  console.log('[Network Test] 测试2: 连接复用测试');
  const test2Start = performance.now();
  
  try {
    const response = await fetch(healthUrl, {
      method: 'GET',
      headers: { 'Connection': 'keep-alive' }
    });
    const test2Time = performance.now() - test2Start;
    console.log('[Network Test] ✅ 连接复用测试完成:', {
      耗时: `${test2Time.toFixed(2)}ms`,
      状态: response.status,
      改善: test2Time < 100 ? '良好' : '需要优化'
    });
  } catch (error) {
    console.error('[Network Test] ❌ 连接复用测试失败:', error);
  }
  
  console.log('[Network Test] 🏁 测试完成');
}
