import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { StatusPill } from '../components/common/StatusPill'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

// ── Types ──────────────────────────────────────────────────────────────────
interface ExecutiveSummary {
  status: string; message: string
  total_patterns: number; high_impact_patterns: number
  top_concern: { type: string; impact: number }
}
interface ActionItem { timeframe: string; actions: string[] }
interface ActionPlan {
  immediate_actions: ActionItem
  short_term_actions: ActionItem
  long_term_actions: ActionItem
}
interface RiskAssessment {
  overall_risk_level: string
  risk_distribution: { critical: { description: string }[]; high: { description: string }[] }
}
interface ProgressTracking {
  trend: string
  changes: { health_change: number; mood_change: number; stress_change: number }
}
interface Report {
  user_id: string; report_date: string
  executive_summary: ExecutiveSummary
  risk_assessment: RiskAssessment
  action_plan: ActionPlan
  progress_tracking: ProgressTracking
  recommendations: string[]
}

// ── Helpers ────────────────────────────────────────────────────────────────
const STATUS_TONE: Record<string, 'danger' | 'warning' | 'primary' | 'success'> = {
  critical: 'danger', warning: 'warning', caution: 'primary', healthy: 'success',
}
const STATUS_LABEL: Record<string, string> = {
  critical: '严重', warning: '警告', caution: '注意', healthy: '健康',
}
const STATUS_COLOR: Record<string, string> = {
  critical: '#FF4444', warning: '#FF8844', caution: '#FFAA44', healthy: '#44AA44',
}
const TREND_ICON: Record<string, string> = { improving: '↑', stable: '→', declining: '↓' }
const TREND_COLOR: Record<string, string> = { improving: '#00C853', stable: '#0A59F7', declining: '#FF3B30' }

function ChangeChip({ label, value }: { label: string; value: number }) {
  const color = value > 0 ? '#00C853' : value < 0 ? '#FF3B30' : '#999'
  return (
    <div style={{ padding: '8px 14px', borderRadius: 12, background: color + '18', textAlign: 'center' }}>
      <div style={{ fontSize: 20, fontWeight: 800, color }}>{value > 0 ? '+' : ''}{value}%</div>
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{label}</div>
    </div>
  )
}

