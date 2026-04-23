import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type FormEvent } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PasswordStrengthIndicator } from '../components/auth/PasswordStrengthIndicator';
import { validatePassword } from '../utils/passwordValidator';

interface ProfileNode {
  id: string;
  title: string;
  subtitle: string;
  action?: () => void;
  top: string;
  left: string;
  gradient: [string, string];
  icon: string;
}

export function ProfilePageNew() {
  const navigate = useNavigate();
  const { user, updateProfile, changePassword, logout } = useAuth();
  const [activeSection, setActiveSection] = useState<'overview' | 'profile' | 'password'>('overview');
  const [profileForm, setProfileForm] = useState({ nickname: '', phone: '', avatar_url: '' });
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState<'profile' | 'password' | ''>('');
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  useEffect(() => {
    setProfileForm({ 
      nickname: user?.nickname || '', 
      phone: user?.phone || '', 
      avatar_url: user?.avatar_url || '' 
    });
  }, [user]);

  const initial = (user?.nickname || user?.username || 'U').slice(0, 1).toUpperCase();

  async function handleProfileSubmit(e: FormEvent) {
    e.preventDefault();
    setMessage('');
    setError('');
    setLoading('profile');
    try {
      await updateProfile(profileForm);
      setMessage('资料已更新');
      setTimeout(() => setActiveSection('overview'), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新失败');
    } finally {
      setLoading('');
    }
  }

  async function handlePasswordSubmit(e: FormEvent) {
    e.preventDefault();
    setMessage('');
    setError('');
    
    const passwordCheck = validatePassword(passwordForm.new_password);
    if (passwordCheck.score < 2) {
      setError('新密码强度太弱，请使用更强的密码');
      return;
    }
    
    if (passwordForm.new_password !== passwordForm.confirm) {
      setError('两次密码不一致');
      return;
    }
    
    setLoading('password');
    try {
      await changePassword({ 
        old_password: passwordForm.old_password, 
        new_password: passwordForm.new_password 
      });
      setPasswordForm({ old_password: '', new_password: '', confirm: '' });
      setMessage('密码已修改');
      setTimeout(() => setActiveSection('overview'), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改失败');
    } finally {
      setLoading('');
    }
  }

  const profileNodes = useMemo<ProfileNode[]>(() => [
    {
      id: 'edit',
      title: '编辑资料',
      subtitle: '更新信息',
      action: () => setActiveSection('profile'),
      top: '5%',
      left: '50%',
      gradient: ['#4a4a4a', '#2c2c2c'],
      icon: 'user',
    },
    {
      id: 'password',
      title: '修改密码',
      subtitle: '安全设置',
      action: () => setActiveSection('password'),
      top: '24%',
      left: '84%',
      gradient: ['#5a5a5a', '#3a3a3a'],
      icon: 'lock',
    },
    {
      id: 'lora',
      title: '个性模型',
      subtitle: 'LoRA训练',
      action: () => navigate('/lora-training'),
      top: '79%',
      left: '70%',
      gradient: ['#6a6a6a', '#4a4a4a'],
      icon: 'ai',
    },
    {
      id: 'learning',
      title: '学习进度',
      subtitle: '强化统计',
      action: () => navigate('/learning-progress'),
      top: '79%',
      left: '30%',
      gradient: ['#7a7a7a', '#5a5a5a'],
      icon: 'chart',
    },
    {
      id: 'insights',
      title: '智能洞察',
      subtitle: '涌现分析',
      action: () => navigate('/insights'),
      top: '24%',
      left: '16%',
      gradient: ['#8a8a8a', '#6a6a6a'],
      icon: 'insight',
    },
  ], [navigate]);

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

    const nodePositions = profileNodes.map(n => ({
      x: (parseFloat(n.left) / 100) * W,
      y: (parseFloat(n.top) / 100) * H,
      color: n.gradient[1],
    }));

    // 六边形网格背景
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
        ctx.strokeStyle = `rgba(0, 0, 0, ${alpha})`;
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }
    }
    ctx.restore();

    // 同心圆弧装饰
    [0.44, 0.72, 0.96].forEach((ratio, i) => {
      const r = (Math.min(W, H) / 2) * ratio;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(0, 0, 0, ${0.05 - i * 0.01})`;
      ctx.lineWidth = i === 0 ? 1.0 : 0.6;
      ctx.setLineDash(i === 1 ? [4, 8] : []);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // 从核心到节点的能量通道
    nodePositions.forEach(node => {
      const grad = ctx.createLinearGradient(cx, cy, node.x, node.y);
      grad.addColorStop(0, `${node.color}44`);
      grad.addColorStop(0.5, `${node.color}22`);
      grad.addColorStop(1, `${node.color}08`);
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
  }, [profileNodes]);

  // 粒子系统动画
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

    const particles: Particle[] = [];
    profileNodes.forEach((_, ni) => {
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
      if (W === 0) {
        raf = requestAnimationFrame(animate);
        return;
      }
      canvas.width = W;
      canvas.height = H;
      const ctx = canvas.getContext('2d')!;
      const cx = W / 2,
        cy = H / 2;

      ctx.clearRect(0, 0, W, H);
      drawField();

      const nodes = profileNodes.map(n => ({
        x: (parseFloat(n.left) / 100) * W,
        y: (parseFloat(n.top) / 100) * H,
        color: n.gradient[1],
      }));

      particles.forEach(p => {
        p.t += p.speed;
        if (p.t > 1) p.t -= 1;

        const node = nodes[p.nodeIdx];
        const mx = (cx + node.x) / 2 + (node.y - cy) * 0.18;
        const my = (cy + node.y) / 2 - (node.x - cx) * 0.18;
        const t = p.t;
        const px = (1 - t) * (1 - t) * cx + 2 * (1 - t) * t * mx + t * t * node.x;
        const py = (1 - t) * (1 - t) * cy + 2 * (1 - t) * t * my + t * t * node.y;

        const boost = t > 0.8 ? (t - 0.8) / 0.2 : 0;
        const r = p.size * (1 + boost * 1.5);
        const alpha = p.opacity * (0.4 + t * 0.6);

        const grd = ctx.createRadialGradient(px, py, 0, px, py, r * 2.5);
        grd.addColorStop(
          0,
          `${node.color}${Math.round(alpha * 255)
            .toString(16)
            .padStart(2, '0')}`
        );
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
  }, [drawField, profileNodes]);

  const getIcon = (type: string) => {
    const icons: Record<string, JSX.Element> = {
      user: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      ),
      lock: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
      ),
      ai: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
          <path d="M16 14v2a4 4 0 0 1-8 0v-2" />
          <line x1="12" y1="18" x2="12" y2="22" />
          <line x1="8" y1="22" x2="16" y2="22" />
        </svg>
      ),
      chart: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="20" x2="18" y2="10" />
          <line x1="12" y1="20" x2="12" y2="4" />
          <line x1="6" y1="20" x2="6" y2="14" />
        </svg>
      ),
      insight: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ),
    };
    return icons[type] || icons.user;
  };

  return (
    <div className="ls-homepage" style={{ minHeight: '100vh' }}>
      {/* 动画背景 */}
      <div className="ls-background">
        <div className="ls-blob ls-blob-1" />
        <div className="ls-blob ls-blob-2" />
        <div className="ls-blob ls-blob-3" />
      </div>

      {/* 顶部导航 */}
      <div className="app-topnav">
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            borderRadius: 12,
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.08)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span style={{ fontSize: 14, fontWeight: 600 }}>返回首页</span>
        </button>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => logout().then(() => navigate('/auth'))}
          style={{
            background: 'transparent',
            border: '1px solid rgba(255, 59, 48, 0.2)',
            color: '#FF3B30',
            cursor: 'pointer',
            padding: '8px 16px',
            borderRadius: 12,
            fontSize: 14,
            fontWeight: 600,
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(255, 59, 48, 0.08)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          退出登录
        </button>
      </div>

      {/* 主内容区 */}
      {activeSection === 'overview' && (
        <>
          {/* 用户信息卡片 */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 24, padding: '28px 32px',
            borderRadius: 28, marginBottom: 24,
            background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.08) 0%, rgba(50, 50, 50, 0.06) 100%)',
            border: '1px solid rgba(0, 0, 0, 0.12)',
            position: 'relative',
            overflow: 'hidden',
            boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
          }}>
            {/* 微光效果 */}
            <div style={{
              position: 'absolute', top: 0, right: 0, width: '50%', height: '100%',
              background: 'radial-gradient(ellipse at 80% 50%, rgba(0, 0, 0, 0.08), transparent 60%)',
              pointerEvents: 'none',
            }}/>
            
            {/* 头像 */}
            <div style={{
              width: 80, height: 80, borderRadius: '50%', flexShrink: 0,
              background: 'linear-gradient(135deg, #2c2c2c 0%, #1a1a1a 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 32, fontWeight: 800, color: '#fff',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.25)',
              position: 'relative',
            }}>
              {/* 头像光晕 */}
              <div style={{
                position: 'absolute', inset: -4, borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(0, 0, 0, 0.3), rgba(50, 50, 50, 0.2))',
                filter: 'blur(8px)', zIndex: -1,
              }}/>
              {user?.avatar_url
                ? <img src={user.avatar_url} alt="avatar" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                : initial}
            </div>
            
            {/* 用户信息 */}
            <div style={{ flex: 1, position: 'relative' }}>
              <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 6, color: '#1A1A1A' }}>
                {user?.nickname || user?.username}
              </div>
              <div style={{ fontSize: 14, color: '#666', marginBottom: 12, letterSpacing: '0.02em' }}>{user?.email}</div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <div style={{
                  padding: '4px 12px',
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 600,
                  background: user?.is_verified ? 'rgba(52, 199, 89, 0.12)' : 'rgba(255, 149, 0, 0.12)',
                  color: user?.is_verified ? '#0f7d39' : '#9c6000',
                }}>
                  {user?.is_verified ? '已验证' : '未验证'}
                </div>
                <span style={{ fontSize: 12, color: '#999', letterSpacing: '0.05em' }}>
                  ID: {user?.user_id?.slice(0, 12)}…
                </span>
              </div>
            </div>
          </div>

          {/* 反馈提示 */}
          {message && <div className="form-success" style={{ marginBottom: 20 }}>{message}</div>}
          {error && <div className="form-error" style={{ marginBottom: 20 }}>{error}</div>}

          {/* 功能菜单列表 */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 28,
            padding: 32,
            marginBottom: 24,
            boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
            border: '1px solid rgba(0, 0, 0, 0.06)',
          }}>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>账号设置</h2>
              <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>管理个人信息与安全</p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {profileNodes.map(node => (
                <button key={node.id}
                  onClick={() => {
                    setMessage(''); setError('');
                    node.action?.();
                  }}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 16,
                    padding: '16px 18px', borderRadius: 18, border: 'none',
                    background: hoveredNode === node.id ? 'rgba(0, 0, 0, 0.04)' : 'transparent',
                    cursor: 'pointer', textAlign: 'left', width: '100%',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative', overflow: 'hidden',
                  }}
                >
                  {/* 悬停高亮条 */}
                  <div style={{
                    position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)',
                    width: 4, height: hoveredNode === node.id ? '60%' : '0%',
                    background: `linear-gradient(180deg, ${node.gradient[0]}, ${node.gradient[1]})`,
                    borderRadius: '0 4px 4px 0',
                    transition: 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}/>
                  
                  {/* 图标 */}
                  <div style={{
                    width: 52, height: 52, borderRadius: 16, flexShrink: 0,
                    background: `linear-gradient(135deg, ${node.gradient[0]} 0%, ${node.gradient[1]} 100%)`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff',
                    boxShadow: hoveredNode === node.id 
                      ? `0 8px 24px rgba(0, 0, 0, 0.3)`
                      : '0 4px 12px rgba(0, 0, 0, 0.08)',
                    transform: hoveredNode === node.id ? 'scale(1.05)' : 'scale(1)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}>
                    {getIcon(node.icon)}
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#1A1A1A', marginBottom: 4 }}>{node.title}</div>
                    <div style={{ fontSize: 13, color: '#999', letterSpacing: '0.02em' }}>{node.subtitle}</div>
                  </div>
                  
                  {/* 箭头 */}
                  <div style={{
                    width: 32, height: 32, borderRadius: 12,
                    background: hoveredNode === node.id ? 'rgba(0, 0, 0, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: hoveredNode === node.id ? 'translateX(4px)' : 'translateX(0)',
                  }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={hoveredNode === node.id ? '#2c2c2c' : '#999'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {/* 编辑资料表单 */}
      {activeSection === 'profile' && (
        <div
          style={{
            maxWidth: 600,
            margin: '80px auto',
            padding: '0 24px',
          }}
        >
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              borderRadius: 28,
              padding: 32,
              boxShadow: '0 18px 48px rgba(0, 0, 0, 0.08)',
              border: '1px solid rgba(0, 0, 0, 0.06)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
              <button
                onClick={() => {
                  setActiveSection('overview');
                  setError('');
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 8,
                  marginRight: 12,
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="19" y1="12" x2="5" y2="12" />
                  <polyline points="12 19 5 12 12 5" />
                </svg>
              </button>
              <div>
                <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>编辑资料</h2>
                <p style={{ margin: '4px 0 0', fontSize: 14, color: '#666' }}>
                  更新个人信息
                </p>
              </div>
            </div>

            {message && (
              <div className="form-success" style={{ marginBottom: 20 }}>
                {message}
              </div>
            )}
            {error && (
              <div className="form-error" style={{ marginBottom: 20 }}>
                {error}
              </div>
            )}

            <form onSubmit={handleProfileSubmit} style={{ display: 'grid', gap: 20 }}>
              <label>
                <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>
                  昵称
                </span>
                <input
                  className="input"
                  value={profileForm.nickname}
                  onChange={e =>
                    setProfileForm(p => ({ ...p, nickname: e.target.value }))
                  }
                  placeholder="请输入昵称"
                />
              </label>

              <label>
                <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>
                  手机号
                </span>
                <input
                  className="input"
                  value={profileForm.phone}
                  onChange={e => setProfileForm(p => ({ ...p, phone: e.target.value }))}
                  placeholder="请输入手机号"
                />
              </label>

              <label>
                <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>
                  头像 URL
                </span>
                <input
                  className="input"
                  value={profileForm.avatar_url}
                  onChange={e =>
                    setProfileForm(p => ({ ...p, avatar_url: e.target.value }))
                  }
                  placeholder="https://..."
                />
              </label>

              <button
                className="button button-primary button-large"
                disabled={loading === 'profile'}
                style={{ marginTop: 8 }}
              >
                {loading === 'profile' ? '保存中...' : '保存资料'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* 修改密码表单 */}
      {activeSection === 'password' && (
        <div
          style={{
            maxWidth: 600,
            margin: '80px auto',
            padding: '0 24px',
          }}
        >
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              borderRadius: 28,
              padding: 32,
              boxShadow: '0 18px 48px rgba(0, 0, 0, 0.08)',
              border: '1px solid rgba(0, 0, 0, 0.06)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
              <button
                onClick={() => {
                  setActiveSection('overview');
                  setError('');
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 8,
                  marginRight: 12,
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="19" y1="12" x2="5" y2="12" />
                  <polyline points="12 19 5 12 12 5" />
                </svg>
              </button>
              <div>
                <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>修改密码</h2>
                <p style={{ margin: '4px 0 0', fontSize: 14, color: '#666' }}>
                  保护账号安全
                </p>
              </div>
            </div>

            {message && (
              <div className="form-success" style={{ marginBottom: 20 }}>
                {message}
              </div>
            )}
            {error && (
              <div className="form-error" style={{ marginBottom: 20 }}>
                {error}
              </div>
            )}

            <form onSubmit={handlePasswordSubmit} style={{ display: 'grid', gap: 20 }}>
              <label>
                <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>
                  当前密码
                </span>
                <input
                  className="input"
                  type="password"
                  value={passwordForm.old_password}
                  onChange={e =>
                    setPasswordForm(p => ({ ...p, old_password: e.target.value }))
                  }
                  placeholder="请输入当前密码"
                  required
                />
              </label>

              <label>
                <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>
                  新密码
                </span>
                <input
                  className="input"
                  type="password"
                  value={passwordForm.new_password}
                  onChange={e =>
                    setPasswordForm(p => ({ ...p, new_password: e.target.value }))
                  }
                  placeholder="请输入新密码"
                  required
                />
                <PasswordStrengthIndicator
                  password={passwordForm.new_password}
                  show={passwordForm.new_password.length > 0}
                />
              </label>

              <label>
                <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>
                  确认新密码
                </span>
                <input
                  className="input"
                  type="password"
                  value={passwordForm.confirm}
                  onChange={e => setPasswordForm(p => ({ ...p, confirm: e.target.value }))}
                  placeholder="请再次输入新密码"
                  required
                />
              </label>

              <button
                className="button button-primary button-large"
                disabled={loading === 'password'}
                style={{ marginTop: 8 }}
              >
                {loading === 'password' ? '提交中...' : '确认修改'}
              </button>
            </form>
          </div>
        </div>
      )}

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
    </div>
  );
}
