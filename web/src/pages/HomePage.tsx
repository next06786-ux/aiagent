import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { AICoreModal } from '../components/ai/AICoreModal';
import { GlobalAIFloatingButton } from '../components/ai/GlobalAIFloatingButton';
import { VideoShowcase } from '../components/3d/VideoShowcase';
import { useAuth } from '../hooks/useAuth';
import '../styles/homepage-enhanced.css';
import '../styles/homepage-side-text.css';

interface PentagramNode {
  id: string;
  title: string;
  subtitle: string;
  route?: string;
  top: string;
  left: string;
  gradient: [string, string];
  status: 'live' | 'preview' | 'planned';
}

export function HomePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [isAICoreOpen, setIsAICoreOpen] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // 检查管理员权限 - 管理员不能访问学生端
  useEffect(() => {
    const checkAdminAccess = async () => {
      if (!user) return;
      
      const authData = localStorage.getItem('choicerealm.web.auth');
      if (!authData) return;
      
      try {
        const auth = JSON.parse(authData);
        const token = auth.token;
        
        if (!token) return;
        
        // 使用专门的权限检查API
        const apiBase = import.meta.env.VITE_API_BASE_URL || '';
        const response = await fetch(`${apiBase}/api/admin/check-permission`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.is_admin) {
            // 是管理员，不允许访问学生端
            alert('管理员账号不能访问学生端，请使用管理员界面');
            navigate('/admin');
          }
        } else if (response.status === 401) {
          // Token 无效或过期，忽略（用户可能未登录）
          console.log('[HomePage] 权限检查: 未认证');
        }
      } catch (error) {
        // 忽略错误，可能是网络问题或解析错误
        console.warn('[HomePage] 权限检查失败:', error);
      }
    };
    
    checkAdminAccess();
  }, [user, navigate]);

  // Scroll progress tracker
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      setScrollProgress(progress);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Menu item style for profile dropdown
  const menuItemStyle: CSSProperties = {
    display: 'block', width: '100%', padding: '9px 16px',
    background: 'transparent', border: 'none', cursor: 'pointer',
    fontSize: 13, fontWeight: 600, color: '#e8f0fe', textAlign: 'left',
  };

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }
  }, [user?.user_id]);

  // Scroll reveal observer
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-visible');
            }
          });
        },
        { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
      );

      const revealEls = document.querySelectorAll(
        '.ls-reveal, .ls-reveal-scale, .ls-reveal-left, .ls-reveal-right'
      );
      revealEls.forEach((el) => observer.observe(el));

      return () => observer.disconnect();
    }, 100);

    return () => clearTimeout(timeoutId);
  }, []);

  // Close menu on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setProfileMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const pentagramNodes = useMemo<PentagramNode[]>(() => [
    {
      id: 'decision',
      title: '决策副本',
      subtitle: '分析入口',
      route: '/decision',
      top: '5%',
      left: '50%',
      gradient: ['#E8F4FF', '#B8DCFF'],
      status: 'live',
    },
    {
      id: 'insights',
      title: '智慧洞察',
      subtitle: '决策分析',
      route: '/insights',
      top: '24%',
      left: '84%',
      gradient: ['#D4EBFF', '#A8D5FF'],
      status: 'live',
    },
    {
      id: 'parallel-life',
      title: '平行人生',
      subtitle: '塔罗游戏',
      route: '/parallel-life',
      top: '79%',
      left: '70%',
      gradient: ['#C2E3FF', '#8FC8FF'],
      status: 'live',
    },
    {
      id: 'social',
      title: '社交',
      subtitle: '好友互动',
      route: '/friends',
      top: '79%',
      left: '30%',
      gradient: ['#B0D9FF', '#7DBDFF'],
      status: 'live',
    },
    {
      id: 'knowledge-graph',
      title: '知识星图',
      subtitle: '记忆星空',
      route: '/knowledge-graph',
      top: '24%',
      left: '16%',
      gradient: ['#F0F7FF', '#C8E2FF'],
      status: 'live',
    },
  ], []);

  // Canvas particle flow
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  const drawField = useCallback(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return;
    const W = stage.offsetWidth;
    const H = stage.offsetHeight;
    if (W === 0) return;
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const cx = W / 2, cy = H / 2;

    const nodePositions = [
      { top: '5%',  left: '50%', color: '#B8DCFF' },
      { top: '24%', left: '84%', color: '#A8D5FF' },
      { top: '79%', left: '70%', color: '#8FC8FF' },
      { top: '79%', left: '30%', color: '#7DBDFF' },
      { top: '24%', left: '16%', color: '#C8E2FF' },
    ].map(n => ({
      x: (parseFloat(n.left) / 100) * W,
      y: (parseFloat(n.top)  / 100) * H,
      color: n.color,
    }));

    // Hexagonal grid background
    const hexR = 28;
    const hexW = hexR * Math.sqrt(3);
    const hexH = hexR * 2;
    ctx.save();
    for (let row = -2; row < H / (hexH * 0.75) + 2; row++) {
      for (let col = -2; col < W / hexW + 2; col++) {
        const hx = col * hexW + (row % 2 === 0 ? 0 : hexW / 2);
        const hy = row * hexH * 0.75;
        const dist = Math.hypot(hx - cx, hy - cy);
        const maxDist = Math.min(W, H) * 0.52;
        if (dist > maxDist) continue;
        const alpha = (1 - dist / maxDist) * 0.06;
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
          const angle = (Math.PI / 3) * i - Math.PI / 6;
          const px = hx + hexR * 0.92 * Math.cos(angle);
          const py = hy + hexR * 0.92 * Math.sin(angle);
          i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.strokeStyle = `rgba(10, 89, 247, ${alpha})`;
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }
    }
    ctx.restore();

    // Concentric arc decorations
    [0.44, 0.72, 0.96].forEach((ratio, i) => {
      const r = (Math.min(W, H) / 2) * ratio;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(10, 89, 247, ${0.05 - i * 0.01})`;
      ctx.lineWidth = i === 0 ? 1.0 : 0.6;
      ctx.setLineDash(i === 1 ? [4, 8] : []);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Energy channels from core to nodes
    nodePositions.forEach(node => {
      const grad = ctx.createLinearGradient(cx, cy, node.x, node.y);
      grad.addColorStop(0,   `${node.color}44`);
      grad.addColorStop(0.5, `${node.color}22`);
      grad.addColorStop(1,   `${node.color}08`);
      ctx.beginPath();
      const mx = (cx + node.x) / 2 + (node.y - cy) * 0.18;
      const my = (cy + node.y) / 2 - (node.x - cx) * 0.18;
      ctx.moveTo(cx, cy);
      ctx.quadraticCurveTo(mx, my, node.x, node.y);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    });

    return nodePositions;
  }, []);

  // Particle system
  useEffect(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return;

    interface Particle {
      nodeIdx: number;
      t: number;
      speed: number;
      size: number;
      opacity: number;
    }

    const nodePositions = [
      { top: '5%',  left: '50%', color: '#B8DCFF' },
      { top: '24%', left: '84%', color: '#A8D5FF' },
      { top: '79%', left: '70%', color: '#8FC8FF' },
      { top: '79%', left: '30%', color: '#7DBDFF' },
      { top: '24%', left: '16%', color: '#C8E2FF' },
    ];

    const particles: Particle[] = [];
    nodePositions.forEach((_, ni) => {
      for (let i = 0; i < 8; i++) {
        particles.push({
          nodeIdx: ni,
          t: i / 8,
          speed: 0.0018 + Math.random() * 0.0012,
          size: 2.5 + Math.random() * 2,
          opacity: 0.6 + Math.random() * 0.4,
        });
      }
    });

    let raf = -1;
    const animate = () => {
      const W = stage.offsetWidth;
      const H = stage.offsetHeight;
      if (W === 0) { raf = requestAnimationFrame(animate); return; }
      canvas.width = W;
      canvas.height = H;
      const ctx = canvas.getContext('2d')!;
      const cx = W / 2, cy = H / 2;

      ctx.clearRect(0, 0, W, H);

      drawField();

      const nodes = nodePositions.map(n => ({
        x: (parseFloat(n.left) / 100) * W,
        y: (parseFloat(n.top)  / 100) * H,
        color: n.color,
      }));

      particles.forEach(p => {
        p.t += p.speed;
        if (p.t > 1) p.t -= 1;

        const node = nodes[p.nodeIdx];
        const mx = (cx + node.x) / 2 + (node.y - cy) * 0.18;
        const my = (cy + node.y) / 2 - (node.x - cx) * 0.18;
        const t = p.t;
        const px = (1-t)*(1-t)*cx + 2*(1-t)*t*mx + t*t*node.x;
        const py = (1-t)*(1-t)*cy + 2*(1-t)*t*my + t*t*node.y;

        const boost = t > 0.8 ? (t - 0.8) / 0.2 : 0;
        const r = p.size * (1 + boost * 1.5);
        const alpha = p.opacity * (0.4 + t * 0.6);

        const grd = ctx.createRadialGradient(px, py, 0, px, py, r * 2.5);
        grd.addColorStop(0, `${node.color}${Math.round(alpha * 255).toString(16).padStart(2,'0')}`);
        grd.addColorStop(1, `${node.color}00`);
        ctx.beginPath();
        ctx.arc(px, py, r * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();
      });

      raf = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(raf);
  }, [drawField]);

  // Feature card data from real modules
  const featureCards = useMemo(() => [
    {
      id: 'decision',
      title: '决策副本',
      description: 'AI 核心建模、多维度智能评估、决策分析工作台与平行人生入口。',
      route: '/decision',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
      ),
    },
    {
      id: 'knowledge',
      title: '知识星图',
      description: '多维关系映射、记忆网络构建、智能关联发现，构建你的专属知识网络。',
      route: '/knowledge-graph',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          <path d="M2 12h20"/>
        </svg>
      ),
    },
    {
      id: 'parallel-life',
      title: '平行人生',
      description: '塔罗牌决策游戏，探索人生选择的多元可能性，收集决策逻辑画像。',
      route: '/parallel-life',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      ),
    },
    {
      id: 'dashboard',
      title: '洞察仪表盘',
      description: '可视化数据洞察，实时追踪学习进度与成长轨迹，让每一步都清晰可见。',
      route: '/dashboard',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <line x1="3" y1="9" x2="21" y2="9"/>
          <line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
      ),
    },
    {
      id: 'meta-agent',
      title: '多智能体协调',
      description: '6个专项智能体并行分析，Meta 智能体汇总协调，输出综合评分。',
      route: '/meta-agent',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 2 7 12 12 22 7 12 2"/>
          <polyline points="2 17 12 22 22 17"/>
          <polyline points="2 12 12 17 22 12"/>
        </svg>
      ),
    },
    {
      id: 'chat',
      title: 'AI 对话',
      description: '与 AI 核心实时协作，支持多轮上下文理解，让交流如呼吸般自然。',
      route: '/chat',
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      ),
    },
  ], []);

  // Carousel cards from real features
  const carouselCards = useMemo(() => [
    {
      id: 'emergence',
      badge: 'new',
      title: '涌现模式检测',
      description: '发现行为模式中的涌现特征，AI 从复杂交互中提取有价值的洞察，提前预警潜在风险与机遇。',
      route: '/emergence-patterns',
      meta: '新功能',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      ),
    },
    {
      id: 'life-insights',
      badge: 'beta',
      title: '人生领域洞察',
      description: '多维度分析人生各领域的发展态势，识别关键转折点与优化机会，制定个性化成长路径。',
      route: '/life-domain-insights',
      meta: '测试版',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12" y2="8"/>
        </svg>
      ),
    },
    {
      id: 'lora',
      badge: 'coming',
      title: 'LoRA 个性化训练',
      description: '个性化模型微调服务，训练专属 AI 角色，让 AI 更懂你的需求与偏好，实现深度定制。',
      route: '/lora-training',
      meta: '规划中',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2a10 10 0 1 0 10 10H12V2z"/>
          <path d="M20 12a8 8 0 0 0-8-8v8h8z"/>
        </svg>
      ),
    },
    {
      id: 'learning',
      badge: 'new',
      title: '学习进度追踪',
      description: '智能追踪学习轨迹，分析效率瓶颈，提供个性化改进建议，让学习效果可视化、可量化。',
      route: '/learning-progress',
      meta: '可用',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
      ),
    },
    {
      id: 'risk-analysis',
      badge: 'new',
      title: '决策风险评估',
      description: '全面分析每个决策选项的潜在风险，提供量化风险评分，帮助你做出更理性的选择。',
      route: '/risk-analysis',
      meta: '新功能',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      ),
    },
    {
      id: 'career-path',
      badge: 'beta',
      title: '职业发展模拟',
      description: 'AI 模拟不同职业路径的发展前景，评估技能差距，提供职业转型建议与学习资源推荐。',
      route: '/career-simulation',
      meta: '测试版',
      icon: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
        </svg>
      ),
    },
  ], []);

  const carouselRef = useRef<HTMLDivElement>(null);

  const scrollCarousel = (direction: 'left' | 'right') => {
    if (carouselRef.current) {
      const scrollAmount = 444;
      carouselRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
    }
  };

  return (
    <div className="ls-homepage">
      {/* Scroll Progress */}
      <div 
        className="ls-scroll-progress" 
        style={{ width: `${scrollProgress}%` }}
      />

      {/* Animated Background */}
      <div className="ls-background">
        <div className="ls-blob ls-blob-1" />
        <div className="ls-blob ls-blob-2" />
        <div className="ls-blob ls-blob-3" />
      </div>

      {/* Hero Section - Keep existing pentagram */}
      <section className="hero-card pentagram-hero harmony-fullscreen">
        <div className="pentagram-side-text pentagram-side-left harmony-enter-fade-left">
          <h1 className="brand-title">择境</h1>
          <p className="brand-subtitle">ChoiceRealm</p>
          
          <div className="divider-line"></div>
          
          <h2 className="side-text-title-large">知识星图</h2>
          <div className="side-text-features">
            <p>多维关系映射</p>
            <p>记忆网络构建</p>
            <p>智能关联发现</p>
          </div>
          
          <h2 className="side-text-title-large" style={{ marginTop: '48px' }}>智能决策</h2>
          <div className="side-text-features">
            <p>多路径分析</p>
            <p>历史追溯校准</p>
            <p>最优方案推荐</p>
          </div>
        </div>

        <div className="hero-side harmony-enter-fade-scale harmony-delay-3">
          <div className="pentagram-stage" ref={stageRef}>
            <div className="pentagram-aura pentagram-aura-primary" />
            <div className="pentagram-aura pentagram-aura-secondary" />

            <canvas
              ref={canvasRef}
              aria-hidden="true"
              style={{
                position: 'absolute', inset: 0,
                width: '100%', height: '100%',
                pointerEvents: 'none', zIndex: 1,
              }}
            />

            <div className="pentagram-ring pentagram-ring-outer" />
            <div className="pentagram-ring pentagram-ring-mid" />
            <div className="pentagram-ring pentagram-ring-inner" />

            {pentagramNodes.map((node) => (
              <button
                key={node.id}
                className={`pentagram-node is-${node.status}`}
                style={
                  {
                    '--node-top': node.top,
                    '--node-left': node.left,
                    '--node-start': node.gradient[0],
                    '--node-end': node.gradient[1],
                  } as CSSProperties
                }
                onClick={() => {
                  console.log('[HomePage] Node clicked:', node.title, 'Time:', performance.now());
                  if (node.id === 'profile') {
                    setProfileMenuOpen(v => !v);
                  } else {
                    node.route && navigate(node.route);
                  }
                }}
                type="button"
              >
                <span className="pentagram-node-orbit" />
                <span className="pentagram-node-core">
                  <small>{node.subtitle}</small>
                  <strong>{node.title}</strong>
                </span>
                {node.id === 'profile' && profileMenuOpen && (
                  <div
                    ref={profileMenuRef}
                    style={{
                      position: 'absolute',
                      bottom: 'calc(100% + 10px)',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      background: 'rgba(13,27,42,0.96)',
                      backdropFilter: 'blur(20px)',
                      border: '1px solid rgba(99,179,237,0.2)',
                      borderRadius: 14,
                      padding: '6px 0',
                      minWidth: 140,
                      boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                      zIndex: 999,
                    }}
                    onClick={e => e.stopPropagation()}
                  >
                    {user ? (
                      <>
                        <div style={{ padding: '8px 16px 6px', fontSize: 12, color: 'rgba(255,255,255,0.45)', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: 4 }}>
                          {user.nickname || user.username}
                        </div>
                        <button
                          style={menuItemStyle}
                          onClick={() => { setProfileMenuOpen(false); navigate('/profile'); }}
                        >个人中心</button>
                        <button
                          style={{ ...menuItemStyle, color: '#FF6B6B' }}
                          onClick={() => { setProfileMenuOpen(false); void logout().then(() => navigate('/auth')); }}
                        >退出登录</button>
                      </>
                    ) : (
                      <button
                        style={menuItemStyle}
                        onClick={() => { setProfileMenuOpen(false); navigate('/auth'); }}
                      >去登录</button>
                    )}
                  </div>
                )}
              </button>
            ))}

            <button
              className="pentagram-core"
              onClick={() => setIsAICoreOpen(true)}
              type="button"
              aria-label="打开 AI 核心"
            >
              <span className="pentagram-core-halo" />
              <span className="pentagram-core-ring pentagram-core-ring-outer" />
              <span className="pentagram-core-ring pentagram-core-ring-inner" />
              <span className="pentagram-core-spark pentagram-core-spark-a" />
              <span className="pentagram-core-spark pentagram-core-spark-b" />
              <span className="pentagram-core-shell">
                <span className="pentagram-core-shell-gloss" />
                <span className="pentagram-core-shell-grid" />
                <span className="pentagram-core-shell-pulse" />
                <small>Central Engine</small>
                <strong>AI 核心</strong>
                <span>感知 / 分析 / 决策</span>
              </span>
            </button>
          </div>
        </div>

        {/* Scroll Hint */}
        <div className="ls-scroll-hint" onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}>
          <span className="ls-scroll-hint-text">向下滚动</span>
          <div className="ls-scroll-hint-arrow" />
        </div>
      </section>

      {/* Content Sections */}
      <div className="ls-content-container">
        
        {/* ── Core Architecture Section ──────────────────────────────── */}
        <section className="ls-section">
          <div className="ls-section-header ls-reveal">
            <span className="ls-section-eyebrow">核心架构</span>
            <h2 className="ls-section-title">多智能体协同系统</h2>
            <p className="ls-section-subtitle">
              6大专项智能体 + Meta 协调引擎，构建全方位的 AI 决策支持体系
            </p>
          </div>

          <div className="ls-architecture-card ls-reveal-scale">
            <div className="ls-arch-visual">
              <div className="ls-arch-center">
                <div className="ls-arch-core-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M12 1v6m0 6v6M1 12h6m6 0h6"/>
                    <circle cx="12" cy="12" r="10" opacity="0.3"/>
                  </svg>
                </div>
                <h3>Meta Agent</h3>
                <p>协调中枢</p>
              </div>
              
              <div className="ls-arch-agents">
                <div className="ls-arch-agent ls-arch-agent-1">
                  <div className="ls-arch-agent-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                    </svg>
                  </div>
                  <span>决策分析</span>
                </div>
                
                <div className="ls-arch-agent ls-arch-agent-2">
                  <div className="ls-arch-agent-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <path d="M2 12h20"/>
                    </svg>
                  </div>
                  <span>知识图谱</span>
                </div>
                
                <div className="ls-arch-agent ls-arch-agent-3">
                  <div className="ls-arch-agent-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                  </div>
                  <span>对话理解</span>
                </div>
                
                <div className="ls-arch-agent ls-arch-agent-4">
                  <div className="ls-arch-agent-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="18" height="18" rx="2"/>
                      <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                  </div>
                  <span>数据洞察</span>
                </div>
                
                <div className="ls-arch-agent ls-arch-agent-5">
                  <div className="ls-arch-agent-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                      <circle cx="9" cy="7" r="4"/>
                    </svg>
                  </div>
                  <span>方案评估</span>
                </div>
                
                <div className="ls-arch-agent ls-arch-agent-6">
                  <div className="ls-arch-agent-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                    </svg>
                  </div>
                  <span>涌现检测</span>
                </div>
              </div>
            </div>
            
            <div className="ls-arch-content">
              <div className="ls-arch-description">
                <h4>智能体协同工作流</h4>
                <p>
                  系统采用多智能体协同架构，6个专项智能体各司其职：决策分析 Agent 负责评估方案，知识图谱 Agent 构建关系网络，
                  对话理解 Agent 处理自然交互，数据洞察 Agent 挖掘模式，方案评估 Agent 分析可行性，涌现检测 Agent 发现潜在机会。
                  Meta Agent 作为协调中枢，整合各智能体的分析结果，输出综合评分与行动建议。
                </p>
              </div>
              
              <div className="ls-arch-features">
                <div className="ls-arch-feature">
                  <div className="ls-arch-feature-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                  </div>
                  <div>
                    <h5>并行处理</h5>
                    <p>6个智能体同时工作，大幅提升分析效率</p>
                  </div>
                </div>
                
                <div className="ls-arch-feature">
                  <div className="ls-arch-feature-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2v20M2 12h20"/>
                    </svg>
                  </div>
                  <div>
                    <h5>智能协调</h5>
                    <p>Meta Agent 统筹全局，确保决策一致性</p>
                  </div>
                </div>
                
                <div className="ls-arch-feature">
                  <div className="ls-arch-feature-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12 6 12 12 16 14"/>
                    </svg>
                  </div>
                  <div>
                    <h5>实时反馈</h5>
                    <p>动态调整策略，持续优化决策质量</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Hero Showcase Section ──────────────────────────────── */}
        <section className="ls-showcase-section">
          <div className="ls-showcase-container">
            {/* 视频大框 - 嵌入到第二个页面 */}
            <VideoShowcase isEmbedded={true} />

            <div className="ls-showcase-wrapper ls-reveal-scale">
              {/* Background layers */}
              <div className="ls-showcase-bg" />
              <div className="ls-showcase-grid" />
              
              {/* Floating particles */}
              <div className="ls-showcase-particles">
                <div className="ls-showcase-particle" />
                <div className="ls-showcase-particle" />
                <div className="ls-showcase-particle" />
                <div className="ls-showcase-particle" />
                <div className="ls-showcase-particle" />
                <div className="ls-showcase-particle" />
              </div>
              
              {/* Corner decorations */}
              <div className="ls-showcase-corner ls-showcase-corner-tl" />
              <div className="ls-showcase-corner ls-showcase-corner-tr" />
              <div className="ls-showcase-corner ls-showcase-corner-bl" />
              <div className="ls-showcase-corner ls-showcase-corner-br" />
            </div>
            
            {/* Interactive Feature Showcase - Phone Style */}
            <div className="ls-interactive-showcase">
              <div className="ls-interactive-content ls-reveal-left">
                <h2 className="ls-interactive-title">看它，满屏都是戏</h2>
                <p className="ls-interactive-subtitle">
                  融入 AIGC 能力，可没有理解字体特征，星屏定制专属签名，还能将文字与图形巧妙合一，打造更有趣的合体字；智慧构图功能，可根据你的照片自动化景深，布局与色彩，一键生成风格多变的个性壁纸。
                </p>
                
                <div className="ls-interactive-features">
                  <div className="ls-interactive-feature-item" onClick={() => navigate('/parallel-life')}>
                    <div className="ls-interactive-feature-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
                      </svg>
                    </div>
                    <div className="ls-interactive-feature-text">
                      <h4>平行人生</h4>
                      <p>探索多元可能</p>
                    </div>
                  </div>

                  <div className="ls-interactive-feature-item" onClick={() => navigate('/meta-agent')}>
                    <div className="ls-interactive-feature-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                        <polyline points="2 17 12 22 22 17"/>
                        <polyline points="2 12 12 17 22 12"/>
                      </svg>
                    </div>
                    <div className="ls-interactive-feature-text">
                      <h4>多智能体协调</h4>
                      <p>AI 并行分析</p>
                    </div>
                  </div>

                  <div className="ls-interactive-feature-item" onClick={() => navigate('/chat')}>
                    <div className="ls-interactive-feature-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                    </div>
                    <div className="ls-interactive-feature-text">
                      <h4>AI 对话</h4>
                      <p>实时协作</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="ls-interactive-laptop ls-reveal-right">
                <div className="ls-laptop-mockup">
                  <div className="ls-laptop-screen">
                    <div className="ls-laptop-camera" />
                    <div className="ls-laptop-content">
                      {/* Browser Chrome */}
                      <div className="ls-browser-chrome">
                        <div className="ls-browser-dots">
                          <span className="ls-dot ls-dot-red" />
                          <span className="ls-dot ls-dot-yellow" />
                          <span className="ls-dot ls-dot-green" />
                        </div>
                        <div className="ls-browser-tabs">
                          <div className="ls-browser-tab ls-tab-active">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="12" cy="12" r="10"/>
                            </svg>
                            <span>择境 - AI 决策平台</span>
                          </div>
                        </div>
                      </div>
                      
                      {/* Dashboard Content */}
                      <div className="ls-dashboard-view">
                        <div className="ls-dashboard-sidebar">
                          <div className="ls-sidebar-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="3" y="3" width="7" height="7"/>
                              <rect x="14" y="3" width="7" height="7"/>
                              <rect x="14" y="14" width="7" height="7"/>
                              <rect x="3" y="14" width="7" height="7"/>
                            </svg>
                          </div>
                          <div className="ls-sidebar-item ls-sidebar-active">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                            </svg>
                          </div>
                          <div className="ls-sidebar-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="12" cy="12" r="10"/>
                            </svg>
                          </div>
                          <div className="ls-sidebar-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                            </svg>
                          </div>
                        </div>
                        
                        <div className="ls-dashboard-main">
                          <div className="ls-dashboard-header">
                            <div className="ls-dashboard-title">决策分析中心</div>
                            <div className="ls-dashboard-status">
                              <span className="ls-status-dot" />
                              6个智能体运行中
                            </div>
                          </div>
                          
                          <div className="ls-dashboard-cards">
                            <div className="ls-dash-card">
                              <div className="ls-dash-card-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                                </svg>
                              </div>
                              <div className="ls-dash-card-value">92%</div>
                              <div className="ls-dash-card-label">决策准确率</div>
                            </div>
                            
                            <div className="ls-dash-card">
                              <div className="ls-dash-card-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                                </svg>
                              </div>
                              <div className="ls-dash-card-value">1,247</div>
                              <div className="ls-dash-card-label">分析方案</div>
                            </div>
                            
                            <div className="ls-dash-card">
                              <div className="ls-dash-card-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                  <circle cx="12" cy="12" r="10"/>
                                </svg>
                              </div>
                              <div className="ls-dash-card-value">3.2k</div>
                              <div className="ls-dash-card-label">知识节点</div>
                            </div>
                          </div>
                          
                          <div className="ls-dashboard-chart">
                            <div className="ls-chart-bars">
                              <div className="ls-chart-bar" style={{ height: '60%' }} />
                              <div className="ls-chart-bar" style={{ height: '85%' }} />
                              <div className="ls-chart-bar" style={{ height: '45%' }} />
                              <div className="ls-chart-bar" style={{ height: '92%' }} />
                              <div className="ls-chart-bar" style={{ height: '78%' }} />
                              <div className="ls-chart-bar" style={{ height: '95%' }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="ls-laptop-base">
                    <div className="ls-laptop-keyboard" />
                    <div className="ls-laptop-trackpad" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Horizontal Scroll Carousel ────────────────────── */}
        <section className="ls-carousel-section">
          <div className="ls-carousel-header">
            <div className="ls-section-header ls-reveal-left">
              <span className="ls-section-eyebrow">持续进化</span>
              <h2 className="ls-section-title">探索更多可能</h2>
            </div>
            <div className="ls-carousel-nav ls-reveal-right">
              <button 
                className="ls-carousel-nav-btn"
                onClick={() => scrollCarousel('left')}
                aria-label="向左滚动"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M15 18l-6-6 6-6"/>
                </svg>
              </button>
              <button 
                className="ls-carousel-nav-btn"
                onClick={() => scrollCarousel('right')}
                aria-label="向右滚动"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </button>
            </div>
          </div>

          <div className="ls-carousel-track" ref={carouselRef}>
            {carouselCards.map((card, index) => (
              <article
                key={card.id}
                className={`ls-carousel-card ls-reveal-scale ls-delay-${(index % 4 + 1) * 100}`}
                onClick={() => navigate(card.route)}
              >
                <div className="ls-carousel-icon">
                  {card.icon}
                </div>
                <span className={`ls-carousel-badge ${card.badge}`}>{card.meta}</span>
                <h3 className="ls-carousel-title">{card.title}</h3>
                <p className="ls-carousel-description">{card.description}</p>
                <div className="ls-carousel-footer">
                  <span className="ls-carousel-cta">
                    了解更多
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* ── CTA Section ──────────────────────────────────── */}
        <section className="ls-cta-section">
          <div className="ls-cta-bg" />
          <div className="ls-reveal-scale">
            <h2 className="ls-cta-title">准备好开始了吗？</h2>
            <p className="ls-cta-description">
              加入择境，体验 AI 驱动的智能决策管理与人生规划
            </p>
            <div className="ls-cta-actions">
              <button className="ls-btn ls-btn-primary" onClick={() => setIsAICoreOpen(true)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                立即体验 AI 核心
              </button>
              <button className="ls-btn ls-btn-secondary" onClick={() => navigate('/ability-islands')}>
                探索全部功能
              </button>
            </div>
          </div>
        </section>

      </div>

      {/* Bottom Navigation */}
      <nav className="homepage-bottom-nav">
        <NavLink to="/" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`} end>
          <span>总览</span>
        </NavLink>
        <NavLink to="/decision" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
          <span>决策</span>
        </NavLink>
        <NavLink to="/chat" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
          <span>对话</span>
        </NavLink>
        <NavLink to="/ability-islands" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
          <span>能力</span>
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
          <span>我的</span>
        </NavLink>
      </nav>

      {/* AI Core Modal */}
      {isAICoreOpen && (
        <AICoreModal onClose={() => setIsAICoreOpen(false)} />
      )}

      {/* Global AI Floating Button */}
      <GlobalAIFloatingButton />
    </div>
  );
}
