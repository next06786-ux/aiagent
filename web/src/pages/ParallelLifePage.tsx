import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

// ── Types ──────────────────────────────────────────────────────────────────
interface StatDelta { emotion?: number; finance?: number; social?: number; health?: number; growth?: number; confidence?: number; stress?: number }
interface Stats { emotion: number; finance: number; social: number; health: number; growth: number; confidence: number; stress: number }
interface GameOption { id: string; text: string; sub: string; delta: StatDelta; next: string }
interface GameNode { id: string; type: string; text: string; options: GameOption[]; next?: string }
interface Ending { condition: string; title: string; text: string; badge: string }
interface Chapter { id: string; title: string; subtitle: string; theme: string; accent: string; cover_emoji: string; intro: string; nodes: GameNode[]; endings: Ending[] }

const INIT_STATS: Stats = { emotion: 50, finance: 50, social: 50, health: 50, growth: 50, confidence: 50, stress: 30 }
const STAT_LABELS: Array<{ k: keyof Stats; l: string; color: string }> = [
  { k: 'emotion',    l: '情绪', color: '#FF6B9D' },
  { k: 'finance',    l: '财务', color: '#FFD93D' },
  { k: 'social',     l: '社交', color: '#4ECDC4' },
  { k: 'health',     l: '健康', color: '#6BCF7F' },
  { k: 'growth',     l: '成长', color: '#45B7D1' },
  { k: 'confidence', l: '自信', color: '#B19CD9' },
  { k: 'stress',     l: '压力', color: '#FF8C42' },
]

function clamp(v: number) { return Math.max(-100, Math.min(100, v)) }
function pct(v: number)   { return Math.round((v + 100) / 2) } // -100~100 → 0~100%

