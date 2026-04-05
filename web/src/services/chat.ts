import type {
  ChatSocketRequest,
  ConversationItem,
  ConversationMessageData,
  SuccessEnvelope,
} from '../types/api';
import { ApiError, createSocket, postJson, requestJson } from './api';

export async function listConversations(userId: string) {
  const result = await requestJson<SuccessEnvelope<ConversationItem[]>>(
    `/api/v4/conversations/${encodeURIComponent(userId)}/list`,
  );

  if (!result.success) {
    return [];
  }

  return result.data || [];
}

export async function getConversationMessages(
  userId: string,
  sessionId: string,
) {
  const result = await requestJson<SuccessEnvelope<ConversationMessageData[]>>(
    `/api/v4/conversations/${encodeURIComponent(
      userId,
    )}/${encodeURIComponent(sessionId)}/messages`,
  );

  if (!result.success) {
    return [];
  }

  return result.data || [];
}

export async function createConversation(userId: string) {
  const result = await postJson<
    SuccessEnvelope<{ conversation_id: string }>
  >(`/api/v4/conversations/${encodeURIComponent(userId)}/create`);

  if (!result.success || !result.data?.conversation_id) {
    throw new ApiError(result.message || '创建会话失败');
  }

  return result.data.conversation_id;
}

interface ChatSocketHandlers {
  onStart?: (sessionId: string) => void;
  onProgress?: (progress: string) => void;
  onThinking?: (thinking: string) => void;
  onAnswer?: (answer: string) => void;
  onNavigation?: (navData: any) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
}

export function openChatSocket(
  payload: ChatSocketRequest,
  handlers: ChatSocketHandlers,
) {
  const socket = createSocket('/ws/chat');
  let thinking = '';
  let answer = '';

  socket.addEventListener('open', () => {
    socket.send(JSON.stringify(payload));
  });

  socket.addEventListener('message', (event) => {
    try {
      const parsed = JSON.parse(String(event.data)) as Record<string, unknown>;
      const type = String(parsed.type || '');
      const content = String(parsed.content || '');

      switch (type) {
        case 'start':
          handlers.onStart?.(String(parsed.session_id || ''));
          break;
        case 'progress':
          handlers.onProgress?.(content);
          break;
        case 'thinking_chunk':
          thinking += content;
          handlers.onThinking?.(thinking);
          break;
        case 'thinking':
          thinking = content;
          handlers.onThinking?.(thinking);
          break;
        case 'answer_chunk':
          answer += content;
          handlers.onAnswer?.(answer);
          break;
        case 'answer':
          answer = content;
          handlers.onAnswer?.(answer);
          break;
        case 'navigation':
          // 处理导航建议
          handlers.onNavigation?.(parsed);
          break;
        case 'done':
          handlers.onDone?.();
          socket.close();
          break;
        case 'error':
          handlers.onError?.(content || '聊天流式连接出错');
          socket.close();
          break;
        default:
          break;
      }
    } catch (error) {
      handlers.onError?.(
        error instanceof Error ? error.message : '解析聊天事件失败',
      );
    }
  });

  socket.addEventListener('error', () => {
    handlers.onError?.('聊天连接异常，请稍后重试');
  });

  return () => {
    if (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    ) {
      socket.close();
    }
  };
}
