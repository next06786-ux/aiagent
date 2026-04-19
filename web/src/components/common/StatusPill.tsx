interface StatusPillProps {
  tone?: 'neutral' | 'primary' | 'success' | 'warning' | 'danger';
  children: string;
}

export function StatusPill({
  tone = 'neutral',
  children,
}: StatusPillProps) {
  return <span className={`status-pill status-${tone}`}>{children}</span>;
}
