import { useState, useRef, useEffect } from 'react';
import { API_BASE_URL } from '../services/api';
import '../styles/AgentChatDialog.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  retrievalStats?: {
    rag_results: number;
    neo4j_results: number;
    total_results: number;
  };
}

interface AgentChatDialogProps {
  agentType: 'relationship' | 'education' | 'career';
  agentName: string;
  agentColor: string;
  token: string;
  onClose: () => void;
}

export function AgentChatDialog({ agentType, agentName, agentColor, token, onClose }: AgentChatDialogProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: getWelcomeMessage(agentType),
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 自动聚焦输入框
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // 发送消息
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          agent_type: agentType,
          message: userMessage.content,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      });

      if (!response.ok) {
        throw new Error('对话请求失败');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        retrievalStats: data.retrieval_stats
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Agent对话失败:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，我现在遇到了一些问题。请稍后再试。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 快捷问题
  const quickQuestions = getQuickQuestions(agentType);

  const handleQuickQuestion = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  // 处理回车发送
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="agent-chat-overlay" onClick={onClose}>
      <div className="agent-chat-dialog" onClick={e => e.stopPropagation()}>
        {/* 头部 */}
        <div className="agent-chat-header" style={{ background: agentColor }}>
          <div className="agent-chat-header-info">
            <h3 className="agent-chat-title">{agentName}</h3>
            <p className="agent-chat-subtitle">专业领域对话</p>
          </div>
          <button className="agent-chat-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 快捷问题 */}
        {messages.length === 1 && (
          <div className="agent-chat-quick-questions">
            <p className="quick-questions-title">你可以问我：</p>
            <div className="quick-questions-grid">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  className="quick-question-btn"
                  onClick={() => handleQuickQuestion(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 消息列表 */}
        <div className="agent-chat-messages">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`agent-chat-message ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : getAgentIcon(agentType)}
              </div>
              <div className="message-content">
                <div className="message-text">{msg.content}</div>
                {msg.role === 'assistant' && msg.retrievalStats && msg.retrievalStats.total_results > 0 && (
                  <div className="message-retrieval-stats">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <path d="M12 6v6l4 2" />
                    </svg>
                    检索了 {msg.retrievalStats.total_results} 条信息
                    （RAG: {msg.retrievalStats.rag_results}, 知识图谱: {msg.retrievalStats.neo4j_results}）
                  </div>
                )}
                <div className="message-time">
                  {msg.timestamp.toLocaleTimeString('zh-CN', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="agent-chat-message assistant">
              <div className="message-avatar">{getAgentIcon(agentType)}</div>
              <div className="message-content">
                <div className="message-loading">
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                  <span className="loading-dot"></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区 */}
        <div className="agent-chat-input-area">
          <textarea
            ref={inputRef}
            className="agent-chat-input"
            placeholder={`向${agentName}提问...`}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
          />
          <button
            className="agent-chat-send"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            style={{ background: agentColor }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

// 获取欢迎消息
function getWelcomeMessage(agentType: string): string {
  const messages = {
    relationship: '你好！我是人际关系Agent。我可以帮你分析社交网络、人际关系质量、沟通模式等问题。有什么想了解的吗？',
    education: '你好！我是教育升学Agent。我可以帮你规划升学路径、分析学校选择、专业匹配等问题。有什么想咨询的吗？',
    career: '你好！我是职业规划Agent。我可以帮你分析职业发展、技能匹配、岗位选择等问题。有什么想讨论的吗？'
  };
  return messages[agentType as keyof typeof messages] || '你好！有什么可以帮你的吗？';
}

// 获取Agent图标
function getAgentIcon(agentType: string): string {
  const icons = {
    relationship: '👥',
    education: '🎓',
    career: '💼'
  };
  return icons[agentType as keyof typeof icons] || '🤖';
}

// 获取快捷问题
function getQuickQuestions(agentType: string): string[] {
  const questions = {
    relationship: [
      '我的社交网络健康吗？',
      '如何改善人际关系？',
      '我应该如何扩展社交圈？',
      '如何处理人际冲突？'
    ],
    education: [
      '我适合考研还是就业？',
      '如何选择专业方向？',
      '我的学习路径合理吗？',
      '如何提升学业竞争力？'
    ],
    career: [
      '我适合什么职业方向？',
      '如何规划职业发展？',
      '我需要提升哪些技能？',
      '如何选择工作机会？'
    ]
  };
  return questions[agentType as keyof typeof questions] || [];
}
