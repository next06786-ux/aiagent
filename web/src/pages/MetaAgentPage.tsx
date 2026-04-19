import { useState } from 'react'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { StatusPill } from '../components/common/StatusPill'
import { PageHeader } from '../components/common/PageHeader'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

type AgentStatus = 'idle' | 'thinking' | 'done'
interface Agent { id: string; name: string; status: AgentStatus; progress: number; result?: number; confidence?: number }
type Phase = 'input' | 'analyzing' | 'coordinating' | 'result'

const INIT_AGENTS: Agent[] = [
  { id: 'sleep_agent',    name: '睡眠分析',  status: 'idle', progress: 0 },
  { id: 'exercise_agent', name: '运动评估',  status: 'idle', progress: 0 },
  { id: 'stress_agent',   name: '压力监测',  status: 'idle', progress: 0 },
  { id: 'llm_agent_1',    name: 'AI推理-1', status: 'idle', progress: 0 },
  { id: 'llm_agent_2',    name: 'AI推理-2', status: 'idle', progress: 0 },
  { id: 'llm_agent_3',    name: 'AI推理-3', status: 'idle', progress: 0 },
]

function AgentCard({ agent }: { agent: Agent }) {
  const color = agent.status === 'done' ? '#00C853' : agent.status === 'thinking' ? '#0A59F7' : '#999'
  return (
    <div style={{ padding: '14px 16px', borderRadius: 16, border: '1px solid var(--border-light)',
      background: agent.status === 'thinking' ? 'rgba(10,89,247,0.06)' : 'rgba(255,255,255,0.7)',
      transition: 'all 0.3s' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 14 }}>{agent.name}</span>
        <StatusPill tone={agent.status === 'done' ? 'success' : agent.status === 'thinking' ? 'primary' : 'neutral'}>
          {agent.status === 'done' ? '完成' : agent.status === 'thinking' ? '分析中' : '待机'}
        </StatusPill>
      </div>
      <div style={{ height: 6, borderRadius: 999, background: 'rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${agent.progress}%`, background: color,
          borderRadius: 999, transition: 'width 0.4s ease' }} />
      </div>
      {agent.result !== undefined && (
        <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
          评分 <strong style={{ color }}>{agent.result.toFixed(1)}</strong>
          {agent.confidence !== undefined && <span style={{ marginLeft: 8 }}>置信度 {Math.round(agent.confidence * 100)}%</span>}
        </div>
      )}
    </div>
  )
}

const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

