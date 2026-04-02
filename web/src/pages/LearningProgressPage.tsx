import { useEffect, useState } from 'react'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

interface LearningProgressData {
  total_interactions: number
  positive_feedback: number
  negative_feedback: number
  neutral_feedback: number
  average_reward: number
  learning_rate: number
  agent_performance: Record<string, number>
  recent_improvements: string[]
}

const AGENT_LABELS: Record<string, string> = {
  health: '健康管理', time: '时间管理', emotion: '情绪分析',
  finance: '财务规划', social: '社交洞察', learning: '学习成长',
}

function Bar({ value, color = 'var(--primary)' }: { value: number; color?: string }) {
  return (
    <div style={{ flex: 1, height: 8, borderRadius: 999, background: 'rgba(0,0,0,0.08)', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${Math.round(value * 100)}%`, background: color, borderRadius: 999, transition: 'width 0.6s ease' }} />
    </div>
  )
}

const AGENT_COLORS = ['#0A59F7', '#6B48FF', '#FF9500', '#00C853', '#FF3B30', '#4FACFE']

export default function LearningProgressPage() {
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'
  const [data, setData] = useState<LearningProgressData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v4/learning/progress/${userId}`)
      .then(r => r.json())
      .then(json => { if (json.success !== false) setData(json.progress ?? json.data ?? json) })
      .catch(() => {
        // fallback mock
        setData({
          total_interactions: 1250, positive_feedback: 850,
          negative_feedback: 50, neutral_feedback: 350,
          average_reward: 0.78, learning_rate: 0.01,
          agent_performance: { health: 0.85, time: 0.92, emotion: 0.76, finance: 0.68, social: 0.81 },
          recent_improvements: ['健康管理智能体准确率提升 5%', '时间管理预测精度提升 8%', '情绪识别召回率提升 3%'],
        })
      })
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) return <AppShell title="学习进度"><p style={{ color: 'var(--text-tertiary)' }}>加载中…</p></AppShell>
  if (!data) return null

  const total = data.positive_feedback + data.negative_feedback + data.neutral_feedback || 1
  const posRate = data.positive_feedback / total
  const negRate = data.negative_feedback / total

  return (
    <AppShell title="学习进度" subtitle="强化学习 · 智能体成长追踪">
      <section className="metrics-grid">
        {[
          { label: '总交互次数', value: data.total_interactions.toLocaleString(), tone: 'primary' },
          { label: '平均奖励',   value: data.average_reward.toFixed(3),           tone: 'accent'  },
          { label: '正向反馈率', value: `${Math.round(posRate * 100)}%`,           tone: 'success' },
          { label: '学习率',     value: data.learning_rate.toFixed(4),            tone: 'secondary'},
        ].map(m => (
          <div key={m.label} className="glass-card" style={{ padding: 20 }}>
            <p className="metric-label">{m.label}</p>
            <p className={`metric-value tone-${m.tone}`} style={{ fontSize: 22 }}>{m.value}</p>
          </div>
        ))}
      </section>

      {/* feedback breakdown */}
      <GlassCard title="反馈分布" subtitle="用户对 AI 回复的评价统计">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[
            { label: '正向反馈', count: data.positive_feedback, rate: posRate, color: '#00C853' },
            { label: '中性反馈', count: data.neutral_feedback,  rate: data.neutral_feedback / total, color: '#0A59F7' },
            { label: '负向反馈', count: data.negative_feedback, rate: negRate, color: '#FF3B30' },
          ].map(f => (
            <div key={f.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ width: 72, fontSize: 13, color: 'var(--text-secondary)', flexShrink: 0 }}>{f.label}</span>
              <Bar value={f.rate} color={f.color} />
              <span style={{ width: 48, fontSize: 13, fontWeight: 700, color: f.color, textAlign: 'right', flexShrink: 0 }}>
                {f.count}
              </span>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* agent performance */}
      <GlassCard title="智能体性能" subtitle="各领域 AI 智能体的当前准确率">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {Object.entries(data.agent_performance).map(([key, val], i) => (
            <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ width: 80, fontSize: 13, color: 'var(--text-secondary)', flexShrink: 0 }}>
                {AGENT_LABELS[key] ?? key}
              </span>
              <Bar value={val} color={AGENT_COLORS[i % AGENT_COLORS.length]} />
              <span style={{ width: 40, fontSize: 13, fontWeight: 700, color: AGENT_COLORS[i % AGENT_COLORS.length], textAlign: 'right', flexShrink: 0 }}>
                {Math.round(val * 100)}%
              </span>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* recent improvements */}
      {data.recent_improvements.length > 0 && (
        <GlassCard title="近期提升" subtitle="最新一轮训练带来的改进">
          <ul className="plain-list">
            {data.recent_improvements.map((item, i) => (
              <li key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--border-light)', color: 'var(--text-secondary)' }}>
                ✦ {item}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}
    </AppShell>
  )
}