// ── Component ──────────────────────────────────────────────────────────────
export default function EmergenceDashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'summary' | 'risk' | 'plan' | 'progress'>('summary')

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/emergence/report/${userId}`)
      .then(r => r.json())
      .then(json => setReport(json.data ?? null))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [userId])

  const tabs = [
    { id: 'summary',  label: '执行摘要' },
    { id: 'risk',     label: '风险评估' },
    { id: 'plan',     label: '行动计划' },
    { id: 'progress', label: '进展追踪' },
  ] as const

  return (
    <AppShell
      actions={
        <button className="button button-ghost" onClick={() => navigate('/emergence-patterns')}>
          查看模式详情
        </button>
      }
    >
      <PageHeader title="涌现综合报告" subtitle="跨域风险评估 · 行动计划 · 进展追踪" />
      {loading && <p style={{ color: 'var(--text-tertiary)' }}>加载中…</p>}
      {!loading && !report && (
        <div className="empty-state-block" style={{ padding: 48, textAlign: 'center' }}>
          <strong>暂无报告数据</strong>
          <p>继续使用 AI 对话，系统将自动生成涌现分析报告。</p>
        </div>
      )}

      {report && (
        <>
          {/* status banner */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 16, padding: '16px 20px',
            borderRadius: 20, marginBottom: 4,
            background: `linear-gradient(135deg, ${STATUS_COLOR[report.executive_summary.status]}22, ${STATUS_COLOR[report.executive_summary.status]}08)`,
            border: `1px solid ${STATUS_COLOR[report.executive_summary.status]}33`,
          }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
              background: STATUS_COLOR[report.executive_summary.status],
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22, fontWeight: 800, color: '#fff' }}>
              {STATUS_LABEL[report.executive_summary.status]?.[0] ?? '?'}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <StatusPill tone={STATUS_TONE[report.executive_summary.status] ?? 'primary'}>
                  {STATUS_LABEL[report.executive_summary.status] ?? report.executive_summary.status}
                </StatusPill>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                  {new Date(report.report_date).toLocaleDateString('zh-CN')}
                </span>
              </div>
              <p style={{ margin: 0, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {report.executive_summary.message}
              </p>
            </div>
          </div>

          {/* key metrics */}
          <section className="metrics-grid">
            <div className="glass-card" style={{ padding: 20 }}>
              <p className="metric-label">总模式数</p>
              <p className="metric-value tone-primary" style={{ fontSize: 22 }}>{report.executive_summary.total_patterns}</p>
            </div>
            <div className="glass-card" style={{ padding: 20 }}>
              <p className="metric-label">高影响模式</p>
              <p className="metric-value tone-warning" style={{ fontSize: 22 }}>{report.executive_summary.high_impact_patterns}</p>
            </div>
            <div className="glass-card" style={{ padding: 20 }}>
              <p className="metric-label">主要关注</p>
              <p style={{ fontSize: 14, fontWeight: 700, color: 'var(--danger)', margin: '8px 0 0' }}>
                {report.executive_summary.top_concern?.type ?? '—'}
              </p>
            </div>
            <div className="glass-card" style={{ padding: 20 }}>
              <p className="metric-label">风险等级</p>
              <StatusPill tone={STATUS_TONE[report.risk_assessment?.overall_risk_level] ?? 'primary'} >
                {STATUS_LABEL[report.risk_assessment?.overall_risk_level] ?? report.risk_assessment?.overall_risk_level ?? '—'}
              </StatusPill>
            </div>
          </section>

          {/* tabs */}
          <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--border-light)', paddingBottom: 0 }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                padding: '10px 18px', border: 'none', cursor: 'pointer', fontSize: 14, fontWeight: 600,
                background: 'transparent', borderBottom: tab === t.id ? '2px solid var(--primary)' : '2px solid transparent',
                color: tab === t.id ? 'var(--primary)' : 'var(--text-secondary)',
                transition: 'all 0.15s',
              }}>{t.label}</button>
            ))}
          </div>

          {/* tab content */}
          {tab === 'summary' && (
            <GlassCard title="执行摘要" subtitle="系统综合分析结论">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <p style={{ lineHeight: 1.8, color: 'var(--text-secondary)' }}>{report.executive_summary.message}</p>
                {report.recommendations?.length > 0 && (
                  <div>
                    <p style={{ fontWeight: 600, marginBottom: 8 }}>核心建议</p>
                    <ul className="plain-list">{report.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
                  </div>
                )}
              </div>
            </GlassCard>
          )}

          {tab === 'risk' && report.risk_assessment && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: '严重风险', items: report.risk_assessment.risk_distribution?.critical ?? [], color: '#FF4444' },
                { label: '高风险',   items: report.risk_assessment.risk_distribution?.high ?? [],     color: '#FF8844' },
              ].map(g => g.items.length > 0 && (
                <GlassCard key={g.label} title={g.label} subtitle={`${g.items.length} 项`}>
                  <ul className="plain-list" style={{ color: 'var(--text-secondary)' }}>
                    {g.items.map((item, i) => (
                      <li key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border-light)' }}>
                        <span style={{ color: g.color, marginRight: 6 }}>●</span>{item.description}
                      </li>
                    ))}
                  </ul>
                </GlassCard>
              ))}
            </div>
          )}

          {tab === 'plan' && report.action_plan && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { key: 'immediate_actions', label: '立即行动', color: '#FF3B30' },
                { key: 'short_term_actions', label: '短期计划', color: '#FF9500' },
                { key: 'long_term_actions', label: '长期规划', color: '#00C853' },
              ].map(({ key, label, color }) => {
                const item = report.action_plan[key as keyof ActionPlan]
                if (!item?.actions?.length) return null
                return (
                  <GlassCard key={key} title={label} subtitle={item.timeframe}>
                    <ul className="plain-list">
                      {item.actions.map((a, i) => (
                        <li key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border-light)', color: 'var(--text-secondary)' }}>
                          <span style={{ color, marginRight: 6 }}>▸</span>{a}
                        </li>
                      ))}
                    </ul>
                  </GlassCard>
                )
              })}
            </div>
          )}

          {tab === 'progress' && report.progress_tracking && (
            <GlassCard title="进展追踪" subtitle="近期变化趋势">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 32, fontWeight: 800,
                    color: TREND_COLOR[report.progress_tracking.trend] ?? '#999' }}>
                    {TREND_ICON[report.progress_tracking.trend] ?? '→'}
                  </span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>
                      {report.progress_tracking.trend === 'improving' ? '持续改善' :
                       report.progress_tracking.trend === 'declining' ? '需要关注' : '保持稳定'}
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>整体趋势</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <ChangeChip label="健康变化" value={report.progress_tracking.changes.health_change} />
                  <ChangeChip label="情绪变化" value={report.progress_tracking.changes.mood_change} />
                  <ChangeChip label="压力变化" value={report.progress_tracking.changes.stress_change} />
                </div>
              </div>
            </GlassCard>
          )}
        </>
      )}
    </AppShell>
  )
}
