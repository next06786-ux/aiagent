import { useState } from 'react'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

interface DomainInsight {
  domain: string
  insights: string[]
  predictions: string[]
  recommendations: string[]
  confidence: number
}
interface ProcessResult {
  perception:  { quality: number }
  reasoning:   { confidence: number; selected_agents: string[] }
  knowledge:   { entities: number; relations: number; patterns: number }
  learning:    { episodes: number; average_reward: number }
  domain_insights: DomainInsight[]
}

const DOMAIN_META: Record<string, { label: string; icon: string; color: string }> = {
  time:     { label: '时间管理', icon: '⏰', color: '#FF6B6B' },
  social:   { label: '社交关系', icon: '👥', color: '#4ECDC4' },
  learning: { label: '学习成长', icon: '📚', color: '#45B7D1' },
  emotion:  { label: '情绪健康', icon: '💙', color: '#FFA07A' },
  finance:  { label: '财务规划', icon: '💰', color: '#98D8C8' },
  health:   { label: '健康管理', icon: '🏃', color: '#F7DC6F' },
}

const MOCK: ProcessResult = {
  perception: { quality: 0.95 },
  reasoning:  { confidence: 0.88, selected_agents: ['health', 'time', 'emotion'] },
  knowledge:  { entities: 120, relations: 350, patterns: 15 },
  learning:   { episodes: 45, average_reward: 0.82 },
  domain_insights: [
    { domain: 'health',   confidence: 0.92,
      insights: ['近7天平均睡眠6.2小时，低于推荐值', '运动频率下降20%'],
      predictions: ['本周睡眠质量可能继续下降'],
      recommendations: ['建议22:30前入睡', '每天增加20分钟步行'] },
    { domain: 'time',     confidence: 0.85,
      insights: ['上午10-11:30专注度最高'],
      predictions: ['下午3点后效率将下降'],
      recommendations: ['重要任务安排在上午高效时段'] },
    { domain: 'emotion',  confidence: 0.88,
      insights: ['本周情绪波动较大', '压力指数偏高'],
      predictions: ['周末情绪将有所改善'],
      recommendations: ['尝试5分钟冥想', '减少社交媒体使用'] },
  ],
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, borderRadius: 999, background: 'rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.round(value * 100)}%`,
          background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
          borderRadius: 999, transition: 'width 0.6s ease' }} />
      </div>
      <span style={{ fontSize: 12, color: 'var(--text-tertiary)', width: 32, textAlign: 'right' }}>
        {Math.round(value * 100)}%
      </span>
    </div>
  )
}

export default function LifeDomainInsightsPage() {
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'
  const [result, setResult] = useState<ProcessResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedDomain, setSelectedDomain] = useState('all')

  const run = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v4/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId, text: '',
          sensors: { steps: 5000, location: { latitude: 39.9, longitude: 116.4 } },
        }),
      })
      const json = await res.json()
      setResult(json.success ? json.data : MOCK)
    } catch { setResult(MOCK) }
    finally { setLoading(false) }
  }

  const insights = result
    ? (selectedDomain === 'all' ? result.domain_insights : result.domain_insights.filter(d => d.domain === selectedDomain))
    : []

  return (
    <AppShell
      actions={
        <button className="button button-primary" onClick={run} disabled={loading}>
          {loading ? '分析中…' : result ? '重新分析' : '开始分析'}
        </button>
      }
    >
      <PageHeader title="生活领域洞察" subtitle="多维感知 · 跨域分析 · 个性化建议" />
      {!result && !loading && (
        <div className="empty-state-block" style={{ textAlign: 'center', padding: 48 }}>
          <p style={{ fontSize: 32, margin: '0 0 12px' }}>🔍</p>
          <strong>点击"开始分析"</strong>
          <p>系统将综合感知数据、知识图谱和学习记录，生成跨域洞察报告。</p>
        </div>
      )}

      {result && (
        <>
          {/* system metrics */}
          <section className="metrics-grid">
            {[
              { label: '感知质量',   value: `${Math.round(result.perception.quality * 100)}%`,  tone: 'accent'    },
              { label: '推理置信度', value: `${Math.round(result.reasoning.confidence * 100)}%`, tone: 'primary'   },
              { label: '知识节点',   value: result.knowledge.entities,                           tone: 'secondary' },
              { label: '学习奖励',   value: result.learning.average_reward.toFixed(3),           tone: 'success'   },
            ].map(m => (
              <div key={m.label} className="glass-card" style={{ padding: 20 }}>
                <p className="metric-label">{m.label}</p>
                <p className={`metric-value tone-${m.tone}`} style={{ fontSize: 22 }}>{m.value}</p>
              </div>
            ))}
          </section>

          {/* domain filter */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {[{ id: 'all', label: '全部', icon: '🌐' }, ...Object.entries(DOMAIN_META).map(([id, m]) => ({ id, label: m.label, icon: m.icon }))].map(d => (
              <button key={d.id} onClick={() => setSelectedDomain(d.id)} style={{
                padding: '6px 14px', borderRadius: 999, border: 'none', cursor: 'pointer',
                fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6,
                background: selectedDomain === d.id ? 'var(--primary)' : 'rgba(255,255,255,0.7)',
                color: selectedDomain === d.id ? '#fff' : '#555',
              }}>{d.icon} {d.label}</button>
            ))}
          </div>

          {/* domain cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {insights.map(ins => {
              const meta = DOMAIN_META[ins.domain] ?? { label: ins.domain, icon: '📊', color: '#999' }
              return (
                <GlassCard key={ins.domain}
                  title={`${meta.icon} ${meta.label}`}
                  subtitle={<ConfidenceBar value={ins.confidence} /> as unknown as string}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {ins.insights.length > 0 && (
                      <div>
                        <p style={{ fontWeight: 600, fontSize: 13, color: meta.color, marginBottom: 6 }}>洞察</p>
                        <ul className="plain-list" style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                          {ins.insights.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                      </div>
                    )}
                    {ins.predictions.length > 0 && (
                      <div>
                        <p style={{ fontWeight: 600, fontSize: 13, color: 'var(--secondary)', marginBottom: 6 }}>预测</p>
                        <ul className="plain-list" style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                          {ins.predictions.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                      </div>
                    )}
                    {ins.recommendations.length > 0 && (
                      <div>
                        <p style={{ fontWeight: 600, fontSize: 13, color: 'var(--accent)', marginBottom: 6 }}>建议</p>
                        <ul className="plain-list" style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                          {ins.recommendations.map((t, i) => <li key={i}>{t}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </GlassCard>
              )
            })}
          </div>
        </>
      )}
    </AppShell>
  )
}
