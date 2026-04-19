import { startTransition, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import {
  getConversationMessages,
  listConversations,
  openChatSocket,
} from '../services/chat';
import { routeFutureOsMessage } from '../services/futureOs';
import type { ChatMessage, ConversationItem, FutureOsRouteSuggestion } from '../types/api';

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

function suggestionTitle(value?: FutureOsRouteSuggestion | null) {
  if (!value) {
    return 'AI 核心会根据当前消息判断下一步最适合进入的模块。';
  }
  if (value.recommended_module === 'knowledge_graph') {
    return '这条消息更适合先看知识星图。';
  }
  if (value.recommended_module === 'decision_graph') {
    return '这条消息已经足够进入决策图谱舞台。';
  }
  if (value.recommended_module === 'parallel_life') {
    return '这条消息适合转成情境体验，进入平行人生。';
  }
  return '这条消息还适合继续在 AI 核心对话中补全信息。';
}

export function AIChatPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '我是 AI 核心入口。你可以先自由聊天，我会在合适的时候把问题导向知识星图、决策图谱舞台或平行人生。',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState('');
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [streamStatus, setStreamStatus] = useState('');
  const [error, setError] = useState('');
  const [routeSuggestion, setRouteSuggestion] = useState<FutureOsRouteSuggestion | null>(
    null,
  );
  const [isRouting, setIsRouting] = useState(false);
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
  }, [messages, streamStatus, routeSuggestion]);

  async function refreshConversations() {
    if (!user?.user_id) {
      return;
    }
    const items = await listConversations(user.user_id);
    setConversations(items);
  }

  async function analyzeRoute(message: string) {
    if (!user?.user_id || !message.trim()) {
      return;
    }

    setIsRouting(true);
    try {
      const nextSuggestion = await routeFutureOsMessage({
        user_id: user.user_id,
        message: message.trim(),
      });
      setRouteSuggestion(nextSuggestion);
    } catch {
      setRouteSuggestion(null);
    } finally {
      setIsRouting(false);
    }
  }

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

      const lastUserMessage = [...rows].reverse().find((item) => item.role === 'user');
      if (lastUserMessage?.content) {
        void analyzeRoute(lastUserMessage.content);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '加载会话失败');
    }
  }

  async function handleSend() {
    if (!user?.user_id || !input.trim() || isSending) {
      return;
    }

    socketCloseRef.current?.();
    setError('');

    const prompt = input.trim();
    const userMessage: ChatMessage = {
      id: makeId('user'),
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    };
    const assistantId = makeId('assistant');

    setInput('');
    setIsSending(true);
    setStreamStatus('正在连接 AI 核心...');
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

    void analyzeRoute(prompt);

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
    setRouteSuggestion(null);
    setMessages([
      {
        id: 'welcome_new',
        role: 'assistant',
        content:
          '新对话已准备好。你可以先自由表达，我会帮你判断什么时候切到图谱或平行人生。',
        timestamp: new Date().toISOString(),
      },
    ]);
  }

  function openSuggestedModule() {
    if (!routeSuggestion) {
      return;
    }

    if (routeSuggestion.recommended_module === 'knowledge_graph') {
      navigate('/knowledge-graph', {
        state: {
          question: input.trim() || messages[messages.length - 1]?.content || '',
          view: routeSuggestion.recommended_view,
        },
      });
      return;
    }

    if (routeSuggestion.recommended_module === 'parallel_life') {
      navigate('/parallel-life');
      return;
    }

    if (routeSuggestion.recommended_module === 'decision_graph') {
      navigate('/decision');
    }
  }

  return (
    <AppShell
      actions={
        <button className="button button-primary" onClick={startFreshConversation}>
          新对话
        </button>
      }
    >
      <div className="chat-layout">
        <GlassCard title="会话历史" subtitle="保留与后端聊天主链一致的历史记录。">
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
            title="AI 核心路由"
            subtitle={isRouting ? '正在分析当前消息该进入哪个模块...' : '根据最近一条用户消息进行建议'}
          >
            <div className="future-route-card">
              <div>
                <p className="eyebrow">Routing</p>
                <h3>{suggestionTitle(routeSuggestion)}</h3>
                <p>{routeSuggestion?.reason || '发送消息或点击历史会话后，这里会出现建议。'}</p>
              </div>
              {routeSuggestion &&
              routeSuggestion.recommended_module !== 'chat' ? (
                <button className="button button-ghost" onClick={openSuggestedModule}>
                  前往建议模块
                </button>
              ) : null}
            </div>
          </GlassCard>

          <GlassCard
            title="实时对话"
            subtitle={
              currentSessionId
                ? `当前会话: ${currentSessionId}`
                : '发送第一条消息后会自动生成会话'
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
                    <strong>{message.role === 'user' ? '你' : 'AI Core'}</strong>
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

          <GlassCard
            title="输入区"
            subtitle="你可以直接询问关系影响、决策选择，或让 AI 核心帮你判断先看哪里。"
          >
            <div className="chat-composer">
              <textarea
                className="textarea"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="例如：谁正在影响我该不该离开现在的环境？"
                rows={5}
              />
              {error ? <div className="form-error">{error}</div> : null}
              <div className="composer-actions">
                <button
                  className="button button-secondary"
                  onClick={() => void analyzeRoute(input)}
                  disabled={!input.trim() || isRouting}
                >
                  {isRouting ? '分析中...' : '先做模块判断'}
                </button>
                <button
                  className="button button-primary"
                  onClick={() => void handleSend()}
                  disabled={isSending || !input.trim()}
                >
                  发送给 AI 核心
                </button>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
}