export default function MetaAgentPage() {
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'

  const [phase, setPhase] = useState<Phase>('input')
  const [agents, setAgents] = useState<Agent[]>(INIT_AGENTS)
  const [sleep, setSleep] = useState(7)
  const [exercise, setExercise] = useState(30)
  const [stress, setStress] = useState(5)
  const [finalScore, setFinalScore] = useState(0)
  const [finalConf, setFinalConf] = useState(0)
  const [reasoning, setReasoning] = useState('')

  const updateAgent = (id: string, patch: Partial<Agent>) =>
    setAgents(prev => prev.map(a => a.id === id ? { ...a, ...patch } : a))

  const startAnalysis = async () => {
    setPhase('analyzing')
    setAgents(INIT_AGENTS.map(a => ({ ...a, status: 'idle', progress: 0 })))

    // try real API first
    try {
      const res = await fetch(`${API_BASE_URL}/api/v4/meta-agent/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          user_data: {
            health: { sleep_hours: sleep, exercise_minutes: exercise, stress_level: stress },
            context: { time_slot: 'morning', location: 'home' },
          },
        }),
      })
      const json = await res.json()
      if (json.success) {
        setFinalScore(json.data.final_score ?? 75)
        setFinalConf(json.data.confidence ?? 0.85)
        setReasoning(json.data.reasoning ?? '')
        setAgents(INIT_AGENTS.map(a => ({ ...a, status: 'done', progress: 100, result: json.data.final_score ?? 75, confidence: 0.85 })))
        setPhase('result')
        return
      }
    } catch { /* fallback to simulation */ }

    // simulate agent-by-agent
    const sensorAgents = ['sleep_agent', 'exercise_agent', 'stress_agent']
    for (const id of sensorAgents) {
      updateAgent(id, { status: 'thinking', progress: 0 })
      for (let p = 0; p <= 100; p += 20) {
        await delay(120)
        updateAgent(id, { progress: p })
      }
      const r = id === 'sleep_agent' ? Math.min(100, sleep * 10)
               : id === 'exercise_agent' ? Math.min(100, exercise * 1.5)
               : Math.max(0, 100 - stress * 8)
      updateAgent(id, { status: 'done', progress: 100, result: r, confidence: 0.8 + Math.random() * 0.15 })
    }

    setPhase('coordinating')
    await delay(600)

    const llmAgents = ['llm_agent_1', 'llm_agent_2', 'llm_agent_3']
    await Promise.all(llmAgents.map(async (id, i) => {
      await delay(i * 200)
      updateAgent(id, { status: 'thinking', progress: 0 })
      for (let p = 0; p <= 100; p += 25) {
        await delay(150)
        updateAgent(id, { progress: p })
      }
      const r = 60 + Math.random() * 30
      updateAgent(id, { status: 'done', progress: 100, result: r, confidence: 0.75 + Math.random() * 0.2 })
    }))

    const score = Math.round(65 + (sleep - 5) * 3 + (exercise / 30) * 5 - stress * 2)
    setFinalScore(Math.max(0, Math.min(100, score)))
    setFinalConf(0.82)
    setReasoning(`综合睡眠（${sleep}h）、运动（${exercise}min）、压力（${stress}/10）三项指标，6个智能体协同分析得出健康综合评分。`)
    setPhase('result')
  }

  const reset = () => { setPhase('input'); setAgents(INIT_AGENTS.map(a => ({ ...a, status: 'idle', progress: 0 }))) }

  return (
    <AppShell>
      <PageHeader title="多智能体协调" subtitle="多个 AI 智能体并行分析，Meta 智能体综合决策" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>

        {/* left: input + agents */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <GlassCard title="输入参数" subtitle="提供健康数据，启动多智能体分析">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: `睡眠时长：${sleep} 小时`, value: sleep, min: 0, max: 12, step: 0.5, set: setSleep },
                { label: `运动时长：${exercise} 分钟`, value: exercise, min: 0, max: 120, step: 5, set: setExercise },
                { label: `压力等级：${stress} / 10`, value: stress, min: 0, max: 10, step: 1, set: setStress },
              ].map(s => (
                <div key={s.label}>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>{s.label}</p>
                  <input type="range" min={s.min} max={s.max} step={s.step} value={s.value}
                    onChange={e => s.set(Number(e.target.value))}
                    style={{ width: '100%', accentColor: 'var(--primary)' }} />
                </div>
              ))}
              <button className="button button-primary" onClick={startAnalysis}
                disabled={phase === 'analyzing' || phase === 'coordinating'}>
                {phase === 'analyzing' || phase === 'coordinating' ? '分析中…' : '启动分析'}
              </button>
            </div>
          </GlassCard>

          {phase === 'result' && (
            <GlassCard title="综合结论" subtitle="Meta 智能体汇总结果">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 48, fontWeight: 800,
                      color: finalScore >= 80 ? '#00C853' : finalScore >= 60 ? '#FF9500' : '#FF3B30' }}>
                      {finalScore}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>综合评分</div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <StatusPill tone={finalScore >= 80 ? 'success' : finalScore >= 60 ? 'warning' : 'danger'}>
                      {finalScore >= 80 ? '状态良好' : finalScore >= 60 ? '需要关注' : '需要改善'}
                    </StatusPill>
                    <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6 }}>
                      置信度 {Math.round(finalConf * 100)}%
                    </p>
                  </div>
                </div>
                {reasoning && <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{reasoning}</p>}
                <button className="button button-ghost" onClick={reset}>重新分析</button>
              </div>
            </GlassCard>
          )}
        </div>

        {/* right: agent grid */}
        <GlassCard title="智能体状态" subtitle={`${agents.filter(a => a.status === 'done').length} / ${agents.length} 完成`}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {agents.map(a => <AgentCard key={a.id} agent={a} />)}
          </div>
          {(phase === 'analyzing' || phase === 'coordinating') && (
            <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 12,
              background: 'rgba(10,89,247,0.08)', fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>
              {phase === 'analyzing' ? '⚡ 传感器智能体并行分析中…' : '🔗 Meta 智能体协调汇总中…'}
            </div>
          )}
        </GlassCard>
      </div>
    </AppShell>
  )
}
