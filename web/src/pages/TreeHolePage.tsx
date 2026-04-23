import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTrendingDecisions, TrendingDecision, getAllTreeHoles, createTreeHole, sendMessage, getTreeHoleMessages } from '../services/treeHoleService';
import '../styles/TreeHolePage.css';

interface TreeHole {
  id: string;
  x: number;
  y: number;
  title: string;
  description: string;
  messageCount: number;
  lastMessage?: string;
  color: string;
}

interface TreeHoleMessage {
  id: string;
  content: string;
  created_at: string;
  likes: number;
  is_anonymous: boolean;
}

export function TreeHolePage() {
  const navigate = useNavigate();
  const [selectedHole, setSelectedHole] = useState<TreeHole | null>(null);
  const [selectedHoleMessages, setSelectedHoleMessages] = useState<TreeHoleMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [newMessageContent, setNewMessageContent] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [hoveredHole, setHoveredHole] = useState<string | null>(null);
  const [trendingDecisions, setTrendingDecisions] = useState<TrendingDecision[]>([]);
  const [loadingTrending, setLoadingTrending] = useState(true);
  const [showTrending, setShowTrending] = useState(true);
  const [treeHoles, setTreeHoles] = useState<TreeHole[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTreeHoleTitle, setNewTreeHoleTitle] = useState('');
  const [newTreeHoleDesc, setNewTreeHoleDesc] = useState('');
  const [timelineOffset, setTimelineOffset] = useState(0);
  const [isDraggingTimeline, setIsDraggingTimeline] = useState(false);
  const [dragStartX, setDragStartX] = useState(0);
  const [dragStartOffset, setDragStartOffset] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // 树洞颜色配置
  const treeHoleColors = ['#E8F4FF', '#D4EBFF', '#C2E3FF', '#B0D9FF', '#F0F7FF'];
  
  // 根据时间线位置计算树洞的x坐标（横向流动布局）
  const calculateTreeHolePosition = (index: number, total: number) => {
    const baseX = 15 + (index * 18); // 每个树洞间隔18%
    const x = baseX - timelineOffset;
    
    // y坐标使用正弦波形成流动效果
    const wave = Math.sin(index * 0.8) * 15;
    const y = 50 + wave;
    
    return { x, y };
  };

  // 时间线拖动处理
  const handleTimelineMouseDown = (e: React.MouseEvent) => {
    setIsDraggingTimeline(true);
    setDragStartX(e.clientX);
    setDragStartOffset(timelineOffset);
  };

  const handleTimelineMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingTimeline) return;
    
    const deltaX = e.clientX - dragStartX;
    const timelineWidth = timelineRef.current?.offsetWidth || 1000;
    const maxOffset = Math.max(0, treeHoles.length * 18 - 70); // 最大偏移量
    
    // 将像素移动转换为百分比偏移
    const offsetChange = (deltaX / timelineWidth) * 100;
    const newOffset = Math.max(0, Math.min(maxOffset, dragStartOffset - offsetChange));
    
    setTimelineOffset(newOffset);
  };

  const handleTimelineMouseUp = () => {
    setIsDraggingTimeline(false);
  };

  // 全局鼠标事件监听
  useEffect(() => {
    if (isDraggingTimeline) {
      const handleGlobalMouseMove = (e: MouseEvent) => {
        const deltaX = e.clientX - dragStartX;
        const timelineWidth = timelineRef.current?.offsetWidth || 1000;
        const maxOffset = Math.max(0, treeHoles.length * 18 - 70);
        
        const offsetChange = (deltaX / timelineWidth) * 100;
        const newOffset = Math.max(0, Math.min(maxOffset, dragStartOffset - offsetChange));
        
        setTimelineOffset(newOffset);
      };

      const handleGlobalMouseUp = () => {
        setIsDraggingTimeline(false);
      };

      window.addEventListener('mousemove', handleGlobalMouseMove);
      window.addEventListener('mouseup', handleGlobalMouseUp);

      return () => {
        window.removeEventListener('mousemove', handleGlobalMouseMove);
        window.removeEventListener('mouseup', handleGlobalMouseUp);
      };
    }
  }, [isDraggingTimeline, dragStartX, dragStartOffset, treeHoles.length]);

  // 滚轮控制时间线
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      // 检查是否在地图区域内滚动
      const target = e.target as HTMLElement;
      if (target.closest('.tree-hole-map-container')) {
        e.preventDefault();
        
        const maxOffset = Math.max(0, treeHoles.length * 18 - 70);
        const scrollSpeed = 2; // 滚动速度
        const newOffset = Math.max(0, Math.min(maxOffset, timelineOffset + e.deltaY * scrollSpeed * 0.05));
        
        setTimelineOffset(newOffset);
      }
    };

    window.addEventListener('wheel', handleWheel, { passive: false });
    return () => window.removeEventListener('wheel', handleWheel);
  }, [timelineOffset, treeHoles.length]);

  // 加载树洞数据（公共空间，显示所有树洞）
  useEffect(() => {
    const loadTreeHoles = async () => {
      try {
        setLoading(true);
        const holes = await getAllTreeHoles();
        
        console.log('获取到的树洞数据:', holes);
        
        // 按创建时间排序（最新的在右边）
        const sortedHoles = [...holes].sort((a, b) => {
          const timeA = new Date(a.created_at || 0).getTime();
          const timeB = new Date(b.created_at || 0).getTime();
          return timeA - timeB;
        });
        
        // 将后端数据映射到前端格式
        const mappedHoles = sortedHoles.map((hole, index) => {
          return {
            id: hole.id,
            title: hole.title,
            description: hole.description,
            messageCount: hole.message_count,
            x: 0, // 初始值，会在下面更新
            y: 0,
            color: treeHoleColors[index % treeHoleColors.length],
            createdAt: hole.created_at,
          };
        });
        
        setTreeHoles(mappedHoles);
      } catch (error) {
        console.error('加载树洞失败:', error);
        setTreeHoles([]);
      } finally {
        setLoading(false);
      }
    };
    
    loadTreeHoles();
  }, []);

  // 根据时间线偏移量更新树洞位置
  useEffect(() => {
    setTreeHoles(prevHoles => 
      prevHoles.map((hole, index) => {
        const pos = calculateTreeHolePosition(index, prevHoles.length);
        return {
          ...hole,
          x: pos.x,
          y: pos.y,
        };
      })
    );
  }, [timelineOffset]);

  // 加载热门决策
  useEffect(() => {
    const loadTrendingDecisions = async () => {
      setLoadingTrending(true);
      try {
        const decisions = await getTrendingDecisions(168); // 改为7天
        console.log('[热门决策] 获取到决策:', decisions);
        setTrendingDecisions(decisions);
      } catch (error) {
        console.error('[热门决策] 加载失败:', error);
        setTrendingDecisions([]);
      } finally {
        setLoadingTrending(false);
      }
    };
    
    loadTrendingDecisions();
    
    // 每5分钟刷新一次
    const interval = setInterval(loadTrendingDecisions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 当选择树洞时，加载消息
  useEffect(() => {
    const loadMessages = async () => {
      if (!selectedHole) {
        setSelectedHoleMessages([]);
        return;
      }
      
      setLoadingMessages(true);
      try {
        const messages = await getTreeHoleMessages(selectedHole.id);
        console.log('加载树洞消息:', messages);
        setSelectedHoleMessages(messages);
      } catch (error) {
        console.error('加载树洞消息失败:', error);
        setSelectedHoleMessages([]);
      } finally {
        setLoadingMessages(false);
      }
    };
    
    loadMessages();
  }, [selectedHole]);

  // 绘制2.5D地图背景
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W;
    canvas.height = H;

    // 绘制网格背景（2.5D透视效果）
    ctx.save();
    ctx.strokeStyle = 'rgba(10, 89, 247, 0.08)';
    ctx.lineWidth = 1;

    // 垂直线
    for (let x = 0; x <= W; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }

    // 水平线（带透视）
    for (let y = 0; y <= H; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }

    ctx.restore();

    // 绘制装饰性的光点
    for (let i = 0; i < 20; i++) {
      const x = Math.random() * W;
      const y = Math.random() * H;
      const radius = Math.random() * 2 + 1;
      
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(10, 89, 247, ${Math.random() * 0.3 + 0.1})`;
      ctx.fill();
    }
  }, []);

  return (
    <div className="tree-hole-page" style={{ 
      minHeight: '100vh', 
      paddingBottom: 120, 
      overflow: 'hidden', 
      position: 'relative',
      background: 'linear-gradient(180deg, #1a3a2e 0%, #2d5a4a 30%, #3d6b5a 60%, #4a7c6a 100%)',
      userSelect: isDraggingTimeline ? 'none' : 'auto',
    }}>
      {/* 森林背景层 */}
      <div style={{
        position: 'fixed',
        inset: 0,
        background: `
          radial-gradient(ellipse at 20% 30%, rgba(139, 90, 43, 0.3) 0%, transparent 50%),
          radial-gradient(ellipse at 80% 20%, rgba(101, 67, 33, 0.2) 0%, transparent 40%),
          radial-gradient(ellipse at 50% 80%, rgba(74, 124, 106, 0.4) 0%, transparent 60%),
          linear-gradient(180deg, rgba(26, 58, 46, 0.9) 0%, rgba(45, 90, 74, 0.7) 50%, rgba(61, 107, 90, 0.8) 100%)
        `,
        zIndex: 0,
      }} />
      
      {/* 树木剪影 */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60%',
        background: `
          radial-gradient(ellipse at 10% 100%, rgba(0, 0, 0, 0.6) 0%, transparent 30%),
          radial-gradient(ellipse at 30% 100%, rgba(0, 0, 0, 0.5) 0%, transparent 25%),
          radial-gradient(ellipse at 70% 100%, rgba(0, 0, 0, 0.5) 0%, transparent 28%),
          radial-gradient(ellipse at 90% 100%, rgba(0, 0, 0, 0.6) 0%, transparent 32%)
        `,
        zIndex: 0,
        pointerEvents: 'none',
      }} />

      {/* 阳光光线效果 */}
      <div style={{
        position: 'fixed',
        top: -100,
        left: '15%',
        width: '250px',
        height: '120%',
        background: 'linear-gradient(180deg, rgba(255, 255, 200, 0.2) 0%, rgba(255, 255, 200, 0.05) 40%, transparent 70%)',
        transform: 'skewX(-12deg)',
        pointerEvents: 'none',
        zIndex: 1,
        animation: 'lightRay 8s ease-in-out infinite',
        filter: 'blur(2px)',
      }} />
      
      <div style={{
        position: 'fixed',
        top: -100,
        right: '25%',
        width: '180px',
        height: '120%',
        background: 'linear-gradient(180deg, rgba(255, 255, 200, 0.15) 0%, rgba(255, 255, 200, 0.03) 35%, transparent 60%)',
        transform: 'skewX(-18deg)',
        pointerEvents: 'none',
        zIndex: 1,
        animation: 'lightRay 10s ease-in-out infinite 2s',
        filter: 'blur(2px)',
      }} />
      
      {/* 漂浮的光点 */}
      {Array.from({ length: 30 }).map((_, i) => (
        <div
          key={`light-${i}`}
          style={{
            position: 'fixed',
            width: `${Math.random() * 4 + 2}px`,
            height: `${Math.random() * 4 + 2}px`,
            borderRadius: '50%',
            background: 'rgba(255, 255, 200, 0.6)',
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            pointerEvents: 'none',
            zIndex: 1,
            animation: `particleFloat ${Math.random() * 6 + 4}s ease-in-out infinite ${Math.random() * 4}s`,
            boxShadow: '0 0 8px rgba(255, 255, 200, 0.8)',
          }}
        />
      ))}

      {/* 顶部导航 */}
      <div className="app-topnav" style={{
        background: 'rgba(0, 0, 0, 0.3)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        padding: '16px 28px',
        display: 'flex',
        alignItems: 'center',
      }}>
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            borderRadius: 12,
            transition: 'all 0.2s',
            color: '#fff',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span style={{ fontSize: 14, fontWeight: 600 }}>返回首页</span>
        </button>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 14, fontWeight: 600, color: '#fff', textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)' }}>
          树洞
        </div>
      </div>

      {/* 主内容 */}
      <div style={{ 
        position: 'relative',
        maxWidth: 1400, 
        margin: '0 auto', 
        padding: '80px 28px 40px',
        height: 'calc(100vh - 120px)',
        zIndex: 10,
        display: 'flex',
        gap: 24,
      }}>
        {/* 左侧主内容区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 24 }}>
        {/* 标题卡片 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 24, padding: '28px 36px',
          borderRadius: 28,
          background: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(20px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.3)',
        }}>
          <div style={{
            position: 'absolute', top: 0, right: 0, width: '50%', height: '100%',
            background: 'radial-gradient(ellipse at 80% 50%, rgba(255, 255, 255, 0.1), transparent 60%)',
            pointerEvents: 'none',
          }}/>
          
          <div style={{
            width: 72, height: 72, borderRadius: '50%', flexShrink: 0,
            background: 'linear-gradient(135deg, rgba(139, 90, 43, 0.9) 0%, rgba(101, 67, 33, 0.8) 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.4)',
            border: '2px solid rgba(255, 255, 255, 0.2)',
          }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255, 255, 255, 0.9)" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
          </div>
          
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 6, color: '#fff', textShadow: '0 2px 8px rgba(0, 0, 0, 0.3)' }}>
              树洞
            </div>
            <div style={{ fontSize: 15, color: 'rgba(255, 255, 255, 0.9)', letterSpacing: '0.02em', textShadow: '0 1px 4px rgba(0, 0, 0, 0.2)' }}>
              在这儿，我们顺时聆听和支持您。
            </div>
          </div>

          <button
            style={{
              padding: '12px 28px',
              borderRadius: 20,
              border: '2px solid rgba(139, 90, 43, 0.4)',
              background: 'linear-gradient(135deg, rgba(139, 90, 43, 0.85) 0%, rgba(101, 67, 33, 0.85) 100%)',
              color: '#fff',
              fontSize: 14,
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 6px 20px rgba(101, 67, 33, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s ease',
              letterSpacing: '0.5px',
              textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
            }}
            onClick={() => setShowCreateModal(true)}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(101, 67, 33, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.25)';
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(139, 90, 43, 0.95) 0%, rgba(101, 67, 33, 0.95) 100%)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(101, 67, 33, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.2)';
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(139, 90, 43, 0.85) 0%, rgba(101, 67, 33, 0.85) 100%)';
            }}
          >
            创建树洞
          </button>
        </div>

        {/* 2.5D地图容器 */}
        <div style={{
          position: 'relative',
          flex: 1,
          background: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(30px) saturate(150%)',
          borderRadius: 28,
          overflow: 'visible',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.15)',
        }}>
          <div className="tree-hole-map-container" style={{
            borderRadius: 28,
            overflow: 'hidden',
          }}>
            <div className="tree-hole-map-scene">
              {/* 地面网格 */}
              <div className="tree-hole-ground" />

              {/* Canvas背景 */}
              <canvas
                ref={canvasRef}
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none',
                }}
              />

              {/* 装饰性粒子 */}
              {Array.from({ length: 15 }).map((_, i) => (
                <div
                  key={`particle-${i}`}
                  className="tree-hole-particle"
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 4}s`,
                  }}
                />
              ))}

              {/* 加载状态 */}
              {loading && (
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                  color: 'rgba(255, 255, 255, 0.8)',
                }}>
                  <div style={{
                    width: 48,
                    height: 48,
                    margin: '0 auto 16px',
                    borderRadius: '50%',
                    border: '4px solid rgba(255, 255, 255, 0.2)',
                    borderTopColor: 'rgba(255, 255, 255, 0.8)',
                    animation: 'spin 1s linear infinite',
                  }} />
                  <div style={{ fontSize: 14, fontWeight: 600 }}>加载中...</div>
                </div>
              )}

              {/* 树洞节点 */}
              {!loading && treeHoles.map((hole, index) => {
                // 判断树洞是否在可视区域内
                const isInView = hole.x >= -10 && hole.x <= 110;
                
                return (
                  <div
                    key={hole.id}
                    className={`tree-hole-node ${isInView ? 'flowing' : ''}`}
                    style={{
                      left: `${hole.x}%`,
                      top: `${hole.y}%`,
                      width: 160,
                      height: 160,
                      transform: hoveredHole === hole.id 
                        ? 'translate(-50%, -50%) scale(1.08)' 
                        : 'translate(-50%, -50%) scale(1)',
                      zIndex: hoveredHole === hole.id ? 1000 : 100 + index,
                      position: 'absolute',
                      filter: hoveredHole === hole.id 
                        ? 'drop-shadow(0 12px 24px rgba(0, 0, 0, 0.3))' 
                        : 'drop-shadow(0 8px 16px rgba(0, 0, 0, 0.2))',
                      opacity: isInView ? 1 : 0.3,
                      pointerEvents: isInView ? 'auto' : 'none',
                    }}
                  >
                  <button
                    onClick={() => setSelectedHole(hole)}
                    onMouseEnter={() => setHoveredHole(hole.id)}
                    onMouseLeave={() => setHoveredHole(null)}
                    className="tree-hole-content"
                    style={{
                      border: 'none',
                      cursor: 'pointer',
                      background: 'transparent',
                      padding: 0,
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      pointerEvents: 'auto',
                      outline: 'none',
                      WebkitTapHighlightColor: 'transparent',
                    }}
                  >
                    {/* 树洞主体 - 木质纹理 */}
                    <div style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      width: 140,
                      height: 140,
                      transform: hoveredHole === hole.id ? 'translate(-50%, -50%) scale(1.05)' : 'translate(-50%, -50%) scale(1)',
                      borderRadius: '50%',
                      background: `
                        radial-gradient(ellipse at 30% 30%, rgba(139, 90, 43, 0.9), transparent 70%),
                        radial-gradient(ellipse at 70% 70%, rgba(101, 67, 33, 0.8), transparent 60%),
                        linear-gradient(135deg, #8B5A2B 0%, #654321 50%, #4A3319 100%)
                      `,
                      boxShadow: `
                        inset 0 4px 12px rgba(0, 0, 0, 0.4),
                        inset 0 -4px 8px rgba(255, 255, 255, 0.1),
                        0 8px 24px rgba(0, 0, 0, 0.3)
                      `,
                      transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                      pointerEvents: 'none',
                    }}>
                      {/* 木质纹理细节 */}
                      <div style={{
                        position: 'absolute',
                        inset: '10%',
                        borderRadius: '50%',
                        background: `
                          radial-gradient(ellipse at 40% 40%, rgba(139, 90, 43, 0.6), transparent 50%),
                          radial-gradient(ellipse at 60% 60%, rgba(101, 67, 33, 0.5), transparent 40%)
                        `,
                        opacity: 0.6,
                        pointerEvents: 'none',
                      }} />
                      
                      {/* 树洞内部阴影 */}
                      <div style={{
                        position: 'absolute',
                        inset: '15%',
                        borderRadius: '50%',
                        background: 'radial-gradient(circle, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 60%, transparent 100%)',
                        boxShadow: 'inset 0 0 20px rgba(0, 0, 0, 0.8)',
                        pointerEvents: 'none',
                      }} />
                      
                      {/* 树洞边缘高光 */}
                      <div style={{
                        position: 'absolute',
                        top: '8%',
                        left: '8%',
                        right: '8%',
                        height: '25%',
                        borderRadius: '50% 50% 0 0',
                        background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, transparent 100%)',
                        pointerEvents: 'none',
                      }} />
                      
                      {/* 树皮裂纹 - 固定位置 */}
                      <div style={{ position: 'absolute', width: '2px', height: '25%', background: 'rgba(0, 0, 0, 0.3)', top: '15%', left: '20%', transform: 'rotate(25deg)', borderRadius: '1px', pointerEvents: 'none' }} />
                      <div style={{ position: 'absolute', width: '2px', height: '30%', background: 'rgba(0, 0, 0, 0.3)', top: '35%', left: '65%', transform: 'rotate(-15deg)', borderRadius: '1px', pointerEvents: 'none' }} />
                      <div style={{ position: 'absolute', width: '2px', height: '22%', background: 'rgba(0, 0, 0, 0.3)', top: '45%', left: '30%', transform: 'rotate(40deg)', borderRadius: '1px', pointerEvents: 'none' }} />
                      <div style={{ position: 'absolute', width: '2px', height: '28%', background: 'rgba(0, 0, 0, 0.3)', top: '20%', left: '75%', transform: 'rotate(-30deg)', borderRadius: '1px', pointerEvents: 'none' }} />
                      <div style={{ position: 'absolute', width: '2px', height: '20%', background: 'rgba(0, 0, 0, 0.3)', top: '55%', left: '50%', transform: 'rotate(10deg)', borderRadius: '1px', pointerEvents: 'none' }} />
                    </div>

                    {/* 发光效果 */}
                    {hoveredHole === hole.id && (
                      <div style={{
                        position: 'absolute',
                        inset: -8,
                        borderRadius: '50%',
                        background: `radial-gradient(circle, rgba(255, 255, 200, 0.25) 0%, transparent 60%)`,
                        animation: 'pulse 2.5s ease-in-out infinite',
                        pointerEvents: 'none',
                      }} />
                    )}

                    {/* 信息标签 */}
                    <div style={{
                      position: 'absolute',
                      bottom: -50,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: 'rgba(255, 255, 255, 0.95)',
                      backdropFilter: 'blur(10px)',
                      padding: '8px 16px',
                      borderRadius: 12,
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                      whiteSpace: 'nowrap',
                      border: '1px solid rgba(0, 0, 0, 0.05)',
                      opacity: hoveredHole === hole.id ? 1 : 0.8,
                      transition: 'all 0.3s',
                      pointerEvents: 'none',
                    }}>
                      <div style={{ 
                        fontSize: 13, 
                        fontWeight: 700, 
                        color: '#1A1A1A',
                        marginBottom: 2,
                      }}>
                        {hole.title}
                      </div>
                      <div style={{ 
                        fontSize: 11, 
                        color: '#666',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span>{hole.messageCount} 条消息</span>
                      </div>
                    </div>

                    {/* 悬停提示 */}
                    {hoveredHole === hole.id && (
                      <div style={{
                        position: 'absolute',
                        top: -35,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(139, 90, 43, 0.95)',
                        color: '#fff',
                        padding: '6px 14px',
                        borderRadius: 10,
                        fontSize: 12,
                        fontWeight: 600,
                        whiteSpace: 'nowrap',
                        boxShadow: '0 4px 12px rgba(101, 67, 33, 0.4)',
                        animation: 'fadeIn 0.3s',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                      }}>
                        点击进入
                        <div style={{
                          position: 'absolute',
                          bottom: -4,
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '4px solid transparent',
                          borderRight: '4px solid transparent',
                          borderTop: '4px solid rgba(139, 90, 43, 0.95)',
                        }} />
                      </div>
                    )}
                  </button>
                </div>
              );
              })}

              {/* 装饰性的连接路径 */}
              <svg
                className="tree-hole-path"
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                }}
              >
                {treeHoles.map((hole, i) => {
                  if (i === treeHoles.length - 1) return null;
                  const nextHole = treeHoles[i + 1];
                  return (
                    <line
                      key={`line-${hole.id}`}
                      x1={`${hole.x}%`}
                      y1={`${hole.y}%`}
                      x2={`${nextHole.x}%`}
                      y2={`${nextHole.y}%`}
                    />
                  );
                })}
              </svg>
            </div>
          </div>
        </div>
        </div>

        {/* 右侧热门决策排行榜 */}
        {showTrending && (
          <div style={{
            width: 360,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}>
            {/* 排行榜标题 */}
            <div style={{
              background: 'rgba(139, 90, 43, 0.25)',
              backdropFilter: 'blur(20px) saturate(180%)',
              border: '1px solid rgba(139, 90, 43, 0.4)',
              borderRadius: 20,
              padding: '20px 24px',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.3)',
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}>
                  {/* 火焰图标 */}
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: 12,
                    background: 'linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 12px rgba(255, 107, 107, 0.4)',
                  }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M12 2C12 2 8 6 8 10C8 12.2091 9.79086 14 12 14C14.2091 14 16 12.2091 16 10C16 6 12 2 12 2Z" fill="white" opacity="0.9"/>
                      <path d="M12 14C12 14 9 16 9 18.5C9 20.433 10.567 22 12.5 22C14.433 22 16 20.433 16 18.5C16 16 12 14 12 14Z" fill="white" opacity="0.7"/>
                    </svg>
                  </div>
                  <div>
                    <div style={{
                      fontSize: 20,
                      fontWeight: 800,
                      color: '#fff',
                      textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                      letterSpacing: '0.5px',
                    }}>
                      热门决策
                    </div>
                    <div style={{
                      fontSize: 13,
                      color: 'rgba(255, 255, 255, 0.85)',
                      marginTop: 4,
                      letterSpacing: '0.3px',
                    }}>
                      大家都在纠结的选择
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setShowTrending(false)}
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    border: 'none',
                    background: 'rgba(255, 255, 255, 0.15)',
                    color: '#fff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s',
                    fontSize: 20,
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.25)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
                  }}
                >
                  ×
                </button>
              </div>
            </div>

            {/* 决策列表 */}
            <div style={{
              flex: 1,
              background: 'rgba(139, 90, 43, 0.15)',
              backdropFilter: 'blur(20px) saturate(180%)',
              border: '1px solid rgba(139, 90, 43, 0.3)',
              borderRadius: 20,
              padding: '16px',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.3)',
              overflow: 'auto',
              maxHeight: 'calc(100vh - 280px)',
            }}>
              {loadingTrending ? (
                <div style={{
                  textAlign: 'center',
                  padding: '60px 20px',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: 14,
                }}>
                  <div style={{
                    width: 64,
                    height: 64,
                    margin: '0 auto 16px',
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="rgba(255, 255, 255, 0.6)" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                      <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>正在分析热门决策...</div>
                  <div style={{ fontSize: 12, marginTop: 8, opacity: 0.7 }}>AI正在处理数据</div>
                </div>
              ) : trendingDecisions.length === 0 ? (
                <div style={{
                  textAlign: 'center',
                  padding: '60px 20px',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: 14,
                }}>
                  <div style={{
                    width: 64,
                    height: 64,
                    margin: '0 auto 16px',
                    borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="rgba(255, 255, 255, 0.6)" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>暂无热门决策</div>
                  <div style={{ fontSize: 12, marginTop: 8, opacity: 0.7 }}>
                    树洞中还没有足够的消息
                    <br />
                    快去发表你的想法吧！
                  </div>
                </div>
              ) : (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}>
                  {trendingDecisions.map((decision, index) => {
                    // 决策类型配置
                    const typeConfig = {
                      problem: { 
                        icon: (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
                          </svg>
                        ),
                        color: '#ff6b6b', 
                        label: '痛点' 
                      },
                      success: { 
                        icon: (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <polyline points="20 6 9 17 4 12"/>
                          </svg>
                        ),
                        color: '#51cf66', 
                        label: '成功' 
                      },
                      question: { 
                        icon: (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                          </svg>
                        ),
                        color: '#ffa94d', 
                        label: '纠结' 
                      },
                    }[decision.type] || { 
                      icon: (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                          <circle cx="12" cy="12" r="2"/>
                        </svg>
                      ),
                      color: '#999', 
                      label: '其他' 
                    };

                    // 领域图标配置
                    const domainConfig = {
                      career: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
                          </svg>
                        ),
                        color: '#4c6ef5'
                      },
                      education: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
                          </svg>
                        ),
                        color: '#7950f2'
                      },
                      relationship: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                          </svg>
                        ),
                        color: '#f06595'
                      },
                      family: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                            <polyline points="9 22 9 12 15 12 15 22"/>
                          </svg>
                        ),
                        color: '#fd7e14'
                      },
                      finance: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="12" y1="1" x2="12" y2="23"/>
                            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                          </svg>
                        ),
                        color: '#20c997'
                      },
                      health: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                          </svg>
                        ),
                        color: '#ff6b6b'
                      },
                      lifestyle: {
                        icon: (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
                          </svg>
                        ),
                        color: '#fab005'
                      },
                    }[decision.domain] || {
                      icon: (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                      ),
                      color: '#868e96'
                    };
                    
                    return (
                    <div
                      key={index}
                      style={{
                        background: 'linear-gradient(135deg, rgba(240, 253, 244, 0.95) 0%, rgba(230, 252, 245, 0.95) 100%)',
                        borderRadius: 16,
                        padding: '18px',
                        cursor: 'pointer',
                        transition: 'all 0.3s',
                        border: '1.5px solid rgba(139, 90, 43, 0.2)',
                        boxShadow: '0 2px 8px rgba(74, 124, 106, 0.15)',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.transform = 'translateY(-3px)';
                        e.currentTarget.style.boxShadow = '0 8px 24px rgba(74, 124, 106, 0.3)';
                        e.currentTarget.style.background = 'linear-gradient(135deg, rgba(240, 253, 244, 1) 0%, rgba(230, 252, 245, 1) 100%)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(74, 124, 106, 0.15)';
                        e.currentTarget.style.background = 'linear-gradient(135deg, rgba(240, 253, 244, 0.95) 0%, rgba(230, 252, 245, 0.95) 100%)';
                      }}
                    >
                      {/* 排名和趋势 */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 12,
                        marginBottom: 12,
                      }}>
                        <div style={{
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          background: decision.rank <= 3 
                            ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)'
                            : 'linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: 16,
                          fontWeight: 800,
                          color: decision.rank <= 3 ? '#fff' : '#495057',
                          boxShadow: decision.rank <= 3 ? '0 4px 12px rgba(255, 215, 0, 0.4)' : '0 2px 6px rgba(0, 0, 0, 0.1)',
                          flexShrink: 0,
                        }}>
                          {decision.rank}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: 16,
                            fontWeight: 700,
                            color: '#1a3a2e',
                            marginBottom: 8,
                          }}>
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 8,
                            }}>
                              <span style={{ 
                                color: domainConfig.color,
                                display: 'flex',
                                alignItems: 'center',
                              }}>
                                {domainConfig.icon}
                              </span>
                              <span>{decision.decision}</span>
                            </div>
                          </div>
                          <div style={{
                            fontSize: 12,
                            color: '#2d5a4a',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 12,
                          }}>
                            <span style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4,
                            }}>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                              </svg>
                              <span style={{ fontWeight: 600 }}>{decision.message_count}</span>
                            </span>
                            <span style={{ color: '#dee2e6' }}>•</span>
                            <span style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4,
                              color: '#ff6b6b',
                            }}>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2L1 21h22L12 2z"/>
                              </svg>
                              <span style={{ fontWeight: 600 }}>{decision.score.toFixed(0)}</span>
                            </span>
                          </div>
                        </div>
                        {/* 决策类型标签 */}
                        <div style={{
                          padding: '8px 16px',
                          borderRadius: 20,
                          background: `${typeConfig.color}15`,
                          color: typeConfig.color,
                          fontSize: 12,
                          fontWeight: 700,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          flexShrink: 0,
                          border: `1.5px solid ${typeConfig.color}30`,
                        }}>
                          {typeConfig.icon}
                          <span>{typeConfig.label}</span>
                        </div>
                      </div>

                      {/* 关键词 */}
                      {decision.keywords && decision.keywords.length > 0 && (
                        <div style={{
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: 8,
                          marginBottom: 12,
                        }}>
                          {decision.keywords.slice(0, 3).map((keyword, i) => (
                            <span
                              key={i}
                              style={{
                                padding: '6px 12px',
                                borderRadius: 12,
                                background: 'rgba(76, 110, 245, 0.1)',
                                color: '#4c6ef5',
                                fontSize: 12,
                                fontWeight: 600,
                                border: '1px solid rgba(76, 110, 245, 0.2)',
                              }}
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* 描述 */}
                      <div style={{
                        fontSize: 13,
                        color: '#2d5a4a',
                        lineHeight: 1.6,
                        marginBottom: decision.pain_point ? 12 : 0,
                      }}>
                        {decision.description}
                      </div>

                      {/* 痛点（如果有） */}
                      {decision.pain_point && (
                        <div style={{
                          padding: '10px 14px',
                          borderRadius: 10,
                          background: 'rgba(255, 107, 107, 0.08)',
                          border: '1.5px solid rgba(255, 107, 107, 0.2)',
                          fontSize: 12,
                          color: '#ff6b6b',
                          lineHeight: 1.6,
                          display: 'flex',
                          gap: 8,
                        }}>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ flexShrink: 0, marginTop: 2 }}>
                            <path d="M12 2L1 21h22L12 2zm0 3.83L19.53 19H4.47L12 5.83zM11 16h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
                          </svg>
                          <span style={{ fontWeight: 600 }}>{decision.pain_point}</span>
                        </div>
                      )}

                      {/* 相关树洞 */}
                      {decision.tree_holes && decision.tree_holes.length > 0 && (
                        <div style={{
                          marginTop: 12,
                          paddingTop: 12,
                          borderTop: '1.5px solid rgba(74, 124, 106, 0.2)',
                          fontSize: 12,
                          color: '#3d6b5a',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <circle cx="12" cy="12" r="6"/>
                            <circle cx="12" cy="12" r="2"/>
                          </svg>
                          <span style={{ fontWeight: 600 }}>来自:</span>
                          <span>{decision.tree_holes.map(h => h.title).join(', ')}</span>
                        </div>
                      )}
                    </div>
                  )})}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 显示热门决策按钮（当侧边栏隐藏时） */}
        {!showTrending && (
          <button
            onClick={() => setShowTrending(true)}
            style={{
              position: 'fixed',
              right: 28,
              top: '50%',
              transform: 'translateY(-50%)',
              width: 48,
              height: 48,
              borderRadius: '50%',
              border: 'none',
              background: 'linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%)',
              color: '#fff',
              cursor: 'pointer',
              boxShadow: '0 8px 24px rgba(255, 107, 107, 0.4)',
              transition: 'all 0.3s',
              zIndex: 100,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
              e.currentTarget.style.boxShadow = '0 12px 32px rgba(255, 107, 107, 0.6)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(255, 107, 107, 0.4)';
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C12 2 8 6 8 10C8 12.2091 9.79086 14 12 14C14.2091 14 16 12.2091 16 10C16 6 12 2 12 2Z" fill="white" opacity="0.9"/>
              <path d="M12 14C12 14 9 16 9 18.5C9 20.433 10.567 22 12.5 22C14.433 22 16 20.433 16 18.5C16 16 12 14 12 14Z" fill="white" opacity="0.7"/>
            </svg>
          </button>
        )}
      </div>

      {/* 树洞详情弹窗 */}
      {selectedHole && (
        <div
          className="tree-hole-modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => {
            setSelectedHole(null);
            setNewMessageContent('');
          }}
        >
          <div
            className="tree-hole-modal-content"
            style={{
              background: 'rgba(255, 255, 255, 0.98)',
              borderRadius: 28,
              padding: 40,
              maxWidth: 600,
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 24px 64px rgba(0, 0, 0, 0.2)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
              <div style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${selectedHole.color} 0%, rgba(10, 89, 247, 0.3) 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 24px rgba(10, 89, 247, 0.2)',
              }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="rgba(10, 89, 247, 0.8)" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <circle cx="12" cy="12" r="6"/>
                  <circle cx="12" cy="12" r="2"/>
                </svg>
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: '#1A1A1A' }}>
                  {selectedHole.title}
                </h2>
                <p style={{ margin: '4px 0 0', fontSize: 14, color: '#666' }}>
                  {selectedHole.messageCount} 条匿名消息
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedHole(null);
                  setNewMessageContent('');
                }}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  border: 'none',
                  background: 'rgba(0, 0, 0, 0.05)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s',
                  fontSize: 18,
                  color: '#666',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = 'rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)';
                }}
              >
                ✕
              </button>
            </div>

            {/* 消息列表 */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {loadingMessages ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px 0', 
                  color: '#999',
                  fontSize: 14,
                }}>
                  加载中...
                </div>
              ) : selectedHoleMessages.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px 0', 
                  color: '#999',
                  fontSize: 14,
                }}>
                  还没有消息，快来发表第一条吧！
                </div>
              ) : (
                selectedHoleMessages.map(message => {
                  // 计算时间差
                  const now = new Date();
                  const messageTime = new Date(message.created_at);
                  const diffMs = now.getTime() - messageTime.getTime();
                  const diffMins = Math.floor(diffMs / 60000);
                  const diffHours = Math.floor(diffMins / 60);
                  const diffDays = Math.floor(diffHours / 24);
                  
                  let timeText = '';
                  if (diffDays > 0) {
                    timeText = `${diffDays}天前`;
                  } else if (diffHours > 0) {
                    timeText = `${diffHours}小时前`;
                  } else if (diffMins > 0) {
                    timeText = `${diffMins}分钟前`;
                  } else {
                    timeText = '刚刚';
                  }
                  
                  return (
                    <div key={message.id} className="tree-hole-message">
                      <div style={{ fontSize: 15, color: '#1A1A1A', lineHeight: 1.6, marginBottom: 12 }}>
                        {message.content}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#999' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                          </svg>
                          {timeText}
                        </span>
                        <span>•</span>
                        <button
                          style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            color: '#999',
                            transition: 'color 0.2s',
                          }}
                          onMouseEnter={e => {
                            e.currentTarget.style.color = '#ff6b6b';
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.color = '#999';
                          }}
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                          </svg>
                          <span>{message.likes || 0}</span>
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* 发送消息 */}
            <div style={{ marginTop: 24 }}>
              <textarea
                value={newMessageContent}
                onChange={e => setNewMessageContent(e.target.value)}
                placeholder="匿名分享你的想法..."
                disabled={sendingMessage}
                style={{
                  width: '100%',
                  minHeight: 100,
                  padding: 16,
                  borderRadius: 16,
                  border: '2px solid rgba(10, 89, 247, 0.15)',
                  fontSize: 14,
                  resize: 'vertical',
                  outline: 'none',
                  fontFamily: 'inherit',
                  transition: 'border-color 0.3s',
                  opacity: sendingMessage ? 0.6 : 1,
                }}
                onFocus={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.4)';
                }}
                onBlur={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.15)';
                }}
              />
              <button
                onClick={async () => {
                  if (!newMessageContent.trim()) {
                    alert('请输入消息内容');
                    return;
                  }
                  
                  if (!selectedHole) return;
                  
                  setSendingMessage(true);
                  try {
                    const userStr = localStorage.getItem('user');
                    const user = userStr ? JSON.parse(userStr) : null;
                    const userId = user?.id || 'guest';
                    
                    const success = await sendMessage(selectedHole.id, userId, newMessageContent, true);
                    
                    if (success) {
                      setNewMessageContent('');
                      // 重新加载消息列表
                      const messages = await getTreeHoleMessages(selectedHole.id);
                      setSelectedHoleMessages(messages);
                      
                      // 更新树洞的消息计数
                      setTreeHoles(prevHoles => 
                        prevHoles.map(hole => 
                          hole.id === selectedHole.id 
                            ? { ...hole, messageCount: messages.length }
                            : hole
                        )
                      );
                      
                      // 更新选中的树洞信息
                      setSelectedHole(prev => prev ? { ...prev, messageCount: messages.length } : null);
                    } else {
                      alert('发送失败，请重试');
                    }
                  } catch (error) {
                    console.error('发送消息失败:', error);
                    alert('发送失败，请重试');
                  } finally {
                    setSendingMessage(false);
                  }
                }}
                disabled={sendingMessage}
                style={{
                  marginTop: 12,
                  width: '100%',
                  padding: '14px',
                  borderRadius: 16,
                  border: 'none',
                  background: sendingMessage 
                    ? 'linear-gradient(135deg, #999 0%, #666 100%)'
                    : 'linear-gradient(135deg, #8B4513 0%, #A0522D 100%)',
                  color: '#fff',
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: sendingMessage ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s',
                  boxShadow: '0 8px 24px rgba(139, 69, 19, 0.3)',
                }}
                onMouseEnter={e => {
                  if (!sendingMessage) {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 12px 32px rgba(139, 69, 19, 0.4)';
                  }
                }}
                onMouseLeave={e => {
                  if (!sendingMessage) {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(139, 69, 19, 0.3)';
                  }
                }}
              >
                {sendingMessage ? '发送中...' : '匿名发送'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建树洞弹窗 */}
      {showCreateModal && (
        <div
          className="tree-hole-modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="tree-hole-modal-content"
            style={{
              background: 'rgba(255, 255, 255, 0.98)',
              borderRadius: 28,
              padding: 40,
              maxWidth: 500,
              width: '90%',
              boxShadow: '0 24px 64px rgba(0, 0, 0, 0.2)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
              <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: '#1A1A1A' }}>
                创建树洞
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  border: 'none',
                  background: 'rgba(0, 0, 0, 0.05)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s',
                  fontSize: 18,
                  color: '#666',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = 'rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)';
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 600, color: '#333', marginBottom: 8 }}>
                树洞名称
              </label>
              <input
                type="text"
                value={newTreeHoleTitle}
                onChange={e => setNewTreeHoleTitle(e.target.value)}
                placeholder="给你的树洞起个名字..."
                style={{
                  width: '100%',
                  padding: 12,
                  borderRadius: 12,
                  border: '2px solid rgba(10, 89, 247, 0.15)',
                  fontSize: 14,
                  outline: 'none',
                  transition: 'border-color 0.3s',
                }}
                onFocus={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.4)';
                }}
                onBlur={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.15)';
                }}
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', fontSize: 14, fontWeight: 600, color: '#333', marginBottom: 8 }}>
                描述（可选）
              </label>
              <textarea
                value={newTreeHoleDesc}
                onChange={e => setNewTreeHoleDesc(e.target.value)}
                placeholder="简单描述一下这个树洞的用途..."
                style={{
                  width: '100%',
                  minHeight: 80,
                  padding: 12,
                  borderRadius: 12,
                  border: '2px solid rgba(10, 89, 247, 0.15)',
                  fontSize: 14,
                  resize: 'vertical',
                  outline: 'none',
                  fontFamily: 'inherit',
                  transition: 'border-color 0.3s',
                }}
                onFocus={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.4)';
                }}
                onBlur={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.15)';
                }}
              />
            </div>

            <button
              onClick={async () => {
                if (!newTreeHoleTitle.trim()) {
                  alert('请输入树洞名称');
                  return;
                }
                
                const userStr = localStorage.getItem('user');
                const user = userStr ? JSON.parse(userStr) : null;
                const userId = user?.id || 'guest';
                
                const treeHoleId = await createTreeHole(userId, newTreeHoleTitle, newTreeHoleDesc);
                
                if (treeHoleId) {
                  setShowCreateModal(false);
                  setNewTreeHoleTitle('');
                  setNewTreeHoleDesc('');
                  
                  // 重新加载树洞列表
                  const holes = await getAllTreeHoles();
                  
                  // 按创建时间排序
                  const sortedHoles = [...holes].sort((a, b) => {
                    const timeA = new Date(a.created_at || 0).getTime();
                    const timeB = new Date(b.created_at || 0).getTime();
                    return timeA - timeB;
                  });
                  
                  // 映射树洞数据
                  const mappedHoles = sortedHoles.map((hole, index) => {
                    const pos = calculateTreeHolePosition(index, sortedHoles.length);
                    return {
                      id: hole.id,
                      title: hole.title,
                      description: hole.description,
                      messageCount: hole.message_count,
                      x: pos.x,
                      y: pos.y,
                      color: treeHoleColors[index % treeHoleColors.length],
                      createdAt: hole.created_at,
                    };
                  });
                  
                  setTreeHoles(mappedHoles);
                  
                  // 自动滚动到最新创建的树洞（最右边）
                  const maxOffset = Math.max(0, mappedHoles.length * 18 - 70);
                  setTimelineOffset(maxOffset);
                } else {
                  alert('创建失败，请重试');
                }
              }}
              style={{
                width: '100%',
                padding: '14px 24px',
                borderRadius: 20,
                border: '2px solid rgba(139, 90, 43, 0.4)',
                background: 'linear-gradient(135deg, rgba(139, 90, 43, 0.9) 0%, rgba(101, 67, 33, 0.9) 100%)',
                color: '#fff',
                fontSize: 15,
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 6px 20px rgba(101, 67, 33, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
                letterSpacing: '0.5px',
                textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 8px 24px rgba(101, 67, 33, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.25)';
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(139, 90, 43, 1) 0%, rgba(101, 67, 33, 1) 100%)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(101, 67, 33, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2)';
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(139, 90, 43, 0.9) 0%, rgba(101, 67, 33, 0.9) 100%)';
              }}
            >
              创建
            </button>
          </div>
        </div>
      )}

      {/* 底部时间线滑动条 */}
      <div
        ref={timelineRef}
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 100,
          background: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          zIndex: 200,
          cursor: isDraggingTimeline ? 'grabbing' : 'grab',
          userSelect: 'none',
        }}
        onMouseDown={handleTimelineMouseDown}
        onMouseMove={handleTimelineMouseMove}
        onMouseUp={handleTimelineMouseUp}
      >
        <div style={{
          maxWidth: 1400,
          margin: '0 auto',
          padding: '16px 28px',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}>
          {/* 时间线标题 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: '#fff',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              fontWeight: 600,
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>时间线</span>
              <span style={{ 
                fontSize: 11, 
                opacity: 0.7,
                marginLeft: 4,
              }}>
                拖动查看更多树洞
              </span>
            </div>
            <div style={{
              fontSize: 12,
              opacity: 0.8,
            }}>
              {treeHoles.length} 个树洞
            </div>
          </div>

          {/* 时间线轨道 */}
          <div style={{
            position: 'relative',
            flex: 1,
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 12,
            overflow: 'hidden',
            boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.3)',
          }}>
            {/* 时间线刻度和树洞标记 */}
            <div style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              padding: '0 20px',
            }}>
              {treeHoles.map((hole, index) => {
                const position = ((index * 18 - timelineOffset) / (treeHoles.length * 18 - 70)) * 100;
                const isVisible = position >= 0 && position <= 100;
                
                return (
                  <div
                    key={hole.id}
                    style={{
                      position: 'absolute',
                      left: `${position}%`,
                      transform: 'translateX(-50%)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 4,
                      opacity: isVisible ? 1 : 0.3,
                      transition: 'opacity 0.3s',
                      pointerEvents: 'none',
                    }}
                  >
                    {/* 树洞标记点 */}
                    <div style={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      background: isVisible 
                        ? 'linear-gradient(135deg, #8B5A2B 0%, #654321 100%)'
                        : 'rgba(139, 90, 43, 0.5)',
                      border: '2px solid rgba(255, 255, 255, 0.8)',
                      boxShadow: isVisible 
                        ? '0 0 12px rgba(139, 90, 43, 0.8), 0 2px 4px rgba(0, 0, 0, 0.3)'
                        : 'none',
                      transition: 'all 0.3s',
                    }} />
                    
                    {/* 刻度线 */}
                    <div style={{
                      width: 2,
                      height: 8,
                      background: isVisible 
                        ? 'rgba(255, 255, 255, 0.6)'
                        : 'rgba(255, 255, 255, 0.2)',
                      borderRadius: 1,
                    }} />
                    
                    {/* 树洞名称（仅显示可见的） */}
                    {isVisible && (
                      <div style={{
                        fontSize: 10,
                        color: '#fff',
                        fontWeight: 600,
                        whiteSpace: 'nowrap',
                        textShadow: '0 1px 2px rgba(0, 0, 0, 0.5)',
                        maxWidth: 80,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {hole.title}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* 当前视窗指示器 */}
            <div style={{
              position: 'absolute',
              left: '10%',
              right: '10%',
              top: 0,
              bottom: 0,
              border: '2px solid rgba(255, 255, 200, 0.4)',
              borderRadius: 8,
              pointerEvents: 'none',
              boxShadow: 'inset 0 0 20px rgba(255, 255, 200, 0.2)',
            }} />
          </div>
        </div>
      </div>
    </div>
  );
}
