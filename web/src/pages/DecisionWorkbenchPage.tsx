import { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { GlassCard } from '../components/common/GlassCard';
import { StatusPill } from '../components/common/StatusPill';
import { BackButton } from '../components/common/BackButton';
import { StreamingCollectionChat } from '../components/decision/StreamingCollectionChat';
import { useAuth } from '../hooks/useAuth';
import {
  startDecisionCollection,
  streamStartDecisionCollection,
  continueDecisionCollection,
  streamDecisionCollection,
  generateDecisionOptions,
  openDecisionSimulationSocket,
  getDecisionHistory,
} from '../services/decision';
import type { CollectedInfo, DecisionHistoryRecord, OptionInput } from '../types/api';

// ── 阶段定义 ─────────────────────────────────────────────────
type Phase = 'input' | 'collecting' | 'options' | 'simulating';

interface ChatMsg { 
  role: 'ai' | 'user' | 'system'; 
  text: string;
  timestamp: number;
  isStreaming?: boolean;
}

export function DecisionWorkbenchPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // 阶段状态
  const [phase, setPhase] = useState<Phase>('input');
  const [question, setQuestion] = useState('');
  const [decisionType, setDecisionType] = useState<'career' | 'relationship' | 'education' | 'general'>('general');
  const [sessionId, setSessionId] = useState('');
  const [chatLog, setChatLog] = useState<ChatMsg[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [systemStatus, setSystemStatus] = useState('');
  const [collectedInfo, setCollectedInfo] = useState<CollectedInfo | null>(null);
  const [options, setOptions] = useState<OptionInput[]>([]);
  const [optionInput, setOptionInput] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState<DecisionHistoryRecord[]>([]);
  const [progress, setProgress] = useState<{ current: number; total: number; stage: string } | undefined>();
  const [useStreaming, setUseStreaming] = useState(true); // 是否使用流式响应
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 检查是否有已完成的推演，如果有则重置状态
  // 每次路由到这个页面时都会检查
  useEffect(() => {
    const lastSimulationCompleted = localStorage.getItem('lastSimulationCompleted');
    if (lastSimulationCompleted === 'true') {
      console.log('[决策工作台] 检测到推演完成标记，重置状态');
      // 重置所有状态到初始值
      setPhase('input');
      setQuestion('');
      setSessionId('');
      setChatLog([]);
      setUserInput('');
      setIsBusy(false);
      setSystemStatus('');
      setCollectedInfo(null);
      setOptions([]);
      setOptionInput('');
      setError('');
      setProgress(undefined);
      setSimulatingStatus('');
      
      // 清除标记
      localStorage.removeItem('lastSimulationCompleted');
    }
  }, [location.pathname]); // 依赖路由路径，每次导航到此页面时都会执行

  useEffect(() => {
    if (user?.user_id && phase === 'input') {
      // 延迟加载历史记录，不阻塞页面渲染
      const timer = setTimeout(() => {
        getDecisionHistory(user.user_id).then(setHistory).catch(() => {});
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [user, phase]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog]);

  // ── 阶段1：开始信息采集 ───────────────────────────────────
  async function handleStart() {
    if (!user?.user_id || !question.trim()) return;
    setIsBusy(true); setError('');
    
    try {
      // 使用流式API，实时显示状态
      for await (const chunk of streamStartDecisionCollection({
        user_id: user.user_id,
        initial_question: question.trim(),
        decision_type: decisionType,
      })) {
        if (chunk.type === 'status') {
          setSystemStatus(chunk.content || '');
        } else if (chunk.type === 'complete' && chunk.data) {
          setSessionId(chunk.data.session_id);
          setChatLog([{ role: 'ai', text: chunk.data.message, timestamp: Date.now() }]);
          setPhase('collecting');
          setSystemStatus('');
        } else if (chunk.type === 'error') {
          throw new Error(chunk.content || '启动失败');
        }
      }
      
    } catch (e) {
      setError(e instanceof Error ? e.message : '启动失败');
      setSystemStatus('');
    } finally {
      setIsBusy(false);
    }
  }

  // ── 阶段2：继续信息采集对话（支持流式响应）───────────────────────────────
  async function handleCollectReplyWithMessage(reply: string) {
    if (!reply.trim() || isBusy) return;
    
    if (useStreaming) {
      // 使用流式响应
      try {
        let streamingMessage: ChatMsg | null = null;
        let streamBuffer = '';
        
        for await (const chunk of streamDecisionCollection({ 
          session_id: sessionId, 
          user_response: reply 
        })) {
          if (chunk.type === 'status') {
            // 只显示关键状态，跳过"分析用户情况"等冗余提示
            const status = chunk.content || '';
            if (!status.includes('分析你的情况') && !status.includes('理解回答')) {
              setSystemStatus(status);
            }
          } else if (chunk.type === 'progress') {
            // 只在生成问题阶段显示进度
            if (chunk.progress?.stage === '生成问题') {
              setProgress(chunk.progress);
            }
          } else if (chunk.type === 'message') {
            // 清除状态提示，开始显示AI消息
            setSystemStatus('');
            setProgress(undefined);
            
            // 流式显示AI消息
            streamBuffer += chunk.content || '';
            
            if (!streamingMessage) {
              streamingMessage = {
                role: 'ai',
                text: streamBuffer,
                timestamp: Date.now(),
                isStreaming: true,
              };
              setChatLog(prev => [...prev, streamingMessage!]);
            } else {
              setChatLog(prev => {
                const newLog = [...prev];
                const lastMsg = newLog[newLog.length - 1];
                if (lastMsg && lastMsg.isStreaming) {
                  lastMsg.text = streamBuffer;
                }
                return newLog;
              });
            }
          } else if (chunk.type === 'complete') {
            // 完成流式显示
            if (streamingMessage) {
              setChatLog(prev => {
                const newLog = [...prev];
                const lastMsg = newLog[newLog.length - 1];
                if (lastMsg && lastMsg.isStreaming) {
                  lastMsg.isStreaming = false;
                }
                return newLog;
              });
            }
            
            if (chunk.data?.is_complete) {
              console.log('[信息采集] 采集完成');
              setCollectedInfo(chunk.data.collected_info || null);
              setChatLog(prev => [...prev, { 
                role: 'system', 
                text: '✓ 信息采集完成！正在生成分析方案...',
                timestamp: Date.now(),
              }]);
              
              setSystemStatus('正在生成分析方案...');
              const aiOptions = await generateDecisionOptions({ session_id: sessionId, user_options: [] });
              
              setOptions(aiOptions.length ? aiOptions : [
                { title: '保守稳定路线', description: '优先稳住现有基础，再寻找窗口' },
                { title: '主动突破路线', description: '接受短期波动，投向长期跃迁' },
              ]);
              setPhase('options');
            }
            
            setSystemStatus('');
            setProgress(undefined);
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : '对话失败');
        setSystemStatus('');
        setProgress(undefined);
      } finally {
        setIsBusy(false);
      }
    } else {
      // 使用传统非流式响应
      try {
        const result = await continueDecisionCollection({ session_id: sessionId, user_response: reply });
        
        if (result.ai_question) {
          setChatLog(prev => [...prev, { role: 'ai', text: result.ai_question!, timestamp: Date.now() }]);
        }
        
        if (result.is_complete) {
          console.log('[信息采集] 采集完成');
          
          setCollectedInfo(result.collected_info || null);
          setChatLog(prev => [...prev, { 
            role: 'system', 
            text: '✓ 信息采集完成！正在生成分析方案...',
            timestamp: Date.now(),
          }]);
          
          setSystemStatus('正在生成分析方案...');
          const aiOptions = await generateDecisionOptions({ session_id: sessionId, user_options: [] });
          
          setOptions(aiOptions.length ? aiOptions : [
            { title: '保守稳定路线', description: '优先稳住现有基础，再寻找窗口' },
            { title: '主动突破路线', description: '接受短期波动，投向长期跃迁' },
          ]);
          setPhase('options');
          setSystemStatus('');
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : '对话失败');
        setSystemStatus('');
      } finally {
        setIsBusy(false);
      }
    }
  }

  // ── 阶段2：继续信息采集对话（旧版本，保留兼容）───────────────────────────────
  async function handleCollectReply() {
    if (!userInput.trim() || isBusy) return;
    const reply = userInput.trim();
    setUserInput('');
    setChatLog(prev => [...prev, { role: 'user', text: reply, timestamp: Date.now() }]);
    await handleCollectReplyWithMessage(reply);
  }

  // ── 阶段3：确认选项，发起决策分析 ─────────────────────
  function handleAddOption() {
    if (!optionInput.trim()) return;
    setOptions(prev => [...prev, { title: optionInput.trim(), description: '' }]);
    setOptionInput('');
  }

  function handleRemoveOption(i: number) {
    setOptions(prev => prev.filter((_, idx) => idx !== i));
  }

  function handleStartSimulation() {
    if (!sessionId || options.length === 0) return;
    
    console.log('[决策副本] 准备显示轮数配置对话框');
    
    // 显示轮数配置对话框
    setShowRoundsConfig(true);
  }

  // 确认轮数配置后启动推演
  function handleConfirmRoundsAndStart() {
    console.log('[决策副本] 准备跳转到推演页面');
    console.log('[决策副本] sessionId:', sessionId);
    console.log('[决策副本] question:', question);
    console.log('[决策副本] options:', options);
    console.log('[决策副本] collectedInfo:', collectedInfo);
    console.log('[决策副本] personaRounds:', personaRounds);
    
    // 关闭配置对话框
    setShowRoundsConfig(false);
    
    // 显示跳转状态
    setSimulatingStatus('正在初始化推演环境...');
    
    // 短暂延迟以显示状态
    setTimeout(() => {
      setSimulatingStatus('正在连接推演引擎...');
      
      setTimeout(() => {
        // 跳转到推演页，携带 session_id + options + personaRounds
        navigate('/decision/simulation', {
          state: {
            mode: 'future',
            sessionId,
            question,
            userId: user?.user_id || '',
            options,
            collectedInfo,
            decisionType,
            personaRounds, // 传递轮数配置
          },
        });
      }, 300);
    }, 300);
  }

  // 启动模拟时的状态
  const [simulatingStatus, setSimulatingStatus] = useState('');
  
  // Agent轮数配置
  const [showRoundsConfig, setShowRoundsConfig] = useState(false);
  const [personaRounds, setPersonaRounds] = useState<Record<string, number>>({
    rational_analyst: 2,
    adventurer: 2,
    pragmatist: 2,
    idealist: 2,
    conservative: 2,
    social_navigator: 2,
    innovator: 2,
  });

  // ── 根据决策类型获取问题模板提示 ────────────────────────────
  const placeholderByType: Record<string, string> = {
    career: '例如：我要不要在今年离开现在的工作，去做更适合我的方向？',
    relationship: '例如：我和相处了两年的女朋友之间出现了一些价值观冲突，该如何处理？',
    education: '例如：我是985高校的大三学生，纠结是考研还是直接就业？',
    general: '例如：我正在考虑是否要换城市发展？',
  };

  const decisionTypeLabel: Record<string, string> = {
    career: '职业发展',
    relationship: '人际关系',
    education: '教育升学',
    general: '通用决策',
  };

  const decisionTypeColor: Record<string, string> = {
    career: '#4facfe',
    relationship: '#FF6B6B',
    education: '#43e97b',
    general: '#a18cd1',
  };

  // ── 渲染 ─────────────────────────────────────────────────
  return (
    <AppShell>
      <BackButton to="/" label="返回" />
      <div className="stack-layout">

        {/* ── 阶段1：输入问题 ── */}
        {phase === 'input' && (
          <GlassCard title="发起决策分析" subtitle="描述你正在面对的真实决策问题，AI 会通过几轮对话深入了解你的处境。">
            {/* 初始化状态提示 */}
            {systemStatus && (
              <div style={{
                padding: '12px 16px',
                borderRadius: 14,
                background: 'rgba(232, 213, 208, 0.08)',
                border: '1px solid rgba(220, 210, 200, 0.2)',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                marginBottom: 16,
              }}>
                <div style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #E8D5D0, #D4C4BF)',
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                }} />
                <span style={{ fontSize: 13, color: '#7a6f65', fontWeight: 500 }}>
                  {systemStatus}
                </span>
              </div>
            )}
            <div className="form-stack">
              {/* 当前决策类型指示 */}
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                borderRadius: 20,
                background: `${decisionTypeColor[decisionType]}18`,
                border: `1px solid ${decisionTypeColor[decisionType]}40`,
                marginBottom: 12,
                width: 'fit-content',
              }}>
                <div style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: decisionTypeColor[decisionType],
                }} />
                <span style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: decisionTypeColor[decisionType],
                }}>
                  {decisionTypeLabel[decisionType]}决策
                </span>
              </div>
              
              {/* 决策类型选择 */}
              <label className="field-block">
                <span>决策类型</span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginTop: 8 }}>
                  <button
                    type="button"
                    onClick={() => setDecisionType('career')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'career' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'career' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ 
                      fontSize: 16, 
                      fontWeight: 600, 
                      marginBottom: 4,
                      background: 'linear-gradient(135deg, #1e293b 0%, #64748b 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>职业发展</div>
                    <div style={{ 
                      fontSize: 12,
                      background: 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>求职、跳槽、转行</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('relationship')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'relationship' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'relationship' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ 
                      fontSize: 16, 
                      fontWeight: 600, 
                      marginBottom: 4,
                      background: 'linear-gradient(135deg, #1e293b 0%, #64748b 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>人际关系</div>
                    <div style={{ 
                      fontSize: 12,
                      background: 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>恋爱、婚姻、社交</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('education')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'education' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'education' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ 
                      fontSize: 16, 
                      fontWeight: 600, 
                      marginBottom: 4,
                      background: 'linear-gradient(135deg, #1e293b 0%, #64748b 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>教育升学</div>
                    <div style={{ 
                      fontSize: 12,
                      background: 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>考研、留学、专业选择</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('general')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'general' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'general' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ 
                      fontSize: 16, 
                      fontWeight: 600, 
                      marginBottom: 4,
                      background: 'linear-gradient(135deg, #1e293b 0%, #64748b 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>通用决策</div>
                    <div style={{ 
                      fontSize: 12,
                      background: 'linear-gradient(135deg, #1e293b 0%, #475569 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                    }}>其他类型决策</div>
                  </button>
                </div>
              </label>
              
              <label className="field-block">
                <span>当前问题（{decisionTypeLabel[decisionType]}）</span>
                <textarea
                  className="textarea" rows={5}
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  placeholder={placeholderByType[decisionType]}
                />
              </label>
              {error && <div className="form-error">{error}</div>}
              
              {/* 实时状态显示 - 与界面风格一致 */}
              {isBusy && systemStatus && (
                <div style={{
                  marginTop: 16,
                  padding: '12px 16px',
                  borderRadius: 14,
                  background: 'rgba(232, 213, 208, 0.08)',
                  border: '1px solid rgba(220, 210, 200, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  animation: 'fadeInUp 0.3s ease',
                }}>
                  <div style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #E8D5D0, #D4C4BF)',
                    animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    flexShrink: 0,
                  }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      fontSize: 13, 
                      fontWeight: 500, 
                      color: '#7a6f65',
                    }}>
                      {systemStatus}
                    </div>
                  </div>
                </div>
              )}
              
              <div className="composer-actions" style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 24 }}>
                <button
                  onClick={() => void handleStart()}
                  disabled={isBusy || !question.trim()}
                  style={{
                    position: 'relative',
                    width: 80,
                    height: 80,
                    borderRadius: '50%',
                    border: 'none',
                    background: isBusy || !question.trim() 
                      ? 'linear-gradient(135deg, #64748b 0%, #475569 100%)'
                      : 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                    boxShadow: isBusy || !question.trim()
                      ? 'none'
                      : '0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1) inset',
                    cursor: isBusy || !question.trim() ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                    fontWeight: 600,
                    color: '#ffffff',
                    transform: isBusy || !question.trim() ? 'scale(0.95)' : 'scale(1)',
                    opacity: isBusy || !question.trim() ? 0.6 : 1,
                  }}
                  onMouseEnter={(e) => {
                    if (!isBusy && question.trim()) {
                      e.currentTarget.style.transform = 'scale(1.05)';
                      e.currentTarget.style.boxShadow = '0 12px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.2) inset';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isBusy && question.trim()) {
                      e.currentTarget.style.transform = 'scale(1)';
                      e.currentTarget.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1) inset';
                    }
                  }}
                >
                  <span style={{ 
                    textAlign: 'center',
                    lineHeight: 1.2,
                    padding: '0 8px',
                  }}>
                    {isBusy ? '启动中' : '开始采集'}
                  </span>
                  {!isBusy && question.trim() && (
                    <div style={{
                      position: 'absolute',
                      inset: -4,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.3), rgba(15, 23, 42, 0.3))',
                      filter: 'blur(8px)',
                      zIndex: -1,
                      animation: 'pulse 2s ease-in-out infinite',
                    }} />
                  )}
                </button>
              </div>
            </div>
            
            {/* 添加pulse动画 */}
            <style>{`
              @keyframes pulse {
                0%, 100% {
                  opacity: 1;
                  transform: scale(1);
                }
                50% {
                  opacity: 0.5;
                  transform: scale(0.8);
                }
              }
              
              @keyframes spin {
                from {
                  transform: rotate(0deg);
                }
                to {
                  transform: rotate(360deg);
                }
              }
              
              @keyframes fadeInUp {
                from {
                  opacity: 0;
                  transform: translateY(10px);
                }
                to {
                  opacity: 1;
                  transform: translateY(0);
                }
              }
            `}</style>
          </GlassCard>
        )}

        {/* ── 阶段2：信息采集对话 ── */}
        {phase === 'collecting' && (
          <GlassCard
            title="信息采集"
            subtitle="AI 正在通过对话深入了解你的处境，请如实回答，这会让分析更准确。"
          >
            <StreamingCollectionChat
              messages={chatLog.map(msg => ({
                role: msg.role,
                content: msg.text,
                timestamp: msg.timestamp,
                isStreaming: msg.isStreaming,
              }))}
              onSendMessage={async (message) => {
                // 直接添加用户消息到聊天记录
                setChatLog(prev => [...prev, { role: 'user', text: message, timestamp: Date.now() }]);
                setIsBusy(true);
                setError('');
                
                // 调用处理函数
                await handleCollectReplyWithMessage(message);
              }}
              isProcessing={isBusy}
              currentStatus={systemStatus}
              progress={progress}
            />
            {error && <div className="form-error" style={{ marginTop: 12 }}>{error}</div>}
          </GlassCard>
        )}

        {/* ── 阶段3：确认选项 ── */}
        {phase === 'options' && (
          <GlassCard
            title="确认分析方案"
            subtitle="AI 已为你生成决策方案，你可以修改、删除或添加新方案，然后启动多维度智能评估。"
          >
            <div className="form-stack">
              {/* 选项列表 - 使用消息气泡样式 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {options.map((opt, i) => (
                  <div 
                    key={`option-${i}-${opt.title}`} 
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-start',
                      animation: 'fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}
                  >
                    <div style={{
                      maxWidth: '82%',
                      padding: '14px 20px',
                      borderRadius: 20,
                      background: 'linear-gradient(135deg, rgba(232, 213, 208, 0.15), rgba(220, 205, 195, 0.12))',
                      border: '1px solid rgba(220, 210, 200, 0.25)',
                      boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
                      position: 'relative',
                      flex: 1,
                    }}>
                      <div style={{ 
                        fontWeight: 600, 
                        background: 'linear-gradient(135deg, #1e293b 0%, #64748b 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        fontSize: 15,
                        lineHeight: 1.5,
                        marginBottom: opt.description ? 6 : 0,
                      }}>
                        {opt.title}
                      </div>
                      {opt.description && (
                        <div style={{ 
                          fontSize: 13, 
                          background: 'linear-gradient(135deg, #334155 0%, #64748b 100%)',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                          backgroundClip: 'text',
                          lineHeight: 1.6,
                        }}>
                          {opt.description}
                        </div>
                      )}
                      <button
                        onClick={() => handleRemoveOption(i)}
                        style={{ 
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          background: 'rgba(255, 100, 100, 0.15)', 
                          border: 'none', 
                          color: 'rgba(255, 100, 100, 0.9)', 
                          cursor: 'pointer', 
                          fontSize: 18, 
                          lineHeight: 1,
                          width: 24,
                          height: 24,
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          transition: 'all 0.2s',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(255, 100, 100, 0.25)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(255, 100, 100, 0.15)';
                        }}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* 添加选项 */}
              <div style={{ display: 'flex', gap: 10 }}>
                <input
                  className="textarea"
                  style={{ flex: 1, padding: '8px 14px', borderRadius: 10, fontSize: 13 }}
                  value={optionInput}
                  onChange={e => setOptionInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleAddOption()}
                  placeholder="添加自定义选项…"
                />
                <button className="button button-secondary" onClick={handleAddOption}>添加</button>
              </div>

              {/* 采集摘要 */}
              {collectedInfo && (
                <div style={{ padding: '12px 16px', borderRadius: 14, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', fontSize: 13, color: 'rgba(255,255,255,0.55)' }}>
                  <div style={{ marginBottom: 6, fontWeight: 600, color: 'rgba(147,197,253,0.8)' }}>已采集信息摘要</div>
                  {collectedInfo.concerns && collectedInfo.concerns.length > 0 && (
                    <div>顾虑：{collectedInfo.concerns.join(' / ')}</div>
                  )}
                  {collectedInfo.mentioned_options && collectedInfo.mentioned_options.length > 0 && (
                    <div>提及选项：{collectedInfo.mentioned_options.join(' / ')}</div>
                  )}
                </div>
              )}

              {/* 启动状态 */}
              {simulatingStatus && (
                <div style={{
                  padding: '12px 16px',
                  borderRadius: 10,
                  background: 'rgba(59, 130, 246, 0.08)',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}>
                  <div style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: '#3b82f6',
                    animation: 'pulse 1.5s ease-in-out infinite',
                  }} />
                  <span style={{ fontSize: 13, color: '#3b82f6', fontWeight: 500 }}>{simulatingStatus}</span>
                </div>
              )}

              <div className="composer-actions">
                <button className="button button-ghost" onClick={() => setPhase('collecting')}>
                  返回补充信息
                </button>
                <button
                  className="button button-primary"
                  onClick={handleStartSimulation}
                  disabled={options.length === 0}
                >
                  启动智能评估
                </button>
              </div>
            </div>
          </GlassCard>
        )}

        {/* ── 历史记录 ── */}
        {history.length > 0 && phase === 'input' && (
          <GlassCard title="最近分析" subtitle="点击查看历史记录">
            <div className="history-grid">
              {history.map(item => (
                <article key={item.simulation_id || `history-${Math.random()}`} className="history-card">
                  <div className="module-accent history-accent-primary" />
                  <div className="history-card-body">
                    <div className="history-card-top">
                      <StatusPill tone="primary">Recent</StatusPill>
                      <span>{item.created_at}</span>
                    </div>
                    <h3>{item.question}</h3>
                    <p>{item.recommendation || '暂无推荐'}</p>
                    <div className="history-card-foot">
                      <button
                        className="button button-primary"
                        onClick={() => navigate('/decision/simulation', {
                          state: { mode: 'history', simulationId: item.simulation_id, question: item.question, userId: user?.user_id || '' },
                        })}
                      >
                        打开图谱
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </GlassCard>
        )}
      </div>
      
      {/* Agent轮数配置对话框 */}
      {showRoundsConfig && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000,
        }} onClick={() => setShowRoundsConfig(false)}>
          <div style={{
            background: 'white', borderRadius: 16, padding: 32,
            maxWidth: 600, width: '90%',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ margin: '0 0 8px 0', fontSize: 24, fontWeight: 700 }}>
              🎭 Agent推演轮数配置
            </h2>
            <p style={{ margin: '0 0 24px 0', color: '#666', fontSize: 14, lineHeight: 1.6 }}>
              为每个决策人格Agent设置推演轮数（1-5轮）。轮数越多，思考越深入，但耗时也越长。
            </p>
            
            <div style={{ marginBottom: 24 }}>
              {Object.entries({
                rational_analyst: '理性分析师',
                adventurer: '冒险家',
                pragmatist: '实用主义者',
                idealist: '理想主义者',
                conservative: '保守派',
                social_navigator: '社交导航者',
                innovator: '创新者',
              }).map(([id, name]) => (
                <div key={id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px 0', borderBottom: '1px solid #f0f0f0',
                }}>
                  <span style={{ fontSize: 15, fontWeight: 500 }}>{name}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button
                      onClick={() => setPersonaRounds(prev => ({
                        ...prev,
                        [id]: Math.max(1, prev[id] - 1)
                      }))}
                      style={{
                        width: 32, height: 32, borderRadius: 8,
                        border: '1px solid #e0e0e0', background: 'white',
                        cursor: 'pointer', fontSize: 18, fontWeight: 600,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}
                    >
                      −
                    </button>
                    <span style={{
                      width: 40, textAlign: 'center',
                      fontSize: 16, fontWeight: 600, color: '#0A59F7',
                    }}>
                      {personaRounds[id]}轮
                    </span>
                    <button
                      onClick={() => setPersonaRounds(prev => ({
                        ...prev,
                        [id]: Math.min(5, prev[id] + 1)
                      }))}
                      style={{
                        width: 32, height: 32, borderRadius: 8,
                        border: '1px solid #e0e0e0', background: 'white',
                        cursor: 'pointer', fontSize: 18, fontWeight: 600,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{
              padding: 16, borderRadius: 12,
              background: 'rgba(10, 89, 247, 0.05)',
              border: '1px solid rgba(10, 89, 247, 0.1)',
              marginBottom: 24,
            }}>
              <div style={{ fontSize: 13, color: '#666', lineHeight: 1.6 }}>
                <div style={{ marginBottom: 8, fontWeight: 600, color: '#0A59F7' }}>[推荐配置]</div>
                <div>• 快速决策（日常选择）：1轮，约30秒</div>
                <div>• 标准决策（一般重要）：2轮，约1分钟</div>
                <div>• 深度决策（重大选择）：3-5轮，约2-5分钟</div>
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowRoundsConfig(false)}
                style={{
                  padding: '12px 24px', borderRadius: 10,
                  border: '1px solid #e0e0e0', background: 'white',
                  cursor: 'pointer', fontSize: 14, fontWeight: 600,
                }}
              >
                取消
              </button>
              <button
                onClick={() => {
                  // 快速设置：所有Agent 1轮
                  setPersonaRounds({
                    rational_analyst: 1,
                    adventurer: 1,
                    pragmatist: 1,
                    idealist: 1,
                    conservative: 1,
                    social_navigator: 1,
                    innovator: 1,
                  });
                }}
                style={{
                  padding: '12px 24px', borderRadius: 10,
                  border: '1px solid #e0e0e0', background: 'white',
                  cursor: 'pointer', fontSize: 14, fontWeight: 600,
                }}
              >
                快速(1轮)
              </button>
              <button
                onClick={() => {
                  // 标准设置：所有Agent 2轮
                  setPersonaRounds({
                    rational_analyst: 2,
                    adventurer: 2,
                    pragmatist: 2,
                    idealist: 2,
                    conservative: 2,
                    social_navigator: 2,
                    innovator: 2,
                  });
                }}
                style={{
                  padding: '12px 24px', borderRadius: 10,
                  border: '1px solid #e0e0e0', background: 'white',
                  cursor: 'pointer', fontSize: 14, fontWeight: 600,
                }}
              >
                标准(2轮)
              </button>
              <button
                onClick={handleConfirmRoundsAndStart}
                style={{
                  padding: '12px 24px', borderRadius: 10,
                  border: 'none',
                  background: 'linear-gradient(135deg, #0A59F7, #6B48FF)',
                  color: 'white', cursor: 'pointer',
                  fontSize: 14, fontWeight: 600,
                }}
              >
                确认并启动
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
