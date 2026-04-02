import { startTransition, useEffect, useRef, useState } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import {
  getConversationMessages,
  listConversations,
  openChatSocket,
} from '../services/chat';
import type { ChatMessage, ConversationItem } from '../types/api';

function makeId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function formatMessageTime(timestamp: string) {
  if (!timestamp) {
    return '';
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${String(
    date.getHours(),
  ).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

export function AIChatPage() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '这里是 Web 端 AI 对话。它继续连接同一套后端 /ws/chat，并保留实时 thinking 与 answer 增量输出。',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [streamStatus, setStreamStatus] = useState('');
  const [error, setError] = useState('');
  const socketCloseRef = useRef<(() => void) | null>(null);
  const threadRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }

    let active = true;
    listConversations(user.user_id)
      .then((items) => {
        if (active) {
          setConversations(items);
        }
      })
      .catch(() => {
        if (active) {
          setConversations([]);
        }
      });

    return () => {
      active = false;
    };
  }, [user]);

  useEffect(() => {
    return () => {
      socketCloseRef.current?.();
      socketCloseRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!threadRef.current) {
      return;
    }

    threadRef.current.scrollTo({
      top: threadRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages, streamStatus]);

  async function openConversation(sessionId: string) {
    if (!user?.user_id) {
      return;
    }

    socketCloseRef.current?.();
    socketCloseRef.current = null;
    setIsSending(false);
    setError('');

    try {
      const rows = await getConversationMessages(user.user_id, sessionId);
      setCurrentSessionId(sessionId);
      setMessages(
        rows.length > 0
          ? rows.map((row) => ({
              id: row.id,
              role: row.role,
              content: row.content,
              thinking: row.thinking,
              timestamp: row.timestamp,
            }))
          : [
              {
                id: 'empty',
                role: 'assistant',
                content: '当前会话还没有消息。',
                timestamp: new Date().toISOString(),
              },
            ],
      );
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '加载会话失败');
    }
  }

  async function refreshConversations() {
    if (!user?.user_id) {
      return;
    }
    const items = await listConversations(user.user_id);
    setConversations(items);
  }

  async function handleSend() {
    if (!user?.user_id || !input.trim() || isSending) {
      return;
    }

    socketCloseRef.current?.();
    setError('');

    const prompt = input.trim();
    const now = new Date().toISOString();
    const userMessage: ChatMessage = {
      id: makeId('user'),
      role: 'user',
      content: prompt,
      timestamp: now,
    };
    const assistantId = makeId('assistant');

    setInput('');
    setIsSending(true);
    setStreamStatus('正在连接智能体...');
    setMessages((current) => [
      ...current,
      userMessage,
      {
        id: assistantId,
        role: 'assistant',
        content: '',
        thinking: '',
        timestamp: new Date().toISOString(),
      },
    ]);

    socketCloseRef.current = openChatSocket(
      {
        user_id: user.user_id,
        message: prompt,
        context: null,
        session_id: currentSessionId || undefined,
      },
      {
        onStart: (sessionId) => {
          if (sessionId) {
            setCurrentSessionId(sessionId);
          }
        },
        onProgress: (progress) => {
          setStreamStatus(progress);
        },
        onThinking: (thinking) => {
          startTransition(() => {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId ? { ...message, thinking } : message,
              ),
            );
          });
        },
        onAnswer: (answer) => {
          startTransition(() => {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId ? { ...message, content: answer } : message,
              ),
            );
          });
        },
        onDone: () => {
          setIsSending(false);
          setStreamStatus('');
          socketCloseRef.current = null;
          void refreshConversations();
        },
        onError: (message) => {
          setIsSending(false);
          setStreamStatus('');
          socketCloseRef.current = null;
          setError(message);
        },
      },
    );
  }

  function startFreshConversation() {
    socketCloseRef.current?.();
    socketCloseRef.current = null;
    setCurrentSessionId('');
    setError('');
    setStreamStatus('');
    setIsSending(false);
    setMessages([
      {
        id: 'welcome_new',
        role: 'assistant',
        content: '新会话已就绪。你可以继续自由聊天，或者把当前问题引导到决策副本。',
        timestamp: new Date().toISOString(),
      },
    ]);
  }

  return (
    <AppShell
      title="AI 对话"
      subtitle="保留 Harmony 端的实时输出体验，并继续使用同一后端 /ws/chat。"
      actions={
        <button className="button button-primary" onClick={startFreshConversation}>
          新对话
        </button>
      }
    >
      <div className="chat-layout">
        <GlassCard title="会话历史" subtitle="来自 V4 conversations 接口" className="chat-sidebar">
          <div className="chat-history-list">
            {conversations.length === 0 ? (
              <p className="empty-copy">还没有历史会话。</p>
            ) : (
              conversations.map((item) => (
                <button
                  key={item.id}
                  className={`history-item${currentSessionId === item.id ? ' is-active' : ''}`}
                  onClick={() => void openConversation(item.id)}
                >
                  <strong>{item.title || '未命名会话'}</strong>
                  <span>{item.preview || '暂无预览'}</span>
                  <small>{item.last_message_time || ''}</small>
                </button>
              ))
            )}
          </div>
        </GlassCard>

        <div className="chat-main">
          <GlassCard
            title="实时对话"
            subtitle={
              currentSessionId
                ? `当前会话: ${currentSessionId}`
                : '发送第一条消息后会自动生成 session_id'
            }
            action={streamStatus ? <span className="stream-status">{streamStatus}</span> : null}
          >
            <div className="chat-thread" ref={threadRef}>
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`chat-bubble ${
                    message.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'
                  }`}
                >
                  <div className="chat-bubble-meta">
                    <strong>{message.role === 'user' ? '你' : 'AI'}</strong>
                    <span>{formatMessageTime(message.timestamp)}</span>
                  </div>

                  {message.thinking ? (
                    <details className="thinking-block">
                      <summary>查看推理过程</summary>
                      <pre>{message.thinking}</pre>
                    </details>
                  ) : null}

                  <div className="chat-bubble-content">
                    {message.content || (message.role === 'assistant' && isSending ? '...' : '')}
                  </div>
                </article>
              ))}
            </div>
          </GlassCard>

          <GlassCard title="输入区" subtitle="聊天内容会继续沉淀到同一后端记忆与历史">
            <div className="chat-composer">
              <textarea
                className="textarea"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="输入想聊的问题，或者让它帮你分析当下的处境..."
                rows={5}
              />
              {error ? <div className="form-error">{error}</div> : null}
              <div className="composer-actions">
                <button className="button button-ghost" onClick={startFreshConversation}>
                  清空当前会话
                </button>
                <button
                  className="button button-primary"
                  onClick={() => void handleSend()}
                  disabled={isSending || !input.trim()}
                >
                  {isSending ? '发送中...' : '发送'}
                </button>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
}
