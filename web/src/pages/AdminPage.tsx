import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { API_BASE_URL } from '../services/api';
import { AICoreModal } from '../components/ai/AICoreModal';
import { GlobalAIFloatingButton } from '../components/ai/GlobalAIFloatingButton';
import '../styles/AdminPage.css';

interface PentagramNode {
  id: string;
  title: string;
  subtitle: string;
  route?: string;
  action?: () => void;
  top: string;
  left: string;
  gradient: [string, string];
  status: 'live' | 'preview' | 'planned';
}

interface UserStats {
  total: number;
  active: number;
  inactive: number;
  new_7d: number;
  active_24h: number;
}

interface DecisionStats {
  total: number;
  today: number;
  this_week: number;
  by_category: Record<string, number>;
  avg_options: number;
}

interface SystemStats {
  users: UserStats;
  decisions: DecisionStats;
  timestamp: string;
}

export function AdminPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAICoreOpen, setIsAICoreOpen] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  // 简化权限检查：只检查是否登录
  useEffect(() => {
    if (!user) {
      // 未登录，跳转到登录页
      navigate('/auth');
      return;
    }
    
    setLoading(false);
  }, [user, navigate]);

  // 获取系统统计
  useEffect(() => {
    if (!user || loading) return;

    const fetchStats = async () => {
      try {
        const authData = localStorage.getItem('choicerealm.web.auth');
        if (!authData) return;
        
        const auth = JSON.parse(authData);
        const token = auth.token;
        
        const response = await fetch(`${API_BASE_URL}/api/admin/stats`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        } else if (response.status === 403) {
          // 没有管理员权限
          alert('您没有管理员权限');
          navigate('/');
        }
      } catch (error) {
        // 静默处理连接错误，避免控制台刷屏
        // 只在开发环境输出
        if (import.meta.env.DEV) {
          console.log('获取统计数据失败（后端可能未启动）:', error);
        }
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, [user, loading, navigate]);

  const pentagramNodes = useMemo<PentagramNode[]>(() => [
    {
      id: 'users',
      title: '用户管理',
      subtitle: '管理用户',
      route: '/admin/users',
      top: '5%',
      left: '50%',
      gradient: ['#B0D9FF', '#7DBDFF'],
      status: 'live',
    },
    {
      id: 'stats',
      title: '系统统计',
      subtitle: '数据分析',
      route: '/admin/stats',
      top: '24%',
      left: '84%',
      gradient: ['#B0D9FF', '#7DBDFF'],
      status: 'live',
    },
    {
      id: 'activities',
      title: '活动监控',
      subtitle: '实时监控',
      action: () => {
        alert('活动监控功能开发中...');
      },
      top: '79%',
      left: '70%',
      gradient: ['#B0D9FF', '#7DBDFF'],
      status: 'preview',
    },
    {
      id: 'settings',
      title: '系统设置',
      subtitle: '配置管理',
      action: () => {
        alert('系统设置功能开发中...');
      },
      top: '79%',
      left: '30%',
      gradient: ['#B0D9FF', '#7DBDFF'],
      status: 'preview',
    },
    {
      id: 'logout',
      title: '退出登录',
      subtitle: '安全退出',
      action: async () => {
        if (confirm('确定要退出登录吗？')) {
          const authData = localStorage.getItem('choicerealm.web.auth');
          if (authData) {
            const auth = JSON.parse(authData);
            try {
              await fetch(`${API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${auth.token}`
                },
                body: JSON.stringify({ token: auth.token })
              });
            } catch (error) {
              console.error('退出登录失败:', error);
            }
          }
          // 清除本地存储
          localStorage.removeItem('choicerealm.web.auth');
          // 强制跳转到登录页
          window.location.href = '/auth';
        }
      },
      top: '24%',
      left: '16%',
      gradient: ['#B0D9FF', '#7DBDFF'],
      status: 'live',
    },
  ], [navigate]);

  // Canvas particle flow
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

  if (loading) {
    return (
      <div className="admin-loading">
        <div className="loading-spinner" />
        <p>加载中...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="admin-page">
      {/* Animated Background */}
      <div className="admin-background">
        <div className="admin-blob admin-blob-1" />
        <div className="admin-blob admin-blob-2" />
        <div className="admin-blob admin-blob-3" />
      </div>

      {/* Hero Section */}
      <section className="admin-hero">
        <div className="admin-side-text admin-side-left">
          <h1 className="admin-brand-title">管理中心</h1>
          <p className="admin-brand-subtitle">Admin Center</p>
          
          <div className="admin-divider-line"></div>
          
          <h2 className="admin-side-title">系统概览</h2>
          {stats && (
            <>
              <div className="admin-stats-section">
                <h3 className="admin-stats-section-title">用户数据</h3>
                <div className="admin-stats-summary">
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">总用户</span>
                    <span className="admin-stat-value">{stats.users.total}</span>
                  </div>
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">活跃用户</span>
                    <span className="admin-stat-value">{stats.users.active}</span>
                  </div>
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">24h活跃</span>
                    <span className="admin-stat-value">{stats.users.active_24h}</span>
                  </div>
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">7天新增</span>
                    <span className="admin-stat-value">{stats.users.new_7d}</span>
                  </div>
                </div>
              </div>
              
              <div className="admin-stats-section">
                <h3 className="admin-stats-section-title">决策数据</h3>
                <div className="admin-stats-summary">
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">总决策数</span>
                    <span className="admin-stat-value admin-stat-primary">{stats.decisions.total}</span>
                  </div>
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">今日决策</span>
                    <span className="admin-stat-value admin-stat-primary">{stats.decisions.today}</span>
                  </div>
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">本周决策</span>
                    <span className="admin-stat-value admin-stat-primary">{stats.decisions.this_week}</span>
                  </div>
                  <div className="admin-stat-item">
                    <span className="admin-stat-label">平均选项</span>
                    <span className="admin-stat-value admin-stat-primary">{stats.decisions.avg_options}</span>
                  </div>
                </div>
                
                {Object.keys(stats.decisions.by_category).length > 0 && (
                  <div className="admin-category-stats">
                    <h4 className="admin-category-title">决策分类</h4>
                    {Object.entries(stats.decisions.by_category)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 5)
                      .map(([category, count]) => (
                        <div key={category} className="admin-category-item">
                          <span className="admin-category-name">{category}</span>
                          <span className="admin-category-count">{count}</span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </>
          )}
          
          <div className="admin-quick-actions">
            <button 
              className="admin-quick-action-btn"
              onClick={() => navigate('/admin/users')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              管理用户
            </button>
          </div>
        </div>

        <div className="admin-hero-side">
          <div className="admin-pentagram-stage" ref={stageRef}>
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
                  if (node.action) {
                    node.action();
                  } else if (node.route) {
                    navigate(node.route);
                  }
                }}
                type="button"
              >
                <span className="pentagram-node-orbit" />
                <span className="pentagram-node-core">
                  <small>{node.subtitle}</small>
                  <strong>{node.title}</strong>
                </span>
              </button>
            ))}

            <button
              className="pentagram-core admin-core"
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
                <small>Admin Control</small>
                <strong>管理核心</strong>
                <span>监控 / 管理 / 配置</span>
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* AI Core Modal */}
      {isAICoreOpen && (
        <AICoreModal 
          onClose={() => setIsAICoreOpen(false)} 
          disableNavigation={true}
          disableQuickActions={true}
        />
      )}

      {/* Global AI Floating Button */}
      <GlobalAIFloatingButton 
        disableNavigation={true}
        disableQuickActions={true}
      />
    </div>
  );
}
