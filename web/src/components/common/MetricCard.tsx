interface MetricCardProps {
  label: string;
  value: string;
  helper?: string;
  tone?: 'primary' | 'secondary' | 'accent' | 'warning';
}

export function MetricCard({
  label,
  value,
  helper,
  tone = 'primary',
}: MetricCardProps) {
  return (
    <article className={`metric-card tone-${tone}`}>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      {helper ? <span className="metric-helper">{helper}</span> : null}
    </article>
  );
}
