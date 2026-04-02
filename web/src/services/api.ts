const rawBaseUrl =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  'https://u821458-a197-3cecd37e.westc.seetacloud.com:8443';

export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');
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
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  });

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

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
