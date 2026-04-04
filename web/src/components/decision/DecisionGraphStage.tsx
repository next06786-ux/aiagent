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

function nodeAccentColor(node: DecisionGraphNode, accent: string) {
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
        <Handle type="source" position={Position.Right} style={{ background: 'rgba(59,130,246,0.6)', border: 'none', width: 8, height: 8 }} />
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
        <Handle type="target" position={Position.Left} style={{ background: `${color}99`, border: 'none', width: 6, height: 6 }} />
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
      <Handle type="target" position={Position.Left} style={{ background: `${color}99`, border: 'none', width: 8, height: 8 }} />
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

//  自定义节点：AI机器人指示器
interface AgentBotData {
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

const nodeTypes = { decisionEvent: DecisionEventNode, agentBot: AgentBotNode };

//  布局计算 - 三个分支向不同方向延伸 + 机器人指示器
function buildLayout(nodes: DecisionGraphNode[], accent: string, agentProgress?: Map<string, { latestNode: DecisionGraphNode; thinking: string }>) {
  const sorted = [...nodes].sort((a, b) => a.month !== b.month ? a.month - b.month : (a.node_level || 0) - (b.node_level || 0));
  
  // 按分支策略分组
  const branchGroups = new Map<string, DecisionGraphNode[]>();
  sorted.forEach(n => {
    const branch = n.branch_strategy || 'main';
    if (!branchGroups.has(branch)) {
      branchGroups.set(branch, []);
    }
    branchGroups.get(branch)!.push(n);
  });

  const posMap = new Map<string, { x: number; y: number }>();
  const X_STEP = 200; // 水平步长（按月份）
  const Y_CENTER = 400; // 中心线Y坐标
  
  // 三个分支的角度：向上30度、水平、向下30度
  const branchAngles = [
    -Math.PI / 6,  // -30度（向上）
    0,              // 0度（水平）
    Math.PI / 6,    // 30度（向下）
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
      const distance = n.month * X_STEP;
      
      // 根据角度计算X和Y偏移
      const x = 320 + distance * Math.cos(angle);
      const y = Y_CENTER + distance * Math.sin(angle);
      
      // 添加轻微的随机波动，让节点不完全在一条直线上
      const wobble = Math.sin(i * 0.8) * 20;
      
      posMap.set(n.event_id, {
        x: x,
        y: y + wobble
      });
    });
  });

  // Origin node - 中心起点
  const rfNodes: Node[] = [
    {
      id: '__origin__',
      type: 'decisionEvent',
      position: { x: 80, y: Y_CENTER - 60 },
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
  });

  // 添加机器人指示器节点
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
            } as AgentBotData,
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

  // Origin -> 每个分支的第一个节点
  if (branchGroups) {
    branchGroups.forEach((branchNodes, branchName) => {
      if (branchNodes.length > 0) {
        const firstNode = branchNodes[0];
        const color = branchColorMap.get(branchName) || accent;
        edges.push({
          id: `origin_${firstNode.event_id}`,
          source: '__origin__',
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
    // 原有逻辑：连接所有根节点
    sorted.filter(n => !n.parent_event_id).forEach(n => {
      edges.push({
        id: `origin_${n.event_id}`,
        source: '__origin__',
        target: n.event_id,
        animated: true,
        style: { stroke: `${accent}88`, strokeWidth: 2 },
      });
    });
  }

  // Node -> node（同一分支内的连接）
  sorted.filter(n => n.parent_event_id).forEach(n => {
    const prob = n.probability || 0;
    const branch = n.branch_strategy || 'main';
    const color = branchColorMap.get(branch) || (n.risk_tag === 'high' ? '#ff6b6b' : n.opportunity_tag === 'high' ? '#2fe0a5' : accent);
    
    edges.push({
      id: `${n.parent_event_id}_${n.event_id}`,
      source: n.parent_event_id!,
      target: n.event_id,
      animated: prob > 0.5,
      style: { stroke: `${color}88`, strokeWidth: 1.2 + prob * 2.4 },
      label: prob > 0.3 ? `${Math.round(prob * 100)}%` : undefined,
      labelStyle: { fill: color, fontSize: 11, fontWeight: 600 },
      labelBgStyle: { fill: 'rgba(7,17,31,0.85)', rx: 6 },
    });
  });

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
  agentProgress?: Map<string, { latestNode: DecisionGraphNode; thinking: string }>; // 机器人进度
}

export function DecisionGraphStage({ graph, accent, selectedNodeId, onSelect, fullscreen = false, height = 680, agentProgress }: DecisionGraphStageProps) {
  const { rfNodes: initNodes, sorted, branchGroups } = useMemo(() => {
    if (!graph?.nodes?.length) return { rfNodes: [], sorted: [], branchGroups: undefined };
    // 暂时不传递 agentProgress，避免复杂度
    return buildLayout(graph.nodes, accent, undefined);
  }, [graph, accent]);

  const initEdges = useMemo(() => {
    if (!sorted.length) return [];
    return buildEdges(sorted, accent, branchGroups);
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
            return nodeAccentColor(d?.node, accent);
          }}
          maskColor="rgba(7,17,31,0.6)"
        />
      </ReactFlow>
    </div>
  );
}
