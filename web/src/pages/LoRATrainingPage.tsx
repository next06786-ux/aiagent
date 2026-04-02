import { useEffect, useRef, useState } from 'react'
import { AppShell } from '../components/shell/AppShell'
import { GlassCard } from '../components/common/GlassCard'
import { StatusPill } from '../components/common/StatusPill'
import { useAuth } from '../hooks/useAuth'
import { getLoraStatus, getLoraProgress, triggerLoraTraining } from '../services/decision'

export default function LoRATrainingPage() {
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'

  const [status, setStatus] = useState<Awaited<ReturnType<typeof getLoraStatus>> | null>(null)
  const [progress, setProgress] = useState<Awaited<ReturnType<typeof getLoraProgress>> | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [msg, setMsg] = useState('')
  const pollRef = useRef<number>(-1)

  const load = async () => {
    try {
      const s = await getLoraStatus(userId)
      setStatus(s)
      if (s.is_loaded || progress?.is_training) {
        const p = await getLoraProgress(userId)
        setProgress(p)
      }
    } catch { /* ignore */ } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [userId]) // eslint-disable-line

  // poll while training
  useEffect(() => {
    if (progress?.is_training) {
      pollRef.current = window.setInterval(async () => {
        try {
          const p = await getLoraProgress(userId)
          setProgress(p)
          if (!p.is_training) {
            clearInterval(pollRef.current)
            load()
          }
        } catch { clearInterval(pollRef.current) }
      }, 3000)
    }
    return () => clearInterval(pollRef.current)
  }, [progress?.is_training]) // eslint-disable-line

  const handleTrain = async () => {
    setTriggering(true); setMsg('')
    try {
      await triggerLoraTraining(userId)
      setMsg('训练任务已提交，正在后台运行…')
      const p = await getLoraProgress(userId)
      setProgress(p)
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '触发失败')
    } finally { setTriggering(false) }
  }

  const pct = Math.round((progress?.progress ?? 0) * 100)

  return (
    <AppShell title="个性模型训练" subtitle="保留训练能力，但当前决策推演默认走云端/API 主链">
      {loading && <p style={{ color: 'var(--text-tertiary)' }}>加载中…</p>}

      {status && (
        <>
          <section className="metrics-grid">
            {[
              { label: '储备模型', value: status.has_lora ? '已就绪' : '未训练',   tone: status.has_lora ? 'accent' : 'warning' },
              { label: '模型版本',   value: `v${status.model_version}`,        tone: 'primary'   },
              { label: '训练样本数', value: String(status.training_data_size), tone: 'secondary' },
              { label: '最近训练',   value: status.last_train_time ? new Date(status.last_train_time).toLocaleDateString('zh-CN') : '从未', tone: 'primary' },
            ].map(m => (
              <div key={m.label} className="glass-card" style={{ padding: 20 }}>
                <p className="metric-label">{m.label}</p>
                <p className={`metric-value tone-${m.tone}`} style={{ fontSize: 22 }}>{m.value}</p>
              </div>
            ))}
          </section>

          <GlassCard title="模型状态" subtitle="当前储备中的个性化模型信息">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={row}>
                <span style={label}>模型路径</span>
                <code style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{status.lora_path ?? '暂无'}</code>
              </div>
              <div style={row}>
                <span style={label}>状态</span>
                <StatusPill tone={status.is_loaded ? 'success' : 'warning'}>
                  {status.is_loaded ? '已加载' : '未加载'}
                </StatusPill>
              </div>
            </div>
          </GlassCard>

          {/* training progress */}
          {progress?.is_training && (
            <GlassCard title="训练进行中" subtitle={progress.stage ?? '处理中…'}>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{progress.stage}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)' }}>{pct}%</span>
              </div>
              <div className="progress-bar">
                <div className="progress-bar-fill" style={{ width: `${pct}%`, transition: 'width 0.4s ease' }} />
              </div>
            </GlassCard>
          )}

          {msg && (
            <div className={msg.includes('失败') ? 'form-error' : 'form-success'}>{msg}</div>
          )}

          <GlassCard title="触发训练" subtitle={`当前样本数 ${status.training_data_size}，建议积累 50+ 条后再训练储备模型`}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>
              个性化训练会学习你的对话风格、决策偏好和反馈模式，作为后续可切换的储备能力。当前决策推演默认仍走云端/API，训练在后台 GPU 服务器运行，通常需要几分钟。
            </p>
            <button
              className="button button-primary"
              onClick={handleTrain}
              disabled={triggering || progress?.is_training || status.training_data_size < 10}
            >
              {triggering ? '提交中…' : progress?.is_training ? '训练中…' : '开始训练'}
            </button>
            {status.training_data_size < 10 && (
              <p style={{ marginTop: 8, fontSize: 13, color: 'var(--text-tertiary)' }}>
                样本不足 10 条，请先多使用 AI 对话积累数据。
              </p>
            )}
          </GlassCard>
        </>
      )}
    </AppShell>
  )
}

const row: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border-light)' }
const label: React.CSSProperties = { fontSize: 13, color: 'var(--text-tertiary)', flexShrink: 0, marginRight: 12 }
