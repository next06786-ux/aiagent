import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { API_BASE_URL } from '../services/api'

// ── Types ──────────────────────────────────────────────────────────────────
interface GraphNode {
  id: string
  name: string
  type: string
  category?: string
  x: number
  y: number
  vx: number
  vy: number
  fx?: number
  fy?: number
  pulsePhase: number
  glowIntensity: number
}

interface GraphLink {
  source: string
  target: string
  type: string
  flowPhase: number
}

interface KGSession {
  session_id: string
  title: string
  node_count: number
  last_update: string
}

interface GraphData {
  information?: Array<{ id: string; name: string; type: string; category?: string; source_id?: string }>
  sources?: Array<{ id: string; name: string; type: string; source_id?: string }>
  entities?: Array<{ id: string; name: string; type: string; category?: string }>
  relationships?: Array<{ source: string; target: string; type: string }>
  relations?: Array<{ source: string; target: string; type: string }>
}

// ── Color map ──────────────────────────────────────────────────────────────
const NODE_COLORS: Record<string, string> = {
  Concept:  '#FF6B6B',
  Entity:   '#4ECDC4',
  Event:    '#45B7D1',
  Pattern:  '#FFA07A',
  Source:   '#95E1D3',
  Photo:    '#A8E6CF',
  Location: '#FFD93D',
  Person:   '#6BCF7F',
  Time:     '#B19CD9',
}
const getNodeColor = (type: string) => NODE_COLORS[type] ?? '#A0A0A0'

