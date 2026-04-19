/**
 * AI核心会话管理Hook
 * 
 * 功能：
 * - 管理全局唯一的AI核心会话
 * - 在页面和悬浮窗之间同步对话历史
 * - 持久化会话ID到localStorage
 */
import { useState, useEffect, useCallback } from 'react';
import { createConversation } from '../services/chat';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
  navigation?: any;
}

const AI_CORE_SESSION_KEY = 'ai_core_session_id';
const AI_CORE_MESSAGES_KEY = 'ai_core_messages';

// 全局状态（在内存中共享）
let globalSessionId: string | null = null;
let globalMessages: Message[] = [];
let listeners: Set<(messages: Message[]) => void> = new Set();

export function useAICoreSession(userId: string | undefined) {
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 初始化会话
  useEffect(() => {
    if (!userId) return;

    const initSession = async () => {
      // 1. 尝试从localStorage恢复会话ID
      const savedSessionId = localStorage.getItem(AI_CORE_SESSION_KEY);

      if (savedSessionId) {
        try {
          // 从后端加载历史消息
          console.log('[AI核心] 从后端加载会话:', savedSessionId);
          const { getConversationMessages } = await import('../services/chat');
          const loadedMessages = await getConversationMessages(userId, savedSessionId);
          
          if (loadedMessages && loadedMessages.length > 0) {
            // 转换后端消息格式到前端格式
            const formattedMessages = loadedMessages.map((msg: any) => ({
              role: msg.role as 'user' | 'assistant',
              content: msg.content || '',
              thinking: msg.thinking,
            }));
            
            globalSessionId = savedSessionId;
            globalMessages = formattedMessages;
            setSessionId(savedSessionId);
            setMessages(formattedMessages);
            
            // 更新localStorage
            localStorage.setItem(AI_CORE_MESSAGES_KEY, JSON.stringify(formattedMessages));
            
            console.log('[AI核心] 成功加载历史消息:', formattedMessages.length, '条');
            return;
          } else {
            console.log('[AI核心] 会话无历史消息，使用现有会话ID');
            globalSessionId = savedSessionId;
            globalMessages = [];
            setSessionId(savedSessionId);
            setMessages([]);
            localStorage.setItem(AI_CORE_MESSAGES_KEY, JSON.stringify([]));
            return;
          }
        } catch (e) {
          console.error('[AI核心] 加载历史消息失败:', e);
          // 加载失败，清除旧会话ID，创建新会话
          localStorage.removeItem(AI_CORE_SESSION_KEY);
          localStorage.removeItem(AI_CORE_MESSAGES_KEY);
        }
      }

      // 2. 创建新会话
      try {
        console.log('[AI核心] 创建新会话');
        const newSessionId = await createConversation(userId);
        globalSessionId = newSessionId;
        globalMessages = [];
        setSessionId(newSessionId);
        setMessages([]);
        localStorage.setItem(AI_CORE_SESSION_KEY, newSessionId);
        localStorage.setItem(AI_CORE_MESSAGES_KEY, JSON.stringify([]));
        console.log('[AI核心] 创建新会话成功:', newSessionId);
      } catch (err) {
        console.error('[AI核心] 创建会话失败:', err);
      }
    };

    initSession();
  }, [userId]);

  // 订阅全局消息变化
  useEffect(() => {
    const listener = (newMessages: Message[]) => {
      setMessages([...newMessages]);
    };
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  // 添加消息
  const addMessage = useCallback((message: Message) => {
    globalMessages = [...globalMessages, message];
    
    // 通知所有监听者
    listeners.forEach(listener => listener(globalMessages));
    
    // 持久化到localStorage
    localStorage.setItem(AI_CORE_MESSAGES_KEY, JSON.stringify(globalMessages));
  }, []);

  // 更新最后一条消息
  const updateLastMessage = useCallback((updates: Partial<Message>) => {
    if (globalMessages.length === 0) return;
    
    globalMessages = [
      ...globalMessages.slice(0, -1),
      { ...globalMessages[globalMessages.length - 1], ...updates }
    ];
    
    // 通知所有监听者
    listeners.forEach(listener => listener(globalMessages));
    
    // 持久化到localStorage
    localStorage.setItem(AI_CORE_MESSAGES_KEY, JSON.stringify(globalMessages));
  }, []);

  // 清空会话
  const clearSession = useCallback(async () => {
    if (!userId) return;

    try {
      const newSessionId = await createConversation(userId);
      globalSessionId = newSessionId;
      globalMessages = [];
      
      setSessionId(newSessionId);
      setMessages([]);
      
      localStorage.setItem(AI_CORE_SESSION_KEY, newSessionId);
      localStorage.setItem(AI_CORE_MESSAGES_KEY, JSON.stringify([]));
      
      // 通知所有监听者
      listeners.forEach(listener => listener([]));
      
      console.log('[AI核心] 清空会话，创建新会话:', newSessionId);
    } catch (err) {
      console.error('[AI核心] 清空会话失败:', err);
    }
  }, [userId]);

  return {
    sessionId,
    messages,
    isLoading,
    setIsLoading,
    addMessage,
    updateLastMessage,
    clearSession,
  };
}
