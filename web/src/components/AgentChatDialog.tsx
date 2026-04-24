import { useState, useRef, useEffect } from 'react';
import { API_BASE_URL } from '../services/api';
import { AgentConversationHistory } from './AgentConversationHistory';
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
  toolCalls?: Array<{
    tool_name: string;
    server_name: string;
    status: 'running' | 'completed' | 'failed';
    result?: string;
  }>;
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
  const [showHistory, setShowHistory] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [currentToolCalls, setCurrentToolCalls] = useState<Array<{
    tool_name: string;
    server_name: string;
    status: 'running' | 'completed' | 'failed';
    result?: string;
  }>>([]);
  const [, forceUpdate] = useState({});  // 用于强制重新渲染

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 自动聚焦输入框
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // 清理WebSocket连接
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  // 发送消息（使用WebSocket）
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
    setCurrentToolCalls([]); // 清空当前工具调用

    try {
      // 创建WebSocket连接
      const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/agent-chat';
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // 连接打开
      ws.onopen = () => {
        console.log('[WebSocket] 连接已建立');
        
        // 发送消息
        ws.send(JSON.stringify({
          token: token,
          agent_type: agentType,
          message: userMessage.content,
          conversation_id: conversationId,
          conversation_history: messages.slice(1).map(m => ({
            role: m.role,
            content: m.content
          }))
        }));
      };

      // 接收消息
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] 收到消息:', data);

        switch (data.type) {
          case 'connected':
            console.log('[WebSocket] 会话ID:', data.session_id);
            break;

          case 'tool_start':
            console.log('[WebSocket] 工具开始:', data.tool_name);
            // 使用函数式更新，不依赖闭包中的currentToolCalls
            setCurrentToolCalls(prev => {
              console.log('[WebSocket] tool_start - 当前状态:', prev);
              const newCalls = [...prev, {
                tool_name: data.tool_name,
                server_name: data.server_name,
                status: 'running' as const
              }];
              console.log('[WebSocket] tool_start - 更新后:', newCalls);
              return newCalls;
            });
            // 强制重新渲染
            forceUpdate({});
            break;

          case 'tool_complete':
            console.log('[WebSocket] 工具完成:', data.tool_name);
            // 使用函数式更新
            setCurrentToolCalls(prev => {
              console.log('[WebSocket] tool_complete - 当前状态:', prev);
              const updated = prev.map(tool => 
                tool.tool_name === data.tool_name && tool.status === 'running'
                  ? { ...tool, status: 'completed' as const, result: data.result }
                  : tool
              );
              console.log('[WebSocket] tool_complete - 更新后:', updated);
              return updated;
            });
            // 强制重新渲染
            forceUpdate({});
            break;

          case 'tool_failed':
            console.log('[WebSocket] 工具失败:', data.tool_name, data.error);
            // 使用函数式更新
            setCurrentToolCalls(prev => 
              prev.map(tool => 
                tool.tool_name === data.tool_name && tool.status === 'running'
                  ? { ...tool, status: 'failed' as const, result: data.error }
                  : tool
              )
            );
            break;

          case 'response':
            console.log('[WebSocket] 收到响应');
            // 使用函数式更新获取最新的currentToolCalls
            setCurrentToolCalls(prevToolCalls => {
              console.log('[WebSocket] response - 当前工具调用:', prevToolCalls);
              console.log('[WebSocket] response - isLoading:', isLoading);
              
              // 创建助手消息
              const assistantMessage: Message = {
                role: 'assistant',
                content: data.content,
                timestamp: new Date(),
                retrievalStats: data.metadata?.retrieval_stats,
                toolCalls: data.metadata?.tool_calls || prevToolCalls
              };
              
              console.log('[WebSocket] 创建的消息:', assistantMessage);
              
              setMessages(prev => [...prev, assistantMessage]);
              
              // 延迟1秒再清空工具调用和设置isLoading=false，让用户能看到completed状态的动画
              setTimeout(() => {
                setCurrentToolCalls([]);
                setIsLoading(false);
              }, 1000);
              
              // 保存conversation_id
              if (data.metadata?.conversation_id && !conversationId) {
                setConversationId(data.metadata.conversation_id);
              }
              
              // 如果还没有标题，使用第一条用户消息作为标题
              if (!conversationTitle && userMessage) {
                const title = userMessage.content.slice(0, 50) + (userMessage.content.length > 50 ? '...' : '');
                setConversationTitle(title);
              }
              
              // 关闭WebSocket
              ws.close();
              wsRef.current = null;
              
              // 返回当前的工具调用（不清空，延迟清空）
              return prevToolCalls;
            });
            break;

          case 'error':
            console.error('[WebSocket] 错误:', data.error);
            const errorMessage: Message = {
              role: 'assistant',
              content: '抱歉，我现在遇到了一些问题。请稍后再试。',
              timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
            setCurrentToolCalls([]);
            setIsLoading(false);
            ws.close();
            wsRef.current = null;
            break;
        }
      };

      // 连接错误
      ws.onerror = (error) => {
        console.error('[WebSocket] 连接错误:', error);
        const errorMessage: Message = {
          role: 'assistant',
          content: '抱歉，连接失败。请稍后再试。',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
        setCurrentToolCalls([]);
        setIsLoading(false);
      };

      // 连接关闭
      ws.onclose = () => {
        console.log('[WebSocket] 连接已关闭');
        wsRef.current = null;
      };

    } catch (error) {
      console.error('WebSocket连接失败:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，我现在遇到了一些问题。请稍后再试。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setCurrentToolCalls([]);
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

  // 加载历史对话
  const handleLoadConversation = (convId: string, historyMessages: any[]) => {
    setConversationId(convId);
    
    // 转换历史消息格式
    const loadedMessages: Message[] = historyMessages.map(msg => ({
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.timestamp),
      retrievalStats: msg.retrieval_stats
    }));
    
    setMessages(loadedMessages);
    setShowHistory(false);
    
    // 设置标题
    if (historyMessages.length > 0) {
      const firstUserMsg = historyMessages.find(m => m.role === 'user');
      if (firstUserMsg) {
        const title = firstUserMsg.content.slice(0, 50) + (firstUserMsg.content.length > 50 ? '...' : '');
        setConversationTitle(title);
      }
    }
  };

  // 新建对话
  const handleNewConversation = () => {
    setMessages([{
      role: 'assistant',
      content: getWelcomeMessage(agentType),
      timestamp: new Date()
    }]);
    setConversationId(null);
    setConversationTitle(null);
    setInput('');
  };

  return (
    <>
      <div className="agent-chat-overlay" onClick={onClose}>
        <div className="agent-chat-dialog" onClick={e => e.stopPropagation()}>
          {/* 头部 */}
          <div className="agent-chat-header" style={{ background: agentColor }}>
            <div className="agent-chat-header-info">
              <h3 className="agent-chat-title">{agentName}</h3>
              <p className="agent-chat-subtitle">
                {conversationTitle || '专业领域对话'}
              </p>
            </div>
            <div className="agent-chat-header-actions">
              <button 
                className="agent-chat-action-btn" 
                onClick={() => setShowHistory(true)}
                title="对话历史"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
              <button 
                className="agent-chat-action-btn" 
                onClick={handleNewConversation}
                title="新建对话"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
              <button className="agent-chat-close" onClick={onClose}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
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
                {/* MCP工具调用动画 */}
                {msg.role === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="message-tool-calls">
                    {msg.toolCalls.map((tool, toolIdx) => (
                      <div key={toolIdx} className={`tool-call-item ${tool.status}`}>
                        <div className="tool-call-icon">
                          {getToolIcon(tool.tool_name)}
                        </div>
                        <div className="tool-call-info">
                          <div className="tool-call-name">
                            {getToolDisplayName(tool.tool_name)}
                          </div>
                          <div className="tool-call-server">
                            {tool.server_name}
                          </div>
                        </div>
                        <div className="tool-call-status">
                          {tool.status === 'running' && (
                            <div className="tool-status-spinner"></div>
                          )}
                          {tool.status === 'completed' && (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M20 6L9 17l-5-5" />
                            </svg>
                          )}
                          {tool.status === 'failed' && (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M18 6L6 18M6 6l12 12" />
                            </svg>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
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
          
          {/* 实时工具调用动画（不依赖isLoading，只要有工具调用就显示） */}
          {currentToolCalls.length > 0 && (
            <div className="agent-chat-message assistant">
              <div className="message-avatar">{getAgentIcon(agentType)}</div>
              <div className="message-content">
                <div className="message-tool-calls">
                  {currentToolCalls.map((tool, toolIdx) => (
                    <div key={toolIdx} className={`tool-call-item ${tool.status}`}>
                      <div className="tool-call-icon">
                        {getToolIcon(tool.tool_name)}
                      </div>
                      <div className="tool-call-info">
                        <div className="tool-call-name">
                          {getToolDisplayName(tool.tool_name)}
                        </div>
                        <div className="tool-call-server">
                          {tool.server_name}
                        </div>
                      </div>
                      <div className="tool-call-status">
                        {tool.status === 'running' && (
                          <div className="tool-status-spinner"></div>
                        )}
                        {tool.status === 'completed' && (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M20 6L9 17l-5-5" />
                          </svg>
                        )}
                        {tool.status === 'failed' && (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 6L6 18M6 6l12 12" />
                          </svg>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {isLoading && currentToolCalls.length === 0 && (
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

    {/* 历史对话面板 */}
    {showHistory && (
      <AgentConversationHistory
        agentType={agentType}
        token={token}
        onSelectConversation={handleLoadConversation}
        onClose={() => setShowHistory(false)}
      />
    )}
  </>
  );
}

// 获取欢迎消息
function getWelcomeMessage(agentType: string): string {
  const messages = {
    relationship: '你好！我是你的人际关系心理学专家。我会运用社会心理学理论，帮你分析社交网络、优化沟通模式、解决关系冲突。无论是亲密关系、友谊还是职场人际，我都能提供专业的诊断和建议。',
    education: '你好！我是你的教育规划战略顾问。我熟悉中国教育体系，能为你提供考研、保研、出国、就业等多路径的数据分析和规划建议。让我帮你做出最优的升学决策，规划未来5-10年的教育投资。',
    career: '你好！我是你的职业发展战略规划师。我深谙各行业动态和职场生态，能帮你进行职业定位、技能规划、求职策略优化。无论是职业选择、转型还是晋升，我都能提供系统化的解决方案。'
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
      '如何评估我的社交网络健康度？',
      '怎样处理职场中的人际冲突？',
      '如何提升我的沟通和共情能力？',
      '亲密关系中如何建立健康边界？'
    ],
    education: [
      '我适合考研、就业还是出国？',
      '如何选择最匹配的院校和专业？',
      '怎样提升我的学业竞争力？',
      '制定一份考研备考时间表'
    ],
    career: [
      '帮我做一个职业竞争力诊断',
      '我适合什么职业方向和岗位？',
      '如何规划未来5年的职业发展？',
      '跨行业转型需要注意什么？'
    ]
  };
  return questions[agentType as keyof typeof questions] || [];
}

// 获取工具图标
function getToolIcon(toolName: string): string {
  if (toolName.includes('search') || toolName.includes('web')) return '🔍';
  if (toolName.includes('analyze') || toolName.includes('assess')) return '📊';
  if (toolName.includes('calculate')) return '🧮';
  if (toolName.includes('generate') || toolName.includes('recommend')) return '💡';
  if (toolName.includes('suggest')) return '💬';
  return '🔧';
}

// 获取工具显示名称
function getToolDisplayName(toolName: string): string {
  const nameMap: Record<string, string> = {
    'web_search': '联网搜索',
    'analyze_communication_pattern': '沟通模式分析',
    'assess_relationship_health': '关系健康评估',
    'generate_conflict_resolution': '冲突解决方案',
    'calculate_social_compatibility': '社交兼容性计算',
    'suggest_conversation_topics': '对话话题推荐',
    'calculate_gpa_requirements': 'GPA要求计算',
    'analyze_major_prospects': '专业前景分析',
    'generate_study_schedule': '学习计划生成',
    'assess_exam_readiness': '考试准备度评估',
    'recommend_universities': '院校推荐'
  };
  return nameMap[toolName] || toolName;
}
