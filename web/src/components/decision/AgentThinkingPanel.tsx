import React from 'react';
import './AgentThinkingPanel.css';

interface Agent {
  id: string;
  name: string;
  status: 'waiting' | 'thinking' | 'complete' | 'error';
  score?: number;
}

interface AgentThinkingPanelProps {
  agents: Agent[];
  month: number;
  isCommunicating?: boolean;
  communicationMessage?: string;
}

export function AgentThinkingPanel({ 
  agents, 
  month, 
  isCommunicating = false,
  communicationMessage 
}: AgentThinkingPanelProps) {
  const getAgentIcon = (status: string) => {
    switch (status) {
      case 'thinking':
        return '🤔';
      case 'complete':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '🤖';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'thinking':
        return '思考中...';
      case 'complete':
        return '完成';
      case 'error':
        return '失败';
      default:
        return '等待中';
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'thinking':
        return 'agent-thinking';
      case 'complete':
        return 'agent-complete';
      case 'error':
        return 'agent-error';
      default:
        return 'agent-waiting';
    }
  };

  return (
    <div className="agent-thinking-panel">
      <div className="panel-header">
        <span className="month-indicator">第 {month} 月推演中</span>
        <span className="agent-count">{agents.filter(a => a.status === 'complete').length}/{agents.length} 完成</span>
      </div>

      <div className="agents-grid">
        {agents.map((agent) => (
          <div key={agent.id} className={`agent-card ${getStatusClass(agent.status)}`}>
            <div className="agent-icon">{getAgentIcon(agent.status)}</div>
            <div className="agent-info">
              <div className="agent-name">{agent.name}</div>
              <div className="agent-status">{getStatusText(agent.status)}</div>
              {agent.score !== undefined && (
                <div className="agent-score">得分: {agent.score.toFixed(1)}</div>
              )}
            </div>
            {agent.status === 'thinking' && (
              <div className="thinking-animation">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            )}
          </div>
        ))}
      </div>

      {isCommunicating && (
        <div className="communication-indicator">
          <div className="communication-icon">💬</div>
          <div className="communication-text">
            {communicationMessage || 'Agent间正在交换信息...'}
          </div>
          <div className="communication-animation">
            <div className="wave"></div>
            <div className="wave"></div>
            <div className="wave"></div>
          </div>
        </div>
      )}
    </div>
  );
}
