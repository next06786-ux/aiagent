/**
 * 决策推演WebSocket事件类型定义
 * 
 * 支持完整的4阶段流程：
 * 1. 独立思考 (Independent Thinking)
 * 2. 查看他人观点 (Observe Others)
 * 3. 深度反思 (Deep Reflection)
 * 4. 决策 (Decision)
 */

// 阶段类型
export type PhaseType = 
  | 'independent_thinking'  // 独立思考
  | 'observe_others'        // 查看他人观点
  | 'deep_reflection'       // 深度反思
  | 'decision';             // 决策

// Agent生命周期事件
export interface AgentStartEvent {
  type: 'agent_start';
  persona_id: string;
  persona_name: string;
  rounds: number;
  timestamp: number;
}

export interface AgentCompleteEvent {
  type: 'agent_complete';
  persona_id: string;
  persona_name: string;
  total_rounds: number;
  total_duration: number;
  final_score: number;
  final_stance: string;
  final_confidence: number;
  timestamp: number;
}

// 轮次事件
export interface RoundStartEvent {
  type: 'round_start';
  persona_id: string;
  persona_name: string;
  round: number;
  total_rounds: number;
  timestamp: number;
}

export interface RoundCompleteEvent {
  type: 'round_complete';
  persona_id: string;
  persona_name: string;
  round: number;
  duration: number;
  timestamp: number;
}

// 阶段事件
export interface PhaseStartEvent {
  type: 'phase_start';
  persona_id: string;
  persona_name: string;
  phase: PhaseType;
  phase_name: string;  // 中文名称
  round: number;
  timestamp: number;
}

// 独立思考阶段完成
export interface IndependentThinkingCompleteEvent {
  type: 'phase_complete';
  persona_id: string;
  persona_name: string;
  phase: 'independent_thinking';
  round: number;
  duration: number;
  result: {
    stance: string;
    score: number;
    reasoning: string;
    key_points: string[];
  };
  timestamp: number;
}

// 查看他人观点阶段完成
export interface ObserveOthersCompleteEvent {
  type: 'phase_complete';
  persona_id: string;
  persona_name: string;
  phase: 'observe_others';
  round: number;
  observed_count: number;
  observed_personas: Array<{
    id: string;
    name: string;
    stance: string;
    score: number;
  }>;
  timestamp: number;
}

// 深度反思阶段完成
export interface DeepReflectionCompleteEvent {
  type: 'phase_complete';
  persona_id: string;
  persona_name: string;
  phase: 'deep_reflection';
  round: number;
  duration: number;
  result: {
    stance: string;
    score: number;
    reasoning: string;
    key_points: string[];
    stance_changed: boolean;
  };
  timestamp: number;
}

// 决策阶段完成
export interface DecisionCompleteEvent {
  type: 'phase_complete';
  persona_id: string;
  persona_name: string;
  phase: 'decision';
  round: number;
  decision: {
    stance: string;
    score: number;
    confidence: number;
    reasoning: string;
    key_points: string[];
    round: number;
    thinking_summary: string;
    reflection_summary: string;
  };
  timestamp: number;
}

// 阶段完成事件联合类型
export type PhaseCompleteEvent = 
  | IndependentThinkingCompleteEvent
  | ObserveOthersCompleteEvent
  | DeepReflectionCompleteEvent
  | DecisionCompleteEvent;

// 流式推理事件
export interface ReasoningStreamEvent {
  type: 'reasoning_stream';
  persona_id: string;
  persona_name: string;
  phase: 'independent_thinking' | 'deep_reflection';
  chunk: string;  // 文本片段
  accumulated: string;  // 累积文本
  timestamp: number;
}

export interface ReasoningStreamCompleteEvent {
  type: 'reasoning_stream_complete';
  persona_id: string;
  persona_name: string;
  phase: 'independent_thinking' | 'deep_reflection';
  full_content: string;
  timestamp: number;
}

// 技能执行事件
export interface SkillSelectionEvent {
  type: 'skill_selection';
  persona_id: string;
  persona_name: string;
  selected_skills: string[];
  reason: string;
  phase: PhaseType;
  round: number;
}

export interface SkillStartEvent {
  type: 'skill_start';
  persona_id: string;
  persona_name: string;
  skill_name: string;
  round: number;
}

export interface SkillCompleteEvent {
  type: 'skill_complete';
  persona_id: string;
  persona_name: string;
  skill_name: string;
  summary: string;
  result: any;
  round: number;
}

// 内心独白事件
export interface ThinkingMonologueEvent {
  type: 'thinking_monologue';
  persona_id: string;
  persona_name: string;
  content: string;
  phase: PhaseType;
  round: number;
}

// 所有事件的联合类型
export type DecisionEvent = 
  | AgentStartEvent
  | AgentCompleteEvent
  | RoundStartEvent
  | RoundCompleteEvent
  | PhaseStartEvent
  | PhaseCompleteEvent
  | ReasoningStreamEvent
  | ReasoningStreamCompleteEvent
  | SkillSelectionEvent
  | SkillStartEvent
  | SkillCompleteEvent
  | ThinkingMonologueEvent
  | { type: 'status'; content: string }
  | { type: 'error'; content: string }
  | { type: 'complete'; [key: string]: any };

// Agent状态
export interface AgentState {
  id: string;
  name: string;
  status: 'waiting' | 'thinking' | 'observing' | 'reflecting' | 'deciding' | 'complete' | 'error';
  currentRound: number;
  totalRounds: number;
  currentPhase: PhaseType | null;
  
  // 当前轮次的数据
  currentThinking?: {
    stance: string;
    score: number;
    reasoning: string;
    key_points: string[];
  };
  
  currentObservation?: {
    observed_count: number;
    observed_personas: Array<{
      id: string;
      name: string;
      stance: string;
      score: number;
    }>;
  };
  
  currentReflection?: {
    stance: string;
    score: number;
    reasoning: string;
    key_points: string[];
    stance_changed: boolean;
  };
  
  currentDecision?: {
    stance: string;
    score: number;
    confidence: number;
    reasoning: string;
    key_points: string[];
  };
  
  // 流式推理
  streamingReasoning?: string;
  
  // 历史记录
  history: Array<{
    round: number;
    phase: PhaseType;
    timestamp: number;
    data: any;
  }>;
  
  // 最终结果
  finalScore?: number;
  finalStance?: string;
  finalConfidence?: number;
}

// 阶段进度
export interface PhaseProgress {
  phase: PhaseType;
  status: 'pending' | 'active' | 'complete';
  startTime?: number;
  endTime?: number;
  duration?: number;
}

// 轮次进度
export interface RoundProgress {
  round: number;
  phases: PhaseProgress[];
  startTime?: number;
  endTime?: number;
  duration?: number;
}
