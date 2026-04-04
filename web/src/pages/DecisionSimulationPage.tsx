import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { DecisionGraphStage } from '../components/decision/DecisionGraphStage';
import { SimulationProgress } from '../components/decision/SimulationProgress';
import { ThinkingStream } from '../components/decision/ThinkingStream';
import { StatusPill } from '../components/common/StatusPill';
import { useAuth } from '../hooks/useAuth';
import { getFutureOsSimulation } from '../services/futureOs';
import { openDecisionSimulationSocket } from '../services/decision';
import type {
  DecisionGraphNode,
  DecisionRecordPayload,
  DecisionSimulationRouteState,
  DecisionOption,
} from '../types/api';
import { ensureDecisionGraph, buildFallbackDecisionGraph } from '../utils/decisionGraph';

function buildLiveGraph(optionId: string, title: string, timeline: DecisionGraphNode[]) {
  return buildFallbackDecisionGraph(optionId, title, timeline);
}

function formatPercent(value?: number | null) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--';
  return `${Math.round(value * 100)}%`;
}

function parseRouteState(
  state: unknown,
  fallbackUserId: string,
  searchParams: URLSearchParams,
): DecisionSimulationRouteState {
  const routeState = (state || {}) as Partial<DecisionSimulationRouteState>;
  return {
    mode: routeState.mode || (searchParams.get('simulationId') ? 'history' : 'future'),
    sessionId: routeState.sessionId,
    simulationId: routeState.simulationId || searchParams.get('simulationId') || undefined,
    dungeonId: routeState.dungeonId,
    question: routeState.question || searchParams.get('question') || '决策图谱舞台',
    userId: routeState.userId || fallbackUserId,
    options: routeState.options,
    collectedInfo: routeState.collectedInfo || null,
    record: routeState.record,
    scenario: routeState.scenario,
    decisionType: routeState.decisionType,
  };
}

function stateEntries(value?: Record<string, string | number | boolean | null>) {
  return Object.entries(value || {}).filter(([, item]) => item !== undefined && item !== '');
}

function impactEntries(value?: Record<string, number>) {
  return Object.entries(value || {}).sort((l, r) => Math.abs(r[1]) - Math.abs(l[1]));
}

function riskTone(level?: string) {
  if (level === 'high') return 'danger';
  if (level === 'medium') return 'warning';
  return 'success';
}

