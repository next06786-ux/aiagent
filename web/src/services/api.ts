const rawBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  'http://127.0.0.1:6006'; // 默认使用 127.0.0.1 而不是 localhost

export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

// 启动时诊断
console.log('[API] 配置信息:', {
  'VITE_API_BASE_URL': import.meta.env.VITE_API_BASE_URL,
  'API_BASE_URL': API_BASE_URL,
  '是否使用localhost': API_BASE_URL.includes('localhost'),
});
export const WS_BASE_URL = API_BASE_URL.replace(/^http:\/\//, 'ws://').replace(
  /^https:\/\//,
  'wss://',
);

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status = 500, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

function buildUrl(path: string) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const startTime = performance.now();
  const url = buildUrl(path);
  console.log('[API] 🚀 发起请求:', url, '时间:', startTime);
  
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'Connection': 'keep-alive',
      ...(init?.headers || {}),
    },
  });
  
  const fetchTime = performance.now() - startTime;
  console.log('[API] 📥 收到响应:', url, '耗时:', `${fetchTime.toFixed(2)}ms`, '状态:', response.status);

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text();
  
  const totalTime = performance.now() - startTime;
  console.log('[API] ✅ 解析完成:', url, '总耗时:', `${totalTime.toFixed(2)}ms`);

  if (!response.ok) {
    const message =
      typeof payload === 'object' && payload && 'message' in payload
        ? String((payload as { message?: unknown }).message || '请求失败')
        : `请求失败 (${response.status})`;
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export async function postJson<T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
) {
  return requestJson<T>(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
    ...init,
  });
}

export async function putJson<T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
) {
  return requestJson<T>(path, {
    method: 'PUT',
    body: body === undefined ? undefined : JSON.stringify(body),
    ...init,
  });
}

export function createSocket(path: string) {
  const wsPath = path.startsWith('/') ? path : `/${path}`;
  return new WebSocket(`${WS_BASE_URL}${wsPath}`);
}
