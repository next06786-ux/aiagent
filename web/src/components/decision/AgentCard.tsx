/**
 * Agent卡片组件
 * 
 * 显示Agent的4阶段推演进度
 */

import React, { useState } from 'react';
import type { AgentState, PhaseType, RoundProgress } from '../../types/decision-events';
import './AgentCard.css';

interface AgentCardProps {
  agent: AgentState;
  roundProgress: RoundProgress[];
  onExpand?: (agentId: string, phase: PhaseType, round: number) => void;
}

const PHASE_ICONS: Record<PhaseType, string> = {
  independent_thinking: '🧠',
  observe_others: '👀',
  deep_reflection: '🤔',
  decision: '⚖️',
};

const PHASE_NAMES: Record<PhaseType, string> = {
  independent_thinking: '独立思考',
  observe_others: '查看他人',
  deep_reflection: '深度反思',
  decision: '决策',
};

export function AgentCard({ agent, roundProgress, onExpand }: AgentCardProps) {
  const [expandedRound, setExpandedRound] = useState<number | null>(null);
  const [expandedPhase, setExpandedPhase] = useState<PhaseType | null>(null);

  const currentRound = roundProgress.find(r => r.round === agent.currentRound);

  const handlePhaseClick = (round: number, phase: PhaseType) => {
    if (expandedRound === round && expandedPhase === phase) {
      setExpandedRound(null);
      setExpandedPhase(null);
    } else {
      setExpandedRound(round);
      setExpandedPhase(phase);
      onExpand?.(agent.id, phase, round);
    }
  };

  return (
    <div className={`agent-card agent-card--${agent.status}`}>
      {/* 头部 */}
      <div className="agent-card__header">
        <div className="agent-card__name">{agent.name}</div>
        <div className="agent-card__round">
          第{agent.currentRound}/{agent.totalRounds}轮
        </div>
      </div>

      {/* 当前轮次的4阶段进度 */}
      {currentRound && (
        <div className="agent-card__phases">
          {currentRound.phases.map((phase, index) => (
            <React.Fragment key={phase.phase}>
              <div
                className={`agent-card__phase agent-card__phase--${phase.status}`}
                onClick={() => handlePhaseClick(currentRound.round, phase.phase)}
              >
                <div className="agent-card__phase-icon">
                  {PHASE_ICONS[phase.phase]}
                </div>
                <div className="agent-card__phase-name">
                  {PHASE_NAMES[phase.phase]}
                </div>
                <div className="agent-card__phase-status">
                  {phase.status === 'pending' && '⏳'}
                  {phase.status === 'active' && '🔄'}
                  {phase.status === 'complete' && '✅'}
                </div>
              </div>
              {index < currentRound.phases.length - 1 && (
                <div className="agent-card__phase-arrow">→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      )}

      {/* 当前状态 */}
      <div className="agent-card__status">
        {agent.status === 'waiting' && '⏳ 等待中'}
        {agent.status === 'thinking' && '🧠 独立思考中'}
        {agent.status === 'observing' && '👀 查看他人观点'}
        {agent.status === 'reflecting' && '🤔 深度反思中'}
        {agent.status === 'deciding' && '⚖️ 做出决策'}
        {agent.status === 'complete' && '✅ 完成'}
        {agent.status === 'error' && '❌ 错误'}
      </div>

      {/* 流式推理 */}
      {agent.streamingReasoning && (
        <div className="agent-card__streaming">
          <div className="agent-card__streaming-text">
            {agent.streamingReasoning}
            <span className="agent-card__cursor">|</span>
          </div>
        </div>
      )}

      {/* 当前决策 */}
      {agent.currentDecision && (
        <div className="agent-card__decision">
          <div className="agent-card__decision-stance">
            {agent.currentDecision.stance}
          </div>
          <div className="agent-card__decision-score">
            {agent.currentDecision.score}分
          </div>
          <div className="agent-card__decision-confidence">
            信心: {(agent.currentDecision.confidence * 100).toFixed(0)}%
          </div>
        </div>
      )}

      {/* 展开的阶段详情 */}
      {expandedRound !== null && expandedPhase !== null && (
        <div className="agent-card__detail">
          <PhaseDetail
            agent={agent}
            round={expandedRound}
            phase={expandedPhase}
            onClose={() => {
              setExpandedRound(null);
              setExpandedPhase(null);
            }}
          />
        </div>
      )}

      {/* 最终结果 */}
      {agent.status === 'complete' && agent.finalScore !== undefined && (
        <div className="agent-card__final">
          <div className="agent-card__final-label">最终结果</div>
          <div className="agent-card__final-stance">{agent.finalStance}</div>
          <div className="agent-card__final-score">{agent.finalScore}分</div>
          <div className="agent-card__final-confidence">
            信心: {((agent.finalConfidence || 0) * 100).toFixed(0)}%
          </div>
        </div>
      )}
    </div>
  );
}

// 阶段详情组件
interface PhaseDetailProps {
  agent: AgentState;
  round: number;
  phase: PhaseType;
  onClose: () => void;
}

function PhaseDetail({ agent, round, phase, onClose }: PhaseDetailProps) {
  const historyItem = agent.history.find(
    h => h.round === round && h.phase === phase
  );

  if (!historyItem) {
    return (
      <div className="phase-detail">
        <div className="phase-detail__header">
          <div className="phase-detail__title">
            {PHASE_ICONS[phase]} {PHASE_NAMES[phase]} (第{round}轮)
          </div>
          <button className="phase-detail__close" onClick={onClose}>×</button>
        </div>
        <div className="phase-detail__empty">暂无数据</div>
      </div>
    );
  }

  return (
    <div className="phase-detail">
      <div className="phase-detail__header">
        <div className="phase-detail__title">
          {PHASE_ICONS[phase]} {PHASE_NAMES[phase]} (第{round}轮)
        </div>
        <button className="phase-detail__close" onClick={onClose}>×</button>
      </div>

      <div className="phase-detail__content">
        {/* 独立思考 */}
        {phase === 'independent_thinking' && historyItem.data.stance && (
          <div className="phase-detail__section">
            <div className="phase-detail__label">立场</div>
            <div className="phase-detail__value">{historyItem.data.stance}</div>
            
            <div className="phase-detail__label">评分</div>
            <div className="phase-detail__value">{historyItem.data.score}/100</div>
            
            <div className="phase-detail__label">推理过程</div>
            <div className="phase-detail__reasoning">{historyItem.data.reasoning}</div>
            
            {historyItem.data.key_points && historyItem.data.key_points.length > 0 && (
              <>
                <div className="phase-detail__label">关键要点</div>
                <ul className="phase-detail__points">
                  {historyItem.data.key_points.map((point: string, index: number) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {/* 查看他人观点 */}
        {phase === 'observe_others' && historyItem.data.observed_personas && (
          <div className="phase-detail__section">
            <div className="phase-detail__label">
              观察到{historyItem.data.observed_count}个其他Agent的观点
            </div>
            <div className="phase-detail__observations">
              {historyItem.data.observed_personas.map((persona: any) => (
                <div key={persona.id} className="phase-detail__observation">
                  <div className="phase-detail__observation-name">{persona.name}</div>
                  <div className="phase-detail__observation-stance">{persona.stance}</div>
                  <div className="phase-detail__observation-score">{persona.score}分</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 深度反思 */}
        {phase === 'deep_reflection' && historyItem.data.stance && (
          <div className="phase-detail__section">
            {historyItem.data.stance_changed && (
              <div className="phase-detail__alert">⚠️ 立场已改变</div>
            )}
            
            <div className="phase-detail__label">立场</div>
            <div className="phase-detail__value">{historyItem.data.stance}</div>
            
            <div className="phase-detail__label">评分</div>
            <div className="phase-detail__value">{historyItem.data.score}/100</div>
            
            <div className="phase-detail__label">反思过程</div>
            <div className="phase-detail__reasoning">{historyItem.data.reasoning}</div>
            
            {historyItem.data.key_points && historyItem.data.key_points.length > 0 && (
              <>
                <div className="phase-detail__label">关键要点</div>
                <ul className="phase-detail__points">
                  {historyItem.data.key_points.map((point: string, index: number) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {/* 决策 */}
        {phase === 'decision' && historyItem.data.stance && (
          <div className="phase-detail__section">
            <div className="phase-detail__label">最终立场</div>
            <div className="phase-detail__value">{historyItem.data.stance}</div>
            
            <div className="phase-detail__label">评分</div>
            <div className="phase-detail__value">{historyItem.data.score}/100</div>
            
            <div className="phase-detail__label">信心度</div>
            <div className="phase-detail__value">
              {(historyItem.data.confidence * 100).toFixed(0)}%
            </div>
            
            <div className="phase-detail__label">独立思考摘要</div>
            <div className="phase-detail__summary">{historyItem.data.thinking_summary}</div>
            
            <div className="phase-detail__label">深度反思摘要</div>
            <div className="phase-detail__summary">{historyItem.data.reflection_summary}</div>
            
            {historyItem.data.key_points && historyItem.data.key_points.length > 0 && (
              <>
                <div className="phase-detail__label">关键要点</div>
                <ul className="phase-detail__points">
                  {historyItem.data.key_points.map((point: string, index: number) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
