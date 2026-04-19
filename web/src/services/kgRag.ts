/**
 * 知识图谱感知RAG服务
 * 将知识图谱融入AI对话和检索
 */
import { postJson, requestJson } from './api';
import type {
  KGRAGContextRequest,
  KGRAGContextResponse,
  KGRAGChatRequest,
  KGRAGChatResponse,
  KGRAGEnhanceRequest,
  KGRAGEnhanceResponse,
} from '../types/api';

/**
 * 查询知识图谱上下文
 * 用于获取与查询相关的图谱节点和关系
 */
export async function queryKGContext(
  request: KGRAGContextRequest
): Promise<KGRAGContextResponse> {
  const result = await postJson<KGRAGContextResponse>(
    '/api/kg-rag/query',
    request
  );
  return result;
}

/**
 * 知识图谱增强对话
 * 结合知识图谱上下文进行对话
 */
export async function kgEnhancedChat(
  request: KGRAGChatRequest
): Promise<KGRAGChatResponse> {
  const result = await postJson<KGRAGChatResponse>(
    '/api/kg-rag/chat',
    request
  );
  return result;
}

/**
 * 增强现有对话
 * 将知识图谱上下文注入对话历史
 */
export async function enhanceChat(
  request: KGRAGEnhanceRequest
): Promise<KGRAGEnhanceResponse> {
  const result = await postJson<KGRAGEnhanceResponse>(
    '/api/kg-rag/enhance',
    request
  );
  return result;
}

/**
 * 获取知识图谱RAG统计信息
 */
export async function getKGRAGStats(userId: string): Promise<{
  success: boolean;
  data?: {
    user_id: string;
    vector_search: {
      enabled: boolean;
      vector_rag: boolean | null;
    };
    graph_reasoning: {
      enabled: boolean;
    };
    vector_rag_stats?: Record<string, unknown>;
  };
  message?: string;
}> {
  const result = await requestJson<{
    success: boolean;
    data?: Record<string, unknown>;
    message?: string;
  }>(`/api/kg-rag/stats/${encodeURIComponent(userId)}`);
  return result as any;
}

/**
 * 健康检查
 */
export async function checkKGRAgHealth(): Promise<{
  status: string;
  service: string;
}> {
  const result = await requestJson<{ status: string; service: string }>(
    '/api/kg-rag/health'
  );
  return result;
}

/**
 * 流式知识图谱增强对话
 */
export function* kgEnhancedChatStream(request: KGRAGChatRequest): Generator<{
  type: 'context' | 'answer' | 'done' | 'error';
  data: Record<string, unknown>;
}, void, unknown> {
  // 注意：这个API返回SSE流，前端需要使用EventSource或fetch流式处理
  // 这里提供接口定义，实际使用时需要配合流式处理逻辑
  return null as any;
}
