import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { AppShell } from '../components/shell/AppShell';
import { StatusPill } from '../components/common/StatusPill';
import { useAuth } from '../hooks/useAuth';

const MENU_ITEMS = [
  { id: 'edit',     label: '编辑资料',   sub: '更新昵称、手机号',   icon: '👤', color: '#667eea', section: 'profile'  },
  { id: 'password', label: '修改密码',   sub: '保护账号安全',       icon: '🔒', color: '#764ba2', section: 'password' },
  { id: 'lora',     label: '个性模型训练', sub: '储备模型管理',     icon: '🧠', color: '#f093fb', route: '/lora-training' },
  { id: 'learning', label: '学习进度',   sub: '强化学习统计',       icon: '📈', color: '#43e97b', route: '/learning-progress' },
  { id: 'insights', label: '智能洞察',   sub: '涌现模式分析',       icon: '✦',  color: '#ff9500', route: '/insights' },
]

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, updateProfile, changePassword } = useAuth();
  const [activeSection, setActiveSection] = useState<'overview' | 'profile' | 'password'>('overview');
  const [profileForm, setProfileForm] = useState({ nickname: '', phone: '', avatar_url: '' });
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState<'profile' | 'password' | ''>('');

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
    <AppShell title="个人中心" subtitle="账号信息 · 资料维护 · 安全设置">
      {/* hero card */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 20, padding: '24px 28px',
        borderRadius: 28, marginBottom: 4,
        background: 'linear-gradient(135deg, rgba(102,126,234,0.18), rgba(118,75,162,0.14))',
        border: '1px solid rgba(102,126,234,0.2)',
      }}>
        <div style={{
          width: 72, height: 72, borderRadius: '50%', flexShrink: 0,
          background: 'linear-gradient(135deg, #667eea, #764ba2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 28, fontWeight: 800, color: '#fff',
          boxShadow: '0 8px 24px rgba(102,126,234,0.4)',
        }}>
          {user?.avatar_url
            ? <img src={user.avatar_url} alt="avatar" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
            : initial}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 4 }}>
            {user?.nickname || user?.username}
          </div>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 8 }}>{user?.email}</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <StatusPill tone={user?.is_verified ? 'success' : 'warning'}>
              {user?.is_verified ? '已验证' : '未验证'}
            </StatusPill>
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)', alignSelf: 'center' }}>
              ID: {user?.user_id?.slice(0, 12)}…
            </span>
          </div>
        </div>
      </div>

      {/* feedback */}
      {message && <div className="form-success">{message}</div>}
      {error   && <div className="form-error">{error}</div>}

      {activeSection === 'overview' && (
        <>
          {/* menu list */}
          <GlassCard title="账号设置" subtitle="管理个人信息与安全">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {MENU_ITEMS.map(item => (
                <button key={item.id}
                  onClick={() => {
                    setMessage(''); setError('');
                    if (item.route) navigate(item.route);
                    else setActiveSection(item.section as 'profile' | 'password');
                  }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 14,
                    padding: '14px 16px', borderRadius: 16, border: 'none',
                    background: 'transparent', cursor: 'pointer', textAlign: 'left', width: '100%',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(0,0,0,0.04)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <div style={{
                    width: 44, height: 44, borderRadius: 14, flexShrink: 0,
                    background: item.color + '22',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 20,
                  }}>{item.icon}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>{item.label}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 2 }}>{item.sub}</div>
                  </div>
                  <span style={{ color: 'var(--text-tertiary)', fontSize: 18 }}>›</span>
                </button>
              ))}
            </div>
          </GlassCard>

          {/* account info */}
          <GlassCard title="账号信息" subtitle="与 Harmony 端共用同一账号体系">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {[
                { label: '用户名',   value: user?.username },
                { label: '邮箱',     value: user?.email },
                { label: '注册时间', value: user?.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '—' },
                { label: '最近登录', value: user?.last_login ? new Date(user.last_login).toLocaleDateString('zh-CN') : '—' },
              ].map(row => (
                <div key={row.label} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 0', borderBottom: '1px solid var(--border-light)',
                }}>
                  <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{row.label}</span>
                  <span style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 500 }}>{row.value || '—'}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </>
      )}

      {activeSection === 'profile' && (
        <GlassCard title="编辑资料" subtitle="更新个人信息"
          action={<button className="button button-ghost" style={{ padding: '6px 14px', minHeight: 'auto' }}
            onClick={() => { setActiveSection('overview'); setError(''); }}>← 返回</button>}
        >
          <form className="stack-form" onSubmit={handleProfileSubmit}>
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
            <button className="button button-primary" disabled={loading === 'profile'}>
              {loading === 'profile' ? '保存中…' : '保存资料'}
            </button>
          </form>
        </GlassCard>
      )}

      {activeSection === 'password' && (
        <GlassCard title="修改密码" subtitle="保护账号安全"
          action={<button className="button button-ghost" style={{ padding: '6px 14px', minHeight: 'auto' }}
            onClick={() => { setActiveSection('overview'); setError(''); }}>← 返回</button>}
        >
          <form className="stack-form" onSubmit={handlePasswordSubmit}>
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
            <button className="button button-secondary" disabled={loading === 'password'}>
              {loading === 'password' ? '提交中…' : '确认修改'}
            </button>
          </form>
        </GlassCard>
      )}
    </AppShell>
  );
}
