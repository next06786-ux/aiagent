/**
 * LLM 提供者管理服务
 * 支持在 API 大模型和基座模型之间切换
 */

// 使用相对路径，由nginx代理到后端
const API_BASE_URL = '';

export interface LLMProvider {
  name: string;
  available: boolean;
  description: string;
  status: string;
  url?: string;
}

export interface LLMStatus {
  current_provider: string;
  available_providers: Record<string, LLMProvider>;
  remote_model_url: string | null;
}

export interface SwitchRequest {
  provider: string;
  remote_url?: string;
}

export interface SwitchResponse {
  success: boolean;
  provider: string;
  message: string;
  test_response?: string;
}

export interface TestResponse {
  success: boolean;
  provider: string;
  response?: string;
  error?: string;
}

/**
 * 获取 LLM 状态
 */
export async function getLLMStatus(): Promise<LLMStatus> {
  const response = await fetch(`${API_BASE_URL}/api/llm/status`);
  
  if (!response.ok) {
    throw new Error(`获取 LLM 状态失败: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * 切换 LLM 提供者
 */
export async function switchLLMProvider(request: SwitchRequest): Promise<SwitchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/llm/switch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `切换失败: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * 测试 LLM 提供者（不切换）
 */
export async function testLLMProvider(request: SwitchRequest): Promise<TestResponse> {
  const response = await fetch(`${API_BASE_URL}/api/llm/test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `测试失败: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * 获取提供者的显示名称
 */
export function getProviderDisplayName(provider: string): string {
  const names: Record<string, string> = {
    qwen: '通义千问 API',
    remote_model: '远程基座模型',
    local_quantized: '本地量化模型',
    openai: 'OpenAI API',
  };
  return names[provider] || provider;
}

/**
 * 获取提供者的图标
 */
export function getProviderIcon(provider: string): string {
  const icons: Record<string, string> = {
    qwen: '☁️',
    remote_model: '🖥️',
    local_quantized: '💻',
    openai: '🤖',
  };
  return icons[provider] || '🔧';
}
