import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { PersonaInteractionView } from '../components/decision/PersonaInteractionView';
import { useAuth } from '../hooks/useAuth';
import { openDecisionSimulationSocket } from '../services/decision';
import type { DecisionOption } from '../types/api';
import { buildFallbackDecisionGraph } from '../utils/decisionGraph';

// 辅助函数
function getOptionLabel(optionId: string, fallbackTitle?: string): string {
  if (fallbackTitle && fallbackTitle !== optionId && !fallbackTitle.startsWith('option_')) {
    return fallbackTitle;
  }
  const match = optionId.match(/^option_(\d+)$/);
  if (match) {
    const num = parseInt(match[1]);
    const chineseNumbers = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
    if (num > 0 && num <= 10) {
      return `选项${chineseNumbers[num]}`;
    }
    return `选项${num}`;
  }
  return optionId;
}

// 路由状态类型
interface RouteConfig {
  mode: 'future';
  sessionId?: string;
  question: string;
  userId: string;
  options?: Array<{ title: string; description: string }>;
  collectedInfo?: any;
  decisionType?: string;
  personaRounds?: Record<string, number>; // 新增：Agent轮数配置
}

function parseRouteState(
  state: unknown,
  fallbackUserId: string,
  searchParams: URLSearchParams,
): RouteConfig {
  const routeState = (state || {}) as Partial<RouteConfig>;
  return {
    mode: 'future',
    sessionId: routeState.sessionId,
    question: routeState.question || searchParams.get('question') || '决策分析',
    userId: routeState.userId || fallbackUserId,
    options: routeState.options,
    collectedInfo: routeState.collectedInfo || null,
    decisionType: routeState.decisionType,
    personaRounds: routeState.personaRounds || {
      rational_analyst: 2,
      adventurer: 2,
      pragmatist: 2,
      idealist: 2,
      conservative: 2,
      social_navigator: 2,
      innovator: 2,
    }, // 默认2轮
  };
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

  // 状态管理
  const [selectedOptionIndex, setSelectedOptionIndex] = useState(0);
  const [error, setError] = useState('');
  
  // Agent轮数配置
  const [showRoundsConfig, setShowRoundsConfig] = useState(false);
  const [personaRounds, setPersonaRounds] = useState<Record<string, number>>(
    config.personaRounds || {
      rational_analyst: 2,
      adventurer: 2,
      pragmatist: 2,
      idealist: 2,
      conservative: 2,
      social_navigator: 2,
      innovator: 2,
    }
  );

  // WebSocket状态
  const [wsPhase, setWsPhase] = useState<'idle' | 'connecting' | 'running' | 'done'>('idle');
  const wsPhaseRef = useRef<'idle' | 'connecting' | 'running' | 'done'>('idle');
  const [wsStatus, setWsStatus] = useState<string>('');
  
  // 实时数据
  const [liveOptions, setLiveOptions] = useState<Map<string, DecisionOption>>(new Map());
  const [record, setRecord] = useState<any>(null);
  
  // 总分数状态 - 按option_id分组
  const [totalScoreByOption, setTotalScoreByOption] = useState<Map<string, number>>(new Map());
  
  // Agent可视化状态 - 按option_id分组
  const [agentsByOption, setAgentsByOption] = useState<Map<string, Array<{
    id: string; 
    name: string; 
    status: 'waiting' | 'thinking' | 'complete' | 'error'; 
    score?: number; 
    stance?: string;
    currentMessage?: string;
    messageTimestamp?: number;
    thinkingHistory?: Array<{
      round: number;
      message: string;
      timestamp: number;
      score?: number;
      stance?: string;
      keyPoints?: string[];
      reasoning?: string;
    }>;
  }>>>(new Map());
  const [currentMonthByOption, setCurrentMonthByOption] = useState<Map<string, number>>(new Map());
  const [interactionsByOption, setInteractionsByOption] = useState<Map<string, Array<{from: string; to: string; type: string; message: string; timestamp: number}>>>(new Map());
  const [completedOptions, setCompletedOptions] = useState<Set<string>>(new Set());
  
  // 推演控制状态
  const [pausedOptions, setPausedOptions] = useState<Set<string>>(new Set());
  const [activeOptionId, setActiveOptionId] = useState<string | null>(null);
  
  const wsCloseRef = useRef<(() => void) | null>(null);

  // CSS动画
  const styles = `
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.2); }
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `;

  // WebSocket连接 - 为每个选项建立独立连接
  useEffect(() => {
    if (!config.sessionId || !config.options?.length || !config.userId) return;
    
    console.log('[推演] 启动并行WebSocket连接:', config.options.length, '个选项');
    
    // 清空之前的完成状态
    setCompletedOptions(new Set());
    
    // 初始化暂停状态：除了第一个选项，其他都暂停
    const initialPausedOptions = new Set<string>();
    config.options.forEach((_, index) => {
      if (index > 0) {
        initialPausedOptions.add(`option_${index + 1}`);
      }
    });
    setPausedOptions(initialPausedOptions);
    setActiveOptionId('option_1'); // 第一个选项开始推演
    
    console.log('[推演] 初始化暂停状态:', Array.from(initialPausedOptions));
    
    setWsPhase('connecting');
    wsPhaseRef.current = 'connecting';
    setWsStatus('正在连接...');

    const wsInstances: Map<string, {close: () => void, send: (data: any) => void}> = new Map();
    let completedCount = 0;
    let cleanupCalled = false; // 清理标志
    
    // 为非暂停的选项建立WebSocket连接
    const connectOption = (option: any, index: number, skipPauseCheck: boolean = false) => {
      const optionId = `option_${index + 1}`;
      
      // 如果已经清理，不建立新连接
      if (cleanupCalled) {
        console.log(`[推演] 已清理，不建立新连接: 选项 ${index + 1}`);
        return;
      }
      
      // 如果不跳过暂停检查，则检查初始暂停状态
      if (!skipPauseCheck) {
        const isPaused = initialPausedOptions.has(optionId);
        
        if (isPaused) {
          console.log(`[推演] 选项 ${index + 1} (${option.title}) 初始暂停，不建立连接`);
          return;
        }
      }
      
      console.log(`[推演] 连接选项 ${index + 1}:`, option.title);
      
      let socket: WebSocket | null = null;
      let isConnectionActive = true; // 每个连接独立的活动标志
      
      const wsInstance = openDecisionSimulationSocket(
        {
          session_id: config.sessionId!,
          user_id: config.userId,
          question: config.question,
          option: { title: option.title, description: option.description || '' },
          option_index: index,
          collected_info: config.collectedInfo,
          decision_type: config.decisionType || 'general',
          persona_rounds: personaRounds, // 传递用户配置的轮数
        },
        {
          onOpen(ws) {
            socket = ws;
            console.log(`[推演] 选项 ${index + 1} WebSocket已连接`);
          },
          onEvent(event) {
            // 只检查当前连接的活动状态和清理标志
            if (cleanupCalled || !isConnectionActive) {
              console.log(`[推演] 选项 ${index + 1} 连接已停止，忽略消息:`, event.type);
              return;
            }
            
            const type = String(event.type || '');
            console.log(`[推演] 选项 ${index + 1} 收到消息类型: ${type}`, event);
            
            // 连接成功
            if (wsPhaseRef.current === 'connecting' && type !== 'error') {
              setWsPhase('running');
              wsPhaseRef.current = 'running';
            }

            // 状态更新
            if (type === 'status') {
              setWsStatus(String(event.content || ''));
            }

            // 选项开始
            if (type === 'option_start' || type === 'start') {
              const optId = String(event.option_id || optionId);
              const title = String(event.title || option.title);
              
              setLiveOptions(prev => {
                const next = new Map(prev);
                if (!next.has(optId)) {
                  const startNode: any = {
                    event_id: `${optId}_start`,
                    parent_event_id: null,
                    month: 0,
                    event: `开始分析：${title}`,
                    probability: 1.0,
                    state_before: {},
                    state_after: {},
                    impact_vector: {},
                    branch_strategy: title,
                    branch_group: optId,
                    risk_tag: 'low',
                    evidence_sources: [],
                    agent_votes: [],
                    impact: 0,
                  };
                  
                  next.set(optId, {
                    option_id: optId,
                    title,
                    description: option.description || '',
                    timeline: [startNode as any],
                    decision_graph: buildFallbackDecisionGraph(optId, title, [startNode as any]),
                    final_score: 0,
                    risk_level: 0,
                    execution_confidence: 0,
                    dropout_risk_month: null,
                    personal_note: '',
                  });
                }
                return next;
              });
            }

            // Agent启动
            if (type === 'agents_start' || type === 'personas_init') {
              console.log(`[Agent初始化] 收到${type}消息`, event);
              const agents = (event.agents || event.personas) as any[] || [];
              const month = (event.month as number) || 0;
              const optId = String(event.option_id || optionId);
              
              console.log(`[Agent初始化] optId=${optId}, agents数量=${agents.length}`);
              
              if (optId && agents.length > 0) {
                const agentList = agents.map((a: any) => ({
                  id: String(a.id),
                  name: String(a.name),
                  status: 'waiting' as const,
                  score: undefined,
                  thinkingHistory: []
                }));
                
                console.log(`[Agent初始化] 创建agentList:`, agentList);
                
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  next.set(optId, agentList);
                  console.log(`[Agent初始化] ✅ 已设置${agentList.length}个agents到optId=${optId}`);
                  return next;
                });
                
                if (type === 'agents_start') {
                  setCurrentMonthByOption(prev => {
                    const next = new Map(prev);
                    next.set(optId, month === 0 ? 1 : month);
                    return next;
                  });
                }
              } else {
                console.warn(`[Agent初始化] ⚠️ 跳过: optId=${optId}, agents.length=${agents.length}`);
              }
            }

            // Agent思考/完成
            if (type === 'agent_thinking') {
              const agentId = event.agent_id;
              const optId = String(event.option_id || optionId);
              const content = String(event.content || '正在思考...');
              const stage = String(event.stage || 'thinking');
              const skillResult = event.skill_result as any;  // 技能执行结果
              
              setAgentsByOption(prev => {
                const next = new Map(prev);
                const agents = next.get(optId) || [];
                next.set(optId, agents.map(a => {
                  if (a.id === agentId) {
                    // 添加到历史记录
                    const historyRecord = {
                      round: stage === 'reflection' ? 1 : 0,
                      message: content,
                      timestamp: Date.now(),
                      score: undefined,
                      stance: undefined,
                      keyPoints: [],
                      reasoning: '',
                      skillResult: skillResult || undefined,  // 保存技能结果
                    };
                    
                    const existingHistory = a.thinkingHistory || [];
                    
                    return { 
                      ...a, 
                      status: 'thinking' as const,
                      currentMessage: content,
                      messageTimestamp: Date.now(),
                      thinkingHistory: [...existingHistory, historyRecord]
                    };
                  }
                  return a;
                }));
                return next;
              });
            }

            // 处理新的agent_event消息
            if (type === 'agent_event') {
              const eventType = String(event.event_type || '');
              const optId = String(event.option_id || optionId);
              const personaId = String(event.persona_id || '');
              const personaName = String(event.persona_name || '');
              
              console.log(`[Agent事件] ${eventType}: ${personaName}`, event);
              
              // Agent开始
              if (eventType === 'agent_start') {
                console.log(`[Agent事件] ${personaName} 开始推演`);
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => 
                    a.id === personaId ? { ...a, status: 'waiting' as const } : a
                  ));
                  return next;
                });
              }
              
              // 轮次开始
              if (eventType === 'round_start') {
                const round = event.round as number || 1;
                console.log(`[Agent事件] 第${round}轮开始`);
                setCurrentMonthByOption(prev => {
                  const next = new Map(prev);
                  next.set(optId, round);
                  return next;
                });
              }
              
              // 思考开始
              if (eventType === 'thinking_start') {
                console.log(`[Agent事件] ${personaName} 开始思考`);
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  const updated = agents.map(a => 
                    a.id === personaId ? { 
                      ...a, 
                      status: 'thinking' as const,
                      currentMessage: '🧠 正在深度思考...',
                      messageTimestamp: Date.now(),
                      streamingMessage: ''  // 初始化流式消息
                    } : a
                  );
                  console.log(`[Agent事件] 更新后的agents:`, updated.find(a => a.id === personaId));
                  next.set(optId, updated);
                  return next;
                });
              }
              
              // 思考片段（流式输出）
              if (eventType === 'thinking_chunk') {
                const content = String(event.content || '');
                const chunkType = String(event.type || 'answer');  // thinking 或 answer
                
                console.log(`[Agent事件] ${personaName} 思考片段: ${content.substring(0, 20)}...`);
                
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => {
                    if (a.id === personaId) {
                      const streamingMessage = (a.streamingMessage || '') + content;
                      const displayPrefix = chunkType === 'thinking' ? '💭 思考中: ' : '📝 分析中: ';
                      
                      return {
                        ...a,
                        status: 'thinking' as const,
                        currentMessage: displayPrefix + streamingMessage.substring(0, 150) + (streamingMessage.length > 150 ? '...' : ''),
                        messageTimestamp: Date.now(),
                        streamingMessage: streamingMessage
                      };
                    }
                    return a;
                  }));
                  return next;
                });
              }
              
              // 技能开始
              if (eventType === 'skill_start') {
                const skillName = String(event.skill_name || '');
                const round = (event.round as number) || 1;
                console.log(`[Agent事件] ${personaName} 开始执行技能: ${skillName}`);
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => {
                    if (a.id === personaId) {
                      // 添加到历史记录
                      const historyRecord = {
                        round: round,
                        message: `🔧 ${skillName}`,
                        timestamp: Date.now(),
                        action: 'skill_start',
                        skillName: skillName,
                        event_type: 'skill_start'
                      };
                      const existingHistory = a.thinkingHistory || [];
                      
                      return {
                        ...a,
                        currentMessage: `🔧 执行技能: ${skillName}`,
                        messageTimestamp: Date.now(),
                        thinkingHistory: [...existingHistory, historyRecord]
                      };
                    }
                    return a;
                  }));
                  return next;
                });
              }
              
              // 技能完成
              if (eventType === 'skill_complete') {
                const skillName = String(event.skill_name || '');
                const summary = String(event.summary || '');
                const result = event.result as any;
                const round = (event.round as number) || 1;
                console.log(`[Agent事件] ${personaName} 技能完成: ${skillName} - ${summary}`);
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => {
                    if (a.id === personaId) {
                      // 添加到历史记录
                      const historyRecord = {
                        round: round,
                        message: summary || `✅ ${skillName}`,
                        timestamp: Date.now(),
                        action: 'skill_complete',
                        skillName: skillName,
                        skillResult: {
                          skill_name: skillName,
                          summary: summary,
                          full_result: result
                        },
                        event_type: 'skill_complete'
                      };
                      const existingHistory = a.thinkingHistory || [];
                      
                      return {
                        ...a,
                        currentMessage: `✅ ${skillName}`,
                        messageTimestamp: Date.now(),
                        thinkingHistory: [...existingHistory, historyRecord]
                      };
                    }
                    return a;
                  }));
                  return next;
                });
              }
              
              // 技能错误
              if (eventType === 'skill_error') {
                const skillName = String(event.skill_name || '');
                const error = String(event.error || '');
                console.log(`[Agent事件] ${personaName} 技能失败: ${skillName} - ${error}`);
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => 
                    a.id === personaId ? { 
                      ...a, 
                      currentMessage: `❌ ${skillName}失败`,
                      messageTimestamp: Date.now()
                    } : a
                  ));
                  return next;
                });
              }
              
              // 思考完成
              if (eventType === 'thinking_complete') {
                const stance = String(event.stance || '中立');
                const score = Number(event.score || 50);
                const reasoning = String(event.reasoning || '');
                const keyPoints = (event.key_points as string[]) || [];
                const confidence = event.confidence as number || 0.7;
                const round = event.round as number || 1;
                
                console.log(`[Agent事件] ${personaName} 思考完成: ${stance} (${score}分)`);
                console.log(`[Agent事件] 推理内容长度: ${reasoning.length}字符, key_points数量: ${keyPoints.length}`);
                console.log(`[Agent事件] reasoning内容:`, reasoning.substring(0, 100));
                console.log(`[Agent事件] key_points:`, keyPoints);
                
                // 构建显示消息
                const displayMessage = `✅ ${stance} (${score}分)`;
                
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  const updated = agents.map(a => {
                    if (a.id === personaId) {
                      const historyRecord = {
                        round,
                        message: `${stance} (${score}分)`,
                        timestamp: Date.now(),
                        score,
                        stance,
                        keyPoints,
                        reasoning,
                        event_type: 'thinking_complete'
                      };
                      
                      console.log(`[Agent事件] 添加历史记录:`, historyRecord);
                      
                      const existingHistory = a.thinkingHistory || [];
                      
                      return { 
                        ...a, 
                        status: 'complete' as const,
                        score,
                        stance,
                        currentMessage: displayMessage,
                        messageTimestamp: Date.now(),
                        streamingMessage: undefined,
                        thinkingHistory: [...existingHistory, historyRecord]
                      };
                    }
                    return a;
                  });
                  console.log(`[Agent事件] 更新后的agents:`, updated.find(a => a.id === personaId));
                  console.log(`[Agent事件] thinkingHistory:`, updated.find(a => a.id === personaId)?.thinkingHistory);
                  next.set(optId, updated);
                  return next;
                });
              }
              
              // 观察其他Agent
              if (eventType === 'observation') {
                const observedCount = event.observed_count as number || 0;
                const observedPersonas = event.observed_personas as string[] || [];
                
                console.log(`[Agent事件] ${personaName} 观察到${observedCount}个观点`);
                
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => {
                    if (a.id === personaId) {
                      const message = `👀 观察到${observedCount}个观点: ${observedPersonas.join(', ')}`;
                      return { 
                        ...a, 
                        currentMessage: message,
                        messageTimestamp: Date.now(),
                        messageAction: 'viewing'
                      };
                    }
                    return a;
                  }));
                  return next;
                });
                
                // 5秒后清除消息
                setTimeout(() => {
                  setAgentsByOption(prev => {
                    const next = new Map(prev);
                    const agents = next.get(optId) || [];
                    next.set(optId, agents.map(a => 
                      a.id === personaId ? { 
                        ...a, 
                        currentMessage: undefined,
                        messageAction: undefined
                      } : a
                    ));
                    return next;
                  });
                }, 5000);
              }
              
              // 信心度调整
              if (eventType === 'confidence_adjusted') {
                const newConfidence = event.new_confidence as number || 0;
                const adjustment = event.adjustment as number || 0;
                
                console.log(`[Agent事件] ${personaName} 信心度调整: ${adjustment > 0 ? '+' : ''}${(adjustment * 100).toFixed(0)}%`);
                
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => {
                    if (a.id === personaId) {
                      const message = adjustment > 0 
                        ? `✓ 信心增强 (+${(adjustment * 100).toFixed(0)}%)`
                        : `⚠️ 信心降低 (${(adjustment * 100).toFixed(0)}%)`;
                      return { 
                        ...a, 
                        currentMessage: message,
                        messageTimestamp: Date.now(),
                        messageAction: 'score_adjusted'
                      };
                    }
                    return a;
                  }));
                  return next;
                });
                
                // 5秒后清除消息
                setTimeout(() => {
                  setAgentsByOption(prev => {
                    const next = new Map(prev);
                    const agents = next.get(optId) || [];
                    next.set(optId, agents.map(a => 
                      a.id === personaId ? { 
                        ...a, 
                        currentMessage: undefined,
                        messageAction: undefined
                      } : a
                    ));
                    return next;
                  });
                }, 5000);
              }
              
              // Agent完成
              if (eventType === 'agent_complete') {
                const finalScore = event.final_score as number || 0;
                const finalStance = String(event.final_stance || '');
                
                console.log(`[Agent事件] ${personaName} 完成推演: ${finalStance} (${finalScore}分)`);
                
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => 
                    a.id === personaId ? { 
                      ...a, 
                      status: 'complete' as const,
                      score: finalScore,
                      stance: finalStance,
                      currentMessage: `✅ ${finalStance} (${finalScore}分)`
                    } : a
                  ));
                  return next;
                });
              }
            }

            // 批量设置智能体思考状态（并行显示）
            if (type === 'agents_thinking_batch') {
              const optId = String(event.option_id || optionId);
              const agents = event.agents as Array<{agent_id: string, persona_name: string, content: string}>;
              
              if (agents && agents.length > 0) {
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const currentAgents = next.get(optId) || [];
                  next.set(optId, currentAgents.map(a => {
                    const agentInfo = agents.find(ag => ag.agent_id === a.id);
                    if (agentInfo) {
                      return {
                        ...a,
                        status: 'thinking' as const,
                        currentMessage: agentInfo.content,
                        messageTimestamp: Date.now()
                      };
                    }
                    return a;
                  }));
                  return next;
                });
              }
            }

            if (type === 'agent_complete') {
              const agentId = event.agent_id;
              const optId = String(event.option_id || optionId);
              const score = typeof event.score === 'number' ? event.score : undefined;
              
              setAgentsByOption(prev => {
                const next = new Map(prev);
                const agents = next.get(optId) || [];
                next.set(optId, agents.map(a => 
                  a.id === agentId ? { ...a, status: 'complete' as const, score } : a
                ));
                return next;
              });
            }

            // 人格分析 - 更新Agent状态和立场
            if (type === 'persona_analysis') {
              const optId = String(event.option_id || optionId);
              const personaData = event.persona_data as any;
              const personaName = String(event.persona_name || '');
              const personaId = String(event.persona_id || '');
              const content = String(event.content || '');
              
              console.log(`[推演] 收到persona_analysis: ${personaName} (${personaId}), 分数: ${personaData?.score}`);
              
              if (personaData && personaData.score !== undefined) {
                // 先更新agents状态，并在回调中计算总分
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  const updatedAgents = agents.map(a => {
                    if (a.id === personaId) {
                      // 添加到历史记录
                      const historyRecord = {
                        round: personaData.round || 0,
                        message: content,
                        timestamp: Date.now(),
                        score: personaData.score,
                        stance: personaData.stance,
                        keyPoints: personaData.key_points || [],
                        reasoning: personaData.reasoning || '',
                      };
                      
                      const existingHistory = a.thinkingHistory || [];
                      
                      return { 
                        ...a, 
                        status: 'complete' as const, 
                        score: personaData.score,
                        stance: personaData.stance,
                        thinkingHistory: [...existingHistory, historyRecord]
                      };
                    }
                    return a;
                  });
                  next.set(optId, updatedAgents);
                  
                  // 立即计算并更新总分数
                  const completedAgents = updatedAgents.filter(a => a.score !== undefined);
                  console.log(`[推演] ${optId} 已完成agents:`, completedAgents.map(a => `${a.name}:${a.score}`));
                  
                  if (completedAgents.length > 0) {
                    const totalScore = completedAgents.reduce((sum, a) => sum + (a.score || 0), 0) / completedAgents.length;
                    console.log(`[推演] ${optId} 计算总分: ${totalScore.toFixed(1)} (${completedAgents.length}/${updatedAgents.length}个完成)`);
                    
                    // 使用setTimeout确保状态更新在下一个事件循环
                    setTimeout(() => {
                      setTotalScoreByOption(prevScores => {
                        const nextScores = new Map(prevScores);
                        nextScores.set(optId, totalScore);
                        console.log(`[推演] ${optId} 总分已更新到state: ${totalScore.toFixed(1)}`);
                        return nextScores;
                      });
                    }, 0);
                  }
                  
                  return next;
                });
                
                const node: any = {
                  event_id: `${optId}_persona_${personaData.id}`,
                  parent_event_id: `${optId}_start`,
                  month: 1,
                  event: `【${personaName}】${personaData.stance || '分析中'}`,
                  probability: personaData.confidence || 0.5,
                  state_before: {},
                  state_after: {
                    '评分': `${personaData.score || 0}/100`,
                    '立场': personaData.stance || '未知',
                  },
                  impact_vector: {},
                  branch_strategy: option.title,
                  branch_group: optId,
                  risk_tag: personaData.score > 70 ? 'low' : personaData.score > 40 ? 'medium' : 'high',
                  evidence_sources: [],
                  agent_votes: [],
                  impact: (personaData.score || 0) / 100,
                };
                
                setLiveOptions(prev => {
                  const next = new Map(prev);
                  const opt = next.get(optId);
                  if (opt) {
                    const updated = { ...opt, timeline: [...opt.timeline, node as any] };
                    updated.decision_graph = buildFallbackDecisionGraph(optId, opt.title, updated.timeline as any);
                    next.set(optId, updated);
                  }
                  return next;
                });
              }
            }

            // 人格交互 - 记录交互并转换为图谱节点
            if (type === 'persona_interaction') {
              const optId = String(event.option_id || optionId);
              const interactionData = event.interaction_data as any;
              const content = String(event.content || '');
              // 从interactionData中获取action类型
              const action = interactionData ? String(interactionData.action || '') : '';
              
              // 从多个可能的位置获取persona_id
              const fromPersonaId = event.persona_id || 
                                   (interactionData && (interactionData.from_persona_id || interactionData.from_persona));
              
              if (fromPersonaId) {
                // 更新发言Agent的消息气泡，并添加到历史记录
                setAgentsByOption(prev => {
                  const next = new Map(prev);
                  const agents = next.get(optId) || [];
                  next.set(optId, agents.map(a => {
                    if (a.id === fromPersonaId) {
                      // 添加到历史记录
                      const historyRecord = {
                        round: 1, // 交互发生在深度反思阶段
                        message: content || (interactionData && interactionData.content),
                        timestamp: Date.now(),
                        score: undefined,
                        stance: undefined,
                        keyPoints: [],
                        reasoning: '',
                        action: action, // 记录action类型
                      };
                      
                      const existingHistory = a.thinkingHistory || [];
                      
                      // 保留原有的status、score、stance等状态
                      return { 
                        ...a, 
                        currentMessage: content || (interactionData && interactionData.content),
                        messageTimestamp: Date.now(),
                        messageAction: action,
                        thinkingHistory: [...existingHistory, historyRecord]
                      };
                    }
                    return a;
                  }));
                  return next;
                });
                
                // 5秒后清除消息（增加显示时间）
                const timerKey = `${optId}_${fromPersonaId}`;
                setTimeout(() => {
                  setAgentsByOption(prev => {
                    const next = new Map(prev);
                    const agents = next.get(optId) || [];
                    next.set(optId, agents.map(a => 
                      a.id === fromPersonaId ? { 
                        ...a, 
                        currentMessage: undefined,
                        messageAction: undefined
                      } : a
                    ));
                    return next;
                  });
                }, 5000);  // 从3秒增加到5秒
              }
              
              if (interactionData) {
                setInteractionsByOption(prev => {
                  const next = new Map(prev);
                  const interactions = next.get(optId) || [];
                  interactions.push({
                    from: interactionData.from_persona_id || '',
                    to: interactionData.to_persona_id || '',
                    type: interactionData.interaction_type || '讨论',
                    message: String(interactionData.content || '').substring(0, 50) + '...',
                    timestamp: Date.now(),
                  });
                  next.set(optId, interactions);
                  return next;
                });
                
                const node: any = {
                  event_id: `${optId}_interaction_${Date.now()}`,
                  parent_event_id: `${optId}_start`,
                  month: 2,
                  event: `人格交互：${interactionData.from_persona || ''}与${interactionData.to_persona || ''}`,
                  probability: 0.8,
                  state_before: {},
                  state_after: {
                    '交互类型': interactionData.interaction_type || '讨论',
                  },
                  impact_vector: {},
                  branch_strategy: option.title,
                  branch_group: optId,
                  risk_tag: 'medium',
                  evidence_sources: [],
                  agent_votes: [],
                  impact: 0.5,
                };
                
                setLiveOptions(prev => {
                  const next = new Map(prev);
                  const opt = next.get(optId);
                  if (opt) {
                    const updated = { ...opt, timeline: [...opt.timeline, node as any] };
                    updated.decision_graph = buildFallbackDecisionGraph(optId, opt.title, updated.timeline as any);
                    next.set(optId, updated);
                  }
                  return next;
                });
              }
            }

            // 最终评估
            if (type === 'final_evaluation') {
              const optId = String(event.option_id || optionId);
              const evaluationData = event.evaluation_data as any;
              
              if (evaluationData) {
                const node: any = {
                  event_id: `${optId}_final`,
                  parent_event_id: `${optId}_start`,
                  month: 3,
                  event: `综合评估：${evaluationData.recommendation || '完成分析'}`,
                  probability: 1.0,
                  state_before: {},
                  state_after: {
                    '综合评分': `${evaluationData.overall_score || 0}/100`,
                    '风险等级': evaluationData.risk_level || '中等',
                    '执行信心': `${Math.round((evaluationData.execution_confidence || 0) * 100)}%`,
                  },
                  impact_vector: evaluationData.impact_summary || {},
                  branch_strategy: option.title,
                  branch_group: optId,
                  risk_tag: evaluationData.risk_level === '高' ? 'high' : evaluationData.risk_level === '低' ? 'low' : 'medium',
                  evidence_sources: [],
                  agent_votes: [],
                  impact: (evaluationData.overall_score || 0) / 100,
                };
                
                setLiveOptions(prev => {
                  const next = new Map(prev);
                  const opt = next.get(optId);
                  if (opt) {
                    const updated = { ...opt, timeline: [...opt.timeline, node as any] };
                    updated.decision_graph = buildFallbackDecisionGraph(optId, opt.title, updated.timeline as any);
                    next.set(optId, updated);
                  }
                  return next;
                });
              }
            }

            // 选项完成
            if (type === 'option_complete') {
              const optId = String(event.option_id || optionId);
              setLiveOptions(prev => {
                const next = new Map(prev);
                const opt = next.get(optId);
                if (opt) {
                  next.set(optId, {
                    ...opt,
                    final_score: Number(event.final_score) || opt.final_score,
                    risk_level: Number(event.risk_level) || opt.risk_level,
                    execution_confidence: Number(event.execution_confidence) || opt.execution_confidence,
                  });
                }
                return next;
              });
            }

            // 推演完成
            if (type === 'done' || type === 'complete') {
              const optId = String(event.option_id || optionId);
              
              // 标记该选项为已完成
              setCompletedOptions(prev => {
                const next = new Set(prev);
                next.add(optId);
                return next;
              });
              
              completedCount++;
              if (completedCount === config.options?.length) {
                setWsPhase('done');
                setWsStatus('✓ 推演完成！');
              }
            }

            // 错误
            if (type === 'error') {
              setError(`选项 ${index + 1} 错误: ${event.content}`);
            }
          },
          onError(msg) {
            if (cleanupCalled || !isConnectionActive) return;
            setError(`选项 ${index + 1} (${option.title}) 连接错误: ${msg}`);
          },
        },
      );
      
      wsInstances.set(optionId, {
        close: () => {
          console.log(`[推演] 关闭选项 ${index + 1} 的WebSocket连接`);
          isConnectionActive = false; // 设置连接为非活动
          
          // 在关闭前发送停止信号给后端
          if (socket && socket.readyState === WebSocket.OPEN) {
            try {
              socket.send(JSON.stringify({
                type: 'stop_simulation',
                option_id: optionId,
                session_id: config.sessionId,
              }));
              console.log(`[推演] 已发送停止信号给选项 ${index + 1}`);
            } catch (e) {
              console.error(`[推演] 发送停止信号失败:`, e);
            }
          }
          
          // 延迟关闭，确保停止信号发送成功
          setTimeout(() => {
            wsInstance(); // 调用原始的close函数
            console.log(`[推演] 选项 ${index + 1} WebSocket已关闭`);
          }, 100);
        },
        send: (data: any) => {
          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify(data));
          }
        }
      });
    };
    
    // 初始化：只连接非暂停的选项
    config.options.forEach((option, index) => {
      connectOption(option, index);
    });
    
    wsCloseRef.current = () => {
      wsInstances.forEach(ws => ws.close());
    };
    
    // 监听暂停状态变化，建立或关闭连接
    const handlePauseChange = (optionId: string, isPaused: boolean) => {
      const optionIndex = parseInt(optionId.replace('option_', '')) - 1;
      if (config.options && optionIndex >= 0 && optionIndex < config.options.length) {
        if (isPaused) {
          // 暂停：关闭WebSocket连接
          console.log(`[推演] 暂停选项 ${optionIndex + 1}`);
          const ws = wsInstances.get(optionId);
          if (ws) {
            ws.close();
            wsInstances.delete(optionId);
            console.log(`[推演] 选项 ${optionIndex + 1} 已从实例列表中移除`);
          } else {
            console.log(`[推演] 选项 ${optionIndex + 1} 没有活动的WebSocket连接`);
          }
        } else {
          // 继续：建立WebSocket连接（跳过暂停检查）
          console.log(`[推演] 继续选项 ${optionIndex + 1}`);
          // 先检查是否已经有连接
          if (wsInstances.has(optionId)) {
            console.log(`[推演] 选项 ${optionIndex + 1} 已有活动连接，跳过`);
            return;
          }
          connectOption(config.options[optionIndex], optionIndex, true);
        }
      }
    };
    
    // 将处理函数保存到ref，供按钮使用
    (window as any).__handlePauseChange = handlePauseChange;
    
    return () => {
      console.log('[推演] useEffect清理函数执行');
      cleanupCalled = true;
      if (wsCloseRef.current) {
        wsCloseRef.current();
      }
    };
  }, [config.sessionId, config.userId, config.question, config.options, config.collectedInfo, config.decisionType]);

  // 同步liveOptions到record
  useEffect(() => {
    if (!config.options) return;
    
    if (liveOptions.size > 0) {
      const opts = Array.from(liveOptions.values());
      const optionsWithGraphs = opts.map(opt => ({
        ...opt,
        decision_graph: opt.timeline.length > 0 
          ? buildFallbackDecisionGraph(opt.option_id, opt.title, opt.timeline as any)
          : null,
      }));
      
      setRecord({
        simulation_id: `live_${Date.now()}`,
        user_id: config.userId,
        question: config.question,
        options_count: opts.length,
        recommendation: '',
        options: optionsWithGraphs,
        created_at: new Date().toISOString(),
      });
    } else if (wsPhase !== 'idle' && !record) {
      const initialOptions = config.options.map((opt, idx) => ({
        option_id: `option_${idx + 1}`,
        title: opt.title,
        description: opt.description || '',
        timeline: [],
        decision_graph: null,
        final_score: 0,
        risk_level: 0,
        execution_confidence: 0,
        dropout_risk_month: null,
        personal_note: '',
      }));
      
      setRecord({
        simulation_id: `live_${Date.now()}`,
        user_id: config.userId,
        question: config.question,
        options_count: config.options.length,
        recommendation: '',
        options: initialOptions,
        created_at: new Date().toISOString(),
      });
    }
    // 移除 record 从依赖数组，避免无限循环
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveOptions, config.userId, config.question, config.options, wsPhase]);

  // 计算当前选中的选项
  const activeOption: DecisionOption | null = record?.options[selectedOptionIndex] || null;

  // 渲染保护 - 只要有智能体数据就可以渲染
  const canRenderPersonas = useMemo(() => {
    if (!activeOption) return false;
    const currentOptionId = activeOption.option_id;
    const personas = agentsByOption.get(currentOptionId);
    return personas && personas.length > 0;
  }, [activeOption, agentsByOption]);

  return (
    <div style={{ 
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.03) 0%, rgba(107, 72, 255, 0.02) 100%), #FFFFFF',
      overflow: 'hidden', display: 'flex', flexDirection: 'column' 
    }}>
      <style>{styles}</style>
      
      {/* 顶部导航栏 */}
      <div style={{ 
        position: 'relative', zIndex: 100, display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
        gap: 20, padding: '14px 24px',
        background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(20px)', 
        borderBottom: '1px solid rgba(0, 0, 0, 0.06)', 
        boxShadow: '0 4px 24px rgba(0, 0, 0, 0.04)' 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button onClick={() => navigate('/emergence-dashboard')} style={{ 
            background: 'rgba(10, 89, 247, 0.06)', border: 'none', borderRadius: 12, 
            padding: '10px 16px', color: '#0A59F7', cursor: 'pointer', fontSize: 14, fontWeight: 600,
            display: 'flex', alignItems: 'center', gap: 6,
            transition: 'all 0.3s ease',
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            返回
          </button>
          
          <button onClick={() => setShowRoundsConfig(true)} style={{ 
            background: 'rgba(107, 72, 255, 0.06)', border: 'none', borderRadius: 12, 
            padding: '10px 16px', color: '#6B48FF', cursor: 'pointer', fontSize: 14, fontWeight: 600,
            display: 'flex', alignItems: 'center', gap: 6,
            transition: 'all 0.3s ease',
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m0 6l4.2 4.2M23 12h-6m-6 0H1m18.2 5.2l-4.2-4.2m0-6l4.2-4.2"/>
            </svg>
            Agent轮数配置
          </button>
          
          <div style={{ borderLeft: '1px solid rgba(0, 0, 0, 0.08)', paddingLeft: 16 }}>
            <div style={{ fontSize: 11, color: '#999', marginBottom: 4 }}>决策图谱舞台</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#1A1A1A' }}>{config.question}</div>
          </div>
          
          {config.options && config.options.length > 1 && (
            <div style={{ 
              display: 'flex', gap: 8, alignItems: 'center',
              borderLeft: '1px solid rgba(0, 0, 0, 0.08)', paddingLeft: 16 
            }}>
              <div style={{ fontSize: 11, color: '#999', marginRight: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                {wsPhase === 'running' && (
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#34C759', animation: 'pulse 2s infinite' }} />
                )}
                {wsPhase === 'running' ? '并行推演中' : '查看选项'}:
              </div>
              {config.options.map((option, idx) => {
                const isActive = idx === selectedOptionIndex;
                const color = '#475569'; // 统一深灰蓝色
                const liveOption = Array.from(liveOptions.values())[idx];
                const nodeCount = liveOption?.timeline?.length || 0;
                const optionId = `option_${idx + 1}`;
                const isPaused = pausedOptions.has(optionId);
                const isRunning = wsPhase === 'running' && nodeCount > 0 && !isPaused;
                
                return (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <button
                      onClick={() => setSelectedOptionIndex(idx)}
                      style={{
                        background: isActive 
                          ? `radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.85) 30%, rgba(255, 255, 255, 0.6) 70%), linear-gradient(135deg, #E8F4FF 0%, #B8DCFF 100%)`
                          : 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 252, 255, 0.9) 100%)',
                        border: isActive ? '1.5px solid rgba(184, 220, 255, 0.6)' : '1px solid rgba(184, 220, 255, 0.3)',
                        borderRadius: 12,
                        padding: '10px 18px',
                        color: isActive ? 'rgba(0, 0, 0, 0.85)' : 'rgba(0, 0, 0, 0.7)',
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: 600,
                        transition: 'all 0.3s ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        position: 'relative',
                        boxShadow: isActive 
                          ? '0 4px 16px rgba(10, 89, 247, 0.15), 0 2px 8px rgba(10, 89, 247, 0.1), inset 0 1px 2px rgba(255, 255, 255, 0.9)'
                          : '0 2px 8px rgba(10, 89, 247, 0.08), inset 0 1px 2px rgba(255, 255, 255, 0.8)',
                        backdropFilter: 'blur(20px)',
                        WebkitBackdropFilter: 'blur(20px)',
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.transform = 'scale(1.05)';
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(10, 89, 247, 0.12), inset 0 1px 2px rgba(255, 255, 255, 0.9)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) {
                          e.currentTarget.style.transform = 'scale(1)';
                          e.currentTarget.style.boxShadow = '0 2px 8px rgba(10, 89, 247, 0.08), inset 0 1px 2px rgba(255, 255, 255, 0.8)';
                        }
                      }}
                    >
                      {isRunning && (
                        <div style={{
                          position: 'absolute', top: -4, right: -4,
                          width: 12, height: 12, borderRadius: '50%',
                          background: '#34C759', border: '2px solid #fff',
                          boxShadow: '0 0 8px rgba(52, 199, 89, 0.6)',
                          animation: 'pulse 2s infinite',
                        }} />
                      )}
                      <div style={{ 
                        width: 8, 
                        height: 8, 
                        borderRadius: '50%', 
                        background: isActive 
                          ? 'linear-gradient(135deg, rgba(10, 89, 247, 0.8), rgba(107, 72, 255, 0.6))'
                          : 'rgba(10, 89, 247, 0.3)',
                        boxShadow: isActive ? '0 0 8px rgba(10, 89, 247, 0.4)' : 'none',
                      }} />
                      <span>{option.title}</span>
                      {nodeCount > 0 && (
                        <span style={{ 
                          fontSize: 11, 
                          opacity: isActive ? 0.8 : 0.6, 
                          marginLeft: 2, 
                          fontWeight: 700,
                          color: isActive ? 'rgba(10, 89, 247, 0.8)' : 'rgba(0, 0, 0, 0.5)',
                        }}>
                          {nodeCount}节点
                        </span>
                      )}
                    </button>
                    
                    {/* 暂停/继续按钮 */}
                    {wsPhase === 'running' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (isPaused) {
                            // 继续推演
                            setPausedOptions(prev => {
                              const next = new Set(prev);
                              next.delete(optionId);
                              return next;
                            });
                            setActiveOptionId(optionId);
                            // 发送继续消息到后端
                            if ((window as any).__handlePauseChange) {
                              (window as any).__handlePauseChange(optionId, false);
                            }
                          } else {
                            // 暂停推演
                            setPausedOptions(prev => new Set(prev).add(optionId));
                            if (activeOptionId === optionId) {
                              setActiveOptionId(null);
                            }
                            // 发送暂停消息到后端
                            if ((window as any).__handlePauseChange) {
                              (window as any).__handlePauseChange(optionId, true);
                            }
                          }
                        }}
                        style={{
                          background: isPaused 
                            ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 252, 255, 0.9) 100%)'
                            : 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 252, 255, 0.9) 100%)',
                          border: '1px solid rgba(184, 220, 255, 0.4)',
                          borderRadius: 10,
                          padding: '8px 14px',
                          color: isPaused ? 'rgba(52, 199, 89, 0.9)' : 'rgba(10, 89, 247, 0.8)',
                          cursor: 'pointer',
                          fontSize: 12,
                          fontWeight: 600,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          transition: 'all 0.2s ease',
                          boxShadow: '0 2px 8px rgba(10, 89, 247, 0.08), inset 0 1px 2px rgba(255, 255, 255, 0.8)',
                          backdropFilter: 'blur(20px)',
                          WebkitBackdropFilter: 'blur(20px)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'scale(1.05)';
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(10, 89, 247, 0.12), inset 0 1px 2px rgba(255, 255, 255, 0.9)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'scale(1)';
                          e.currentTarget.style.boxShadow = '0 2px 8px rgba(10, 89, 247, 0.08), inset 0 1px 2px rgba(255, 255, 255, 0.8)';
                        }}
                        title={isPaused ? '继续推演' : '暂停推演'}
                      >
                        {isPaused ? (
                          <>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M8 5v14l11-7z"/>
                            </svg>
                            <span>继续</span>
                          </>
                        ) : (
                          <>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                            </svg>
                            <span>暂停</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 主内容区域 */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {wsPhase === 'done' && canRenderPersonas && (
          <div style={{
            position: 'absolute', 
            top: 80, 
            right: 24, 
            zIndex: 9999,
            background: 'radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.85) 30%, rgba(255, 255, 255, 0.6) 70%), linear-gradient(135deg, rgba(232, 244, 255, 0.95) 0%, rgba(184, 220, 255, 0.9) 100%)',
            color: 'rgba(0, 0, 0, 0.85)', 
            padding: '12px 24px', 
            borderRadius: 12,
            border: '1.5px solid rgba(184, 220, 255, 0.6)',
            boxShadow: '0 4px 16px rgba(10, 89, 247, 0.15), 0 2px 8px rgba(10, 89, 247, 0.1), inset 0 1px 2px rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            display: 'flex', 
            alignItems: 'center', 
            gap: 10,
            fontSize: 13, 
            fontWeight: 600,
            pointerEvents: 'none',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(52, 199, 89, 0.9)" strokeWidth="2.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <span>分析完成</span>
          </div>
        )}
        
        {canRenderPersonas ? (
          <PersonaInteractionView
            personas={(() => {
              if (activeOption) {
                const currentOptionId = activeOption.option_id;
                return agentsByOption.get(currentOptionId) || [];
              }
              return [];
            })()}
            interactions={(() => {
              if (activeOption) {
                const currentOptionId = activeOption.option_id;
                return interactionsByOption.get(currentOptionId) || [];
              }
              return [];
            })()}
            optionTitle={activeOption?.title || ''}
            currentMonth={(() => {
              if (activeOption) {
                const currentOptionId = activeOption.option_id;
                return currentMonthByOption.get(currentOptionId);
              }
              return undefined;
            })()}
            isComplete={(() => {
              if (activeOption) {
                const currentOptionId = activeOption.option_id;
                return completedOptions.has(currentOptionId);
              }
              return false;
            })()}
            totalScore={(() => {
              if (activeOption) {
                const currentOptionId = activeOption.option_id;
                return totalScoreByOption.get(currentOptionId) || 0;
              }
              return 0;
            })()}
          />
        ) : wsPhase === 'connecting' ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                width: 48, height: 48, border: '3px solid #e2e8f0', borderTopColor: '#3b82f6',
                borderRadius: '50%', margin: '0 auto 16px', animation: 'spin 1s linear infinite',
              }} />
              <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 8 }}>{wsStatus || '正在连接服务器'}</div>
              <div style={{ fontSize: 14, color: '#64748b' }}>等待推演引擎启动...</div>
            </div>
          </div>
        ) : wsPhase === 'running' ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: 32 }}>
            <div style={{ width: 48, height: 48, border: '3px solid #e2e8f0', borderTopColor: '#3b82f6', borderRadius: '50%', marginBottom: 24, animation: 'spin 1s linear infinite' }} />
            <div style={{ fontSize: 18, fontWeight: 600, color: '#1e293b', marginBottom: 12, textAlign: 'center' }}>7个数字生命智能体正在分析中</div>
            <div style={{ fontSize: 14, color: '#3b82f6', textAlign: 'center', maxWidth: 400, lineHeight: 1.6, padding: '16px 24px', background: '#f8fafc', borderRadius: 12, border: '1px solid #e2e8f0' }}>
              {wsStatus || '等待服务器响应...'}
            </div>
            {liveOptions.size > 0 && (
              <div style={{ marginTop: 16, fontSize: 13, color: '#64748b' }}>
                已收到 {Array.from(liveOptions.values()).reduce((sum, opt) => sum + (opt.timeline?.length || 0), 0)} 条分析数据
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ width: 100, height: 100, borderRadius: '50%', margin: '0 auto 24px', background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.06), rgba(107, 72, 255, 0.04))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="1.5">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
              </div>
              <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8, color: '#1A1A1A' }}>未找到推演</div>
              <div style={{ fontSize: 14, color: '#666', marginBottom: 24 }}>这条记录可能已经丢失或尚未生成</div>
              <button onClick={() => navigate('/decision')} style={{ background: 'linear-gradient(135deg, #0A59F7, #6B48FF)', border: 'none', borderRadius: 14, padding: '14px 28px', color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer', transition: 'all 0.3s ease' }}>
                返回决策中心
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{ 
          position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)', 
          background: 'rgba(255, 255, 255, 0.98)', backdropFilter: 'blur(20px)', 
          border: '1px solid rgba(255, 59, 48, 0.2)', borderRadius: 16, 
          padding: '14px 24px', color: '#FF3B30', fontSize: 14, fontWeight: 600, 
          boxShadow: '0 12px 40px rgba(255, 59, 48, 0.15)', zIndex: 200,
          display: 'flex', alignItems: 'center', gap: 10
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {error}
        </div>
      )}
      
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
            <h2 style={{ margin: '0 0 24px 0', fontSize: 24, fontWeight: 700 }}>
              Agent推演轮数配置
            </h2>
            <p style={{ margin: '0 0 24px 0', color: '#666', fontSize: 14 }}>
              为每个决策人格Agent设置推演轮数（1-5轮）。轮数越多，思考越深入，但耗时也越长。
            </p>
            
            <div style={{ display: 'grid', gap: 16 }}>
              {[
                { id: 'rational_analyst', name: '理性分析师', icon: '📊' },
                { id: 'adventurer', name: '冒险家', icon: '🚀' },
                { id: 'pragmatist', name: '实用主义者', icon: '⚙️' },
                { id: 'idealist', name: '理想主义者', icon: '✨' },
                { id: 'conservative', name: '保守派', icon: '🛡️' },
                { id: 'social_navigator', name: '社交导向者', icon: '🤝' },
                { id: 'innovator', name: '创新者', icon: '💡' },
              ].map(({ id, name, icon }) => (
                <div key={id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: 16, background: '#F8FAFC', borderRadius: 12,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 24 }}>{icon}</span>
                    <span style={{ fontSize: 15, fontWeight: 600 }}>{name}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <button
                      onClick={() => setPersonaRounds(prev => ({
                        ...prev,
                        [id]: Math.max(1, prev[id] - 1)
                      }))}
                      style={{
                        width: 32, height: 32, borderRadius: 8,
                        border: '1px solid #E2E8F0', background: 'white',
                        cursor: 'pointer', fontSize: 18, color: '#64748B',
                      }}
                    >−</button>
                    <span style={{
                      width: 40, textAlign: 'center',
                      fontSize: 16, fontWeight: 600,
                    }}>{personaRounds[id]}轮</span>
                    <button
                      onClick={() => setPersonaRounds(prev => ({
                        ...prev,
                        [id]: Math.min(5, prev[id] + 1)
                      }))}
                      style={{
                        width: 32, height: 32, borderRadius: 8,
                        border: '1px solid #E2E8F0', background: 'white',
                        cursor: 'pointer', fontSize: 18, color: '#64748B',
                      }}
                    >+</button>
                  </div>
                </div>
              ))}
            </div>
            
            <div style={{ marginTop: 24, display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowRoundsConfig(false)}
                style={{
                  padding: '12px 24px', borderRadius: 12,
                  border: '1px solid #E2E8F0', background: 'white',
                  cursor: 'pointer', fontSize: 15, fontWeight: 600,
                  color: '#64748B',
                }}
              >取消</button>
              <button
                onClick={() => {
                  setShowRoundsConfig(false);
                  // 配置已保存到state，下次推演时会使用
                }}
                style={{
                  padding: '12px 24px', borderRadius: 12,
                  border: 'none', background: 'linear-gradient(135deg, #6B48FF 0%, #8B5CF6 100%)',
                  cursor: 'pointer', fontSize: 15, fontWeight: 600,
                  color: 'white', boxShadow: '0 4px 12px rgba(107, 72, 255, 0.3)',
                }}
              >确定</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