// ── StatBar ────────────────────────────────────────────────────────────────
function StatBar({ label, value, color }: { label: string; value: number; color: string }) {
  const p = pct(value)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
      <span style={{ width: 32, fontSize: 11, color: '#aaa', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: 6, borderRadius: 999, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${p}%`, background: color, borderRadius: 999, transition: 'width 0.5s ease' }} />
      </div>
      <span style={{ width: 28, fontSize: 11, color, textAlign: 'right', flexShrink: 0 }}>{value}</span>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────
export default function ParallelLifePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'

  const [phase, setPhase] = useState<'loading' | 'chapters' | 'intro' | 'playing' | 'result'>('loading')
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [chapter, setChapter] = useState<Chapter | null>(null)
  const [nodeId, setNodeId] = useState('')
  const [stats, setStats] = useState<Stats>(INIT_STATS)
  const [delta, setDelta] = useState<StatDelta | null>(null)
  const [ending, setEnding] = useState<Ending | null>(null)
  const [freeText, setFreeText] = useState('')
  const [countdown, setCountdown] = useState(15)
  const [countdownActive, setCountdownActive] = useState(false)
  const timerRef = useRef<number>(-1)
  const nodeStartRef = useRef(0)

  // load chapters
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/game/parallel-life/chapters`)
      .then(r => r.json())
      .then(json => { setChapters(json.data ?? []); setPhase('chapters') })
      .catch(() => setPhase('chapters'))
  }, [])

  // countdown
  useEffect(() => {
    if (!countdownActive) return
    timerRef.current = window.setInterval(() => {
      setCountdown(c => {
        if (c <= 1) {
          clearInterval(timerRef.current)
          setCountdownActive(false)
          // auto-pick first option on timeout
          const node = chapter?.nodes.find(n => n.id === nodeId)
          if (node?.options[0]) handleChoice(node.options[0])
          return 15
        }
        return c - 1
      })
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [countdownActive, nodeId]) // eslint-disable-line

  const startCountdown = () => { setCountdown(15); setCountdownActive(true) }
  const stopCountdown  = () => { clearInterval(timerRef.current); setCountdownActive(false) }

  const loadChapter = async (id: string) => {
    const res = await fetch(`${API_BASE_URL}/api/game/parallel-life/chapter/${id}`)
    const json = await res.json()
    setChapter(json.data)
    setPhase('intro')
  }

  const startGame = () => {
    if (!chapter) return
    setStats({ ...INIT_STATS })
    setNodeId(chapter.nodes[0].id)
    setPhase('playing')
    nodeStartRef.current = Date.now()
    startCountdown()
  }

  const currentNode = () => chapter?.nodes.find(n => n.id === nodeId) ?? null

  const handleChoice = (opt: GameOption) => {
    stopCountdown()
    const d = opt.delta
    setDelta(d)
    setStats(prev => ({
      emotion:    clamp(prev.emotion    + (d.emotion    ?? 0)),
      finance:    clamp(prev.finance    + (d.finance    ?? 0)),
      social:     clamp(prev.social     + (d.social     ?? 0)),
      health:     clamp(prev.health     + (d.health     ?? 0)),
      growth:     clamp(prev.growth     + (d.growth     ?? 0)),
      confidence: clamp(prev.confidence + (d.confidence ?? 0)),
      stress:     clamp(prev.stress     + (d.stress     ?? 0)),
    }))
    setTimeout(() => setDelta(null), 1500)
    setTimeout(() => {
      if (opt.next === 'ending' || !chapter?.nodes.find(n => n.id === opt.next)) {
        finishGame()
      } else {
        setNodeId(opt.next)
        nodeStartRef.current = Date.now()
        startCountdown()
      }
    }, 600)
  }

  const finishGame = () => {
    stopCountdown()
    // pick ending by stats
    const e = chapter?.endings?.[0] ?? { condition: '', title: '旅程结束', text: '你完成了这段人生模拟。', badge: '🌟' }
    setEnding(e)
    setPhase('result')
    // submit to backend (fire-and-forget)
    fetch(`${API_BASE_URL}/api/game/parallel-life/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, chapter_id: chapter?.id, final_stats: stats }),
    }).catch(() => {})
  }

  // ── Render phases ────────────────────────────────────────────────────────
  return (
    <div style={S.root}>
      {/* header */}
      <div style={S.header}>
        <button style={S.backBtn} onClick={() => navigate(-1)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <div>
          <div style={{ fontSize: 17, fontWeight: 700 }}>平行人生</div>
          <div style={{ fontSize: 12, color: '#aaa' }}>决策游戏 · 探索另一种可能</div>
        </div>
      </div>

      <div style={S.body}>
        {phase === 'loading' && <p style={{ color: '#aaa', textAlign: 'center', paddingTop: 80 }}>加载中…</p>}

        {/* chapter select */}
        {phase === 'chapters' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ color: '#ccc', fontSize: 15, marginBottom: 4 }}>选择一段人生故事，开始你的旅程</p>
            {chapters.map(ch => (
              <button key={ch.id} style={{ ...S.chapterCard, background: `linear-gradient(135deg, ${ch.theme}, ${ch.accent})` }}
                onClick={() => loadChapter(ch.id)}>
                <span style={{ fontSize: 36 }}>{ch.cover_emoji}</span>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>{ch.title}</div>
                  <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', marginTop: 4 }}>{ch.subtitle}</div>
                </div>
              </button>
            ))}
            {chapters.length === 0 && (
              <div style={S.emptyBox}>
                <p style={{ color: '#aaa' }}>暂无关卡数据，请确保后端服务已启动</p>
                <button style={S.primaryBtn} onClick={() => fetch(`${API_BASE_URL}/api/game/parallel-life/chapters`).then(r=>r.json()).then(j=>{setChapters(j.data??[]);})}>重试</button>
              </div>
            )}
          </div>
        )}

        {/* intro */}
        {phase === 'intro' && chapter && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ ...S.chapterCard, background: `linear-gradient(135deg, ${chapter.theme}, ${chapter.accent})`, flexDirection: 'column', alignItems: 'flex-start', gap: 8 }}>
              <span style={{ fontSize: 48 }}>{chapter.cover_emoji}</span>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#fff' }}>{chapter.title}</div>
              <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.8)' }}>{chapter.subtitle}</div>
            </div>
            <div style={S.introBox}>
              {chapter.intro.split('\n').map((line, i) => <p key={i} style={{ margin: '4px 0', lineHeight: 1.8 }}>{line}</p>)}
            </div>
            <button style={S.primaryBtn} onClick={startGame}>开始旅程</button>
            <button style={S.ghostBtn} onClick={() => setPhase('chapters')}>返回选择</button>
          </div>
        )}

        {/* playing */}
        {phase === 'playing' && chapter && (() => {
          const node = currentNode()
          if (!node) return null
          return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* stats sidebar */}
              <div style={S.statsBox}>
                {STAT_LABELS.map(s => <StatBar key={s.k} label={s.l} value={stats[s.k]} color={s.color} />)}
              </div>

              {/* countdown */}
              {countdownActive && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ flex: 1, height: 4, borderRadius: 999, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${(countdown / 15) * 100}%`, background: countdown <= 5 ? '#FF3B30' : '#0A59F7', transition: 'width 1s linear, background 0.3s' }} />
                  </div>
                  <span style={{ fontSize: 13, color: countdown <= 5 ? '#FF3B30' : '#aaa', fontWeight: 700, width: 20, textAlign: 'right' }}>{countdown}</span>
                </div>
              )}

              {/* node text */}
              <div style={S.nodeBox}>
                <p style={{ fontSize: 16, lineHeight: 1.8, color: '#e8f0fe', margin: 0 }}>{node.text}</p>
              </div>

              {/* delta toast */}
              {delta && (
                <div style={S.deltaToast}>
                  {Object.entries(delta).filter(([,v]) => v !== 0).map(([k, v]) => (
                    <span key={k} style={{ color: (v as number) > 0 ? '#6BCF7F' : '#FF6B6B', fontWeight: 700, fontSize: 13 }}>
                      {STAT_LABELS.find(s => s.k === k)?.l} {(v as number) > 0 ? '+' : ''}{v}
                    </span>
                  ))}
                </div>
              )}

              {/* options */}
              {node.type === 'free_input' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <textarea
                    value={freeText} onChange={e => setFreeText(e.target.value)}
                    placeholder="写下你的想法…"
                    style={{ ...S.textarea }}
                    rows={4}
                  />
                  <button style={S.primaryBtn} onClick={() => { if (freeText.trim()) { stopCountdown(); finishGame() } }}>提交</button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {node.options.map(opt => (
                    <button key={opt.id} style={S.optionBtn} onClick={() => handleChoice(opt)}>
                      <div style={{ fontSize: 15, fontWeight: 600, color: '#e8f0fe', marginBottom: 4 }}>{opt.text}</div>
                      <div style={{ fontSize: 13, color: '#8899aa' }}>{opt.sub}</div>
                      <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                        {Object.entries(opt.delta).filter(([,v]) => v !== 0).map(([k, v]) => (
                          <span key={k} style={{ fontSize: 11, color: (v as number) > 0 ? '#6BCF7F' : '#FF6B6B' }}>
                            {STAT_LABELS.find(s => s.k === k)?.l}{(v as number) > 0 ? '+' : ''}{v}
                          </span>
                        ))}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })()}

        {/* result */}
        {phase === 'result' && ending && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20, alignItems: 'center' }}>
            <div style={{ fontSize: 64 }}>{ending.badge}</div>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: '#e8f0fe', margin: 0 }}>{ending.title}</h2>
            <p style={{ color: '#aaa', textAlign: 'center', lineHeight: 1.8, maxWidth: 400 }}>{ending.text}</p>
            <div style={{ ...S.statsBox, width: '100%', maxWidth: 360 }}>
              {STAT_LABELS.map(s => <StatBar key={s.k} label={s.l} value={stats[s.k]} color={s.color} />)}
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <button style={S.primaryBtn} onClick={() => { setChapter(null); setPhase('chapters') }}>再玩一次</button>
              <button style={S.ghostBtn} onClick={() => navigate(-1)}>返回</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Styles ─────────────────────────────────────────────────────────────────
