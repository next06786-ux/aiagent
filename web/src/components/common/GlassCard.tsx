import type { PropsWithChildren, ReactNode } from 'react';

interface GlassCardProps extends PropsWithChildren {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function GlassCard({
  title,
  subtitle,
  action,
  className,
  children,
}: GlassCardProps) {
  return (
    <section className={['glass-card', className].filter(Boolean).join(' ')}>
      {(title || subtitle || action) && (
        <header className="card-header">
          <div>
            {title ? <h3 className="card-title">{title}</h3> : null}
            {subtitle ? <p className="card-subtitle">{subtitle}</p> : null}
          </div>
          {action ? <div className="card-action">{action}</div> : null}
        </header>
      )}
      {children}
    </section>
  );
}
