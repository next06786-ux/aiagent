import { useCallback, useMemo, useEffect, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { DecisionGraph, DecisionGraphNode } from '../../types/api';

//  工具函数 
function netImpact(node: DecisionGraphNode) {
  return Object.values(node.impact_vector || {}).reduce((s, v) => s + v, 0);
}

function nodeAccentColor(node: DecisionGraphNode | undefined, accent: string) {
  if (!node) return accent;
  if (node.risk_tag === 'high') return '#ff6b6b';
  if (node.opportunity_tag === 'high') return '#2fe0a5';
  return accent;
}

function stanceColor(stance: string) {
  if (/support|支持|推荐/i.test(stance)) return '#10b981';
  if (/risk|风险|反对/i.test(stance)) return '#ef4444';
  return '#3b82f6';
}

//  自定义节点：决策事件卡片 
interface DecisionNodeData {
  node: DecisionGraphNode;
  accent: string;
  isOrigin?: boolean;
  compact?: boolean; // 是否使用紧凑模式
  [key: string]: unknown;
}

function DecisionEventNode({ data, selected }: NodeProps) {
  const d = data as DecisionNodeData;
  const { node, accent, isOrigin, compact = true } = d; // 默认使用紧凑模式
  const color = nodeAccentColor(node, accent);
  const net = netImpact(node);
  const prob = Math.round((node.probability || 0) * 100);

  if (isOrigin) {
    return (
      <div style={{
        width: 120, height: 120, borderRadius: '50%',
        background: `radial-gradient(circle at 35% 30%, rgba(255,255,255,0.22), transparent 40%),
                     linear-gradient(135deg, rgba(96,165,250,0.35), rgba(255,255,255,0.95))`,
        border: `2px solid rgba(59,130,246,0.45)`,
        boxShadow: `0 4px 20px rgba(59,130,246,0.2)`,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', gap: 4, color: '#1e40af', textAlign: 'center',
      }}>
        <span style={{ fontSize: 10, opacity: 0.7, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#1e40af' }}>Current</span>
        <strong style={{ fontSize: 13, color: '#1e40af' }}>Decision Core</strong>
        {/* 三个方向的连接点：上、右下、左下 */}
        <Handle type="source" position={Position.Top} id="top" style={{ background: 'rgba(59,130,246,0.6)', border: 'none', width: 8, height: 8, top: 0 }} />
        <Handle type="source" position={Position.Bottom} id="bottom-right" style={{ background: 'rgba(59,130,246,0.6)', border: 'none', width: 8, height: 8, bottom: 10, right: 20 }} />
        <Handle type="source" position={Position.Bottom} id="bottom-left" style={{ background: 'rgba(59,130,246,0.6)', border: 'none', width: 8, height: 8, bottom: 10, left: 20 }} />
      </div>
    );
  }

  // 紧凑模式：只显示小圆点和月份
  if (compact && !selected) {
    return (
      <div style={{
        width: 60, height: 60, borderRadius: '50%',
        background: `radial-gradient(circle at 30% 30%, ${color}33, ${color}11)`,
        border: `2px solid ${color}88`,
        boxShadow: `0 4px 12px ${color}22`,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', color: '#1e40af',
        transition: 'all 0.2s',
        cursor: 'pointer',
      }}>
        {/* 多方向的Handle，支持从任意方向连接 */}
        <Handle type="target" position={Position.Top} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="target" position={Position.Bottom} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="target" position={Position.Left} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="target" position={Position.Right} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="source" position={Position.Top} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="source" position={Position.Bottom} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="source" position={Position.Left} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <Handle type="source" position={Position.Right} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
        <div style={{ fontSize: 10, opacity: 0.6, marginBottom: 2, color: '#1e40af' }}>M</div>
        <div style={{ fontSize: 16, fontWeight: 700, color: '#1e40af' }}>{node.month}</div>
        {node.risk_tag === 'high' && (
          <div style={{ position: 'absolute', top: -4, right: -4, width: 12, height: 12, borderRadius: '50%', background: '#ff6b6b', border: '2px solid #ffffff' }} />
        )}
        {node.opportunity_tag === 'high' && (
          <div style={{ position: 'absolute', top: -4, right: -4, width: 12, height: 12, borderRadius: '50%', background: '#10b981', border: '2px solid #ffffff' }} />
        )}
      </div>
    );
  }

  // 详细模式：选中时显示完整信息
  const conf = Math.round((node.execution_confidence || 0) * 100);
  const votes = node.agent_votes || [];

  return (
    <div style={{
      width: 200, minHeight: 140, padding: '14px 16px',
      borderRadius: 20,
      background: '#ffffff',
      border: `1px solid ${selected ? 'rgba(59,130,246,0.4)' : 'rgba(0,0,0,0.1)'}`,
      boxShadow: selected
        ? `0 0 0 2px ${color}55, 0 8px 24px rgba(59,130,246,0.12)`
        : `0 4px 12px rgba(0,0,0,0.08)`,
      color: '#1e293b', display: 'flex', flexDirection: 'column', gap: 8,
      transition: 'box-shadow 0.2s, border-color 0.2s',
    }}>
      {/* 多方向的Handle，支持从任意方向连接 */}
      <Handle type="target" position={Position.Top} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="target" position={Position.Bottom} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="target" position={Position.Left} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="target" position={Position.Right} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="source" position={Position.Top} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="source" position={Position.Bottom} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="source" position={Position.Left} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
      <Handle type="source" position={Position.Right} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />

      {/* 月份 + 风险标签 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, opacity: 0.6, color: '#64748b' }}>M{node.month}</span>
        {node.risk_tag === 'high' && (
          <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 999, background: 'rgba(239,68,68,0.1)', color: '#dc2626', border: '1px solid rgba(239,68,68,0.2)' }}>高风险</span>
        )}
        {node.opportunity_tag === 'high' && (
          <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 999, background: 'rgba(16,185,129,0.1)', color: '#059669', border: '1px solid rgba(16,185,129,0.2)' }}>机会</span>
        )}
      </div>

      {/* 事件名 */}
      <strong style={{ fontSize: 13, lineHeight: 1.4, color: '#1e293b' }}>{node.event}</strong>

      {/* 概率 + 执行信心 */}
      <div style={{ display: 'flex', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 10, opacity: 0.5, marginBottom: 3, color: '#64748b' }}>概率</div>
          <div style={{ height: 4, borderRadius: 2, background: 'rgba(0,0,0,0.08)', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${prob}%`, background: color, borderRadius: 2, transition: 'width 0.6s ease' }} />
          </div>
          <div style={{ fontSize: 11, marginTop: 2, color }}>{prob}%</div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 10, opacity: 0.5, marginBottom: 3, color: '#64748b' }}>执行</div>
          <div style={{ height: 4, borderRadius: 2, background: 'rgba(0,0,0,0.08)', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${conf}%`, background: '#3b82f6', borderRadius: 2, transition: 'width 0.6s ease' }} />
          </div>
          <div style={{ fontSize: 11, marginTop: 2, color: '#3b82f6' }}>{conf}%</div>
        </div>
      </div>

      {/* Net impact */}
      <div style={{ fontSize: 11, opacity: 0.65, color: '#64748b' }}>
        净影响 <span style={{ color: net >= 0 ? '#059669' : '#dc2626', fontWeight: 700 }}>{net >= 0 ? '+' : ''}{(net * 100).toFixed(0)}</span>
      </div>

      {/* Agent 投票条 */}
      {votes.length > 0 && (
        <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', marginTop: 2 }}>
          {votes.slice(0, 4).map(v => (
            <div key={v.agent_id} title={`${v.agent_name}: ${v.reason}`} style={{
              fontSize: 9, padding: '2px 6px', borderRadius: 999,
              background: `${stanceColor(v.stance)}18`,
              border: `1px solid ${stanceColor(v.stance)}44`,
              color: stanceColor(v.stance),
              whiteSpace: 'nowrap', overflow: 'hidden', maxWidth: 72, textOverflow: 'ellipsis',
            }}>
              {v.agent_name.replace('Agent', '').trim() || v.stance}
            </div>
          ))}
        </div>
      )}

      {/* 分支策略 */}
      {node.branch_strategy && (
        <div style={{ fontSize: 10, opacity: 0.5, borderTop: '1px solid rgba(0,0,0,0.06)', paddingTop: 6, marginTop: 2, color: '#64748b' }}>
          {node.branch_strategy}
        </div>
      )}
    </div>
  );
}

//  自定义节点：5个AI Agent机器人围绕节点
interface MultiAgentBotData extends Record<string, unknown> {
  nodeId: string;
  agents: Array<{
    id: string;
    name: string;
    status: 'waiting' | 'thinking' | 'complete' | 'error';
    score?: number;
  }>;
  isCommunicating: boolean;
  communicationMessage?: string;
}

function MultiAgentBotNode({ data }: NodeProps) {
  const d = data as MultiAgentBotData;
  const { agents, isCommunicating } = d;

  if (!agents || agents.length === 0) return null;

  // 5个Agent的位置（围绕中心节点，呈五角星分布）
  const agentPositions = [
    { angle: -90, x: 0, y: -120 },      // 上
    { angle: -18, x: 114, y: -37 },     // 右上
    { angle: 54, x: 70, y: 97 },        // 右下
    { angle: 126, x: -70, y: 97 },      // 左下
    { angle: 198, x: -114, y: -37 },    // 左上
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'thinking': return '#3b82f6';
      case 'complete': return '#10b981';
      case 'error': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'thinking': return '🤔';
      case 'complete': return '✓';
      case 'error': return '✗';
      default: return '○';
    }
  };

  return (
    <div style={{
      position: 'relative',
      width: 300,
      height: 300,
      pointerEvents: 'none',
    }}>
      {/* 中心点（对齐到节点） */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: isCommunicating ? '#f59e0b' : '#cbd5e1',
        boxShadow: isCommunicating ? '0 0 20px rgba(245, 158, 11, 0.6)' : 'none',
        animation: isCommunicating ? 'pulse 1s ease-in-out infinite' : 'none',
      }} />

      {/* 5个Agent机器人 */}
      {agents.slice(0, 5).map((agent, index) => {
        const pos = agentPositions[index];
        const color = getStatusColor(agent.status);
        const isActive = agent.status === 'thinking' || agent.status === 'complete';

        return (
          <div key={agent.id} style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(-50%, -50%) translate(${pos.x}px, ${pos.y}px)`,
          }}>
            {/* 连接线（虚线触角） */}
            <svg
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                width: Math.abs(pos.x) + 50,
                height: Math.abs(pos.y) + 50,
                pointerEvents: 'none',
                overflow: 'visible',
              }}
            >
              <line
                x1={pos.x > 0 ? 0 : Math.abs(pos.x)}
                y1={pos.y > 0 ? 0 : Math.abs(pos.y)}
                x2={pos.x > 0 ? Math.abs(pos.x) : 0}
                y2={pos.y > 0 ? Math.abs(pos.y) : 0}
                stroke={color}
                strokeWidth="1.5"
                strokeDasharray={isActive ? "5,5" : "2,4"}
                opacity={isActive ? 0.6 : 0.3}
                style={{
                  animation: agent.status === 'thinking' ? 'dash 1s linear infinite' : 'none',
                }}
              />
            </svg>

            {/* 机器人图标 */}
            <div style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${color}44, ${color}22)`,
              border: `3px solid ${color}`,
              boxShadow: isActive ? `0 0 20px ${color}66, 0 4px 12px ${color}33` : `0 2px 8px ${color}22`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              fontWeight: 700,
              color: color,
              animation: agent.status === 'thinking' ? 'float 2s ease-in-out infinite, glow 1.5s ease-in-out infinite' : 'none',
              transition: 'all 0.3s ease',
              position: 'relative',
            }}>
              {/* SVG机器人图标 */}
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2" />
                <circle cx="12" cy="5" r="2" />
                <path d="M12 7v4" />
                <line x1="8" y1="16" x2="8" y2="16" />
                <line x1="16" y1="16" x2="16" y2="16" />
              </svg>
              
              {/* 思考中的波纹效果 */}
              {agent.status === 'thinking' && (
                <>
                  <div style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    borderRadius: '50%',
                    border: `2px solid ${color}`,
                    animation: 'ripple 1.5s ease-out infinite',
                  }} />
                  <div style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    borderRadius: '50%',
                    border: `2px solid ${color}`,
                    animation: 'ripple 1.5s ease-out 0.5s infinite',
                  }} />
                </>
              )}
              
              {/* 状态指示器 */}
              {agent.status === 'complete' && (
                <div style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  width: 16,
                  height: 16,
                  borderRadius: '50%',
                  background: '#10b981',
                  border: '2px solid #ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 10,
                  color: '#ffffff',
                }}>✓</div>
              )}
            </div>

            {/* Agent名称标签 */}
            <div style={{
              position: 'absolute',
              top: 52,
              left: '50%',
              transform: 'translateX(-50%)',
              fontSize: 10,
              fontWeight: 600,
              color: color,
              background: 'rgba(255, 255, 255, 0.98)',
              padding: '3px 8px',
              borderRadius: 6,
              border: `1px solid ${color}44`,
              whiteSpace: 'nowrap',
              boxShadow: '0 2px 6px rgba(0,0,0,0.12)',
            }}>
              {agent.name.replace('Agent', '').trim()}
              {agent.score !== undefined && ` ${agent.score.toFixed(0)}`}
            </div>

            {/* 思考气泡（仅在thinking状态显示） */}
            {agent.status === 'thinking' && (
              <div style={{
                position: 'absolute',
                top: -50,
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(255, 255, 255, 0.98)',
                border: `2px solid ${color}`,
                borderRadius: 12,
                padding: '6px 10px',
                fontSize: 10,
                color: '#1e293b',
                whiteSpace: 'nowrap',
                boxShadow: `0 4px 12px ${color}33`,
                animation: 'fadeInBounce 0.5s ease-out',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <div style={{
                    width: 4,
                    height: 4,
                    borderRadius: '50%',
                    background: color,
                    animation: 'blink 1s ease-in-out infinite',
                  }} />
                  <div style={{
                    width: 4,
                    height: 4,
                    borderRadius: '50%',
                    background: color,
                    animation: 'blink 1s ease-in-out 0.2s infinite',
                  }} />
                  <div style={{
                    width: 4,
                    height: 4,
                    borderRadius: '50%',
                    background: color,
                    animation: 'blink 1s ease-in-out 0.4s infinite',
                  }} />
                  <span style={{ marginLeft: 4, color: color, fontWeight: 600 }}>思考中...</span>
                </div>
                {/* 气泡尾巴 */}
                <div style={{
                  position: 'absolute',
                  bottom: -8,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 0,
                  height: 0,
                  borderLeft: '8px solid transparent',
                  borderRight: '8px solid transparent',
                  borderTop: `8px solid ${color}`,
                }} />
              </div>
            )}
          </div>
        );
      })}

      {/* Agent间通信的连接线动画 */}
      {isCommunicating && agents.length >= 2 && (
        <svg style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          overflow: 'visible',
        }}>
          {/* 绘制Agent之间的通信连接线 */}
          {agents.slice(0, 5).map((agent, i) => {
            const nextIndex = (i + 1) % Math.min(agents.length, 5);
            const pos1 = agentPositions[i];
            const pos2 = agentPositions[nextIndex];
            const centerX = 150;
            const centerY = 150;
            
            return (
              <line
                key={`comm-${i}`}
                x1={centerX + pos1.x}
                y1={centerY + pos1.y}
                x2={centerX + pos2.x}
                y2={centerY + pos2.y}
                stroke="#f59e0b"
                strokeWidth="2"
                strokeDasharray="5,5"
                opacity="0.5"
                style={{
                  animation: 'dash 1s linear infinite',
                }}
              />
            );
          })}
        </svg>
      )}

      {/* 通信动画 */}
      {isCommunicating && (
        <div style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
          width: 200,
          height: 200,
          borderRadius: '50%',
          border: '2px dashed #f59e0b',
          animation: 'rotate 3s linear infinite',
          opacity: 0.4,
        }} />
      )}

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px currentColor66, 0 4px 12px currentColor33; }
          50% { box-shadow: 0 0 30px currentColor88, 0 6px 16px currentColor44; }
        }
        @keyframes pulse {
          0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          50% { transform: translate(-50%, -50%) scale(1.5); opacity: 0.5; }
        }
        @keyframes dash {
          to { stroke-dashoffset: -20; }
        }
        @keyframes rotate {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @keyframes ripple {
          0% { transform: scale(1); opacity: 0.6; }
          100% { transform: scale(2); opacity: 0; }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes fadeInBounce {
          0% { opacity: 0; transform: translateX(-50%) translateY(10px); }
          60% { opacity: 1; transform: translateX(-50%) translateY(-5px); }
          100% { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
      `}</style>
    </div>
  );
}

//  自定义节点：AI机器人指示器（旧版，保留兼容）
interface AgentBotData extends Record<string, unknown> {
  branchName: string;
  color: string;
  thinkingText: string;
  isActive: boolean;
}

function AgentBotNode({ data }: NodeProps) {
  const d = data as AgentBotData;
  const { branchName, color, thinkingText, isActive } = d;

  if (!isActive) return null;

  return (
    <div style={{
      position: 'relative',
      width: 80,
      height: 80,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      animation: 'float 2s ease-in-out infinite',
    }}>
      {/* 机器人图标 */}
      <div style={{
        width: 50,
        height: 50,
        borderRadius: '50%',
        background: `linear-gradient(135deg, ${color}33, ${color}11)`,
        border: `2px solid ${color}`,
        boxShadow: `0 4px 12px ${color}22`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 24,
        animation: 'pulse 1.5s ease-in-out infinite',
      }}>
        AI
      </div>

      {/* 思考气泡 */}
      {thinkingText && (
        <div style={{
          position: 'absolute',
          top: -60,
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#ffffff',
          border: `1px solid ${color}44`,
          borderRadius: 12,
          padding: '8px 12px',
          maxWidth: 200,
          fontSize: 11,
          color: '#1e293b',
          lineHeight: 1.4,
          boxShadow: `0 4px 12px rgba(0,0,0,0.1)`,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {thinkingText}
          <div style={{
            position: 'absolute',
            bottom: -6,
            left: '50%',
            transform: 'translateX(-50%)',
            width: 0,
            height: 0,
            borderLeft: '6px solid transparent',
            borderRight: '6px solid transparent',
            borderTop: `6px solid ${color}44`,
          }} />
        </div>
      )}

      {/* 分支标签 */}
      <div style={{
        marginTop: 4,
        fontSize: 10,
        fontWeight: 600,
        color: color,
        textAlign: 'center',
      }}>
        {branchName}
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
      `}</style>
    </div>
  );
}

const nodeTypes = { decisionEvent: DecisionEventNode, agentBot: AgentBotNode, multiAgentBot: MultiAgentBotNode };

//  布局计算 - 三个分支向不同方向延伸 + 每条路径各自的5个Agent机器人
function buildLayout(
  nodes: DecisionGraphNode[], 
  accent: string, 
  agentProgress?: Map<string, { latestNode: DecisionGraphNode; thinking: string }>,
  agentsByOption?: Map<string, Array<{id: string; name: string; status: string; score?: number}>>,
  isCommunicatingByOption?: Map<string, boolean>,
  currentMonthByOption?: Map<string, number>
) {
  const sorted = [...nodes].sort((a, b) => a.month !== b.month ? a.month - b.month : (a.node_level || 0) - (b.node_level || 0));
  
  // 按分支策略分组
  const branchGroups = new Map<string, DecisionGraphNode[]>();
  sorted.forEach(n => {
    const branch = n.branch_group || n.branch_strategy || 'main';
    if (!branchGroups.has(branch)) {
      branchGroups.set(branch, []);
    }
    branchGroups.get(branch)!.push(n);
  });

  const posMap = new Map<string, { x: number; y: number }>();
  const DISTANCE_STEP = 200; // 每个月的距离步长
  const CENTER_X = 600; // 中心点X坐标（Decision Core）
  const CENTER_Y = 400; // 中心点Y坐标（Decision Core）
  
  // 三个分支的角度：从中心向上、左下、右下延伸（120度均匀分布）
  const branchAngles = [
    -Math.PI / 2,           // -90度（正上方）
    Math.PI / 6,            // 30度（右下方，顺时针120度）
    Math.PI / 2 + Math.PI / 6,  // 150度（左下方，再顺时针120度）
  ];
  
  // 分支颜色
  const branchColors = ['#3b82f6', '#2fe0a5', '#f59e0b'];
  
  const branchNames = Array.from(branchGroups.keys());
  const branchAngleMap = new Map<string, number>();
  const branchColorMap = new Map<string, string>();
  
  branchNames.forEach((branch, index) => {
    branchAngleMap.set(branch, branchAngles[index % branchAngles.length]);
    branchColorMap.set(branch, branchColors[index % branchColors.length]);
  });

  // 为每个分支的节点计算位置
  branchGroups.forEach((branchNodes, branchName) => {
    const angle = branchAngleMap.get(branchName) || 0;
    
    branchNodes.forEach((n, i) => {
      // 基础距离（按月份）
      const distance = n.month * DISTANCE_STEP;
      
      // 根据角度计算X和Y偏移（从中心点出发）
      const x = CENTER_X + distance * Math.cos(angle);
      const y = CENTER_Y + distance * Math.sin(angle);
      
      // 添加轻微的随机波动，让节点不完全在一条直线上
      const wobble = Math.sin(i * 0.8) * 20;
      
      posMap.set(n.event_id, {
        x: x,
        y: y + wobble
      });
    });
  });

  // Origin node - 中心起点（Decision Core）
  const rfNodes: Node[] = [
    {
      id: '__origin__',
      type: 'decisionEvent',
      position: { x: CENTER_X - 60, y: CENTER_Y - 60 }, // 居中放置
      data: { node: {} as DecisionGraphNode, accent, isOrigin: true } as DecisionNodeData,
      draggable: true,
    },
  ];

  // 添加所有节点
  sorted.forEach(n => {
    const pos = posMap.get(n.event_id) || { x: 320, y: Y_CENTER };
    rfNodes.push({
      id: n.event_id,
      type: 'decisionEvent',
      position: { x: pos.x - 30, y: pos.y - 30 }, // 紧凑模式节点更小，调整偏移
      data: { node: n, accent, compact: true } as DecisionNodeData,
      draggable: true,
    });
    
    // 只为当前正在推理的节点添加机器人
    // 根据节点的branch_group找到对应的Agent状态和当前月份
    const branchGroup = n.branch_group || n.branch_strategy || 'main';
    const agents = agentsByOption?.get(branchGroup);
    const isCommunicating = isCommunicatingByOption?.get(branchGroup) || false;
    const currentMonth = currentMonthByOption?.get(branchGroup);
    
    // 只有当节点的月份等于当前月份时，才显示机器人
    const isCurrentNode = currentMonth !== undefined && n.month === currentMonth;
    
    if (agents && agents.length > 0 && isCurrentNode) {
      rfNodes.push({
        id: `agents_${n.event_id}`,
        type: 'multiAgentBot',
        position: { x: pos.x - 150, y: pos.y - 150 }, // 居中对齐
        data: {
          nodeId: n.event_id,
          agents: agents,
          isCommunicating: isCommunicating,
        } as MultiAgentBotData,
        draggable: false,
        selectable: false,
      });
    }
  });

  // 添加机器人指示器节点（旧版，保留兼容）
  if (agentProgress) {
    branchGroups.forEach((branchNodes, branchName) => {
      const progress = agentProgress.get(branchName);
      if (progress && branchNodes.length > 0) {
        const latestNode = branchNodes[branchNodes.length - 1];
        const pos = posMap.get(latestNode.event_id);
        if (pos) {
          const color = branchColorMap.get(branchName) || accent;
          const angle = branchAngleMap.get(branchName) || 0;
          
          // 机器人位置：在最新节点的延伸方向上
          const botDistance = 100;
          const botX = pos.x + botDistance * Math.cos(angle);
          const botY = pos.y + botDistance * Math.sin(angle);
          
          rfNodes.push({
            id: `bot_${branchName}`,
            type: 'agentBot',
            position: { x: botX - 40, y: botY - 40 },
            data: {
              branchName,
              color,
              thinkingText: progress.thinking,
              isActive: true,
            },
            draggable: false,
          });
        }
      }
    });
  }

  return { rfNodes, posMap, sorted, branchGroups };
}

function buildEdges(sorted: DecisionGraphNode[], accent: string, branchGroups?: Map<string, DecisionGraphNode[]>): Edge[] {
  const edges: Edge[] = [];

  // 为每个分支分配颜色
  const branchColors = [
    '#3b82f6', // 蓝色
    '#2fe0a5', // 绿色
    '#f59e0b', // 橙色
    '#ec4899', // 粉色
    '#8b5cf6', // 紫色
  ];
  
  const branchColorMap = new Map<string, string>();
  if (branchGroups) {
    Array.from(branchGroups.keys()).forEach((branch, index) => {
      branchColorMap.set(branch, branchColors[index % branchColors.length]);
    });
  }

  // Origin -> 每个分支的第一个节点（从不同的Handle连接）
  if (branchGroups) {
    const branchHandles = ['top', 'bottom-right', 'bottom-left']; // 对应三个分支的Handle ID
    
    Array.from(branchGroups.entries()).forEach(([branchName, branchNodes], index) => {
      if (branchNodes.length > 0) {
        const firstNode = branchNodes[0];
        const color = branchColorMap.get(branchName) || accent;
        const handleId = branchHandles[index % branchHandles.length];
        
        edges.push({
          id: `origin_${firstNode.event_id}`,
          source: '__origin__',
          sourceHandle: handleId, // 指定从哪个Handle连接
          target: firstNode.event_id,
          animated: true,
          style: { stroke: `${color}88`, strokeWidth: 2 },
          label: branchName !== 'main' ? branchName : undefined,
          labelStyle: { fill: color, fontSize: 11, fontWeight: 600 },
          labelBgStyle: { fill: 'rgba(7,17,31,0.85)', rx: 6 },
        });
      }
    });
  } else {
    // 原有逻辑：连接所有根节点（parent_event_id为null的节点）
    const rootNodes = sorted.filter(n => !n.parent_event_id);
    console.log('[buildEdges] 找到根节点数量:', rootNodes.length, '节点ID:', rootNodes.map(n => n.event_id));
    
    rootNodes.forEach((n, index) => {
      const color = branchColorMap.get(n.branch_group || '') || accent;
      edges.push({
        id: `origin_${n.event_id}`,
        source: '__origin__',
        target: n.event_id,
        animated: true,
        style: { stroke: `${color}88`, strokeWidth: 2 },
      });
      console.log(`[buildEdges] 创建origin边: __origin__ -> ${n.event_id}`);
    });
  }

  // Node -> node（同一分支内的连接）
  const nodesWithParent = sorted.filter(n => n.parent_event_id);
  console.log('[buildEdges] 有parent的节点数量:', nodesWithParent.length);
  
  nodesWithParent.forEach(n => {
    const feasibility = n.probability || 0;  // 改为可行性
    const branch = n.branch_group || n.branch_strategy || 'main';
    const color = branchColorMap.get(branch) || (n.risk_tag === 'high' ? '#ff6b6b' : n.opportunity_tag === 'high' ? '#2fe0a5' : accent);
    
    console.log(`[buildEdges] 创建节点边: ${n.parent_event_id} -> ${n.event_id}`);
    
    edges.push({
      id: `${n.parent_event_id}_${n.event_id}`,
      source: n.parent_event_id!,
      target: n.event_id,
      animated: feasibility > 0.6,
      style: { stroke: `${color}88`, strokeWidth: 1.2 + feasibility * 2.4 },
      label: feasibility > 0.4 ? `${Math.round(feasibility * 100)}` : undefined,
      labelStyle: { fill: color, fontSize: 11, fontWeight: 600 },
      labelBgStyle: { fill: 'rgba(7,17,31,0.85)', rx: 6 },
    });
  });
  
  console.log('[buildEdges] 完成，总边数:', edges.length);

  return edges;
}

//  主组件 
interface DecisionGraphStageProps {
  graph: DecisionGraph | null;
  accent: string;
  selectedNodeId?: string;
  onSelect?: (node: DecisionGraphNode) => void;
  fullscreen?: boolean;
  height?: number;
  agentProgress?: Map<string, { latestNode: DecisionGraphNode; thinking: string }>; // 机器人进度（旧版）
  agentsByOption?: Map<string, Array<{id: string; name: string; status: string; score?: number}>>; // 按option_id分组的Agent状态
  isCommunicatingByOption?: Map<string, boolean>; // 按option_id分组的通信状态
  currentMonthByOption?: Map<string, number>; // 按option_id分组的当前月份
}

export function DecisionGraphStage({ 
  graph, 
  accent, 
  selectedNodeId, 
  onSelect, 
  fullscreen = false, 
  height = 680, 
  agentProgress,
  agentsByOption,
  isCommunicatingByOption,
  currentMonthByOption
}: DecisionGraphStageProps) {
  const { rfNodes: initNodes, sorted, branchGroups } = useMemo(() => {
    if (!graph?.nodes?.length) return { rfNodes: [], sorted: [], branchGroups: undefined };
    console.log('[DecisionGraphStage] 构建布局，节点数量:', graph.nodes.length);
    console.log('[DecisionGraphStage] 节点详情:', graph.nodes.map(n => ({
      event_id: n.event_id,
      parent_event_id: n.parent_event_id,
      month: n.month,
      branch_group: n.branch_group,
    })));
    return buildLayout(graph.nodes, accent, agentProgress, agentsByOption, isCommunicatingByOption, currentMonthByOption);
  }, [graph, accent, agentProgress, agentsByOption, isCommunicatingByOption, currentMonthByOption]);

  const initEdges = useMemo(() => {
    if (!sorted.length) return [];
    console.log('[DecisionGraphStage] 构建边，节点数量:', sorted.length);
    const edges = buildEdges(sorted, accent, branchGroups);
    console.log('[DecisionGraphStage] 边数量:', edges.length);
    console.log('[DecisionGraphStage] 边详情:', edges.map(e => `${e.source} -> ${e.target}`));
    return edges;
  }, [sorted, accent, branchGroups]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initEdges);

  // 当 initNodes 变化时更新（使用简单的长度检查避免频繁更新）
  const prevNodesLengthRef = useRef(0);
  
  useEffect(() => {
    if (initNodes.length !== prevNodesLengthRef.current) {
      console.log('[DecisionGraphStage] 节点数量变化:', prevNodesLengthRef.current, '->', initNodes.length);
      setNodes(initNodes);
      setEdges(initEdges);
      prevNodesLengthRef.current = initNodes.length;
    }
  }, [initNodes.length, initEdges.length, setNodes, setEdges]);

  // 当选中节点变化时，更新节点数据以显示详细信息
  useMemo(() => {
    if (!selectedNodeId) return;
    
    setNodes(currentNodes => 
      currentNodes.map(node => {
        if (node.id === selectedNodeId) {
          // 选中的节点显示详细信息
          return {
            ...node,
            data: { ...node.data, compact: false } as DecisionNodeData,
          };
        } else if ((node.data as DecisionNodeData).compact === false) {
          // 其他之前选中的节点恢复紧凑模式
          return {
            ...node,
            data: { ...node.data, compact: true } as DecisionNodeData,
          };
        }
        return node;
      })
    );
  }, [selectedNodeId, setNodes]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const d = node.data as DecisionNodeData;
    if (d.node && !d.isOrigin) onSelect?.(d.node);
  }, [onSelect]);

  if (!graph?.nodes?.length) {
    return <p style={{ color: 'rgba(147,197,253,0.6)', padding: 24 }}>暂无图谱节点</p>;
  }

  const containerStyle = fullscreen ? {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
    background: '#f8fafc',
  } : {
    width: '100%',
    height,
    borderRadius: 24,
    overflow: 'hidden',
    background: '#f8fafc',
    border: '1px solid rgba(96,146,255,0.18)',
  };

  // 根据节点数量调整fitView参数
  const fitViewOptions = graph.nodes.length === 1 
    ? { padding: 0.4, maxZoom: 1, minZoom: 0.5 }  // 单个节点时限制缩放
    : { padding: 0.18 };

  return (
    <div style={containerStyle}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={fitViewOptions}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        style={{ background: 'transparent' }}
      >
        <Background variant={BackgroundVariant.Dots} gap={28} size={1} color="rgba(0,0,0,0.08)" />
        <Controls style={{ background: 'rgba(255,255,255,0.95)', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 12 }} />
        <MiniMap
          style={{ background: 'rgba(255,255,255,0.95)', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 12 }}
          nodeColor={n => {
            const d = n.data as DecisionNodeData;
            if (d?.isOrigin) return '#4d9eff';
            // multiAgentBot节点没有node属性，使用默认颜色
            if (!d?.node) return accent;
            return nodeAccentColor(d.node, accent);
          }}
          maskColor="rgba(7,17,31,0.6)"
        />
      </ReactFlow>
    </div>
  );
}