const S: Record<string, React.CSSProperties> = {
  root: { minHeight: '100vh', background: '#0a0a1a', color: '#e8f0fe', fontFamily: '-apple-system, sans-serif', display: 'flex', flexDirection: 'column' },
  header: { display: 'flex', alignItems: 'center', gap: 14, padding: '14px 20px', background: 'rgba(255,255,255,0.04)', backdropFilter: 'blur(16px)', borderBottom: '1px solid rgba(255,255,255,0.06)', position: 'sticky', top: 0, zIndex: 10 },
  backBtn: { background: 'transparent', border: 'none', cursor: 'pointer', color: '#e8f0fe', display: 'flex', alignItems: 'center', padding: 4 },
  body: { flex: 1, maxWidth: 680, width: '100%', margin: '0 auto', padding: '24px 20px 48px' },
  chapterCard: { display: 'flex', alignItems: 'center', gap: 16, padding: '20px 24px', borderRadius: 20, border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', transition: 'transform 0.15s', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' },
  introBox: { background: 'rgba(255,255,255,0.05)', borderRadius: 16, padding: '20px 24px', color: '#ccc', fontSize: 15 },
  statsBox: { background: 'rgba(255,255,255,0.04)', borderRadius: 16, padding: '16px 20px', border: '1px solid rgba(255,255,255,0.06)' },
  nodeBox: { background: 'rgba(255,255,255,0.06)', borderRadius: 16, padding: '20px 24px', border: '1px solid rgba(255,255,255,0.08)' },
  optionBtn: { background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16, padding: '16px 20px', cursor: 'pointer', textAlign: 'left', transition: 'background 0.15s, transform 0.1s', width: '100%' },
  primaryBtn: { background: 'linear-gradient(135deg, #0A59F7, #6B48FF)', color: '#fff', border: 'none', borderRadius: 24, padding: '12px 32px', fontSize: 15, fontWeight: 700, cursor: 'pointer', boxShadow: '0 6px 20px rgba(10,89,247,0.4)' },
  ghostBtn: { background: 'rgba(255,255,255,0.08)', color: '#ccc', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 24, padding: '12px 32px', fontSize: 15, cursor: 'pointer' },
  deltaToast: { display: 'flex', gap: 12, flexWrap: 'wrap', padding: '10px 16px', background: 'rgba(255,255,255,0.06)', borderRadius: 12, justifyContent: 'center' },
  textarea: { background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 12, padding: '12px 16px', color: '#e8f0fe', fontSize: 14, resize: 'vertical', fontFamily: 'inherit', width: '100%', boxSizing: 'border-box' },
  emptyBox: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '48px 24px', background: 'rgba(255,255,255,0.04)', borderRadius: 16 },
}
