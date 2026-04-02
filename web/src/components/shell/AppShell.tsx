import type { PropsWithChildren, ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

interface AppShellProps extends PropsWithChildren {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

const navItems = [
  { to: '/', label: '总览', hint: 'Home' },
  { to: '/decision', label: '决策副本', hint: 'Flow' },
  { to: '/decision/history', label: '预测历史', hint: 'Replay' },
  { to: '/chat', label: 'AI 对话', hint: 'Chat' },
  { to: '/modules', label: '能力地图', hint: 'Map' },
  { to: '/profile', label: '个人中心', hint: 'Me' },
];

export function AppShell({
  title,
  subtitle,
  actions,
  children,
}: AppShellProps) {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <div className="shell-backdrop">
        <div className="shell-glow shell-glow-primary" />
        <div className="shell-glow shell-glow-secondary" />
        <div className="shell-glow shell-glow-accent" />
      </div>

      <aside className="app-sidebar">
        <div className="brand-panel">
          <div className="brand-mark">LS</div>
          <div>
            <strong className="brand-title">LifeSwarm Web</strong>
            <p className="brand-copy">沿用 Harmony 端视觉语言与同一后端协议</p>
          </div>
        </div>

        <div className="sidebar-summary">
          <span className="sidebar-caption">Design Language</span>
          <strong>Celestial / Fluid</strong>
          <p className="nav-link-hint">
            玻璃层、柔光背景、胶囊状态和大圆角卡片统一落地到 Web。
          </p>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `nav-link${isActive ? ' is-active' : ''}`
              }
            >
              <span className="nav-link-label">{item.label}</span>
              <span className="nav-link-hint">{item.hint}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="sidebar-caption">当前账号</span>
          <strong className="sidebar-user">{user?.nickname || user?.username}</strong>
          <button className="button button-ghost" onClick={() => void logout()}>
            退出登录
          </button>
        </div>
      </aside>

      <main className="app-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Harmony Inspired Experience</p>
            <h1 className="page-title">{title}</h1>
            {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
          </div>

          <div className="topbar-actions">
            {actions}
            <div className="user-chip">
              <span className="user-chip-label">UID</span>
              <strong>{user?.user_id || 'guest'}</strong>
            </div>
          </div>
        </header>

        <section className="page-body">{children}</section>

        <nav className="mobile-nav">
          {navItems.map((item) => (
            <NavLink
              key={`mobile_${item.to}`}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `mobile-nav-link${isActive ? ' is-active' : ''}`
              }
            >
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </main>
    </div>
  );
}
