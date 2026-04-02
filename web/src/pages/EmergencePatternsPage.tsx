import { useEffect, useState } from 'react'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { StatusPill } from '../components/common/StatusPill'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

interface EmergentPattern {
  id: string
  type: string
  domains: string[]
  description: string
  confidence: number
  impact_score: number
  recommendations: string[]
}
interface PatternSummary {
  total_patterns: number
  by_type: Record<string, number>
  high_impact: number
  patterns: EmergentPattern[]
}

const TYPE_META: Record<string, { label: string; color: string }> = {
  cascade:      { label: '级联效应', color: '#FF6B6B' },
  feedback_loop:{ label: '反馈环',   color: '#4ECDC4' },
  tipping_point:{ label: '临界点',   color: '#FFE66D' },
  synergy:      { label: '协同效应', color: '#95E1D3' },
}
const impactTone = (s: number): 'danger' | 'warning' | 'primary' | 'success' =>
  s > 0.8 ? 'danger' : s > 0.6 ? 'warning' : s > 0.4 ? 'primary' : 'success'
const impactLabel = (s: number) =>
  s > 0.8 ? '极高' : s > 0.6 ? '高' : s > 0.4 ? '中' : '低'

const TABS = [
  { id: 'all',          label: '全部' },
  { id: 'cascade',      label: '级联效应' },
  { id: 'feedback_loop',label: '反馈环' },
  { id: 'tipping_point',label: '临界点' },
  { id: 'synergy',      label: '协同效应' },
]

export default function EmergencePatternsPage() {
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'
  const [summary, setSummary] = useState<PatternSummary | null>(null)
  const [tab, setTab] = useState('all')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/emergence/patterns/${userId}`)
      .then(r => r.json())
      .then(json => setSummary(json.data ?? null))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [userId])

  const patterns = summary?.patterns ?? []
  const filtered = tab === 'all' ? patterns : patterns.filter(p => p.type === tab)

  return (
    <AppShell title="涌现模式" subtitle="系统检测到的跨域关联模式">
      {loading && <p style={{ color: 'var(--text-tertiary)' }}>加载中…</p>}

      {summary && (
        <section className="metrics-grid">
          {[
            { label: '总模式数',   value: summary.total_patterns, tone: 'primary'   },
            { label: '高影响模式', value: summary.high_impact,    tone: 'warning'   },
            ...Object.entries(summary.by_type).map(([k, v]) => ({
              label: TYPE_META[k]?.label ?? k, value: v, tone: 'secondary' as const,
            })),
          ].slice(0, 4).map(m => (
            <div key={m.label} className="glass-card" style={{ padding: 20 }}>
              <p className="metric-label">{m.label}</p>
              <p className={`metric-value tone-${m.tone}`} style={{ fontSize: 22 }}>{m.value}</p>
            </div>
          ))}
        </section>
      )}

      {/* tabs */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', margin: '4px 0' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: '6px 16px', borderRadius: 999, border: 'none', cursor: 'pointer',
            fontSize: 13, fontWeight: 600,
            background: tab === t.id ? 'var(--primary)' : 'rgba(255,255,255,0.7)',
            color: tab === t.id ? '#fff' : '#555',
            boxShadow: tab === t.id ? '0 4px 12px rgba(10,89,247,0.3)' : 'none',
          }}>{t.label}</button>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {filtered.length === 0 && !loading && (
          <div className="empty-state-block">
            <strong>暂无涌现模式</strong>
            <p>继续使用 AI 对话，系统将自动检测跨域关联。</p>
          </div>
        )}
        {filtered.map(p => {
          const meta = TYPE_META[p.type] ?? { label: p.type, color: '#999' }
          const isOpen = expanded === p.id
          return (
            <article key={p.id} className="glass-card" style={{ cursor: 'pointer' }}
              onClick={() => setExpanded(isOpen ? null : p.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: meta.color,
                    background: meta.color + '22', padding: '3px 10px', borderRadius: 999 }}>
                    {meta.label}
                  </span>
                  {p.domains.map(d => (
                    <span key={d} style={{ fontSize: 11, color: 'var(--text-tertiary)',
                      background: 'rgba(0,0,0,0.05)', padding: '2px 8px', borderRadius: 999 }}>{d}</span>
                  ))}
                </div>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 8 }}>
                  <StatusPill tone={impactTone(p.impact_score)}>影响 {impactLabel(p.impact_score)}</StatusPill>
                </div>
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '0 0 8px' }}>{p.description}</p>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-tertiary)' }}>
                <span>置信度 {Math.round(p.confidence * 100)}%</span>
                <span>影响分 {p.impact_score.toFixed(2)}</span>
                <span style={{ marginLeft: 'auto' }}>{isOpen ? '▲ 收起' : '▼ 展开建议'}</span>
              </div>
              {isOpen && p.recommendations.length > 0 && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-light)' }}>
                  <p style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>行动建议</p>
                  <ul className="plain-list" style={{ color: 'var(--text-secondary)' }}>
                    {p.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
            </article>
          )
        })}
      </div>
    </AppShell>
  )
}
