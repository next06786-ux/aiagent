import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { StatusPill } from '../components/common/StatusPill'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

// ── Types ──────────────────────────────────────────────────────────────────
interface InsightItem {
  id: string; title: string; description: string
  type: 'prediction' | 'anomaly' | 'suggestion'
  confidence: number; timestamp: number
}
interface MetricItem {
  title: string; value: string; trend: string; trendUp: boolean; color: string
}

const TYPE_META: Record<string, { label: string; tone: 'primary' | 'warning' | 'success' }> = {
  prediction: { label: '预测', tone: 'primary'  },
  anomaly:    { label: '异常', tone: 'warning'  },
  suggestion: { label: '建议', tone: 'success'  },
}

// animated counter hook
function useCounter(target: number, duration = 1200) {
  const [val, setVal] = useState(0)
  const raf = useRef(0)
  useEffect(() => {
    const start = performance.now()
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1)
      setVal(Math.round(p * target))
      if (p < 1) raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [target, duration])
  return val
}

function MetricCard({ m }: { m: MetricItem }) {
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <p className="metric-label">{m.title}</p>
        <span style={{ fontSize: 12, fontWeight: 700, color: m.trendUp ? '#00C853' : '#FF3B30' }}>
          {m.trend}
        </span>
      </div>
      <p className="metric-value" style={{ fontSize: 28, color: m.color }}>{m.value}</p>
    </div>
  )
}

// ── Component ──────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'

  const [insights, setInsights] = useState<InsightItem[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState(0)

  // static metrics (animated)
  const c1 = useCounter(12450)
  const c2 = useCounter(856)

  const metrics: MetricItem[] = [
    { title: '感知数据',   value: c1.toLocaleString(), trend: '+12%', trendUp: true,  color: 'var(--primary)'   },
    { title: '预测准确率', value: '94.2%',              trend: '+2.1%',trendUp: true,  color: 'var(--accent)'    },
    { title: '异常检测',   value: '3',                  trend: '-1',   trendUp: false, color: 'var(--warning)'   },
    { title: '知识节点',   value: c2.toLocaleString(),  trend: '+45',  trendUp: true,  color: 'var(--secondary)' },
  ]

  useEffect(() => {
    // try real API, fallback to mock
    fetch(`${API_BASE_URL}/api/v4/emergence/dashboard/${userId}`)
      .then(r => r.json())
      .then(json => {
        if (json.success && json.data?.top_insights?.length) {
          setInsights(json.data.top_insights)
        } else { setInsights(MOCK_INSIGHTS) }
      })
      .catch(() => setInsights(MOCK_INSIGHTS))
      .finally(() => setLoading(false))
  }, [userId])

  const TABS = ['全部', '预测', '异常', '建议']
  const typeFilter = ['all', 'prediction', 'anomaly', 'suggestion']
  const filtered = tab === 0 ? insights : insights.filter(i => i.type === typeFilter[tab])

  return (
    <AppShell title="智能仪表盘" subtitle="感知数据 · 预测分析 · 异常检测"
      actions={
        <button className="button button-ghost" onClick={() => navigate('/insights')}>
          查看洞察详情
        </button>
      }
    >
      {/* metrics */}
      <section className="metrics-grid">
        {metrics.map(m => <MetricCard key={m.title} m={m} />)}
      </section>

      {/* quick links */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {[
          { label: '知识星图',   route: '/knowledge-graph', color: '#667EEA' },
          { label: '智能洞察',   route: '/insights',        color: '#FF9500' },
          { label: '涌现报告',   route: '/emergence-dashboard', color: '#FF6B6B' },
          { label: '生活领域',   route: '/life-domain-insights', color: '#4ECDC4' },
        ].map(l => (
          <button key={l.label} onClick={() => navigate(l.route)} style={{
            padding: '10px 20px', borderRadius: 999, border: 'none', cursor: 'pointer',
            fontSize: 13, fontWeight: 600, color: '#fff',
            background: `linear-gradient(135deg, ${l.color}, ${l.color}bb)`,
            boxShadow: `0 4px 12px ${l.color}44`,
          }}>{l.label}</button>
        ))}
      </div>

      {/* insight list */}
      <GlassCard title="最新洞察" subtitle="AI 系统实时分析结果"
        action={
          <div style={{ display: 'flex', gap: 6 }}>
            {TABS.map((t, i) => (
              <button key={t} onClick={() => setTab(i)} style={{
                padding: '4px 12px', borderRadius: 999, border: 'none', cursor: 'pointer',
                fontSize: 12, fontWeight: 600,
                background: tab === i ? 'var(--primary)' : 'rgba(0,0,0,0.06)',
                color: tab === i ? '#fff' : 'var(--text-secondary)',
              }}>{t}</button>
            ))}
          </div>
        }
      >
        {loading && <p style={{ color: 'var(--text-tertiary)' }}>加载中…</p>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map(ins => {
            const meta = TYPE_META[ins.type] ?? { label: ins.type, tone: 'primary' as const }
            return (
              <div key={ins.id} style={{ padding: '14px 16px', borderRadius: 16,
                background: 'rgba(255,255,255,0.6)', border: '1px solid var(--border-light)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                  <strong style={{ fontSize: 15 }}>{ins.title}</strong>
                  <div style={{ display: 'flex', gap: 8, flexShrink: 0, marginLeft: 12 }}>
                    <StatusPill tone={meta.tone}>{meta.label}</StatusPill>
                    <span style={{ fontSize: 12, color: 'var(--text-tertiary)', alignSelf: 'center' }}>
                      {Math.round(ins.confidence * 100)}%
                    </span>
                  </div>
                </div>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
                  {ins.description}
                </p>
                <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: '6px 0 0' }}>
                  {new Date(ins.timestamp).toLocaleString('zh-CN')}
                </p>
              </div>
            )
          })}
          {!loading && filtered.length === 0 && (
            <p style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: 24 }}>暂无数据</p>
          )}
        </div>
      </GlassCard>
    </AppShell>
  )
}

// ── Mock data ──────────────────────────────────────────────────────────────
const MOCK_INSIGHTS: InsightItem[] = [
  { id: '1', title: '睡眠质量预警', type: 'prediction', confidence: 0.85, timestamp: Date.now() - 3600000,
    description: '根据最近3天的活动数据，预测今晚睡眠质量可能下降，建议提前1小时休息。' },
  { id: '2', title: '工作效率高峰', type: 'suggestion', confidence: 0.92, timestamp: Date.now() - 7200000,
    description: '检测到您在上午10:00-11:30期间专注度最高，建议安排重要任务。' },
  { id: '3', title: '异常心率波动', type: 'anomaly', confidence: 0.78, timestamp: Date.now() - 86400000,
    description: '昨日下午运动后心率恢复较慢，建议关注心血管健康。' },
]
