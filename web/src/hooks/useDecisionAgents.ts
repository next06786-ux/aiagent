/**
 * 决策Agent状态管理Hook
 * 
 * 管理多个Agent的4阶段推演状态
 */

import { useCallback, useState } from 'react';
import type {
  AgentState,
  DecisionEvent,
  PhaseType,
  RoundProgress,
} from '../types/decision-events';

export function useDecisionAgents() {
  const [agents, setAgents] = useState<Map<string, AgentState>>(new Map());
  const [roundProgress, setRoundProgress] = useState<Map<string, RoundProgress[]>>(new Map());

  // 初始化Agent
  const initializeAgents = useCallback((agentList: Array<{ id: string; name: string; rounds: number }>) => {
    const newAgents = new Map<string, AgentState>();
    
    agentList.forEach(agent => {
      newAgents.set(agent.id, {
        id: agent.id,
        name: agent.name,
        status: 'waiting',
        currentRound: 0,
        totalRounds: agent.rounds,
        currentPhase: null,
        history: [],
      });
    });
    
    setAgents(newAgents);
  }, []);

  // 处理WebSocket事件
  const handleEvent = useCallback((event: DecisionEvent) => {
    const type = event.type;
    
    // Agent开始
    if (type === 'agent_start') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (agent) {
          next.set(event.persona_id, {
            ...agent,
            status: 'waiting',
            totalRounds: event.rounds,
          });
        }
        return next;
      });
    }
    
    // 轮次开始
    else if (type === 'round_start') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (agent) {
          next.set(event.persona_id, {
            ...agent,
            currentRound: event.round,
            currentPhase: null,
          });
        }
        return next;
      });
      
      // 初始化轮次进度
      setRoundProgress(prev => {
        const next = new Map(prev);
        const agentRounds = next.get(event.persona_id) || [];
        
        if (!agentRounds.find(r => r.round === event.round)) {
          agentRounds.push({
            round: event.round,
            phases: [
              { phase: 'independent_thinking', status: 'pending' },
              { phase: 'observe_others', status: 'pending' },
              { phase: 'deep_reflection', status: 'pending' },
              { phase: 'decision', status: 'pending' },
            ],
            startTime: event.timestamp,
          });
          next.set(event.persona_id, agentRounds);
        }
        
        return next;
      });
    }
    
    // 阶段开始
    else if (type === 'phase_start') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (agent) {
          // 根据阶段设置状态
          let status: AgentState['status'] = 'thinking';
          if (event.phase === 'observe_others') status = 'observing';
          else if (event.phase === 'deep_reflection') status = 'reflecting';
          else if (event.phase === 'decision') status = 'deciding';
          
          next.set(event.persona_id, {
            ...agent,
            status,
            currentPhase: event.phase,
          });
        }
        return next;
      });
      
      // 更新阶段进度
      setRoundProgress(prev => {
        const next = new Map(prev);
        const agentRounds = next.get(event.persona_id) || [];
        const currentRound = agentRounds.find(r => r.round === event.round);
        
        if (currentRound) {
          const phaseIndex = currentRound.phases.findIndex(p => p.phase === event.phase);
          if (phaseIndex !== -1) {
            currentRound.phases[phaseIndex] = {
              ...currentRound.phases[phaseIndex],
              status: 'active',
              startTime: event.timestamp,
            };
          }
          next.set(event.persona_id, agentRounds);
        }
        
        return next;
      });
    }
    
    // 阶段完成
    else if (type === 'phase_complete') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (!agent) return next;
        
        const updatedAgent = { ...agent };
        
        // 根据阶段类型更新数据
        if (event.phase === 'independent_thinking') {
          updatedAgent.currentThinking = event.result;
          updatedAgent.history.push({
            round: event.round,
            phase: 'independent_thinking',
            timestamp: event.timestamp,
            data: event.result,
          });
        } else if (event.phase === 'observe_others') {
          updatedAgent.currentObservation = {
            observed_count: event.observed_count,
            observed_personas: event.observed_personas,
          };
          updatedAgent.history.push({
            round: event.round,
            phase: 'observe_others',
            timestamp: event.timestamp,
            data: { observed_count: event.observed_count, observed_personas: event.observed_personas },
          });
        } else if (event.phase === 'deep_reflection') {
          updatedAgent.currentReflection = event.result;
          updatedAgent.history.push({
            round: event.round,
            phase: 'deep_reflection',
            timestamp: event.timestamp,
            data: event.result,
          });
        } else if (event.phase === 'decision') {
          updatedAgent.currentDecision = event.decision;
          updatedAgent.history.push({
            round: event.round,
            phase: 'decision',
            timestamp: event.timestamp,
            data: event.decision,
          });
        }
        
        next.set(event.persona_id, updatedAgent);
        return next;
      });
      
      // 更新阶段进度
      setRoundProgress(prev => {
        const next = new Map(prev);
        const agentRounds = next.get(event.persona_id) || [];
        const currentRound = agentRounds.find(r => r.round === event.round);
        
        if (currentRound) {
          const phaseIndex = currentRound.phases.findIndex(p => p.phase === event.phase);
          if (phaseIndex !== -1) {
            const phase = currentRound.phases[phaseIndex];
            currentRound.phases[phaseIndex] = {
              ...phase,
              status: 'complete',
              endTime: event.timestamp,
              duration: phase.startTime ? event.timestamp - phase.startTime : undefined,
            };
          }
          next.set(event.persona_id, agentRounds);
        }
        
        return next;
      });
    }
    
    // 轮次完成
    else if (type === 'round_complete') {
      setRoundProgress(prev => {
        const next = new Map(prev);
        const agentRounds = next.get(event.persona_id) || [];
        const currentRound = agentRounds.find(r => r.round === event.round);
        
        if (currentRound) {
          currentRound.endTime = event.timestamp;
          currentRound.duration = event.duration;
          next.set(event.persona_id, agentRounds);
        }
        
        return next;
      });
    }
    
    // Agent完成
    else if (type === 'agent_complete') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (agent) {
          next.set(event.persona_id, {
            ...agent,
            status: 'complete',
            finalScore: event.final_score,
            finalStance: event.final_stance,
            finalConfidence: event.final_confidence,
          });
        }
        return next;
      });
    }
    
    // 流式推理
    else if (type === 'reasoning_stream') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (agent) {
          next.set(event.persona_id, {
            ...agent,
            streamingReasoning: event.accumulated,
          });
        }
        return next;
      });
    }
    
    // 流式推理完成
    else if (type === 'reasoning_stream_complete') {
      setAgents(prev => {
        const next = new Map(prev);
        const agent = next.get(event.persona_id);
        if (agent) {
          next.set(event.persona_id, {
            ...agent,
            streamingReasoning: undefined,
          });
        }
        return next;
      });
    }
  }, []);

  // 获取Agent状态
  const getAgent = useCallback((agentId: string) => {
    return agents.get(agentId);
  }, [agents]);

  // 获取所有Agent
  const getAllAgents = useCallback(() => {
    return Array.from(agents.values());
  }, [agents]);

  // 获取Agent的轮次进度
  const getAgentRoundProgress = useCallback((agentId: string) => {
    return roundProgress.get(agentId) || [];
  }, [roundProgress]);

  // 重置状态
  const reset = useCallback(() => {
    setAgents(new Map());
    setRoundProgress(new Map());
  }, []);

  return {
    agents: getAllAgents(),
    initializeAgents,
    handleEvent,
    getAgent,
    getAgentRoundProgress,
    reset,
  };
}