export function DecisionSimulationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const config = useMemo(
    () => parseRouteState(location.state, user?.user_id || '', searchParams),
    [location.state, searchParams, user],
  );

  const [record, setRecord] = useState<DecisionRecordPayload | null>(config.record || null);
  const [selectedOptionIndex, setSelectedOptionIndex] = useState(0);
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(!config.record);
  const [showNodeDetail, setShowNodeDetail] = useState(false);
  const [showThinkingPanel, setShowThinkingPanel] = useState(true);
  const [expandedThinking, setExpandedThinking] = useState<Set<string>>(new Set());

  const [wsStatus, setWsStatus] = useState<string>('');
  const [wsStage, setWsStage] = useState<string>('idle');
  const [wsPhase, setWsPhase] = useState<'idle' | 'connecting' | 'running' | 'done'>('idle');
  const wsPhaseRef = useRef<'idle' | 'connecting' | 'running' | 'done'>('idle');
  const [liveOptions, setLiveOptions] = useState<Map<string, DecisionOption>>(new Map());
  const [currentOptionIndex, setCurrentOptionIndex] = useState<number | undefined>(undefined);
  const [thinkingContent, setThinkingContent] = useState<Map<string, string>>(new Map());
  const [currentThinkingOption, setCurrentThinkingOption] = useState<string>('');
  const [agentProgress, setAgentProgress] = useState<Map<string, { latestNode: DecisionGraphNode; thinking: string }>>(new Map());
  const wsCloseRef = useRef<(() => void) | null>(null);

  // 添加错误处理
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      console.error('[全局错误]', event.error);
      setError(`页面错误: ${event.error?.message || '未知错误'}`);
    };
    
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      console.error('[未处理的Promise拒绝]', event.reason);
      setError(`异步错误: ${event.reason?.message || '未知错误'}`);
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  useEffect(() => {
    if (config.mode !== 'future' || !config.sessionId || !config.options?.length) return;
    
    console.log('[推演页面] 建立 WebSocket 连接, sessionId:', config.sessionId);
    setWsPhase('connecting');
    setWsStatus('正在连接推演服务器...');
    setIsLoading(false);

    let isActive = true;
    let wsInstance: ReturnType<typeof openDecisionSimulationSocket> | null = null;
    
    const setupWebSocket = () => {
      if (!config.sessionId || !config.options) {
        console.error('[推演页面] sessionId 或 options 为空');
        return;
      }
      
      wsInstance = openDecisionSimulationSocket(
      { session_id: config.sessionId, options: config.options },
      {
        onEvent(event) {
          if (!isActive) return;
          
          try {
            const type = String(event.type || '');
            console.log('[推演页面] 收到消息:', type, event);

            // 连接成功，开始推演
            if (wsPhaseRef.current === 'connecting') {
              setWsPhase('running');
              wsPhaseRef.current = 'running';
            }

            if (type === 'status') {
              setWsStatus(String(event.content || ''));
              setWsStage(String(event.stage || 'processing'));
            }

            if (type === 'heartbeat') {
              // 心跳消息，更新状态但不打印过多日志
              setWsStatus(String(event.content || '正在生成中...'));
            }

            if (type === 'thinking_chunk') {
              const chunk = String(event.content || '');
              const optionId = String(event.option_id || '');
              const optionTitle = String(event.option_title || '');

              // 追加到该选项的思考内容
              setThinkingContent(prev => {
                const next = new Map(prev);
                const current = next.get(optionId) || '';
                next.set(optionId, current + chunk);
                return next;
              });

              // 更新机器人进度
              const sentences = chunk.split(/[。！？.!?]/);
              const lastSentence = sentences[sentences.length - 2] || sentences[sentences.length - 1] || '';
              const shortThinking = lastSentence.trim().substring(0, 80);

              setAgentProgress(prevProgress => {
                const nextProgress = new Map(prevProgress);
                nextProgress.set(optionTitle, {
                  latestNode: null as any,
                  thinking: shortThinking || 'AI正在思考...',
                });
                return nextProgress;
              });

              setCurrentThinkingOption(optionTitle);
            }

            if (type === 'option_start') {
              const optId = String(event.option_id || '');
              const title = String(event.option_title || event.title || optId);
              console.log('[推演页面] 开始新选项:', optId, title);
              const match = optId.match(/option_(\d+)/);
              if (match) {
                setCurrentOptionIndex(parseInt(match[1]) - 1);
              }
              // 初始化思考内容
              setThinkingContent(prev => {
                const next = new Map(prev);
                next.set(optId, '');
                return next;
              });
              setCurrentThinkingOption(title);
              setLiveOptions(prev => {
                const next = new Map(prev);
                if (!next.has(optId)) {
                  next.set(optId, {
                    option_id: optId, title, description: '',
                    timeline: [], decision_graph: null,
                    final_score: 0, risk_level: 0,
                    execution_confidence: 0, dropout_risk_month: null, personal_note: '',
                  });
                }
                return next;
              });
              // 自动展开第一个选项
              setExpandedThinking(prev => {
                if (prev.size === 0) {
                  return new Set([optId]);
                }
                return prev;
              });
            }

            if (type === 'node') {
              const optId = String(event.option_id || '');
              const node = event.node as DecisionGraphNode;
              if (!node || !node.event_id) {
                console.warn('[推演页面] 收到无效节点:', event);
                return;
              }
              console.log(`[推演页面] ✓ 收到节点: ${optId} - M${node.month} - ${node.event.substring(0, 30)}...`);
              
              // 使用单个状态更新，避免状态不同步
              setLiveOptions(prev => {
                const next = new Map(prev);
                const opt = next.get(optId);
                if (opt) {
                  const updated = { ...opt, timeline: [...opt.timeline, node as any] };
                  updated.decision_graph = buildLiveGraph(optId, opt.title, updated.timeline as any);
                  next.set(optId, updated);
                  console.log(`[推演页面] 更新选项 ${optId}，当前节点数: ${updated.timeline.length}`);
                  console.log(`[推演页面] 所有选项节点数:`, Array.from(next.entries()).map(([id, o]) => `${id}:${o.timeline.length}`).join(', '));
                  
                  // 更新机器人进度
                  setAgentProgress(prevProgress => {
                    const nextProgress = new Map(prevProgress);
                    nextProgress.set(opt.title, {
                      latestNode: node,
                      thinking: prevProgress.get(opt.title)?.thinking || '正在思考...',
                    });
                    return nextProgress;
                  });
                } else {
                  console.warn('[推演页面] 找不到选项:', optId);
                }
                return next;
              });
            }

            if (type === 'option_complete') {
              const optId = String(event.option_id || '');
              setLiveOptions(prev => {
                const next = new Map(prev);
                const opt = next.get(optId);
                if (opt) {
                  next.set(optId, {
                    ...opt,
                    final_score: Number(event.final_score) || opt.final_score,
                    risk_level: Number(event.risk_level) || opt.risk_level,
                    execution_confidence: Number(event.execution_confidence) || opt.execution_confidence,
                    dropout_risk_month: event.dropout_risk_month as number | null,
                    personal_note: String(event.personal_note || ''),
                    decision_graph: (event.decision_graph as DecisionOption['decision_graph']) || opt.decision_graph,
                  });
                }
                return next;
              });
            }

            if (type === 'done') {
              setWsPhase('done');
              setWsStatus('推演完成');
              // 不要在这里设置 record，让 useEffect 处理
              console.log('[推演页面] 推演完成，等待 useEffect 更新 record');
            }

            if (type === 'recommendation') {
              setRecord(prev => prev ? { ...prev, recommendation: String(event.content || '') } : prev);
            }

            if (type === 'error') {
              const errorMsg = String(event.content || 'WebSocket 推演失败');
              console.error('[推演页面] 错误:', errorMsg);
              setError(errorMsg);
              setWsPhase('done');
            }
          } catch (err) {
            console.error('[推演页面] 消息处理错误:', err, event);
            setError(`消息处理错误: ${err instanceof Error ? err.message : '未知错误'}`);
          }
        },
        onError(msg) {
          if (!isActive) return;
          console.error('[推演页面] WebSocket错误:', msg);
          setError(`WebSocket错误: ${msg}`);
          setWsPhase('done');
        },
      },
    );
    wsCloseRef.current = () => {
      if (wsInstance) wsInstance();
    };
    };
    
    setupWebSocket();
    
    return () => {
      console.log('[推演页面] useEffect cleanup');
      isActive = false;
      if (wsInstance) {
        console.log('[推演页面] 关闭 WebSocket');
        wsInstance();
      }
    };
  }, [config.sessionId, config.mode]); // 只依赖 sessionId 和 mode

  // 移除这个 useEffect，因为我们在 node 消息处理中直接更新 record

  // 同步 liveOptions 到 record - 只显示合并视图
  useEffect(() => {
    if (liveOptions.size > 0) {
      const opts = Array.from(liveOptions.values());
      
      console.log('[推演页面] useEffect 触发，liveOptions 大小:', liveOptions.size);
      console.log('[推演页面] 各选项节点数:', opts.map(o => `${o.title}: ${o.timeline.length}`).join(', '));
      
      // 创建一个合并的图表，包含所有选项的节点
      const mergedTimeline: DecisionGraphNode[] = [];
      opts.forEach((opt, optIndex) => {
        opt.timeline.forEach((node: any) => {
          // 为每个节点添加选项标识
          mergedTimeline.push({
            ...node,
            branch_strategy: opt.title,
            option_index: optIndex,
          });
        });
      });
      
      console.log('[推演页面] 合并后总节点数:', mergedTimeline.length);
      
      // 创建一个虚拟的"合并选项"用于显示所有节点
      const mergedOption: DecisionOption = {
        option_id: 'merged_all',
        title: '所有分支实时推演',
        description: '同时显示所有选项的推演结果',
        timeline: mergedTimeline as any,
        decision_graph: mergedTimeline.length > 0 ? buildFallbackDecisionGraph('merged_all', '所有分支', mergedTimeline as any) : null,
        final_score: 0,
        risk_level: 0,
        execution_confidence: 0,
        dropout_risk_month: null,
        personal_note: '',
      };
      
      console.log('[推演页面] 创建合并选项，decision_graph 节点数:', mergedOption.decision_graph?.nodes?.length || 0);
      
      setRecord(prevRecord => ({
        simulation_id: prevRecord?.simulation_id || `live_${Date.now()}`,
        user_id: config.userId,
        question: config.question,
        options_count: opts.length,
        recommendation: prevRecord?.recommendation || '',
        options: [mergedOption], // 只保留合并视图
        created_at: prevRecord?.created_at || new Date().toISOString(),
      }));
      
      // 自动选择合并视图
      setSelectedOptionIndex(0);
    }
  }, [liveOptions, config.userId, config.question]);

  useEffect(() => {
    if (config.record || !config.simulationId) {
      setIsLoading(false);
      return;
    }

    let active = true;
    setIsLoading(true);
    setError('');

    getFutureOsSimulation(config.simulationId)
      .then((payload) => {
        if (active) setRecord(payload);
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : '推演详情加载失败');
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [config.record, config.simulationId]);

  const activeOption: DecisionOption | null = record?.options[selectedOptionIndex] || null;
  const activeGraph = activeOption ? ensureDecisionGraph(activeOption) : null;

  useEffect(() => {
    if (!activeGraph?.nodes?.length) {
      setSelectedNodeId('');
      return;
    }

    const stillExists = activeGraph.nodes.some((node) => node.event_id === selectedNodeId);
    if (!stillExists) {
      setSelectedNodeId(activeGraph.nodes[0].event_id);
    }
  }, [activeGraph, selectedNodeId]);

  const selectedNode: DecisionGraphNode | null =
    activeGraph?.nodes.find((node) => node.event_id === selectedNodeId) || null;

  // 添加渲染保护
  const canRenderGraph = record && activeGraph && activeGraph.nodes && activeGraph.nodes.length > 0;

  return (
    <div style={{ 
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.03) 0%, rgba(107, 72, 255, 0.02) 100%), #FFFFFF',
      overflow: 'hidden', display: 'flex', flexDirection: 'column' 
    }}>
      {/* HarmonyOS 6 - 纯净顶部导航栏 */}
      <div style={{ 
        position: 'relative', zIndex: 100, display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
        gap: 20, padding: '14px 24px',
        background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(20px)', 
        borderBottom: '1px solid rgba(0, 0, 0, 0.06)', 
        boxShadow: '0 4px 24px rgba(0, 0, 0, 0.04)' 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* 返回按钮 - 纯净风格 */}
          <button onClick={() => navigate('/decision/history')} style={{ 
            background: 'rgba(10, 89, 247, 0.06)', border: 'none', borderRadius: 12, 
            padding: '10px 16px', color: '#0A59F7', cursor: 'pointer', fontSize: 14, fontWeight: 600,
            display: 'flex', alignItems: 'center', gap: 6,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          }} 
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(10, 89, 247, 0.1)'; e.currentTarget.style.transform = 'translateX(-2px)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(10, 89, 247, 0.06)'; e.currentTarget.style.transform = 'translateX(0)'; }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            返回
          </button>
          
          {/* 标题区域 */}
          <div style={{ borderLeft: '1px solid rgba(0, 0, 0, 0.08)', paddingLeft: 16 }}>
            <div style={{ fontSize: 11, color: '#999', marginBottom: 4, letterSpacing: '0.1em', textTransform: 'uppercase' }}>决策图谱舞台</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#1A1A1A', letterSpacing: '-0.01em' }}>{config.question}</div>
          </div>
        </div>
        
        {/* 实时统计 - HarmonyOS 6 风格 */}
        {wsPhase === 'running' && liveOptions.size > 0 && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            {Array.from(liveOptions.entries()).map(([optionId, opt]) => {
              const branchColors = ['#0A59F7', '#6B48FF', '#FF9500'];
              const index = Array.from(liveOptions.keys()).indexOf(optionId);
              const color = branchColors[index % branchColors.length];
              
              return (
                <div key={optionId} style={{ 
                  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', 
                  background: 'rgba(255, 255, 255, 0.9)', border: `1px solid ${color}22`, 
                  borderRadius: 14, backdropFilter: 'blur(12px)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, boxShadow: `0 0 12px ${color}66` }} />
                  <div>
                    <div style={{ fontSize: 11, color: '#999', letterSpacing: '0.05em' }}>{opt.title}</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: color }}>{opt.timeline.length} 节点</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 推演进度 - HarmonyOS 6 风格 */}
      {wsPhase === 'running' && (
        <div style={{ 
          position: 'relative', zIndex: 90, padding: '12px 24px', 
          background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(20px)', 
          borderBottom: '1px solid rgba(10, 89, 247, 0.1)' 
        }}>
          <SimulationProgress stage={wsStage} content={wsStatus} optionsCount={config.options?.length || 0} currentOption={currentOptionIndex} />
        </div>
      )}
      
      {/* 主内容区域 - 图表 */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {canRenderGraph ? (
          <DecisionGraphStage 
            graph={activeGraph!} 
            accent="#5aa9ff" 
            selectedNodeId={selectedNodeId} 
            onSelect={(node) => { setSelectedNodeId(node.event_id); setShowNodeDetail(true); }} 
            fullscreen={false} 
            height={window.innerHeight - 80}
            agentProgress={wsPhase === 'running' ? agentProgress : undefined}
          />
        ) : isLoading ? (
          // 加载历史记录状态
          <div style={{ 
            display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%',
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: 48, height: 48, border: '3px solid #e2e8f0', borderTopColor: '#3b82f6',
                borderRadius: '50%', margin: '0 auto 16px',
                animation: 'spin 1s linear infinite',
              }} />
              <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 8 }}>正在加载推演图谱</div>
              <div style={{ fontSize: 14, color: '#64748b' }}>稍等一下...</div>
            </div>
          </div>
        ) : wsPhase === 'connecting' ? (
          // 连接中状态
          <div style={{ 
            display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%',
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: 48, height: 48, border: '3px solid #e2e8f0', borderTopColor: '#3b82f6',
                borderRadius: '50%', margin: '0 auto 16px',
                animation: 'spin 1s linear infinite',
              }} />
              <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 8 }}>{wsStatus || '正在连接服务器'}</div>
              <div style={{ fontSize: 14, color: '#64748b' }}>等待推演引擎启动...</div>
            </div>
          </div>
        ) : wsPhase === 'running' ? (
          // 推演中状态 - 显示真实状态
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            padding: 32,
          }}>
            {/* 简单旋转加载动画 */}
            <div style={{
              width: 48,
              height: 48,
              border: '3px solid #e2e8f0',
              borderTopColor: '#3b82f6',
              borderRadius: '50%',
              marginBottom: 24,
              animation: 'spin 1s linear infinite',
            }} />

            <div style={{
              fontSize: 18,
              fontWeight: 600,
              color: '#1e293b',
              marginBottom: 12,
              textAlign: 'center',
            }}>
              AI 正在推演中
            </div>

            {/* 真实状态信息 */}
            <div style={{
              fontSize: 14,
              color: '#3b82f6',
              textAlign: 'center',
              maxWidth: 400,
              lineHeight: 1.6,
              padding: '16px 24px',
              background: '#f8fafc',
              borderRadius: 12,
              border: '1px solid #e2e8f0',
            }}>
              {wsStatus || '等待服务器响应...'}
            </div>

            {/* 当前选项进度 */}
            {currentOptionIndex !== undefined && (
              <div style={{
                marginTop: 20,
                fontSize: 13,
                color: '#64748b',
              }}>
                正在处理选项 {currentOptionIndex + 1} / {optionsCount || config.options?.length || 0}
              </div>
            )}

            {/* 已生成的节点统计 */}
            {liveOptions.size > 0 && (
              <div style={{
                marginTop: 16,
                fontSize: 13,
                color: '#64748b',
              }}>
                已生成 {Array.from(liveOptions.values()).reduce((sum, opt) => sum + (opt.timeline?.length || 0), 0)} 个节点
              </div>
            )}
          </div>
        ) : (
          // HarmonyOS 6 - 空状态
          <div style={{ 
            display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%',
            animation: 'harmonyFadeIn 0.5s ease-out'
          }}>
            <div style={{ textAlign: 'center', animation: 'harmonyFadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1)' }}>
              <div style={{ 
                width: 100, height: 100, borderRadius: '50%', margin: '0 auto 24px',
                background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.06), rgba(107, 72, 255, 0.04))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </div>
              <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8, color: '#1A1A1A' }}>未找到推演</div>
              <div style={{ fontSize: 14, color: '#666', marginBottom: 24, letterSpacing: '0.02em' }}>这条记录可能已经丢失或尚未生成</div>
              <button onClick={() => navigate('/decision')} style={{ 
                background: 'linear-gradient(135deg, #0A59F7, #6B48FF)', border: 'none', borderRadius: 14, 
                padding: '14px 28px', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
                boxShadow: '0 8px 24px rgba(10, 89, 247, 0.25)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 12px 32px rgba(10, 89, 247, 0.35)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 8px 24px rgba(10, 89, 247, 0.25)'; }}>
                返回决策副本
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* 思考面板 - 3个路径分别显示 */}
      {wsPhase === 'running' && showThinkingPanel && thinkingContent.size > 0 && (
        <div style={{
          position: 'absolute', top: 80, right: 20, width: 420, maxHeight: 'calc(100vh - 120px)',
          overflowY: 'auto', zIndex: 100,
          background: 'rgba(255, 255, 255, 0.98)', backdropFilter: 'blur(24px)',
          border: '1px solid rgba(10, 89, 247, 0.1)', borderRadius: 24,
          padding: 20, boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08)',
          pointerEvents: 'auto', animation: 'harmonyFadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid rgba(0, 0, 0, 0.06)'
          }}>
            <div style={{
              fontSize: 15, fontWeight: 700, color: '#1A1A1A',
              display: 'flex', alignItems: 'center', gap: 8,
              letterSpacing: '0.02em'
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: 10,
                background: 'linear-gradient(135deg, #0A59F7, #6B48FF)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              AI 思考过程
            </div>
            <button onClick={() => setShowThinkingPanel(false)} style={{
              background: 'rgba(0, 0, 0, 0.04)', border: 'none', borderRadius: 10,
              width: 36, height: 36, color: '#666', cursor: 'pointer', fontSize: 18,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0, 0, 0, 0.08)'; e.currentTarget.style.color = '#1A1A1A'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(0, 0, 0, 0.04)'; e.currentTarget.style.color = '#666'; }}>×</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Array.from(thinkingContent.entries()).map(([optionId, content]) => {
              const option = liveOptions.get(optionId);
              const isExpanded = expandedThinking.has(optionId);
              const title = option?.title || optionId;

              return (
                <div key={optionId} style={{
                  background: 'rgba(10, 89, 247, 0.04)',
                  border: '1px solid rgba(10, 89, 247, 0.08)',
                  borderRadius: 16, overflow: 'hidden',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }}>
                  <button
                    onClick={() => {
                      const next = new Set(expandedThinking);
                      if (isExpanded) {
                        next.delete(optionId);
                      } else {
                        next.add(optionId);
                      }
                      setExpandedThinking(next);
                    }}
                    style={{
                      width: '100%', background: 'none', border: 'none',
                      padding: '14px 18px', color: '#1A1A1A', cursor: 'pointer',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      fontSize: 14, fontWeight: 600,
                      transition: 'background 0.2s ease'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(10, 89, 247, 0.06)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'none'}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#0A59F7' }}/>
                      {title}
                    </span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                      style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.3s ease' }}>
                      <polyline points="6 9 12 15 18 9"/>
                    </svg>
                  </button>
                  {isExpanded && (
                    <div style={{
                      padding: '0 18px 18px 18px', maxHeight: 300, overflowY: 'auto',
                      fontSize: 13, lineHeight: 1.7, color: '#666',
                      fontFamily: 'inherit', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                      animation: 'harmonyFadeIn 0.3s ease-out'
                    }}>
                      {content || '等待AI响应...'}
                      {content && (
                        <span style={{ display: 'inline-block', width: 6, height: 14, background: '#0A59F7', marginLeft: 4, borderRadius: 2, animation: 'blink 1s infinite' }} />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {wsPhase === 'running' && !showThinkingPanel && (thinkingContent.size > 0 || agentThinkings.size > 0) && (
        <button
          onClick={() => setShowThinkingPanel(true)}
          style={{
            position: 'absolute', top: 80, right: 20, zIndex: 100,
            background: 'linear-gradient(135deg, #0A59F7, #6B48FF)', backdropFilter: 'blur(12px)',
            border: 'none', borderRadius: 16, padding: '14px 20px', color: '#fff', cursor: 'pointer',
            fontSize: 14, fontWeight: 600,
            boxShadow: '0 8px 32px rgba(10, 89, 247, 0.3)',
            pointerEvents: 'auto', transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            animation: 'harmonyFadeIn 0.3s ease-out',
            display: 'flex', alignItems: 'center', gap: 8
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(10, 89, 247, 0.4)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 8px 32px rgba(10, 89, 247, 0.3)';
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          {agentThinkings.size > 0 ? `5个Agent思考 (${agentThinkings.size})` : `显示思考过程 (${thinkingContent.size})`}
        </button>
      )}

      {/* 节点详情面板 - HarmonyOS 6 纯净风格 */}
      {selectedNode && showNodeDetail && (
        <div style={{ 
          position: 'absolute', top: 80, right: 20, width: 420, maxHeight: 'calc(100vh - 120px)', 
          overflowY: 'auto', zIndex: 100, 
          background: 'rgba(255, 255, 255, 0.98)', backdropFilter: 'blur(24px)', 
          border: '1px solid rgba(10, 89, 247, 0.1)', borderRadius: 24, 
          padding: 24, boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08)', 
          pointerEvents: 'auto', animation: 'harmonyFadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
          <button onClick={() => setShowNodeDetail(false)} style={{ 
            position: 'absolute', top: 16, right: 16, 
            background: 'rgba(0, 0, 0, 0.04)', border: 'none', borderRadius: 10, 
            width: 36, height: 36, color: '#666', cursor: 'pointer', fontSize: 18,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0, 0, 0, 0.08)'; e.currentTarget.style.color = '#1A1A1A'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(0, 0, 0, 0.04)'; e.currentTarget.style.color = '#666'; }}>×</button>
          
          <div style={{ color: '#1A1A1A' }}>
            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                <StatusPill tone={riskTone(selectedNode.risk_tag)}>{selectedNode.branch_strategy || activeOption?.branch_strategy || '当前分支'}</StatusPill>
                <span style={{ fontSize: 13, color: '#999', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                  M{selectedNode.month} / 概率 {formatPercent(selectedNode.probability)}
                </span>
              </div>
              <h3 style={{ fontSize: 20, fontWeight: 800, margin: 0, letterSpacing: '-0.01em', lineHeight: 1.4 }}>{selectedNode.event}</h3>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ background: 'rgba(10, 89, 247, 0.04)', borderRadius: 16, padding: 18 }}>
                <div style={{ 
                  fontSize: 12, fontWeight: 700, color: '#0A59F7', marginBottom: 10, 
                  letterSpacing: '0.1em', textTransform: 'uppercase',
                  display: 'flex', alignItems: 'center', gap: 6
                }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                  状态前
                </div>
                <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {stateEntries(selectedNode.state_before).map(([key, value]) => (
                    <span key={key} style={{ fontSize: 14, color: '#666', display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ color: '#999', minWidth: 60 }}>{key}:</span>
                      <span style={{ color: '#1A1A1A', fontWeight: 500 }}>{String(value)}</span>
                    </span>
                  ))}
                </div>
              </div>
              
              <div style={{ background: 'rgba(107, 72, 255, 0.04)', borderRadius: 16, padding: 18 }}>
                <div style={{ 
                  fontSize: 12, fontWeight: 700, color: '#6B48FF', marginBottom: 10, 
                  letterSpacing: '0.1em', textTransform: 'uppercase',
                  display: 'flex', alignItems: 'center', gap: 6
                }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                    <polyline points="17 6 23 6 23 12"/>
                  </svg>
                  状态后
                </div>
                <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {stateEntries(selectedNode.state_after).map(([key, value]) => (
                    <span key={key} style={{ fontSize: 14, color: '#666', display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ color: '#999', minWidth: 60 }}>{key}:</span>
                      <span style={{ color: '#1A1A1A', fontWeight: 500 }}>{String(value)}</span>
                    </span>
                  ))}
                </div>
              </div>
              
              <div style={{ background: 'rgba(0, 200, 83, 0.04)', borderRadius: 16, padding: 18 }}>
                <div style={{ 
                  fontSize: 12, fontWeight: 700, color: '#34C759', marginBottom: 10, 
                  letterSpacing: '0.1em', textTransform: 'uppercase',
                  display: 'flex', alignItems: 'center', gap: 6
                }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="20" x2="18" y2="10"/>
                    <line x1="12" y1="20" x2="12" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="14"/>
                  </svg>
                  影响向量
                </div>
                <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {impactEntries(selectedNode.impact_vector).map(([key, value]) => (
                    <span key={key} style={{ 
                      padding: '8px 14px', borderRadius: 12, fontSize: 13, fontWeight: 600, 
                      background: value >= 0 ? 'rgba(52, 199, 89, 0.1)' : 'rgba(255, 59, 48, 0.1)', 
                      color: value >= 0 ? '#34C759' : '#FF3B30', 
                      border: `1px solid ${value >= 0 ? 'rgba(52, 199, 89, 0.2)' : 'rgba(255, 59, 48, 0.2)'}`,
                      transition: 'all 0.2s ease',
                    }}>
                      {key} {value >= 0 ? '+' : ''}{(value * 100).toFixed(0)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 错误提示 - HarmonyOS 6 风格 */}
      {error && (
        <div style={{ 
          position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)', 
          background: 'rgba(255, 255, 255, 0.98)', backdropFilter: 'blur(20px)', 
          border: '1px solid rgba(255, 59, 48, 0.2)', borderRadius: 16, 
          padding: '14px 24px', color: '#FF3B30', fontSize: 14, fontWeight: 600, 
          boxShadow: '0 12px 40px rgba(255, 59, 48, 0.15)', zIndex: 200,
          display: 'flex', alignItems: 'center', gap: 10,
          animation: 'harmonyFadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}