// ── Main Component ─────────────────────────────────────────────────────────
export default function KnowledgeGraphPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const userId = user?.user_id ?? 'default_user'

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animTimerRef = useRef<number>(-1)
  const frameCountRef = useRef(0)

  // graph state (mutable refs for perf, mirrored to state for UI)
  const nodesRef = useRef<GraphNode[]>([])
  const linksRef = useRef<GraphLink[]>([])

  const [nodeCount, setNodeCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [loadError, setLoadError] = useState('')

  // sessions
  const [sessions, setSessions] = useState<KGSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState('')
  const [showSessionPanel, setShowSessionPanel] = useState(false)
  const [isLoadingSessions, setIsLoadingSessions] = useState(false)

  // selected node panel
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  // view transform
  const offsetRef = useRef({ x: 0, y: 0 })
  const zoomRef = useRef(1.0)
  const [zoom, setZoom] = useState(1.0)

  // drag state
  const dragCanvasRef = useRef(false)
  const dragStartRef = useRef({ x: 0, y: 0 })
  const dragNodeRef = useRef<GraphNode | null>(null)

  // ── Canvas render ────────────────────────────────────────────────────────
  const render = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const W = canvas.width
    const H = canvas.height
    const nodes = nodesRef.current
    const links = linksRef.current
    const sel = dragNodeRef.current?.id ?? null

    ctx.clearRect(0, 0, W, H)

    // dark starfield background
    const bg = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.8)
    bg.addColorStop(0, '#0d1b2a')
    bg.addColorStop(1, '#060d14')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    ctx.save()
    ctx.translate(W / 2 + offsetRef.current.x, H / 2 + offsetRef.current.y)
    ctx.scale(zoomRef.current, zoomRef.current)

    // draw links
    links.forEach(link => {
      const src = nodes.find(n => n.id === link.source)
      const tgt = nodes.find(n => n.id === link.target)
      if (!src || !tgt) return

      // animated flow dot
      const t = (link.flowPhase % (Math.PI * 2)) / (Math.PI * 2)
      const fx = src.x + (tgt.x - src.x) * t
      const fy = src.y + (tgt.y - src.y) * t

      // gradient line
      const grad = ctx.createLinearGradient(src.x, src.y, tgt.x, tgt.y)
      grad.addColorStop(0, 'rgba(99,179,237,0.15)')
      grad.addColorStop(0.5, 'rgba(99,179,237,0.45)')
      grad.addColorStop(1, 'rgba(99,179,237,0.15)')
      ctx.beginPath()
      ctx.moveTo(src.x, src.y)
      ctx.lineTo(tgt.x, tgt.y)
      ctx.strokeStyle = grad
      ctx.lineWidth = 1.5
      ctx.stroke()

      // flow dot
      ctx.beginPath()
      ctx.arc(fx, fy, 3, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(147,210,255,0.9)'
      ctx.fill()
    })

    // draw nodes
    nodes.forEach(node => {
      const color = getNodeColor(node.type)
      const r = 22
      const pulse = Math.sin(node.pulsePhase) * 0.3 + 0.7
      const isSelected = selectedNodeRef.current?.id === node.id

      // outer glow
      const glow = ctx.createRadialGradient(node.x, node.y, r * 0.5, node.x, node.y, r * 2.2)
      glow.addColorStop(0, color + Math.round(node.glowIntensity * pulse * 120).toString(16).padStart(2, '0'))
      glow.addColorStop(1, 'transparent')
      ctx.beginPath()
      ctx.arc(node.x, node.y, r * 2.2, 0, Math.PI * 2)
      ctx.fillStyle = glow
      ctx.fill()

      // selection ring
      if (isSelected) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, r + 7, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(255,255,255,0.85)'
        ctx.lineWidth = 2.5
        ctx.stroke()
      }

      // node circle
      const nodeGrad = ctx.createRadialGradient(node.x - r * 0.3, node.y - r * 0.3, 2, node.x, node.y, r)
      nodeGrad.addColorStop(0, lighten(color, 40))
      nodeGrad.addColorStop(1, color)
      ctx.beginPath()
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2)
      ctx.fillStyle = nodeGrad
      ctx.fill()
      ctx.strokeStyle = 'rgba(255,255,255,0.5)'
      ctx.lineWidth = 1.5
      ctx.stroke()

      // initial letter
      ctx.fillStyle = '#fff'
      ctx.font = `bold 14px -apple-system, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.name.charAt(0).toUpperCase(), node.x, node.y)

      // label below
      ctx.fillStyle = 'rgba(220,235,255,0.9)'
      ctx.font = `11px -apple-system, sans-serif`
      ctx.fillText(node.name.length > 8 ? node.name.slice(0, 7) + '…' : node.name, node.x, node.y + r + 13)
    })

    ctx.restore()
  }, [])

  // helper: lighten hex color
  function lighten(hex: string, amt: number) {
    const n = parseInt(hex.slice(1), 16)
    const r = Math.min(255, (n >> 16) + amt)
    const g = Math.min(255, ((n >> 8) & 0xff) + amt)
    const b = Math.min(255, (n & 0xff) + amt)
    return '#' + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1)
  }

  // keep selectedNode accessible inside render without re-creating render
  const selectedNodeRef = useRef<GraphNode | null>(null)
  useEffect(() => { selectedNodeRef.current = selectedNode }, [selectedNode])

  // ── Physics simulation ───────────────────────────────────────────────────
  const stopSimulation = useCallback(() => {
    if (animTimerRef.current !== -1) {
      clearInterval(animTimerRef.current)
      animTimerRef.current = -1
    }
  }, [])

  const startSimulation = useCallback(() => {
    stopSimulation()
    frameCountRef.current = 0
    animTimerRef.current = window.setInterval(() => {
      frameCountRef.current++
      const nodes = nodesRef.current
      const links = linksRef.current

      // update pulse & flow phases
      nodes.forEach(n => { n.pulsePhase += 0.025; if (n.pulsePhase > Math.PI * 2) n.pulsePhase -= Math.PI * 2 })
      links.forEach(l => { l.flowPhase += 0.04; if (l.flowPhase > Math.PI * 2) l.flowPhase -= Math.PI * 2 })

      if (frameCountRef.current <= 120) {
        // repulsion
        nodes.forEach(n => { n.vx = 0; n.vy = 0 })
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i], b = nodes[j]
            const dx = b.x - a.x, dy = b.y - a.y
            const dist = Math.sqrt(dx * dx + dy * dy) || 1
            const f = 1200 / (dist * dist)
            const fx = (dx / dist) * f, fy = (dy / dist) * f
            a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy
          }
        }
        // attraction
        links.forEach(link => {
          const s = nodes.find(n => n.id === link.source)
          const t = nodes.find(n => n.id === link.target)
          if (!s || !t) return
          const dx = t.x - s.x, dy = t.y - s.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const f = dist * 0.03
          const fx = (dx / dist) * f, fy = (dy / dist) * f
          s.vx += fx; s.vy += fy; t.vx -= fx; t.vy -= fy
        })
        // integrate
        let maxV = 0
        nodes.forEach(n => {
          if (n.fx !== undefined) { n.x = n.fx; n.y = n.fy!; return }
          const spd = Math.sqrt(n.vx * n.vx + n.vy * n.vy)
          if (spd > 6) { n.vx = n.vx / spd * 6; n.vy = n.vy / spd * 6 }
          n.x += n.vx; n.y += n.vy
          const d = Math.sqrt(n.x * n.x + n.y * n.y)
          if (d > 260) { n.x = n.x / d * 260; n.y = n.y / d * 260 }
          n.vx *= 0.72; n.vy *= 0.72
          maxV = Math.max(maxV, Math.abs(n.vx), Math.abs(n.vy))
        })
        if (maxV < 0.05 && frameCountRef.current > 30) frameCountRef.current = 121
      }

      render()
    }, 16)
  }, [render, stopSimulation])

  // ── Data loading ─────────────────────────────────────────────────────────
  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v4/knowledge-graph/${userId}/sessions`)
      if (res.ok) {
        const json = await res.json()
        if (json.success && Array.isArray(json.data)) setSessions(json.data)
      }
    } catch { /* ignore */ } finally { setIsLoadingSessions(false) }
  }, [userId])

  const loadGraphData = useCallback(async (sessionId = '') => {
    setIsLoading(true)
    setLoadError('')
    stopSimulation()
    try {
      let url = `${API_BASE_URL}/api/v4/knowledge-graph/${userId}/export`
      if (sessionId) url += `?session_id=${sessionId}`
      const res = await fetch(url)
      if (!res.ok) { setLoadError(`后端错误 (${res.status})，请检查服务状态`); return }
      const json = await res.json()
      if (!json.success || !json.data) {
        if (json.error_code === 'KG_EMPTY') setLoadError('知识图谱为空，请先进行对话以构建知识网络')
        else setLoadError(json.message || '知识图谱加载失败')
        return
      }
      const data: GraphData = json.data
      let nodeData = data.information?.length ? data.information : (data.entities ?? [])
      if (data.sources?.length) {
        data.sources.forEach(s => nodeData.push({ id: s.id, name: s.source_id ?? s.type, type: 'Source' }))
      }
      const radius = 160
      nodesRef.current = nodeData.map((n, i) => {
        const angle = (i / nodeData.length) * Math.PI * 2
        return {
          id: n.id, name: n.name, type: n.type, category: n.category,
          x: Math.cos(angle) * radius, y: Math.sin(angle) * radius,
          vx: 0, vy: 0,
          pulsePhase: Math.random() * Math.PI * 2,
          glowIntensity: 0.5 + Math.random() * 0.5,
        }
      })
      const linkData = data.relationships ?? data.relations ?? []
      linksRef.current = linkData.map(l => ({ ...l, flowPhase: Math.random() * Math.PI * 2 }))
      setNodeCount(nodesRef.current.length)
      setSelectedNode(null)
      startSimulation()
      loadSessions()
    } catch { setLoadError('无法连接到后端服务，请确保后端已启动') }
    finally { setIsLoading(false) }
  }, [userId, startSimulation, stopSimulation, loadSessions])

  // initial load
  useEffect(() => {
    loadSessions()
    loadGraphData()
    return () => stopSimulation()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // resize canvas to fill container
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const obs = new ResizeObserver(() => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
      render()
    })
    obs.observe(canvas)
    return () => obs.disconnect()
  }, [render])

  // ── Mouse / touch interaction ────────────────────────────────────────────
  const toCanvasCoords = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current!
    const rect = canvas.getBoundingClientRect()
    const cx = clientX - rect.left
    const cy = clientY - rect.top
    return {
      x: (cx - canvas.width / 2 - offsetRef.current.x) / zoomRef.current,
      y: (cy - canvas.height / 2 - offsetRef.current.y) / zoomRef.current,
    }
  }

  const findNodeAt = (x: number, y: number) =>
    nodesRef.current.find(n => Math.hypot(n.x - x, n.y - y) <= 26) ?? null

  const handleMouseDown = (e: React.MouseEvent) => {
    const { x, y } = toCanvasCoords(e.clientX, e.clientY)
    const hit = findNodeAt(x, y)
    if (hit) {
      dragNodeRef.current = hit
      hit.fx = hit.x; hit.fy = hit.y
      setSelectedNode(hit)
    } else {
      dragCanvasRef.current = true
      dragStartRef.current = { x: e.clientX, y: e.clientY }
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (dragNodeRef.current) {
      const { x, y } = toCanvasCoords(e.clientX, e.clientY)
      dragNodeRef.current.fx = x; dragNodeRef.current.fy = y
    } else if (dragCanvasRef.current) {
      offsetRef.current.x += e.clientX - dragStartRef.current.x
      offsetRef.current.y += e.clientY - dragStartRef.current.y
      dragStartRef.current = { x: e.clientX, y: e.clientY }
    }
  }

  const handleMouseUp = () => {
    if (dragNodeRef.current) {
      dragNodeRef.current.fx = undefined; dragNodeRef.current.fy = undefined
      dragNodeRef.current = null
    }
    dragCanvasRef.current = false
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const factor = e.deltaY < 0 ? 1.12 : 0.89
    zoomRef.current = Math.min(3, Math.max(0.25, zoomRef.current * factor))
    setZoom(zoomRef.current)
    render()
  }

  const handleZoomIn  = () => { zoomRef.current = Math.min(3, zoomRef.current * 1.2); setZoom(zoomRef.current); render() }
  const handleZoomOut = () => { zoomRef.current = Math.max(0.25, zoomRef.current / 1.2); setZoom(zoomRef.current); render() }
  const handleReset   = () => { offsetRef.current = { x: 0, y: 0 }; zoomRef.current = 1; setZoom(1); render() }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={styles.root}>
      {/* Top nav */}
      <div style={styles.navbar}>
        <button style={styles.iconBtn} onClick={() => navigate(-1)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <div style={{ flex: 1, marginLeft: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={styles.navTitle}>知识星图</span>
            {nodeCount > 0 && <span style={styles.badge}>{nodeCount}</span>}
          </div>
          <div style={styles.navSub}>灵动流体 · 记忆永存</div>
        </div>
        <button style={styles.iconBtn} title="会话" onClick={() => setShowSessionPanel(v => !v)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </button>
        <button style={styles.iconBtn} title="刷新" onClick={() => loadGraphData(currentSessionId)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </button>
      </div>

      {/* Canvas area */}
      <div style={styles.canvasWrap}>
        {isLoading && (
          <div style={styles.overlay}>
            <div style={styles.spinner}/>
            <p style={styles.overlayTitle}>加载知识图谱中…</p>
            <p style={styles.overlaySub}>正在从数据库读取</p>
          </div>
        )}
        {!isLoading && loadError && (
          <div style={styles.overlay}>
            <div style={{ ...styles.iconCircle, background: 'rgba(255,59,48,0.12)' }}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            </div>
            <p style={styles.overlayTitle}>加载失败</p>
            <p style={styles.overlaySub}>{loadError}</p>
            <button style={styles.primaryBtn} onClick={() => loadGraphData(currentSessionId)}>重新加载</button>
          </div>
        )}
        {!isLoading && !loadError && nodeCount === 0 && (
          <div style={styles.overlay}>
            <div style={styles.iconCircle}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#0A59F7" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>
            </div>
            <p style={styles.overlayTitle}>暂无知识图谱</p>
            <p style={styles.overlaySub}>开始使用 AI 助手对话，系统将自动构建您的知识网络</p>
            <button style={styles.primaryBtn} onClick={() => navigate('/chat')}>开始对话</button>
          </div>
        )}
        <canvas
          ref={canvasRef}
          style={{ width: '100%', height: '100%', cursor: 'grab', display: 'block' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        />

        {/* Zoom controls */}
        <div style={styles.zoomPanel}>
          <button style={styles.zoomBtn} onClick={handleZoomIn}>＋</button>
          <span style={styles.zoomLabel}>{Math.round(zoom * 100)}%</span>
          <button style={styles.zoomBtn} onClick={handleZoomOut}>－</button>
          <button style={{ ...styles.zoomBtn, marginTop: 4 }} onClick={handleReset} title="重置视图">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          </button>
        </div>

        {/* Legend */}
        <div style={styles.legend}>
          {Object.entries(NODE_COLORS).slice(0, 6).map(([type, color]) => (
            <div key={type} style={styles.legendItem}>
              <span style={{ ...styles.legendDot, background: color }}/>
              <span style={styles.legendLabel}>{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Session panel */}
      {showSessionPanel && (
        <div style={styles.sessionOverlay} onClick={() => setShowSessionPanel(false)}>
          <div style={styles.sessionPanel} onClick={e => e.stopPropagation()}>
            <div style={styles.sessionHeader}>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#e8f0fe' }}>对话会话</span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button style={styles.chipBtn} onClick={() => { setCurrentSessionId(''); setShowSessionPanel(false); loadGraphData('') }}>全部</button>
                <button style={{ ...styles.iconBtn, color: '#8899aa' }} onClick={() => setShowSessionPanel(false)}>✕</button>
              </div>
            </div>
            {isLoadingSessions ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><div style={styles.spinner}/></div>
            ) : sessions.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#8899aa', padding: 40 }}>暂无会话数据</p>
            ) : (
              <div style={{ overflowY: 'auto', maxHeight: 360, padding: '0 12px 12px' }}>
                {sessions.map(s => (
                  <div
                    key={s.session_id}
                    style={{ ...styles.sessionItem, background: currentSessionId === s.session_id ? 'rgba(10,89,247,0.18)' : 'rgba(255,255,255,0.05)' }}
                    onClick={() => { setCurrentSessionId(s.session_id); setShowSessionPanel(false); loadGraphData(s.session_id) }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: '#dce8ff', fontWeight: 600, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '70%' }}>{s.title}</span>
                      <span style={{ color: '#8899aa', fontSize: 12 }}>{s.node_count} 节点</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: '#8899aa', fontSize: 12 }}>…{s.session_id.slice(-8)}</span>
                      <span style={{ color: '#8899aa', fontSize: 11 }}>{s.last_update}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Selected node panel */}
      {selectedNode && (
        <div style={styles.nodePanel}>
          <div style={styles.nodePanelHandle}/>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ ...styles.nodeAvatar, background: getNodeColor(selectedNode.type), boxShadow: `0 6px 20px ${getNodeColor(selectedNode.type)}55` }}>
              {selectedNode.name.charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#e8f0fe', marginBottom: 6 }}>{selectedNode.name}</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span style={{ ...styles.tag, color: '#63b3ed', background: 'rgba(99,179,237,0.15)' }}>{selectedNode.type}</span>
                {selectedNode.category && <span style={{ ...styles.tag, color: '#8899aa', background: 'rgba(255,255,255,0.07)' }}>{selectedNode.category}</span>}
              </div>
            </div>
            <button style={{ ...styles.iconBtn, color: '#8899aa' }} onClick={() => setSelectedNode(null)}>✕</button>
          </div>
          <div style={styles.divider}/>
          <div style={{ color: '#8899aa', fontSize: 13, textAlign: 'center', padding: '8px 0' }}>
            连接数：{linksRef.current.filter(l => l.source === selectedNode.id || l.target === selectedNode.id).length}
          </div>
          <button style={styles.primaryBtn}>查看详细档案</button>
        </div>
      )}
    </div>
  )
}

// ── Styles ─────────────────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex', flexDirection: 'column', height: '100vh',
    background: '#060d14', color: '#e8f0fe', fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
    overflow: 'hidden',
  },
  navbar: {
    display: 'flex', alignItems: 'center', padding: '0 16px',
    height: 56, flexShrink: 0,
    background: 'rgba(13,27,42,0.85)', backdropFilter: 'blur(20px)',
    borderBottom: '1px solid rgba(99,179,237,0.12)',
    zIndex: 100,
  },
  navTitle: { fontSize: 18, fontWeight: 700, color: '#e8f0fe' },
  navSub:   { fontSize: 12, color: '#8899aa', marginTop: 1 },
  badge: {
    fontSize: 12, fontWeight: 700, color: '#fff',
    background: '#0A59F7', borderRadius: 10,
    padding: '2px 8px',
  },
  iconBtn: {
    background: 'transparent', border: 'none', cursor: 'pointer',
    color: '#dce8ff', display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: 36, height: 36, borderRadius: '50%', padding: 0,
    transition: 'background 0.2s',
  },
  canvasWrap: {
    flex: 1, position: 'relative', overflow: 'hidden',
  },
  overlay: {
    position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center', gap: 12, zIndex: 10,
    background: 'rgba(6,13,20,0.7)', backdropFilter: 'blur(4px)',
  },
  iconCircle: {
    width: 72, height: 72, borderRadius: '50%',
    background: 'rgba(10,89,247,0.12)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  overlayTitle: { fontSize: 20, fontWeight: 700, color: '#e8f0fe', margin: 0 },
  overlaySub:   { fontSize: 14, color: '#8899aa', margin: 0, textAlign: 'center', maxWidth: 280 },
  spinner: {
    width: 40, height: 40, borderRadius: '50%',
    border: '3px solid rgba(99,179,237,0.2)',
    borderTopColor: '#63b3ed',
    animation: 'spin 0.8s linear infinite',
  },
  primaryBtn: {
    background: 'linear-gradient(135deg, #0A59F7, #3b82f6)',
    color: '#fff', border: 'none', borderRadius: 24,
    padding: '12px 32px', fontSize: 15, fontWeight: 600,
    cursor: 'pointer', marginTop: 4,
    boxShadow: '0 6px 20px rgba(10,89,247,0.4)',
  },
  zoomPanel: {
    position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)',
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
    background: 'rgba(13,27,42,0.8)', backdropFilter: 'blur(16px)',
    borderRadius: 16, padding: '10px 8px',
    border: '1px solid rgba(99,179,237,0.15)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  },
  zoomBtn: {
    background: 'transparent', border: 'none', cursor: 'pointer',
    color: '#63b3ed', fontSize: 20, width: 36, height: 36,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    borderRadius: 8, transition: 'background 0.2s',
  },
  zoomLabel: { fontSize: 11, color: '#8899aa', userSelect: 'none' },
  legend: {
    position: 'absolute', left: 12, bottom: 12,
    display: 'flex', flexDirection: 'column', gap: 5,
    background: 'rgba(13,27,42,0.75)', backdropFilter: 'blur(12px)',
    borderRadius: 12, padding: '10px 12px',
    border: '1px solid rgba(99,179,237,0.1)',
  },
  legendItem: { display: 'flex', alignItems: 'center', gap: 7 },
  legendDot:  { width: 10, height: 10, borderRadius: '50%', flexShrink: 0 },
  legendLabel:{ fontSize: 11, color: '#8899aa' },
  sessionOverlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(4px)', zIndex: 200,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  sessionPanel: {
    width: '85%', maxWidth: 420,
    background: 'rgba(13,27,42,0.95)', backdropFilter: 'blur(30px)',
    borderRadius: 20, border: '1px solid rgba(99,179,237,0.2)',
    boxShadow: '0 24px 64px rgba(0,0,0,0.6)',
    overflow: 'hidden',
  },
  sessionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '16px 16px 12px',
    borderBottom: '1px solid rgba(99,179,237,0.1)',
  },
  sessionItem: {
    borderRadius: 12, padding: 12, marginBottom: 8,
    cursor: 'pointer', transition: 'background 0.2s',
    border: '1px solid rgba(99,179,237,0.08)',
  },
  chipBtn: {
    background: 'rgba(10,89,247,0.15)', border: 'none', borderRadius: 16,
    color: '#63b3ed', fontSize: 13, padding: '4px 14px', cursor: 'pointer',
  },
  nodePanel: {
    position: 'fixed', bottom: 0, left: 0, right: 0,
    background: 'rgba(13,27,42,0.95)', backdropFilter: 'blur(30px)',
    borderRadius: '24px 24px 0 0',
    border: '1px solid rgba(99,179,237,0.15)',
    boxShadow: '0 -8px 40px rgba(0,0,0,0.5)',
    padding: '12px 20px 28px',
    zIndex: 150,
    animation: 'slideUp 0.25s ease',
  },
  nodePanelHandle: {
    width: 40, height: 4, borderRadius: 2,
    background: 'rgba(255,255,255,0.15)',
    margin: '0 auto 16px',
  },
  nodeAvatar: {
    width: 52, height: 52, borderRadius: '50%',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 22, fontWeight: 700, color: '#fff', flexShrink: 0,
  },
  tag: {
    fontSize: 12, borderRadius: 6, padding: '3px 10px',
  },
  divider: {
    height: 1, background: 'rgba(99,179,237,0.1)', margin: '14px 0',
  },
}
