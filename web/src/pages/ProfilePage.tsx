import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { AppShell } from '../components/shell/AppShell';
import { StatusPill } from '../components/common/StatusPill';
import { PageHeader } from '../components/common/PageHeader';
import { useAuth } from '../hooks/useAuth';

// HarmonyOS 6 - 纯净几何图标组件
function ProfileIcon({ type }: { type: 'user' | 'lock' | 'ai' | 'chart' | 'insight' }) {
  const iconMap = {
    user: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    ),
    lock: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
    ),
    ai: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
        <path d="M16 14v2a4 4 0 0 1-8 0v-2"/>
        <line x1="12" y1="18" x2="12" y2="22"/>
        <line x1="8" y1="22" x2="16" y2="22"/>
      </svg>
    ),
    chart: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/>
        <line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
      </svg>
    ),
    insight: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    ),
  };
  return iconMap[type];
}

const MENU_ITEMS = [
  { id: 'edit',      label: '编辑资料',   sub: '更新昵称、手机号',        icon: 'user' as const,    section: 'profile',  gradient: 'linear-gradient(135deg, #0A59F7 0%, #6B48FF 100%)' },
  { id: 'password',  label: '修改密码',   sub: '保护账号安全',            icon: 'lock' as const,    section: 'password', gradient: 'linear-gradient(135deg, #6B48FF 0%, #9B6BFF 100%)' },
  { id: 'lora',      label: '个性模型训练', sub: '储备模型管理',           icon: 'ai' as const,      route: '/lora-training', gradient: 'linear-gradient(135deg, #00C8FF 0%, #00E5FF 100%)' },
  { id: 'learning',  label: '学习进度',   sub: '强化学习统计',            icon: 'chart' as const,   route: '/learning-progress', gradient: 'linear-gradient(135deg, #34C759 0%, #30D158 100%)' },
  { id: 'insights',  label: '智能洞察',   sub: '涌现模式分析',            icon: 'insight' as const, route: '/insights', gradient: 'linear-gradient(135deg, #FF9500 0%, #FFB340 100%)' },
];

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, updateProfile, changePassword } = useAuth();
  const [activeSection, setActiveSection] = useState<'overview' | 'profile' | 'password'>('overview');
  const [profileForm, setProfileForm] = useState({ nickname: '', phone: '', avatar_url: '' });
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState<'profile' | 'password' | ''>('');
  const [hoveredMenuId, setHoveredMenuId] = useState<string | null>(null);

  useEffect(() => {
    setProfileForm({ nickname: user?.nickname || '', phone: user?.phone || '', avatar_url: user?.avatar_url || '' });
  }, [user]);

  const initial = (user?.nickname || user?.username || 'U').slice(0, 1).toUpperCase();

  async function handleProfileSubmit(e: FormEvent) {
    e.preventDefault(); setMessage(''); setError(''); setLoading('profile');
    try { await updateProfile(profileForm); setMessage('资料已更新'); setActiveSection('overview'); }
    catch (err) { setError(err instanceof Error ? err.message : '更新失败'); }
    finally { setLoading(''); }
  }

  async function handlePasswordSubmit(e: FormEvent) {
    e.preventDefault(); setMessage(''); setError('');
    if (passwordForm.new_password.length < 6) { setError('新密码至少 6 位'); return; }
    if (passwordForm.new_password !== passwordForm.confirm) { setError('两次密码不一致'); return; }
    setLoading('password');
    try {
      await changePassword({ old_password: passwordForm.old_password, new_password: passwordForm.new_password });
      setPasswordForm({ old_password: '', new_password: '', confirm: '' });
      setMessage('密码已修改'); setActiveSection('overview');
    } catch (err) { setError(err instanceof Error ? err.message : '修改失败'); }
    finally { setLoading(''); }
  }

  return (
    <AppShell>
      <PageHeader title="个人中心" subtitle="账号信息 · 资料维护 · 安全设置" />
      {/* HarmonyOS 6 - 纯净渐变英雄卡片 */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 24, padding: '28px 32px',
        borderRadius: 28, marginBottom: 4,
        background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.08) 0%, rgba(107, 72, 255, 0.06) 100%)',
        border: '1px solid rgba(10, 89, 247, 0.12)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* 微光效果 */}
        <div style={{
          position: 'absolute', top: 0, right: 0, width: '50%', height: '100%',
          background: 'radial-gradient(ellipse at 80% 50%, rgba(10, 89, 247, 0.08), transparent 60%)',
          pointerEvents: 'none',
        }}/>
        
        {/* 头像 */}
        <div style={{
          width: 80, height: 80, borderRadius: '50%', flexShrink: 0,
          background: 'linear-gradient(135deg, #0A59F7 0%, #6B48FF 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 32, fontWeight: 800, color: '#fff',
          boxShadow: '0 12px 32px rgba(10, 89, 247, 0.25)',
          position: 'relative',
        }}>
          {/* 头像光晕 */}
          <div style={{
            position: 'absolute', inset: -4, borderRadius: '50%',
            background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.3), rgba(107, 72, 255, 0.2))',
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
            <StatusPill tone={user?.is_verified ? 'success' : 'warning'}>
              {user?.is_verified ? '已验证' : '未验证'}
            </StatusPill>
            <span style={{ fontSize: 12, color: '#999', letterSpacing: '0.05em' }}>
              ID: {user?.user_id?.slice(0, 12)}…
            </span>
          </div>
        </div>
      </div>

      {/* 反馈提示 */}
      {message && <div className="form-success harmony-tooltip">{message}</div>}
      {error   && <div className="form-error harmony-error">{error}</div>}

      {activeSection === 'overview' && (
        <>
          {/* HarmonyOS 6 - 纯净功能菜单卡片 */}
          <GlassCard title="账号设置" subtitle="管理个人信息与安全">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {MENU_ITEMS.map(item => (
                <button key={item.id}
                  onClick={() => {
                    setMessage(''); setError('');
                    if (item.route) navigate(item.route);
                    else setActiveSection(item.section as 'profile' | 'password');
                  }}
                  onMouseEnter={() => setHoveredMenuId(item.id)}
                  onMouseLeave={() => setHoveredMenuId(null)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 16,
                    padding: '16px 18px', borderRadius: 18, border: 'none',
                    background: hoveredMenuId === item.id ? 'rgba(10, 89, 247, 0.04)' : 'transparent',
                    cursor: 'pointer', textAlign: 'left', width: '100%',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative', overflow: 'hidden',
                  }}
                >
                  {/* 悬停高亮条 */}
                  <div style={{
                    position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)',
                    width: 4, height: hoveredMenuId === item.id ? '60%' : '0%',
                    background: 'linear-gradient(180deg, #0A59F7, #6B48FF)',
                    borderRadius: '0 4px 4px 0',
                    transition: 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}/>
                  
                  {/* 图标 */}
                  <div style={{
                    width: 52, height: 52, borderRadius: 16, flexShrink: 0,
                    background: item.gradient,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff',
                    boxShadow: hoveredMenuId === item.id 
                      ? `0 8px 24px ${item.gradient.includes('0A59F7') ? 'rgba(10, 89, 247, 0.3)' : 'rgba(107, 72, 255, 0.3)'}`
                      : '0 4px 12px rgba(0, 0, 0, 0.08)',
                    transform: hoveredMenuId === item.id ? 'scale(1.05)' : 'scale(1)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}>
                    <ProfileIcon type={item.icon} />
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#1A1A1A', marginBottom: 4 }}>{item.label}</div>
                    <div style={{ fontSize: 13, color: '#999', letterSpacing: '0.02em' }}>{item.sub}</div>
                  </div>
                  
                  {/* 箭头 */}
                  <div style={{
                    width: 32, height: 32, borderRadius: 12,
                    background: hoveredMenuId === item.id ? 'rgba(10, 89, 247, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: hoveredMenuId === item.id ? 'translateX(4px)' : 'translateX(0)',
                  }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={hoveredMenuId === item.id ? '#0A59F7' : '#999'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </GlassCard>

          {/* HarmonyOS 6 - 纯净账号信息卡片 */}
          <GlassCard title="账号信息" subtitle="与 Harmony 端共用同一账号体系">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {[
                { label: '用户名',   value: user?.username },
                { label: '邮箱',     value: user?.email },
                { label: '注册时间', value: user?.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '—' },
                { label: '最近登录', value: user?.last_login ? new Date(user.last_login).toLocaleDateString('zh-CN') : '—' },
              ].map((row, idx, arr) => (
                <div key={row.label} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '14px 0', borderBottom: idx < arr.length - 1 ? '1px solid rgba(0, 0, 0, 0.04)' : 'none',
                }}>
                  <span style={{ fontSize: 14, color: '#999', letterSpacing: '0.02em' }}>{row.label}</span>
                  <span style={{ fontSize: 14, color: '#1A1A1A', fontWeight: 600 }}>{row.value || '—'}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </>
      )}

      {activeSection === 'profile' && (
        <GlassCard title="编辑资料" subtitle="更新个人信息"
          action={<button className="button button-ghost" style={{ padding: '8px 16px', minHeight: 'auto', fontSize: 13 }}
            onClick={() => { setActiveSection('overview'); setError(''); }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            返回
          </button>}
        >
          <form className="stack-form" onSubmit={handleProfileSubmit} style={{ gap: 20 }}>
            <label><span>昵称</span>
              <input className="input" value={profileForm.nickname}
                onChange={e => setProfileForm(p => ({ ...p, nickname: e.target.value }))} />
            </label>
            <label><span>手机号</span>
              <input className="input" value={profileForm.phone}
                onChange={e => setProfileForm(p => ({ ...p, phone: e.target.value }))} />
            </label>
            <label><span>头像 URL</span>
              <input className="input" placeholder="https://…" value={profileForm.avatar_url}
                onChange={e => setProfileForm(p => ({ ...p, avatar_url: e.target.value }))} />
            </label>
            <button className="button button-primary" disabled={loading === 'profile'} style={{ marginTop: 8 }}>
              {loading === 'profile' ? '保存中…' : '保存资料'}
            </button>
          </form>
        </GlassCard>
      )}

      {activeSection === 'password' && (
        <GlassCard title="修改密码" subtitle="保护账号安全"
          action={<button className="button button-ghost" style={{ padding: '8px 16px', minHeight: 'auto', fontSize: 13 }}
            onClick={() => { setActiveSection('overview'); setError(''); }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            返回
          </button>}
        >
          <form className="stack-form" onSubmit={handlePasswordSubmit} style={{ gap: 20 }}>
            <label><span>当前密码</span>
              <input className="input" type="password" value={passwordForm.old_password}
                onChange={e => setPasswordForm(p => ({ ...p, old_password: e.target.value }))} />
            </label>
            <label><span>新密码（至少 6 位）</span>
              <input className="input" type="password" value={passwordForm.new_password}
                onChange={e => setPasswordForm(p => ({ ...p, new_password: e.target.value }))} />
            </label>
            <label><span>确认新密码</span>
              <input className="input" type="password" value={passwordForm.confirm}
                onChange={e => setPasswordForm(p => ({ ...p, confirm: e.target.value }))} />
            </label>
            <button className="button button-primary" disabled={loading === 'password'} style={{ marginTop: 8 }}>
              {loading === 'password' ? '提交中…' : '确认修改'}
            </button>
          </form>
        </GlassCard>
      )}
    </AppShell>
  );
}
