import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { StatusPill } from '../components/common/StatusPill'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

interface SmartInsight {
  insight_id: string
  category: string
  level: string
  title: string
  description: string
  evidence: string[]
  recommendations: string[]
  confidence: number
  impact_score: number
  created_at: string
}

interface DashboardSummary {
  total_insights: number
  critical_count: number
  warning_count: number
  suggestion_count: number
}

interface EmotionTrendItem { date: string; avg_emotion: number; count: number }
interface TopicItem { topic: string; count: number }
interface EmergenceStats {
  total_events: number; pattern_events: number; synergy_events: number
  feedback_loop_events: number; threshold_events: number
}
interface DashboardData {
  summary: DashboardSummary
  emotion_trend: EmotionTrendItem[]
  topic_distribution: TopicItem[]
  top_insights: SmartInsight[]
  emergence_stats: EmergenceStats
}

const CATEGORIES = [
  { id: 'all',          label: '全部',     color: '#6B48FF' },
  { id: 'cascade',      label: '级联效应', color: '#FF9500' },
  { id: 'synergy',      label: '协同增益', color: '#00C853' },
  { id: 'tipping_point',label: '临界点',   color: '#FF3B30' },
  { id: 'feedback_loop',label: '反馈环路', color: '#0A59F7' },
  { id: 'pattern',      label: '行为模式', color: '#6B48FF' },
]

const LEVEL_TONE: Record<string, 'danger' | 'warning' | 'primary' | 'success'> = {
  critical: 'danger', warning: 'warning', suggestion: 'primary', info: 'success',
}
const LEVEL_LABEL: Record<string, string> = {
  critical: '严重', warning: '警告', suggestion: '建议', info: '信息',
}

export default function SmartInsightsPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'

  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [insights, setInsights] = useState<SmartInsight[]>([])
  const [category, setCategory] = useState('all')
  const [selected, setSelected] = useState<SmartInsight | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE_URL}/api/v4/emergence/dashboard/${userId}`).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/v4/emergence/insights/${userId}?limit=50`).then(r => r.json()),
    ]).then(([dash, ins]) => {
      if (dash.success) setDashboard(dash.data)
      if (ins.success) setInsights(ins.insights ?? [])
    }).catch(() => setError('无法加载洞察数据')).finally(() => setLoading(false))
  }, [userId])

  const filtered = category === 'all' ? insights : insights.filter(i => i.category === category)

  return (
    <AppShell>
      <PageHeader title="智能洞察" subtitle="涌现发现 · 级联效应 · 行为模式分析" />
      {loading && <div className="app-loading-screen" style={{ minHeight: 300 }}><p>加载中…</p></div>}
      {error && <p style={{ color: 'var(--danger)', padding: 16 }}>{error}</p>}

      {dashboard && (
        <section className="metrics-grid">
          {[
            { label: '总洞察数',   value: dashboard.summary.total_insights,   tone: 'primary'   },
            { label: '严重预警',   value: dashboard.summary.critical_count,   tone: 'warning'   },
            { label: '警告事项',   value: dashboard.summary.warning_count,    tone: 'secondary' },
            { label: '优化建议',   value: dashboard.summary.suggestion_count, tone: 'accent'    },
          ].map(m => (
            <div key={m.label} className={`glass-card tone-${m.tone}`} style={{ padding: 20 }}>
              <p className="metric-label">{m.label}</p>
              <p className="metric-value">{m.value}</p>
            </div>
          ))}
        </section>
      )}

      {/* category filter */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', margin: '8px 0' }}>
        {CATEGORIES.map(c => (
          <button
            key={c.id}
            onClick={() => setCategory(c.id)}
            style={{
              padding: '6px 16px', borderRadius: 999, border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, transition: 'all 0.15s',
              background: category === c.id ? c.color : 'rgba(255,255,255,0.7)',
              color: category === c.id ? '#fff' : '#555',
              boxShadow: category === c.id ? `0 4px 12px ${c.color}44` : 'none',
            }}
          >{c.label}</button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 380px' : '1fr', gap: 18 }}>
        {/* insight list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.length === 0 && !loading && (
            <div className="empty-state-block"><strong>暂无洞察数据</strong><p>继续使用 AI 对话，系统将自动分析行为模式。</p></div>
          )}
          {filtered.map(ins => (
            <article
              key={ins.insight_id}
              className="glass-card"
              style={{ cursor: 'pointer', borderColor: selected?.insight_id === ins.insight_id ? 'rgba(10,89,247,0.3)' : undefined }}
              onClick={() => setSelected(ins.insight_id === selected?.insight_id ? null : ins)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <strong style={{ fontSize: 15 }}>{ins.title}</strong>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 12 }}>
                  <StatusPill tone={LEVEL_TONE[ins.level] ?? 'primary'}>{LEVEL_LABEL[ins.level] ?? ins.level}</StatusPill>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)', alignSelf: 'center' }}>
                    {Math.round(ins.confidence * 100)}%
                  </span>
                </div>
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0 }}>{ins.description}</p>
              <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  影响分: {ins.impact_score?.toFixed(1)}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {new Date(ins.created_at).toLocaleDateString('zh-CN')}
                </span>
              </div>
            </article>
          ))}
        </div>

        {/* detail panel */}
        {selected && (
          <GlassCard title={selected.title} subtitle={`置信度 ${Math.round(selected.confidence * 100)}%`}
            action={<button className="button button-ghost" style={{ padding: '6px 12px', minHeight: 'auto' }} onClick={() => setSelected(null)}>✕</button>}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <p style={{ margin: 0, lineHeight: 1.7 }}>{selected.description}</p>
              {selected.evidence.length > 0 && (
                <div>
                  <p style={{ fontWeight: 600, marginBottom: 6 }}>支撑证据</p>
                  <ul className="plain-list">{selected.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul>
                </div>
              )}
              {selected.recommendations.length > 0 && (
                <div>
                  <p style={{ fontWeight: 600, marginBottom: 6 }}>行动建议</p>
                  <ul className="plain-list">{selected.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
                </div>
              )}
            </div>
          </GlassCard>
        )}
      </div>

      {/* emergence stats */}
      {dashboard?.emergence_stats && (
        <GlassCard title="涌现事件统计" subtitle="系统检测到的跨域关联模式">
          <div className="metrics-grid" style={{ gap: 12 }}>
            {[
              { label: '总事件', value: dashboard.emergence_stats.total_events },
              { label: '行为模式', value: dashboard.emergence_stats.pattern_events },
              { label: '协同增益', value: dashboard.emergence_stats.synergy_events },
              { label: '反馈环路', value: dashboard.emergence_stats.feedback_loop_events },
              { label: '临界点', value: dashboard.emergence_stats.threshold_events },
            ].map(s => (
              <div key={s.label} style={{ padding: '12px 16px', borderRadius: 14, background: 'rgba(255,255,255,0.6)', border: '1px solid var(--border-light)' }}>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-tertiary)' }}>{s.label}</p>
                <p style={{ margin: '4px 0 0', fontSize: 24, fontWeight: 800, color: 'var(--primary)' }}>{s.value}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </AppShell>
  )
}
