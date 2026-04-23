import React, { useEffect, useState, useRef } from 'react';
import { PersonaAvatar } from './PersonaAvatar';
import './PersonaInteractionView.css';

interface Persona {
  id: string;
  name: string;
  status: 'waiting' | 'thinking' | 'complete' | 'error';
  score?: number;
  stance?: string;
  color?: string;
  currentMessage?: string;  // 当前显示的消息
  messageTimestamp?: number;  // 消息时间戳
  messageAction?: string;  // 消息的action类型
  thinkingHistory?: Array<{  // 历史思考记录
    round: number;
    message: string;
    timestamp: number;
    score?: number;
    stance?: string;
    keyPoints?: string[];
    reasoning?: string;
    action?: string;  // 交互类型（viewing, stance_changed等）
    skillResult?: {  // 技能执行结果
      skill_name: string;
      summary: string;
      full_result?: any;
    };
  }>;
}

interface Interaction {
  from: string;
  to: string;
  type: string;
  message: string;
  timestamp: number;
}

interface PersonaInteractionViewProps {
  personas: Persona[];
  interactions: Interaction[];
  optionTitle: string;
  currentMonth?: number;
  isComplete?: boolean;
  totalScore?: number;  // 总分数
}

export function PersonaInteractionView({
  personas,
  interactions,
  optionTitle,
  currentMonth = 0,
  isComplete = false,
  totalScore = 0,
}: PersonaInteractionViewProps) {
  const [activeInteraction, setActiveInteraction] = useState<Interaction | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);  // 改为存储完整的persona对象
  
  // 🔍 调试：打印接收到的personas数据
  useEffect(() => {
    console.log(`[PersonaInteractionView] 🔍 personas数量: ${personas.length}`);
    personas.forEach((p, i) => {
      console.log(`[PersonaInteractionView] 🔍 persona[${i}]:`, {
        id: p.id,
        name: p.name,
        status: p.status,
        score: p.score,
        stance: p.stance,
        currentMessage: p.currentMessage,
        hasCurrentMessage: !!p.currentMessage
      });
    });
  }, [personas]);
  
  // 缩放和平移状态
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  
  // 观察连线动画状态
  const [observationLines, setObservationLines] = useState<Array<{
    id: string;
    from: string;  // 观察者 persona id
    to: string[];  // 被观察者 persona ids
    timestamp: number;
  }>>([]);
  
  // 监听 personas 的 thinkingHistory，检测 observe_others 事件
  useEffect(() => {
    personas.forEach(persona => {
      const history = persona.thinkingHistory || [];
      const latestObserve = history
        .filter(h => h.event_type === 'phase_complete' && (h as any).phase === 'observe_others')
        .sort((a, b) => b.timestamp - a.timestamp)[0];
      
      if (latestObserve) {
        const observedPersonas = (latestObserve as any).observed_personas || [];
        const observedIds = observedPersonas.map((p: any) => p.id);
        
        // 检查是否已经有这个观察关系的动画
        const hasAnimation = observationLines.some(
          line => line.from === persona.id && line.timestamp === latestObserve.timestamp
        );
        
        if (!hasAnimation && observedIds.length > 0) {
          const lineId = `${persona.id}_${latestObserve.timestamp}`;
          console.log(`[连线动画] ${persona.name} 观察 ${observedIds.length} 个Agent`);
          
          setObservationLines(prev => [...prev, {
            id: lineId,
            from: persona.id,
            to: observedIds,
            timestamp: latestObserve.timestamp,
          }]);
          
          // 2.5秒后移除连线
          setTimeout(() => {
            setObservationLines(prev => prev.filter(l => l.id !== lineId));
          }, 2500);
        }
      }
    });
  }, [personas]);
  
  // 分数影响动画状态
  const [scoreImpactAnimations, setScoreImpactAnimations] = useState<Array<{
    id: string;
    personaId: string;
    score: number;  // 分数值
    timestamp: number;
  }>>([]);
  
  // 监听personas的score变化，触发动画
  useEffect(() => {
    personas.forEach(persona => {
      if (persona.score !== undefined && persona.status === 'thinking') {
        // 检查是否已经有这个persona的动画
        const hasAnimation = scoreImpactAnimations.some(anim => anim.personaId === persona.id);
        if (!hasAnimation) {
          const animId = `${persona.id}_${Date.now()}`;
          console.log(`[动画] 触发分数影响动画: ${persona.name} (${persona.score}分)`);
          setScoreImpactAnimations(prev => [...prev, {
            id: animId,
            personaId: persona.id,
            score: persona.score,
            timestamp: Date.now(),
          }]);
          
          // 2秒后移除动画
          setTimeout(() => {
            setScoreImpactAnimations(prev => prev.filter(a => a.id !== animId));
          }, 2000);
        }
      }
    });
  }, [personas]);
  
  // 监听totalScore变化
  useEffect(() => {
    console.log(`[分数] 总分更新: ${totalScore.toFixed(1)}`);
  }, [totalScore]);

  // 智能体颜色映射 - 统一深灰蓝色调
  const personaColors: Record<string, string> = {
    'rational_analyst': '#475569',
    'adventurer': '#475569',
    'pragmatist': '#475569',
    'conservative': '#475569',
    'emotional_intuitive': '#475569',
    'social_navigator': '#475569',
    'innovator': '#475569',
  };

  // 如果没有智能体数据，初始化7个默认智能体
  const displayPersonas = personas.length > 0 ? personas : [
    { id: 'rational_analyst', name: '理性分析师', status: 'waiting' as const },
    { id: 'adventurer', name: '冒险家', status: 'waiting' as const },
    { id: 'pragmatist', name: '实用主义者', status: 'waiting' as const },
    { id: 'conservative', name: '保守派', status: 'waiting' as const },
    { id: 'emotional_intuitive', name: '情感直觉者', status: 'waiting' as const },
    { id: 'social_navigator', name: '社交导向者', status: 'waiting' as const },
    { id: 'innovator', name: '创新者', status: 'waiting' as const },
  ];

  // 智能体位置（优化的多层圆形排列）
  const getPersonaPosition = (index: number, total: number) => {
    // 根据智能体数量动态调整布局
    if (total <= 5) {
      // 5个或更少：单层五边形
      const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
      const radius = 32;
      const x = 50 + radius * Math.cos(angle);
      const y = 50 + radius * Math.sin(angle);
      return { x, y };
    } else if (total <= 7) {
      // 6-7个：单层圆形，稍大半径
      const angle = (index / total) * 2 * Math.PI - Math.PI / 2;
      const radius = 35;
      const x = 50 + radius * Math.cos(angle);
      const y = 50 + radius * Math.sin(angle);
      return { x, y };
    } else {
      // 8个或更多：双层布局
      // 内层：前5个
      // 外层：剩余的
      const innerCount = 5;
      const outerCount = total - innerCount;
      
      if (index < innerCount) {
        // 内层
        const angle = (index / innerCount) * 2 * Math.PI - Math.PI / 2;
        const radius = 25;
        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);
        return { x, y };
      } else {
        // 外层
        const outerIndex = index - innerCount;
        const angle = (outerIndex / outerCount) * 2 * Math.PI - Math.PI / 2 + (Math.PI / outerCount); // 错开角度
        const radius = 40;
        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);
        return { x, y };
      }
    }
  };

  // 显示最新的交互
  useEffect(() => {
    if (interactions.length > 0) {
      const latest = interactions[interactions.length - 1];
      setActiveInteraction(latest);
      
      // 3秒后清除
      const timer = setTimeout(() => {
        setActiveInteraction(null);
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [interactions]);
  
  // 处理鼠标滚轮缩放
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.min(Math.max(0.5, scale * delta), 2);
      
      setScale(newScale);
    };
    
    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [scale]);
  
  // 处理鼠标拖拽平移
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) { // 左键
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  };
  
  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };
  
  const handleMouseUp = () => {
    setIsDragging(false);
  };
  
  // 重置视图
  const handleResetView = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  return (
    <div 
      ref={containerRef}
      className="persona-interaction-view"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
    >
      {/* 缩放控制按钮 */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: 20,
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: 12,
        padding: 8,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      }}>
        <button
          onClick={() => setScale(Math.min(scale * 1.2, 2))}
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            border: '1px solid #e2e8f0',
            background: 'white',
            cursor: 'pointer',
            fontSize: 18,
            fontWeight: 600,
            color: '#0A59F7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}
          title="放大"
        >
          +
        </button>
        <button
          onClick={() => setScale(Math.max(scale * 0.8, 0.5))}
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            border: '1px solid #e2e8f0',
            background: 'white',
            cursor: 'pointer',
            fontSize: 18,
            fontWeight: 600,
            color: '#0A59F7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}
          title="缩小"
        >
          −
        </button>
        <button
          onClick={handleResetView}
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            border: '1px solid #e2e8f0',
            background: 'white',
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 600,
            color: '#0A59F7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}
          title="重置视图"
        >
          ⟲
        </button>
        <div style={{
          fontSize: 11,
          color: '#64748b',
          textAlign: 'center',
          marginTop: 4,
          fontWeight: 600,
        }}>
          {Math.round(scale * 100)}%
        </div>
      </div>
      
      {/* 可缩放的内容容器 */}
      <div style={{
        transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
        transformOrigin: 'center center',
        transition: isDragging ? 'none' : 'transform 0.2s ease',
        width: '100%',
        height: '100%',
        position: 'relative',
      }}>
      {/* 中心选项 */}
      <div 
        className={`center-option ${scoreImpactAnimations.length > 0 ? 'score-impact-center' : ''}`}
        style={{
          transition: 'all 0.3s ease-out',
        }}
      >
        <div className="option-title">{optionTitle}</div>
        {currentMonth > 0 && (
          <div className="option-month">第 {currentMonth} 轮</div>
        )}
        {/* 总分数显示 */}
        <div style={{
          position: 'relative',
          zIndex: 2,
          marginTop: 8,
          fontSize: 36,
          fontWeight: 700,
          background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0.75) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textAlign: 'center',
          lineHeight: 1,
          textShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        }}>
          {totalScore.toFixed(1)}
        </div>
        <div style={{
          position: 'relative',
          zIndex: 2,
          fontSize: 11,
          color: 'rgba(0, 0, 0, 0.55)',
          textAlign: 'center',
          marginTop: 6,
          fontWeight: 600,
          letterSpacing: '0.5px',
        }}>
          综合评分
        </div>
      </div>

      {/* 分数影响动画 - 从persona到中心的实线 + 粒子效果 */}
      {scoreImpactAnimations.map(anim => {
        const personaIndex = displayPersonas.findIndex(p => p.id === anim.personaId);
        if (personaIndex === -1) return null;
        
        const personaPos = getPersonaPosition(personaIndex, displayPersonas.length);
        const centerPos = { x: 50, y: 50 };
        const color = personaColors[anim.personaId] || '#999';
        const score = anim.score;
        const isPositive = score >= 0;
        
        // 生成粒子
        const particles = Array.from({ length: 8 }, (_, i) => {
          const angle = (i / 8) * Math.PI * 2;
          const distance = 30 + Math.random() * 20;
          return {
            id: `${anim.id}-particle-${i}`,
            tx: Math.cos(angle) * distance,
            ty: Math.sin(angle) * distance,
            delay: i * 0.05,
          };
        });
        
        return (
          <React.Fragment key={anim.id}>
            {/* 连线动画 */}
            <svg 
              className="score-impact-line"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 15,
              }}
            >
              <defs>
                <linearGradient id={`gradient-${anim.id}`} x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={color} stopOpacity="0" />
                  <stop offset="50%" stopColor={color} stopOpacity="1" />
                  <stop offset="100%" stopColor={color} stopOpacity="0" />
                </linearGradient>
              </defs>
              <line
                x1={`${personaPos.x}%`}
                y1={`${personaPos.y}%`}
                x2={`${centerPos.x}%`}
                y2={`${centerPos.y}%`}
                stroke={`url(#gradient-${anim.id})`}
                strokeWidth="3"
                style={{
                  animation: 'scoreImpactPulse 2s ease-out',
                }}
              />
              {/* 移动的光点 */}
              <circle
                r="5"
                fill={color}
                filter="url(#glow)"
                style={{
                  animation: 'scoreImpactMove 1.5s ease-out',
                  animationFillMode: 'forwards',
                }}
              >
                <animateMotion
                  dur="1.5s"
                  path={`M ${personaPos.x},${personaPos.y} L ${centerPos.x},${centerPos.y}`}
                  fill="freeze"
                />
              </circle>
              <defs>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
            </svg>
            
            {/* 粒子效果 - 从中心向外扩散 */}
            {particles.map(particle => (
              <div
                key={particle.id}
                className="score-particle"
                style={{
                  left: '50%',
                  top: '50%',
                  backgroundColor: color,
                  '--tx': `${particle.tx}px`,
                  '--ty': `${particle.ty}px`,
                  animationDelay: `${particle.delay}s`,
                  zIndex: 18,
                } as React.CSSProperties}
              />
            ))}
            
            {/* 分数变化显示 */}
            <div
              className={`score-number-indicator ${isPositive ? 'positive' : 'negative'}`}
              style={{
                zIndex: 20,
              }}
            >
              {isPositive ? '+' : ''}{score.toFixed(1)}
            </div>
          </React.Fragment>
        );
      })}

      {/* 智能体节点 */}
      {displayPersonas.map((persona, index) => {
        const pos = getPersonaPosition(index, displayPersonas.length);
        const color = personaColors[persona.id] || '#999';
        const isActive = activeInteraction && 
          (activeInteraction.from === persona.id || activeInteraction.to === persona.id);

        // 计算相对于中心的角度，用于确定外侧方向
        const centerX = 50;
        const centerY = 50;
        const angle = Math.atan2(pos.y - centerY, pos.x - centerX);
        const isTop = pos.y < centerY;
        const isBottom = pos.y > centerY;
        const isLeft = pos.x < centerX;
        const isRight = pos.x > centerX;
        
        // 根据位置决定元素的放置方向
        // 上方：放在球体上方
        // 下方：放在球体下方
        // 左右：根据角度微调
        const labelPosition = isTop ? 'top' : 'bottom';

        return (
          <div
            key={persona.id}
            className={`persona-node ${persona.status} ${isActive ? 'active' : ''}`}
            style={{
              left: `${pos.x}%`,
              top: `${pos.y}%`,
            }}
          >
            {/* 智能体球体 */}
            <div 
              className="persona-avatar"
              style={{ 
                background: `
                  radial-gradient(circle at 50% 30%, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.85) 30%, rgba(255, 255, 255, 0.6) 70%),
                  linear-gradient(135deg, #E8F4FF 0%, #B8DCFF 100%)
                `
              }}
            >
              {/* 人格图标 - 居中 */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
              }}>
                <PersonaAvatar personaId={persona.id} size={110} />
              </div>
            </div>
            
            {/* 智能体名称 - 根据位置动态放置 */}
            <div 
              className="persona-name-external"
              style={{
                [labelPosition]: labelPosition === 'top' ? '-28px' : '-28px',
              }}
            >
              {persona.name}
            </div>
            
            {/* 状态指示器 */}
            {persona.status === 'thinking' && (
              <div style={{
                position: 'absolute',
                [labelPosition]: labelPosition === 'top' ? '-55px' : '-55px',
                left: '50%',
                transform: 'translateX(-50%)',
                fontSize: 9,
                color: 'rgba(0, 0, 0, 0.5)',
                fontWeight: 600,
                whiteSpace: 'nowrap',
                background: 'rgba(255, 255, 255, 0.95)',
                padding: '3px 10px',
                borderRadius: 10,
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(0, 0, 0, 0.08)',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.06)',
              }}>
                思考中...
              </div>
            )}

            {/* 评分显示 - 只要有分数就显示 */}
            {persona.score !== undefined && (
              <div 
                className="persona-score" 
                style={{ 
                  borderColor: color,
                  [labelPosition]: labelPosition === 'top' ? '-68px' : '-68px',
                }}
              >
                {persona.score}
                <div className="score-label">分</div>
              </div>
            )}

            {/* 立场标签 - 显示在球体外侧 */}
            {persona.stance && (
              <div 
                className={`persona-stance ${persona.stance.includes('支持') ? 'support' : persona.stance.includes('反对') ? 'oppose' : 'neutral'}`}
                style={{ 
                  [labelPosition]: labelPosition === 'top' ? '-110px' : '-110px',
                }}
              >
                {persona.stance}
              </div>
            )}

            {/* 查看历史按钮 - 只要有历史记录就显示 */}
            {persona.thinkingHistory && persona.thinkingHistory.length > 0 && (
              <button
                className="view-history-btn"
                style={{
                  right: '-50px',
                  top: '50%',
                  left: 'auto',
                  transform: 'translateY(-50%)',
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPersona(persona);
                }}
                title="查看思考历程"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </button>
            )}
          </div>
        );
      })}

      {/* 消息气泡 - 独立渲染，不在节点内部 */}
      {displayPersonas.map((persona, index) => {
        // 🆕 如果没有currentMessage但有score和stance，自动生成消息
        let displayMessage = persona.currentMessage;
        if (!displayMessage && persona.score !== undefined && persona.stance) {
          displayMessage = `${persona.stance} (${persona.score}分)`;
          console.log(`[消息气泡] 自动生成消息: ${persona.name} - ${displayMessage}`);
        }
        
        // 🔍 调试：打印每个persona的消息状态
        console.log(`[消息气泡] ${persona.name}:`, {
          hasCurrentMessage: !!persona.currentMessage,
          currentMessage: persona.currentMessage,
          displayMessage: displayMessage,
          score: persona.score,
          stance: persona.stance,
          status: persona.status
        });
        
        if (!displayMessage) {
          console.log(`[消息气泡] 跳过渲染: ${persona.name} - 无消息`);
          return null;
        }

        const pos = getPersonaPosition(index, displayPersonas.length);
        const color = personaColors[persona.id] || '#999';
        
        // 计算气泡应该在外侧的位置（相对于中心，使用百分比）
        const angle = (index / displayPersonas.length) * 2 * Math.PI - Math.PI / 2;
        // 气泡距离中心的距离（百分比，比Agent节点更远，避免遮挡）
        const bubbleRadius = 52; // Agent在35%半径，气泡在52%半径，确保不遮挡
        const bubbleX = 50 + bubbleRadius * Math.cos(angle);
        const bubbleY = 50 + bubbleRadius * Math.sin(angle);
        
        // 检测是否是立场改变的消息
        const isStanceChange = displayMessage.includes('[立场已改变]') || displayMessage.includes('改变了立场');
        
        // 根据action类型添加CSS类
        const actionClass = persona.messageAction ? `action-${persona.messageAction}` : '';
        
        // 智能截断消息：如果太长则显示前150个字符
        const maxLength = 150;
        const shortMessage = displayMessage.length > maxLength 
          ? displayMessage.substring(0, maxLength) + '...' 
          : displayMessage;
        
        return (
          <div 
            key={`bubble-${persona.id}`}
            className={`persona-message-bubble ${isStanceChange ? 'stance-changed' : ''} ${actionClass}`}
            style={{ 
              borderColor: isStanceChange ? '#f59e0b' : color,
              backgroundColor: isStanceChange ? 'rgba(245, 158, 11, 0.1)' : undefined,
              position: 'absolute',
              left: `${bubbleX}%`,
              top: `${bubbleY}%`,
              transform: 'translate(-50%, -50%)',  // 居中对齐
              zIndex: 5,  // 低于Agent节点(10)，避免遮挡
              animation: isStanceChange ? 'pulse 1s ease-in-out 3' : undefined,
            }}
            onClick={(e) => {
              e.stopPropagation();
              setSelectedPersona(persona);  // 打开历史记录弹窗
            }}
          >
            {isStanceChange && (
              <div style={{
                position: 'absolute',
                top: -8,
                right: -8,
                width: 20,
                height: 20,
                borderRadius: '50%',
                background: '#f59e0b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 12,
                fontWeight: 'bold',
                color: 'white',
                animation: 'bounce 0.5s ease-in-out 3'
              }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
              </div>
            )}
            <div className="message-content">
              {shortMessage}
            </div>
            <div className="message-more">详细 →</div>
          </div>
        );
      })}

      {/* 观察连线动画 */}
      {observationLines.map(line => {
        const fromIndex = displayPersonas.findIndex(p => p.id === line.from);
        if (fromIndex === -1) return null;
        
        const fromPos = getPersonaPosition(fromIndex, displayPersonas.length);
        const fromColor = personaColors[line.from] || '#999';
        
        return line.to.map(toId => {
          const toIndex = displayPersonas.findIndex(p => p.id === toId);
          if (toIndex === -1) return null;
          
          const toPos = getPersonaPosition(toIndex, displayPersonas.length);
          
          return (
            <svg
              key={`observe-line-${line.id}-${toId}`}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 3,
              }}
            >
              <defs>
                <linearGradient id={`gradient-${line.id}-${toId}`} x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={fromColor} stopOpacity="0.8" />
                  <stop offset="100%" stopColor={fromColor} stopOpacity="0.2" />
                </linearGradient>
              </defs>
              <line
                x1={`${fromPos.x}%`}
                y1={`${fromPos.y}%`}
                x2={`${toPos.x}%`}
                y2={`${toPos.y}%`}
                stroke={`url(#gradient-${line.id}-${toId})`}
                strokeWidth="2"
                strokeDasharray="8,4"
                className="observation-line"
                style={{
                  animation: 'observation-line-flow 2.5s ease-out forwards',
                }}
              />
              {/* 箭头 */}
              <circle
                cx={`${toPos.x}%`}
                cy={`${toPos.y}%`}
                r="4"
                fill={fromColor}
                className="observation-arrow"
                style={{
                  animation: 'observation-arrow-pulse 2.5s ease-out forwards',
                }}
              />
            </svg>
          );
        });
      })}

      {/* 交互连线和对话 */}
      {activeInteraction && (() => {
        const fromIndex = displayPersonas.findIndex(p => p.id === activeInteraction.from);
        const toIndex = displayPersonas.findIndex(p => p.id === activeInteraction.to);
        
        if (fromIndex === -1 || toIndex === -1) return null;
        
        const fromPos = getPersonaPosition(fromIndex, displayPersonas.length);
        const toPos = getPersonaPosition(toIndex, displayPersonas.length);
        
        return (
          <>
            {/* 连线 */}
            <svg className="interaction-line">
              <line
                x1={`${fromPos.x}%`}
                y1={`${fromPos.y}%`}
                x2={`${toPos.x}%`}
                y2={`${toPos.y}%`}
                stroke={personaColors[activeInteraction.from] || '#999'}
                strokeWidth="2"
                strokeDasharray="5,5"
                className="animated-line"
              />
            </svg>

            {/* 对话气泡 */}
            <div
              className="interaction-bubble"
              style={{
                left: `${(fromPos.x + toPos.x) / 2}%`,
                top: `${(fromPos.y + toPos.y) / 2}%`,
              }}
            >
              <div className="bubble-type">{activeInteraction.type}</div>
              <div className="bubble-message">{activeInteraction.message}</div>
            </div>
          </>
        );
      })()}

      {/* 完成状态 - 显示在右上角顶部边缘 */}
      {isComplete && (
        <div style={{
          position: 'absolute',
          top: '5px',
          right: '5px',
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'rgba(255, 255, 255, 0.98)',
          padding: '12px 20px',
          borderRadius: '16px',
          boxShadow: '0 8px 24px rgba(52, 199, 89, 0.2), 0 4px 12px rgba(52, 199, 89, 0.15)',
          border: '2px solid rgba(52, 199, 89, 0.3)',
          animation: 'slideInRight 0.5s ease',
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #34C759, #30D158)',
            color: 'white',
            fontSize: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(52, 199, 89, 0.3)',
          }}>
            ✓
          </div>
          <div style={{
            fontSize: '16px',
            fontWeight: 700,
            color: '#34C759',
          }}>
            分析完成
          </div>
        </div>
      )}

      {/* Agent历史思考记录模态框 */}
      {selectedPersona && (
        <div 
          className="message-modal-overlay"
          onClick={() => setSelectedPersona(null)}
          onWheel={(e) => e.stopPropagation()}
        >
          <div 
            className="message-modal history-modal"
            onClick={(e) => e.stopPropagation()}
            onWheel={(e) => e.stopPropagation()}
          >
            <div className="message-modal-header">
              <h3>【{selectedPersona.name}】的思考历程</h3>
              <button 
                className="message-modal-close"
                onClick={() => setSelectedPersona(null)}
              >
                ✕
              </button>
            </div>
            <div className="message-modal-content history-content">
              {/* 当前状态 */}
              <div className="history-current-state">
                <div className="state-label">当前状态</div>
                <div className="state-info">
                  {selectedPersona.stance && (
                    <span className={`stance-badge ${selectedPersona.stance.includes('支持') ? 'support' : selectedPersona.stance.includes('反对') ? 'oppose' : 'neutral'}`}>
                      {selectedPersona.stance}
                    </span>
                  )}
                  {selectedPersona.score !== undefined && (
                    <span className="score-badge">{selectedPersona.score}分</span>
                  )}
                </div>
                {selectedPersona.currentMessage && (
                  <div className="current-message">
                    {selectedPersona.currentMessage}
                  </div>
                )}
              </div>

              {/* 历史思考记录 */}
              {selectedPersona.thinkingHistory && selectedPersona.thinkingHistory.length > 0 ? (
                <div className="history-timeline">
                  <div className="timeline-label">思考历程</div>
                  {selectedPersona.thinkingHistory.map((record, index) => (
                    <div key={index} className={`history-record ${record.action ? 'interaction-record' : ''}`}>
                      <div className="record-header">
                        <span className="record-round">第{record.round}轮</span>
                        {record.action && (
                          <span className={`record-action action-${record.action}`}>
                            {record.action === 'viewing' && (
                              <>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                  <circle cx="12" cy="12" r="3"/>
                                </svg>
                                查看观点
                              </>
                            )}
                            {record.action === 'stance_changed' && (
                              <>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                                </svg>
                                立场改变
                              </>
                            )}
                            {record.action === 'score_adjusted' && (
                              <>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: 4 }}>
                                  <line x1="18" y1="20" x2="18" y2="10"/>
                                  <line x1="12" y1="20" x2="12" y2="4"/>
                                  <line x1="6" y1="20" x2="6" y2="14"/>
                                </svg>
                                评分调整
                              </>
                            )}
                            {record.action === 'stance_hold' && '✓ 坚持观点'}
                            {!['viewing', 'stance_changed', 'score_adjusted', 'stance_hold'].includes(record.action) && record.action}
                          </span>
                        )}
                        {record.stance && (
                          <span className={`record-stance ${record.stance.includes('支持') ? 'support' : record.stance.includes('反对') ? 'oppose' : 'neutral'}`}>
                            {record.stance}
                          </span>
                        )}
                        {record.score !== undefined && (
                          <span className="record-score">{record.score}分</span>
                        )}
                      </div>
                      <div className="record-message">{record.message}</div>
                      {record.skillResult && (
                        <div className="record-skill-result">
                          <div className="skill-result-header">
                            <span className="skill-icon">🔧</span>
                            <span className="skill-name">{record.skillResult.skill_name}</span>
                          </div>
                          <div className="skill-result-summary">{record.skillResult.summary}</div>
                        </div>
                      )}
                      {record.keyPoints && record.keyPoints.length > 0 && (
                        <div className="record-points">
                          <div className="points-label">关键论点:</div>
                          <ul>
                            {record.keyPoints.map((point, i) => (
                              <li key={i}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {record.reasoning && (
                        <div className="record-reasoning">
                          <div className="reasoning-label">推理过程:</div>
                          <div>{record.reasoning}</div>
                        </div>
                      )}
                      <div className="record-time">
                        {new Date(record.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-history">
                  <p>暂无历史思考记录</p>
                  <p className="no-history-hint">Agent的思考过程将在推演过程中记录</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      </div> {/* 关闭可缩放的内容容器 */}
    </div>
  );
}
