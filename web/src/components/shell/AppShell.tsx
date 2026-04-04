import type { PropsWithChildren, ReactNode } from 'react';
import { NavLink } from 'react-router-dom';

interface AppShellProps extends PropsWithChildren {
  showNav?: boolean;
  actions?: ReactNode;
}

const navItems = [
  { to: '/', label: '总览' },
  { to: '/decision', label: '决策' },
  { to: '/chat', label: '对话' },
  { to: '/modules', label: '能力' },
  { to: '/profile', label: '我的' },
];

export function AppShell({
  showNav = true,
  actions,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="shell-backdrop">
        <div className="shell-glow shell-glow-primary" />
        <div className="shell-glow shell-glow-secondary" />
        <div className="shell-glow shell-glow-accent" />
      </div>

      <main className="app-main">
        {actions && <div className="page-actions">{actions}</div>}
        <section className="page-body">{children}</section>

        {showNav && (
          <nav className="mobile-nav">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
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
        )}
      </main>
    </div>
  );
}
