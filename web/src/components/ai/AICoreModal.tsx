import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { createConversation, openChatSocket } from '../../services/chat';
import './AICoreModal.css';

interface AICoreModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AICoreModal({ isOpen, onClose }: AICoreModalProps) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; thinking?: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const closeSocketRef = useRef<(() => void) | null>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 打开时聚焦输入框并创建会话
  useEffect(() => {
    if (isOpen && user?.user_id) {
      setTimeout(() => inputRef.current?.focus(), 100);
      
      // 如果没有会话ID,创建一个新会话
      if (!sessionId) {
        createConversation(user.user_id)
          .then(id => setSessionId(id))
          .catch(err => console.error('创建会话失败:', err));
      }
    }
  }, [isOpen, user, sessionId]);

  // ESC 关闭
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  // 清理WebSocket连接
  useEffect(() => {
    return () => {
      if (closeSocketRef.current) {
        closeSocketRef.current();
        closeSocketRef.current = null;
      }
    };
  }, []);

  const handleSend = async () => {
    if (!input.trim() || !user?.user_id || isLoading || !sessionId) return;

    const userMessage = input.trim();
    setInput('');
    
    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    // 添加一个空的助手消息用于流式更新
    const assistantMsgIndex = messages.length + 1;
    setMessages(prev => [...prev, { role: 'assistant', content: '', thinking: '' }]);

    try {
      // 关闭之前的连接
      if (closeSocketRef.current) {
        closeSocketRef.current();
      }

      let currentThinking = '';
      let currentAnswer = '';

      closeSocketRef.current = openChatSocket(
        {
          user_id: user.user_id,
          session_id: sessionId,
          message: userMessage,
          context: null,
        },
        {
          onThinking: (thinking) => {
            currentThinking = thinking;
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[assistantMsgIndex] = {
                role: 'assistant',
                content: currentAnswer,
                thinking: currentThinking,
              };
              return newMessages;
            });
          },
          onAnswer: (answer) => {
            currentAnswer = answer;
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[assistantMsgIndex] = {
                role: 'assistant',
                content: currentAnswer,
                thinking: currentThinking,
              };
              return newMessages;
            });
          },
          onDone: () => {
            setIsLoading(false);
            closeSocketRef.current = null;
          },
          onError: (error) => {
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[assistantMsgIndex] = {
                role: 'assistant',
                content: `抱歉，我遇到了一些问题：${error}`,
              };
              return newMessages;
            });
            setIsLoading(false);
            closeSocketRef.current = null;
          },
        }
      );
    } catch (error) {
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[assistantMsgIndex] = {
          role: 'assistant',
          content: '抱歉，我遇到了一些问题。请稍后再试。',
        };
        return newMessages;
      });
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 快捷功能按钮
  const quickActions = [
    { label: '决策推演', action: () => navigate('/decision') },
    { label: '知识星图', action: () => navigate('/knowledge-graph') },
    { label: '平行人生', action: () => navigate('/parallel-life') },
    { label: '涌现洞察', action: () => navigate('/emergence-dashboard') },
  ];

  if (!isOpen) return null;

  return (
    <>
      {/* HarmonyOS 6 - 纯净遮罩层 */}
      <div className="ai-modal-backdrop" onClick={onClose} />

      {/* HarmonyOS 6 - 悬浮窗主体 */}
      <div className="ai-modal-container">
        {/* 顶部栏 */}
        <div className="ai-modal-header">
          <div className="ai-modal-header-content">
            {/* AI 核心图标 */}
            <div className="ai-core-icon">
              <div className="ai-core-icon-pulse" />
              <div className="ai-core-icon-inner">
                <span className="ai-core-icon-text">AI</span>
              </div>
            </div>
            <div className="ai-modal-title-group">
              <div className="ai-modal-title">AI 核心</div>
              <div className="ai-modal-subtitle">Central Intelligence Engine</div>
            </div>
          </div>

          {/* 关闭按钮 */}
          <button onClick={onClose} className="ai-modal-close-btn" aria-label="关闭">
            ×
          </button>
        </div>

        {/* 快捷功能栏 */}
        <div className="ai-modal-quick-actions">
          {quickActions.map((action, i) => (
            <button
              key={i}
              onClick={() => {
                action.action();
                onClose();
              }}
              className="quick-action-btn"
            >
              <span className="quick-action-label">{action.label}</span>
            </button>
          ))}
        </div>

        {/* 消息区域 */}
        <div className="ai-modal-messages">
          {messages.length === 0 ? (
            <div className="ai-modal-empty">
              <div className="empty-icon">
                <div className="empty-icon-circle">
                  <span>AI</span>
                </div>
              </div>
              <div className="empty-title">你好！我是 AI 核心</div>
              <div className="empty-desc">
                我可以帮你进行决策推演、查看知识星图、分析涌现模式，或者回答任何问题。
                <br />
                试试问我一些问题吧！
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}>
                {/* 头像 */}
                <div className={`message-avatar ${msg.role}-avatar`}>
                  <span className="avatar-text">{msg.role === 'user' ? 'U' : 'AI'}</span>
                </div>

                {/* 消息内容 */}
                <div className="message-content-wrapper">
                  {/* 思考过程 */}
                  {msg.thinking && (
                    <div className="message-thinking">
                      <span className="thinking-label">思考中：</span>{msg.thinking}
                    </div>
                  )}
                  
                  {/* 回答内容 */}
                  <div className="message-bubble">
                    {msg.content || (msg.role === 'assistant' && isLoading ? '...' : '')}
                  </div>
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="chat-message assistant-message">
              <div className="message-avatar assistant-avatar">
                <span className="avatar-text">AI</span>
              </div>
              <div className="message-bubble loading-bubble">
                <span className="typing-indicator">思考中</span>
                <span className="dot-1">.</span>
                <span className="dot-2">.</span>
                <span className="dot-3">.</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="ai-modal-input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
              className="message-input"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="send-btn"
            >
              ↑
            </button>
          </div>
          <div className="input-hint">
            AI 核心可以帮你导航到任何功能模块，或回答你的问题
          </div>
        </div>
      </div>
    </>
  );
}
