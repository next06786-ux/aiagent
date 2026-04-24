import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useAICoreSession } from '../../hooks/useAICoreSession';
import { openChatSocket } from '../../services/chat';
import './AICoreModal.css';

interface AICoreModalProps {
  onClose: () => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
  navigation?: {
    prompt: string;
    routes: Array<{
      module: string;
      name: string;
      path: string;
      confidence: number;
      reason: string;
      description: string;
      view_mode?: string;
    }>;
    primary_route?: any;
  };
}

export function AICoreModal({ onClose }: AICoreModalProps) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [input, setInput] = useState('');
  const [hiddenNavigations, setHiddenNavigations] = useState<Set<number>>(new Set());
  
  // 使用共享会话管理
  const {
    sessionId,
    messages,
    isLoading,
    setIsLoading,
    addMessage,
    updateLastMessage,
    clearSession,
  } = useAICoreSession(user?.user_id);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const closeSocketRef = useRef<(() => void) | null>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 打开时聚焦输入框
  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  // ESC 关闭
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

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
    
    // 添加用户消息到共享会话
    addMessage({ role: 'user', content: userMessage });
    setIsLoading(true);

    // 添加一个空的助手消息用于流式更新
    addMessage({ role: 'assistant', content: '', thinking: '' });

    try {
      // 关闭之前的连接
      if (closeSocketRef.current) {
        closeSocketRef.current();
      }

      let currentThinking = '';
      let currentAnswer = '';
      let currentNavigation: any = null;

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
            updateLastMessage({
              content: currentAnswer,
              thinking: currentThinking,
              navigation: currentNavigation,
            });
          },
          onAnswer: (answer) => {
            currentAnswer = answer;
            updateLastMessage({
              content: currentAnswer,
              thinking: currentThinking,
              navigation: currentNavigation,
            });
          },
          onNavigation: (navData: any) => {
            // 处理导航建议
            currentNavigation = {
              prompt: navData.content,
              routes: navData.routes || [],
              primary_route: navData.primary_route,
            };
            updateLastMessage({
              content: currentAnswer,
              thinking: currentThinking,
              navigation: currentNavigation,
            });
          },
          onDone: () => {
            setIsLoading(false);
            closeSocketRef.current = null;
          },
          onError: (error) => {
            updateLastMessage({
              content: `抱歉，我遇到了一些问题：${error}`,
            });
            setIsLoading(false);
            closeSocketRef.current = null;
          },
        }
      );
    } catch (error) {
      updateLastMessage({
        content: '抱歉，我遇到了一些问题。请稍后再试。',
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

  // 处理"不跳转"按钮点击
  const handleNoNavigate = async (messageIndex: number, originalQuestion: string) => {
    console.log('[导航] 用户选择不跳转，原问题:', originalQuestion);
    
    // 隐藏导航建议
    setHiddenNavigations(prev => new Set(prev).add(messageIndex));
    
    // 发送新请求，让AI重新生成不带导航的回答
    console.log('[导航] 发送新请求让AI重新回答');
    setIsLoading(true);
    
    try {
      // 关闭之前的连接
      if (closeSocketRef.current) {
        console.log('[导航] 关闭之前的WebSocket连接');
        closeSocketRef.current();
      }

      let currentThinking = '';
      let currentAnswer = '';

      console.log('[导航] 发送特殊消息到后端');

      closeSocketRef.current = openChatSocket(
        {
          user_id: user!.user_id,
          session_id: sessionId!,
          message: `[用户选择不跳转] 请直接回答以下问题，不要建议跳转：${originalQuestion}`,
          context: null,
        },
        {
          onThinking: (thinking) => {
            console.log('[导航] 收到思考过程');
            currentThinking = thinking;
            updateLastMessage({
              content: currentAnswer,
              thinking: currentThinking,
              navigation: null,  // 清除导航状态
            });
          },
          onAnswer: (answer) => {
            console.log('[导航] 收到回答内容');
            currentAnswer = answer;
            updateLastMessage({
              content: currentAnswer,
              thinking: currentThinking,
              navigation: null,  // 清除导航状态
            });
          },
          onNavigation: (navData: any) => {
            // 忽略新的导航建议
            console.log('[导航] 收到导航建议，但忽略');
          },
          onDone: () => {
            console.log('[导航] WebSocket完成');
            setIsLoading(false);
            closeSocketRef.current = null;
          },
          onError: (error) => {
            console.log('[导航] WebSocket错误:', error);
            updateLastMessage({
              content: `抱歉，我遇到了一些问题：${error}`,
              navigation: null,  // 清除导航状态
            });
            setIsLoading(false);
            closeSocketRef.current = null;
          },
        }
      );
    } catch (error) {
      console.log('[导航] 异常:', error);
      updateLastMessage({
        content: '抱歉，我遇到了一些问题。请稍后再试。',
        navigation: null,  // 清除导航状态
      });
      setIsLoading(false);
    }
  };

  // 快捷功能按钮
  const quickActions = [
    { label: '决策推演', action: () => navigate('/decision') },
    { label: '知识星图', action: () => navigate('/knowledge-graph') },
    { label: '平行人生', action: () => navigate('/parallel-life') },
    { label: '涌现洞察', action: () => navigate('/emergence-dashboard') },
  ];

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

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* 清空会话按钮 */}
            {messages.length > 0 && (
              <button
                onClick={clearSession}
                className="ai-modal-action-btn"
                aria-label="清空会话"
                title="清空会话"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  <line x1="10" y1="11" x2="10" y2="17"/>
                  <line x1="14" y1="11" x2="14" y2="17"/>
                </svg>
              </button>
            )}
            
            {/* 关闭按钮 */}
            <button onClick={onClose} className="ai-modal-close-btn" aria-label="关闭">
              ×
            </button>
          </div>
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
            messages.map((msg, i) => {
              // 找到对应的用户问题（前一条消息）
              const userQuestion = i > 0 && messages[i - 1].role === 'user' 
                ? messages[i - 1].content 
                : '';
              
              return (
              <div key={i} className={`chat-message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}>
                {/* 头像 - 白色球体样式 */}
                <div className={`message-avatar-orb ${msg.role}-avatar-orb`}>
                  <div className="avatar-orb-pulse" />
                  <div className="avatar-orb-inner">
                    <span className="avatar-orb-text">{msg.role === 'user' ? 'U' : 'AI'}</span>
                  </div>
                </div>

                {/* 消息内容 */}
                <div className="message-content-wrapper">
                  {/* 导航建议 - 可以被隐藏 */}
                  {msg.navigation && !hiddenNavigations.has(i) && (
                    <div className="message-navigation">
                      <div className="navigation-prompt">{msg.navigation.prompt}</div>
                      {msg.navigation.routes && msg.navigation.routes.length > 0 && (
                        <div className="navigation-actions">
                          {msg.navigation.routes.map((route: any, idx: number) => (
                            <button
                              key={idx}
                              className={`navigation-btn ${idx === 0 ? 'primary' : ''}`}
                              onClick={() => {
                                if (route.view_mode) {
                                  navigate(route.path, { state: { view: route.view_mode } });
                                } else {
                                  navigate(route.path);
                                }
                                onClose();
                              }}
                            >
                              <span className="nav-btn-name">{route.name}</span>
                              <span className="nav-btn-desc">{route.description}</span>
                              {route.confidence && (
                                <span className="nav-btn-confidence">{Math.round(route.confidence * 100)}% 匹配</span>
                              )}
                            </button>
                          ))}
                          {/* 不跳转按钮 */}
                          <button
                            className="navigation-btn no-navigate-btn"
                            onClick={() => handleNoNavigate(i, userQuestion)}
                          >
                            <span className="nav-btn-name">❌ 不跳转</span>
                            <span className="nav-btn-desc">继续在这里对话</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* 思考过程 */}
                  {msg.thinking && (
                    <div className="message-thinking">
                      <span className="thinking-label">思考中：</span>{msg.thinking}
                    </div>
                  )}
                  
                  {/* 回答内容 - 只在没有导航或导航已隐藏时显示 */}
                  {(msg.content || (msg.role === 'assistant' && isLoading)) && 
                   (!msg.navigation || hiddenNavigations.has(i)) && (
                    <div className="message-bubble">
                      {msg.content || '...'}
                    </div>
                  )}
                </div>
              </div>
            );
            })
          )}

          {/* 加载气泡 - 只在真正加载中且最后一条消息还没有内容时显示 */}
          {isLoading && (() => {
            const lastMsg = messages[messages.length - 1];
            const hasContent = lastMsg && (lastMsg.thinking || lastMsg.content || lastMsg.navigation);
            return !hasContent;
          })() && (
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
              className="send-btn-orb"
            >
              <div className="send-orb-pulse" />
              <div className="send-orb-inner">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="19" x2="12" y2="5"/>
                  <polyline points="5 12 12 5 19 12"/>
                </svg>
              </div>
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
