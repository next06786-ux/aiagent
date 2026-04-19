import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PasswordStrengthIndicator } from '../components/auth/PasswordStrengthIndicator';
import { validatePassword } from '../utils/passwordValidator';

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
      await changePassword({ old_password: passwordForm.old_password, new_password: passwordForm.new_password });
      setPasswordForm({ old_password: '', new_password: '', confirm: '' });
      setMessage('密码已修改');
      setActiveSection('overview');
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改失败');
    } finally {
      setLoading('');
    }
  }

  return (
    <div className="ls-homepage" style={{ minHeight: '100vh', paddingBottom: 80 }}>
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
            color: 'var(--text-primary)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(10, 89, 247, 0.08)';
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
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>
          个人中心
        </div>
      </div>

      {/* 主内容容器 */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 28px 40px' }}>
        {/* HarmonyOS 6 - 纯净渐变英雄卡片 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 24, padding: '28px 32px',
          borderRadius: 28, marginBottom: 24,
          background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.08) 0%, rgba(107, 72, 255, 0.06) 100%)',
          border: '1px solid rgba(10, 89, 247, 0.12)',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
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

        {activeSection === 'overview' && (
          <>
            {/* HarmonyOS 6 - 纯净功能菜单卡片 */}
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
            </div>

            {/* HarmonyOS 6 - 纯净账号信息卡片 */}
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              borderRadius: 28,
              padding: 32,
              boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
              border: '1px solid rgba(0, 0, 0, 0.06)',
            }}>
              <div style={{ marginBottom: 24 }}>
                <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>账号信息</h2>
                <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>与 Harmony 端共用同一账号体系</p>
              </div>
            </div>
          </>
        )}

      {activeSection === 'profile' && (
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: 28,
          padding: 32,
          boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
          border: '1px solid rgba(0, 0, 0, 0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
            <button
              onClick={() => { setActiveSection('overview'); setError(''); }}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 8,
                marginRight: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12 19 5 12 12 5"/>
              </svg>
            </button>
            <div>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>编辑资料</h2>
              <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>更新个人信息</p>
            </div>
          </div>

          {message && <div className="form-success" style={{ marginBottom: 20 }}>{message}</div>}
          {error && <div className="form-error" style={{ marginBottom: 20 }}>{error}</div>}

          <form className="stack-form" onSubmit={handleProfileSubmit} style={{ gap: 20 }}>
            <label>
              <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>昵称</span>
              <input className="input" value={profileForm.nickname}
                onChange={e => setProfileForm(p => ({ ...p, nickname: e.target.value }))} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>手机号</span>
              <input className="input" value={profileForm.phone}
                onChange={e => setProfileForm(p => ({ ...p, phone: e.target.value }))} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>头像 URL</span>
              <input className="input" placeholder="https://…" value={profileForm.avatar_url}
                onChange={e => setProfileForm(p => ({ ...p, avatar_url: e.target.value }))} />
            </label>
            <button className="button button-primary" disabled={loading === 'profile'} style={{ marginTop: 8 }}>
              {loading === 'profile' ? '保存中…' : '保存资料'}
            </button>
          </form>
        </div>
      )}

      {activeSection === 'password' && (
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: 28,
          padding: 32,
          boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
          border: '1px solid rgba(0, 0, 0, 0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
            <button
              onClick={() => { setActiveSection('overview'); setError(''); }}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 8,
                marginRight: 12,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12 19 5 12 12 5"/>
              </svg>
            </button>
            <div>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>修改密码</h2>
              <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>保护账号安全</p>
            </div>
          </div>

          {message && <div className="form-success" style={{ marginBottom: 20 }}>{message}</div>}
          {error && <div className="form-error" style={{ marginBottom: 20 }}>{error}</div>}

          <form className="stack-form" onSubmit={handlePasswordSubmit} style={{ gap: 20 }}>
            <label>
              <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>当前密码</span>
              <input className="input" type="password" value={passwordForm.old_password}
                onChange={e => setPasswordForm(p => ({ ...p, old_password: e.target.value }))} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>新密码</span>
              <input className="input" type="password" value={passwordForm.new_password}
                onChange={e => setPasswordForm(p => ({ ...p, new_password: e.target.value }))} />
              <PasswordStrengthIndicator password={passwordForm.new_password} show={passwordForm.new_password.length > 0} />
            </label>
            <label>
              <span style={{ display: 'block', marginBottom: 8, fontSize: 14, fontWeight: 600 }}>确认新密码</span>
              <input className="input" type="password" value={passwordForm.confirm}
                onChange={e => setPasswordForm(p => ({ ...p, confirm: e.target.value }))} />
            </label>
            <button className="button button-primary" disabled={loading === 'password'} style={{ marginTop: 8 }}>
              {loading === 'password' ? '提交中…' : '确认修改'}
            </button>
          </form>
        </div>
      )}
      </div>
    </div>
  );
}

