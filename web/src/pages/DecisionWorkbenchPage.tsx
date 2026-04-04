import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { GlassCard } from '../components/common/GlassCard';
import { StatusPill } from '../components/common/StatusPill';
import { StreamingCollectionChat } from '../components/decision/StreamingCollectionChat';
import { useAuth } from '../hooks/useAuth';
import {
  startDecisionCollection,
  continueDecisionCollection,
  streamDecisionCollection,
  generateDecisionOptions,
  openDecisionSimulationSocket,
  getDecisionHistory,
  getWarmupStatus,
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
  const [warmupProgress, setWarmupProgress] = useState<{ stage: string; progress: number } | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 检查AI核心预热状态（简化版 - 只查询一次）
  useEffect(() => {
    if (user?.user_id && phase === 'input' && warmupProgress === null) {
      getWarmupStatus(user.user_id).then(status => {
        if (status.status !== 'ready') {
          setWarmupProgress({ stage: status.stage, progress: status.progress });
        }
      }).catch(() => {
        // 查询失败，假设已就绪
        setWarmupProgress(null);
      });
    }
  }, [user, phase, warmupProgress]);

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
      // 显示正在连接的状态
      setSystemStatus('正在连接决策引擎...');
      
      const { session_id, message } = await startDecisionCollection({
        user_id: user.user_id,
        initial_question: question.trim(),
        decision_type: decisionType,
      });
      
      // 显示正在初始化的状态
      setSystemStatus('正在初始化对话...');
      
      // 短暂延迟让用户看到状态变化
      await new Promise(resolve => setTimeout(resolve, 100));
      
      setSessionId(session_id);
      setChatLog([{ role: 'ai', text: message, timestamp: Date.now() }]);
      setPhase('collecting');
      setSystemStatus('');
      
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
                text: '✓ 信息采集完成！正在生成推演选项...',
                timestamp: Date.now(),
              }]);
              
              setSystemStatus('正在生成推演选项...');
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
            text: '✓ 信息采集完成！正在生成推演选项...',
            timestamp: Date.now(),
          }]);
          
          setSystemStatus('正在生成推演选项...');
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

  // ── 阶段3：确认选项，发起 WebSocket 推演 ─────────────────
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
    
    console.log('[决策副本] 准备跳转到推演页面');
    console.log('[决策副本] sessionId:', sessionId);
    console.log('[决策副本] question:', question);
    console.log('[决策副本] options:', options);
    console.log('[决策副本] collectedInfo:', collectedInfo);
    
    // 显示跳转状态
    setSimulatingStatus('正在初始化推演环境...');
    
    // 短暂延迟以显示状态
    setTimeout(() => {
      setSimulatingStatus('正在连接推演引擎...');
      
      setTimeout(() => {
        // 跳转到推演页，携带 session_id + options，由推演页建立 WebSocket
        navigate('/decision/simulation', {
          state: {
            mode: 'future',
            sessionId,
            question,
            userId: user?.user_id || '',
            options,
            collectedInfo,
            decisionType,
          },
        });
      }, 300);
    }, 300);
  }

  // 启动模拟时的状态
  const [simulatingStatus, setSimulatingStatus] = useState('');

  // ── 渲染 ─────────────────────────────────────────────────
  return (
    <AppShell>
      <div className="stack-layout">

        {/* ── 阶段1：输入问题 ── */}
        {phase === 'input' && (
          <GlassCard title="发起推演" subtitle="描述你正在面对的真实决策问题，AI 会通过几轮对话深入了解你的处境。">
            {/* AI核心预热状态 */}
            {warmupProgress && warmupProgress.progress < 100 && (
              <div style={{
                padding: '14px 18px',
                borderRadius: 16,
                background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.08), rgba(107, 72, 255, 0.08))',
                border: '1px solid rgba(10, 89, 247, 0.2)',
                marginBottom: 16,
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 10,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #0A59F7, #6B48FF)',
                      animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    }} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#0A59F7' }}>
                      AI核心预热中
                    </span>
                  </div>
                  <span style={{ fontSize: 12, color: '#6B48FF', fontWeight: 600 }}>
                    {warmupProgress.progress}%
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#5a5a6e', marginBottom: 8 }}>
                  {warmupProgress.stage}
                </div>
                <div style={{
                  height: 6,
                  borderRadius: 999,
                  background: 'rgba(10, 89, 247, 0.1)',
                  overflow: 'hidden',
                }}>
                  <div
                    style={{
                      height: '100%',
                      borderRadius: 999,
                      background: 'linear-gradient(90deg, #0A59F7, #6B48FF)',
                      width: `${warmupProgress.progress}%`,
                      transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                    }}
                  />
                </div>
              </div>
            )}
            
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
                      color: '#e0f2fe',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>职业发展</div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>求职、跳槽、转行</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('relationship')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'relationship' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'relationship' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      color: '#e0f2fe',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>人际关系</div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>恋爱、婚姻、社交</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('education')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'education' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'education' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      color: '#e0f2fe',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>教育升学</div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>考研、留学、专业选择</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType('general')}
                    style={{
                      padding: '16px',
                      borderRadius: 12,
                      border: decisionType === 'general' ? '2px solid #0A59F7' : '1px solid rgba(255,255,255,0.2)',
                      background: decisionType === 'general' ? 'rgba(10,89,247,0.12)' : 'rgba(255,255,255,0.05)',
                      color: '#e0f2fe',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>通用决策</div>
                    <div style={{ fontSize: 12, color: '#94a3b8' }}>其他类型决策</div>
                  </button>
                </div>
              </label>
              
              <label className="field-block">
                <span>当前问题</span>
                <textarea
                  className="textarea" rows={5}
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  placeholder="例如：我要不要在今年离开现在的工作，去做更适合我的方向？"
                />
              </label>
              {error && <div className="form-error">{error}</div>}
              <div className="composer-actions">
                <button
                  className="button button-primary"
                  onClick={() => void handleStart()}
                  disabled={isBusy || !question.trim()}
                >
                  {isBusy ? '启动中…' : '开始信息采集'}
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
            `}</style>
          </GlassCard>
        )}

        {/* ── 阶段2：信息采集对话 ── */}
        {phase === 'collecting' && (
          <GlassCard
            title="信息采集"
            subtitle="AI 正在通过对话深入了解你的处境，请如实回答，这会让推演更准确。"
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
            title="确认推演选项"
            subtitle="AI 已为你生成推演分支，你可以修改、删除或添加新选项，然后启动多 Agent 实时推演。"
          >
            <div className="form-stack">
              {/* 选项列表 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {options.map((opt, i) => (
                  <div key={`option-${i}-${opt.title}`} style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '12px 16px', borderRadius: 14,
                    background: 'rgba(10,89,247,0.08)',
                    border: '1px solid rgba(10,89,247,0.18)',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, color: '#e8f0fe', fontSize: 14 }}>{opt.title}</div>
                      {opt.description && (
                        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', marginTop: 3 }}>{opt.description}</div>
                      )}
                    </div>
                    <button
                      onClick={() => handleRemoveOption(i)}
                      style={{ background: 'none', border: 'none', color: 'rgba(255,100,100,0.7)', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
                    >×</button>
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
                  {collectedInfo.concerns.length > 0 && (
                    <div>顾虑：{collectedInfo.concerns.join(' / ')}</div>
                  )}
                  {collectedInfo.options_mentioned.length > 0 && (
                    <div>提及选项：{collectedInfo.options_mentioned.join(' / ')}</div>
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
                  启动多 Agent 推演
                </button>
              </div>
            </div>
          </GlassCard>
        )}

        {/* ── 历史记录 ── */}
        {history.length > 0 && phase === 'input' && (
          <GlassCard title="最近推演" subtitle="点击打开历史图谱">
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
    </AppShell>
  );
}
