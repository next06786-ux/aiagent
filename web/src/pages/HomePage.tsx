import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AICoreModal } from '../components/ai/AICoreModal';
import { GlobalAIFloatingButton } from '../components/ai/GlobalAIFloatingButton';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { StatusPill } from '../components/common/StatusPill';
import { featureModules } from '../data/features';
import { useAuth } from '../hooks/useAuth';
import { listConversations } from '../services/chat';
import { getFutureOsHistory } from '../services/futureOs';
import { API_BASE_URL } from '../services/api';
import { testApiConnection } from '../utils/networkDiagnostics';
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
  const [predictionCount, setPredictionCount] = useState(0);
  const [conversationCount, setConversationCount] = useState(0);
  const [branchCount, setBranchCount] = useState(0);
  const [knowledgeMode, setKnowledgeMode] = useState('people');
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [isAICoreOpen, setIsAICoreOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // close menu on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setProfileMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }

    let active = true;
    
    // 网络诊断和预热
    console.log('[HomePage] 🔥 开始网络诊断和API预热');
    testApiConnection(API_BASE_URL).then(() => {
      console.log('[HomePage] ✅ 网络诊断完成');
    });
    
    Promise.allSettled([
      getFutureOsHistory(user.user_id),
      listConversations(user.user_id),
    ]).then((results) => {
      if (!active) {
        return;
      }

      const [historyResult, chatResult] = results;

      if (historyResult.status === 'fulfilled') {
        setPredictionCount(historyResult.value.length);
        setBranchCount(
          historyResult.value.reduce(
            (sum, item) => sum + Number(item.options_count || 0),
            0,
          ),
        );
      }
      if (chatResult.status === 'fulfilled') {
        setConversationCount(chatResult.value.length);
      }
      setKnowledgeMode(historyResult.status === 'fulfilled' && historyResult.value.length > 0 ? 'signals' : 'people');
    });

    return () => {
      active = false;
    };
  }, [user]);

  const menuItemStyle: CSSProperties = {
    display: 'block', width: '100%', padding: '9px 16px',
    background: 'transparent', border: 'none', cursor: 'pointer',
    fontSize: 13, fontWeight: 600, color: '#e8f0fe', textAlign: 'left',
  };

  const pentagramNodes = useMemo<PentagramNode[]>(    () => [
      {
        id: 'decision',
        title: '决策副本',
        subtitle: '推演入口',
        route: '/decision',
        top: '5%',
        left: '50%',
        gradient: ['#4facfe', '#00f2fe'],  // 华为蓝青渐变
        status: 'live',
      },
      {
        id: 'history',
        title: '预测历史',
        subtitle: '回访校准',
        route: '/decision/history',
        top: '24%',
        left: '84%',
        gradient: ['#43e97b', '#38f9d7'],  // 清新绿蓝渐变
        status: 'live',
      },
      {
        id: 'chat',
        title: 'AI 对话',
        subtitle: '实时协作',
        route: '/chat',
        top: '79%',
        left: '70%',
        gradient: ['#fa709a', '#fee140'],  // 活力粉橙渐变
        status: 'live',
      },
      {
        id: 'profile',
        title: '个人中心',
        subtitle: '身份画像',
        route: '/profile',
        top: '79%',
        left: '30%',
        gradient: ['#a18cd1', '#fbc2eb'],  // 梦幻紫粉渐变
        status: 'live',
      },
      {
        id: 'knowledge-graph',
        title: '知识星图',
        subtitle: '记忆星空',
        route: '/knowledge-graph',
        top: '24%',
        left: '16%',
        gradient: ['#0A59F7', '#6B48FF'],  // 华为品牌蓝紫渐变
        status: 'live',
      },
    ],
    [],
  );

  // Canvas 粒子流：从核心向各节点发射能量粒子
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

    // 节点位置（与 CSS top/left 对应）HarmonyOS 6 纯净色调
    const nodePositions = [
      { top: '5%',  left: '50%', color: '#4facfe' },  // 华为蓝青渐变
      { top: '24%', left: '84%', color: '#43e97b' },  // 清新绿蓝渐变
      { top: '79%', left: '70%', color: '#fa709a' },  // 活力粉橙渐变
      { top: '79%', left: '30%', color: '#a18cd1' },  // 梦幻紫粉渐变
      { top: '24%', left: '16%', color: '#0A59F7' },  // 华为品牌蓝紫渐变
    ].map(n => ({
      x: (parseFloat(n.left) / 100) * W,
      y: (parseFloat(n.top)  / 100) * H,
      color: n.color,
    }));

    // ── 六边形网格背�?──────────────────────────────────────
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
        ctx.strokeStyle = `rgba(10, 89, 247, ${alpha})`;  // HarmonyOS 6 蓝色
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }
    }
    ctx.restore();

    // ── 同心圆弧装饰 ────────────────────────────────────────
    [0.44, 0.72, 0.96].forEach((ratio, i) => {
      const r = (Math.min(W, H) / 2) * ratio;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(10, 89, 247, ${0.05 - i * 0.01})`;  // HarmonyOS 6 蓝色
      ctx.lineWidth = i === 0 ? 1.0 : 0.6;
      ctx.setLineDash(i === 1 ? [4, 8] : []);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // ── 从核心到节点的弧形能量通道 ──────────────────────────
    nodePositions.forEach(node => {
      const grad = ctx.createLinearGradient(cx, cy, node.x, node.y);
      grad.addColorStop(0,   `${node.color}44`);
      grad.addColorStop(0.5, `${node.color}22`);
      grad.addColorStop(1,   `${node.color}08`);
      ctx.beginPath();
      // 贝塞尔曲线，控制点偏向圆心外侧，产生弧形
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

  // 粒子系统
  useEffect(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return;

    interface Particle {
      nodeIdx: number;
      t: number;       // 0到1 沿路径进度
      speed: number;
      size: number;
      opacity: number;
    }

    const nodePositions = [
      { top: '5%',  left: '50%', color: '#4facfe' },  // 华为蓝青渐变
      { top: '24%', left: '84%', color: '#43e97b' },  // 清新绿蓝渐变
      { top: '79%', left: '70%', color: '#fa709a' },  // 活力粉橙渐变
      { top: '79%', left: '30%', color: '#a18cd1' },  // 梦幻紫粉渐变
      { top: '24%', left: '16%', color: '#0A59F7' },  // 华为品牌蓝紫渐变
    ];

    const particles: Particle[] = [];
    // 初始化粒子，每条路8 个，错开相位
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

      // 重绘静态背景      drawField();

      // 节点实际坐标
      const nodes = nodePositions.map(n => ({
        x: (parseFloat(n.left) / 100) * W,
        y: (parseFloat(n.top)  / 100) * H,
        color: n.color,
      }));

      // 绘制粒子
      particles.forEach(p => {
        p.t += p.speed;
        if (p.t > 1) p.t -= 1;

        const node = nodes[p.nodeIdx];
        // 贝塞尔插值
        const mx = (cx + node.x) / 2 + (node.y - cy) * 0.18;
        const my = (cy + node.y) / 2 - (node.x - cx) * 0.18;
        const t = p.t;
        const px = (1-t)*(1-t)*cx + 2*(1-t)*t*mx + t*t*node.x;
        const py = (1-t)*(1-t)*cy + 2*(1-t)*t*my + t*t*node.y;

        // 粒子在接近节点时变大变亮
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

  return (
    <div className="homepage-fullscreen-wrapper">
      <div className="shell-backdrop">
        <div className="shell-glow shell-glow-primary" />
        <div className="shell-glow shell-glow-secondary" />
        <div className="shell-glow shell-glow-accent" />
      </div>
      <section className="hero-card pentagram-hero harmony-fullscreen">
        {/* 左侧文案 - 与法阵融合 */}
        <div className="pentagram-side-text pentagram-side-left harmony-enter-fade-left">
          <div className="side-text-glow" />
          <p className="side-text-label">智能感知</p>
          <h3 className="side-text-title">知识星图</h3>
          <p className="side-text-desc">
            多维关系映射<br/>
            记忆网络构建<br/>
            智能关联发现
          </p>
        </div>

        {/* 右侧文案 - 与法阵融合 */}
        <div className="pentagram-side-text pentagram-side-right harmony-enter-fade-right">
          <div className="side-text-glow" />
          <p className="side-text-label">决策引擎</p>
          <h3 className="side-text-title">智能决策</h3>
          <p className="side-text-desc">
            多路径分析<br/>
            历史追溯校准<br/>
            最优方案推荐
          </p>
        </div>

        <div className="hero-side harmony-enter-fade-scale harmony-delay-3">
          <div className="pentagram-stage" ref={stageRef}>
            {/* 背景光晕 */}
            <div className="pentagram-aura pentagram-aura-primary" />
            <div className="pentagram-aura pentagram-aura-secondary" />

            {/* Canvas：六边形网格 + 粒子能量流（无五角星） */}
            <canvas
              ref={canvasRef}
              aria-hidden="true"
              style={{
                position: 'absolute', inset: 0,
                width: '100%', height: '100%',
                pointerEvents: 'none', zIndex: 1,
              }}
            />

            {/* 同心轨道线 */}
            <div className="pentagram-ring pentagram-ring-outer" />
            <div className="pentagram-ring pentagram-ring-mid" />
            <div className="pentagram-ring pentagram-ring-inner" />

            {/* 功能节点 */}
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
                  console.log('[HomePage] 🖱️ 节点点击:', node.title, '时间:', performance.now());
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

            {/* AI 核心 */}
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
                <span>感知 / 推演 / 校准</span>
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* 底部浮动导航 */}
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
        <NavLink to="/modules" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
          <span>能力</span>
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => `nav-item${isActive ? ' is-active' : ''}`}>
          <span>我的</span>
        </NavLink>
      </nav>

      {/* 隐藏的内容区域（可滚动查看） */}
      <div className="homepage-content-wrapper">
        <section className="metrics-grid homepage-metrics">
        <MetricCard
          label="决策图谱"
          value={String(predictionCount)}
          helper="Future OS 推演记录"
          tone="primary"
        />
        <MetricCard
          label="AI 会话"
          value={String(conversationCount)}
          helper="AI 核心聊天主链"
          tone="secondary"
        />
        <MetricCard
          label="累计分支"
          value={String(branchCount)}
          helper="多 Agent 分支总数"
          tone="accent"
        />
        <MetricCard
          label="知识星图"
          value={knowledgeMode === 'people' ? '人物视图' : '升学规划视图'}
          helper="AI 核心当前更推荐的投影方向"
          tone="warning"
        />
      </section>

      <section className="two-column-grid">
        <GlassCard
          title="核心法阵入口"
          subtitle="五个球体都对应真实功能，不是装饰性的静态图标"
        >
          <div className="summary-groups">
            <div>
              <strong>中央 AI 核心</strong>
              <p>作为首页的认知中心，承接对话、推演、追踪与校准的统一入口。</p>
            </div>
            <div>
              <strong>五角功能球</strong>
              <p>决策副本、预测历史、AI 对话、个人中心、知识星图沿法阵分布，形成鸿蒙化主视觉。</p>
            </div>
            <div>
              <strong>视觉方向</strong>
              <p>保留蓝紫高光、玻璃流体感、光晕扩散和中控式结构，而不是传统卡片门户页。</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard title="Web 化原则" subtitle="继续沿 Harmony 端的价值判断推进">
          <ul className="plain-list">
            <li>首页先做品牌感和结构辨识度，让用户一眼知道这是 AI 中枢而不是普通后台。</li>
            <li>功能球必须可点击并直达真实模块，不做只有概念没有落点的展示。</li>
            <li>视觉上延续柔和高光、玻璃卡片、环形能量场和大圆角，不另起一套设计语言。</li>
            <li>后续再继续把决策详情、历史页和能力页的细节往 Harmony 风格拉齐。</li>
          </ul>
        </GlassCard>
      </section>

      <GlassCard
        title="能力地图"
        subtitle="Harmony 端已有功能会分批迁移，先把真实高频链路做扎实，再补其他模块。"
        action={
          <button className="button button-ghost" onClick={() => navigate('/modules')}>
            查看全部
          </button>
        }
      >
        <div className="module-grid">
          {featureModules.map((module) => (
            <article key={module.slug} className="module-card">
              <div
                className="module-accent"
                style={{
                  backgroundImage: `linear-gradient(135deg, ${module.gradient[0]}, ${module.gradient[1]})`,
                }}
              />
              <div className="module-content">
                <div className="module-header">
                  <h3>{module.title}</h3>
                  <StatusPill
                    tone={
                      module.status === 'live'
                        ? 'success'
                        : module.status === 'preview'
                          ? 'primary'
                          : 'warning'
                    }
                  >
                    {module.status === 'live'
                      ? '已上线'
                      : module.status === 'preview'
                        ? '预备迁移'
                        : '规划中'}
                  </StatusPill>
                </div>
                <p>{module.summary}</p>
                {module.route ? (
                  <Link className="text-link" to={module.route}>
                    进入模块
                  </Link>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </GlassCard>
      </div>

      {/* AI 核心悬浮窗 */}
      {isAICoreOpen && (
        <AICoreModal onClose={() => setIsAICoreOpen(false)} />
      )}

      {/* 全局 AI 悬浮按钮 */}
      <GlobalAIFloatingButton />
    </div>
  );
}
