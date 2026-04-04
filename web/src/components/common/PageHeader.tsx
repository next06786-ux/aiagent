interface PageHeaderProps {
  title: string;
  subtitle?: string;
}

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div style={{
      marginBottom: 24,
      paddingBottom: 16,
      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    }}>
      <h1 style={{
        fontSize: 28,
        fontWeight: 700,
        color: 'var(--text-primary)',
        marginBottom: subtitle ? 8 : 0,
      }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{
          fontSize: 14,
          color: 'var(--text-secondary)',
          margin: 0,
        }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}
