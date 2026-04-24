import { useState, useEffect, useRef } from 'react';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import { 
  generateRelationshipInsight, 
  generateEducationInsight, 
  generateCareerInsight,
  type AgentInsightReport 
} from '../services/agentInsightsService';
import { IframeLive2DAvatar } from '../components/IframeLive2DAvatar';
import { CrossDomainAnalysis } from '../components/CrossDomainAnalysis';
import { AgentChatDialog } from '../components/AgentChatDialog';
import { AgentDataImport } from '../components/AgentDataImport';
import '../styles/DecisionInsights.css';

interface AgentCard {
  id: string;
  name: string;
  type: 'relationship' | 'education' | 'career';
  icon: string;
  description: string;
  color: string;
}

export function DecisionInsightsPage() {
  const { token } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Agent相关状态
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentReport, setAgentReport] = useState<AgentInsightReport | null>(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);
  
  // 视图模式：'agents' | 'cross-domain'
  const [viewMode, setViewMode] = useState<'agents' | 'cross-domain'>('agents');
  
  // Agent对话状态
  const [chatAgent, setChatAgent] = useState<{
    type: 'relationship' | 'education' | 'career';
    name: string;
    color: string;
  } | null>(null);
  
  // Agent导入资料状态
  const [importAgent, setImportAgent] = useState<{
    type: 'relationship' | 'education' | 'career';
    name: string;
    color: string;
  } | null>(null);

  const agents: AgentCard[] = [
    {
      id: 'relationship',
      name: '人际关系Agent',
      type: 'relationship',
      icon: '👥',
      description: '分析人际关系网络、社交模式、关系质量',
      color: '#10b981'
    },
    {
      id: 'education',
      name: '教育升学Agent',
      type: 'education',
      icon: '🎓',
      description: '分析升学路径、学校选择、专业匹配',
      color: '#3b82f6'
    },
    {
      id: 'career',
      name: '职业规划Agent',
      type: 'career',
      icon: '💼',
      description: '分析职业发展、技能匹配、岗位选择',
      color: '#f59e0b'
    }
  ];

  // 背景粒子动画
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      opacity: number;
    }> = [];

    // 创建粒子
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 2 + 1,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }

    let animationId: number;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((particle, i) => {
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;

        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(10, 89, 247, ${particle.opacity})`;
        ctx.fill();

        // 连接附近的粒子
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[j].x - particle.x;
          const dy = particles[j].y - particle.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 150) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(10, 89, 247, ${0.1 * (1 - distance / 150)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      });

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationId);
  }, []);

  // 处理Agent点击
  const handleAgentClick = async (agentType: 'relationship' | 'education' | 'career') => {
    if (!token) {
      setError('请先登录');
      return;
    }

    setSelectedAgent(agentType);
    setAgentLoading(true);
    setAgentReport(null);
    setError(null);

    try {
      let report: AgentInsightReport;
      
      switch (agentType) {
        case 'relationship':
          report = await generateRelationshipInsight(token);
          break;
        case 'education':
          report = await generateEducationInsight(token);
          break;
        case 'career':
          report = await generateCareerInsight(token);
          break;
      }

      setAgentReport(report);
    } catch (err: any) {
      console.error('Agent分析失败:', err);
      setError(err.message || 'Agent分析失败');
    } finally {
      setAgentLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="insights-page">
        {/* 背景粒子画布 */}
        <canvas ref={canvasRef} className="insights-particles-canvas" />

        {/* 背景渐变球 */}
        <div className="insights-background">
          <div className="insights-blob insights-blob-1" />
          <div className="insights-blob insights-blob-2" />
          <div className="insights-blob insights-blob-3" />
        </div>

        {/* 主内容 */}
        <div className="insights-container">
          {/* 标题区 */}
          <div className="insights-hero insights-reveal">
            <h1 className="insights-title">智慧洞察</h1>
            <p className="insights-subtitle">三个专业Agent · 实时智能分析 · 多Agent协作</p>
          </div>

          {/* 视图切换 */}
          <div className="insights-view-switcher insights-reveal">
            <button
              className={`insights-view-btn ${viewMode === 'agents' ? 'active' : ''}`}
              onClick={() => {
                setViewMode('agents');
                setSelectedAgent(null);
                setAgentReport(null);
              }}
            >
              <svg className="view-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <circle cx="12" cy="12" r="3" fill="currentColor"/>
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              单Agent分析
            </button>
            <button
              className={`insights-view-btn ${viewMode === 'cross-domain' ? 'active' : ''}`}
              onClick={() => {
                setViewMode('cross-domain');
                setSelectedAgent(null);
                setAgentReport(null);
              }}
            >
              <svg className="view-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="currentColor" strokeWidth="2"/>
              </svg>
              跨领域综合分析
            </button>
          </div>

          {/* 跨领域综合分析视图 */}
          {viewMode === 'cross-domain' && token && (
            <div className="insights-cross-domain-section insights-reveal-scale">
              <CrossDomainAnalysis token={token} />
            </div>
          )}

          {/* Agent选择界面 */}
          {viewMode === 'agents' && !selectedAgent && (
            <div className="insights-agents-section insights-reveal-scale">
              <h2 className="insights-section-title">选择专业Agent</h2>
              <p className="insights-section-desc">点击Agent小人物查看专业洞察报告</p>
              
              <div className="insights-agents-grid">
                {agents.map((agent, index) => (
                  <div
                    key={agent.id}
                    className="insights-agent-card"
                    style={{ 
                      animationDelay: `${index * 0.1}s`,
                      borderColor: agent.color
                    }}
                    onClick={() => handleAgentClick(agent.type)}
                    onMouseEnter={() => setHoveredAgent(agent.id)}
                    onMouseLeave={() => setHoveredAgent(null)}
                  >
                    {/* 使用iframe隔离的Live2D模型 - 完全避免WebGL冲突 */}
                    {/* 延迟加载：第一个立即加载，后续每个延迟500ms */}
                    <IframeLive2DAvatar 
                      type={agent.type}
                      isHovered={hoveredAgent === agent.id}
                      loadDelay={index * 500}
                    />
                    
                    <h3 className="insights-agent-name">{agent.name}</h3>
                    <p className="insights-agent-desc">{agent.description}</p>
                    <div className="insights-agent-actions">
                      <button 
                        className="insights-agent-btn insights-agent-btn-primary"
                        style={{ background: agent.color }}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAgentClick(agent.type);
                        }}
                      >
                        查看报告
                      </button>
                      <button 
                        className="insights-agent-btn insights-agent-btn-chat"
                        onClick={(e) => {
                          e.stopPropagation();
                          setChatAgent({
                            type: agent.type,
                            name: agent.name,
                            color: agent.color
                          });
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span>对话</span>
                      </button>
                      <button 
                        className="insights-agent-btn insights-agent-btn-import"
                        onClick={(e) => {
                          e.stopPropagation();
                          setImportAgent({
                            type: agent.type,
                            name: agent.name,
                            color: agent.color
                          });
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                          <polyline points="7 10 12 15 17 10"/>
                          <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                        <span>导入</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agent加载状态 */}
          {viewMode === 'agents' && agentLoading && (
            <div className="insights-loading-section insights-reveal-scale">
              <div className="insights-loading-card">
                <div className="insights-loading-spinner" />
                <h2 className="insights-loading-title">
                  {selectedAgent === 'relationship' && '人际关系Agent正在分析...'}
                  {selectedAgent === 'education' && '教育升学Agent正在分析...'}
                  {selectedAgent === 'career' && '职业规划Agent正在分析...'}
                </h2>
                <p className="insights-loading-desc">
                  正在通过RAG和Neo4j混合检索生成专业洞察报告
                </p>
              </div>
            </div>
          )}

          {/* Agent报告结果 */}
          {viewMode === 'agents' && agentReport && !agentLoading && (
            <div className="insights-results">
              {/* 返回按钮 */}
              <button 
                className="insights-back-btn"
                onClick={() => {
                  setSelectedAgent(null);
                  setAgentReport(null);
                }}
              >
                ← 返回Agent选择
              </button>

              {/* 报告标题 */}
              <div className="insights-report-header insights-reveal">
                <h2 className="insights-report-title">{agentReport.title}</h2>
                <div className="insights-report-meta">
                  <span className="insights-report-type">{agentReport.agent_type}</span>
                  <span className="insights-report-confidence">
                    置信度: {(agentReport.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* AI摘要 */}
              <div className="insights-section insights-reveal">
                <h3 className="insights-section-title">
                  <span className="insights-title-icon">AI</span>
                  智能摘要
                </h3>
                <div className="insights-llm-card">
                  <p className="insights-llm-text">{agentReport.summary}</p>
                </div>
              </div>

              {/* 关键发现 */}
              {agentReport.key_findings && agentReport.key_findings.length > 0 && (
                <div className="insights-section insights-reveal">
                  <h3 className="insights-section-title">关键发现</h3>
                  <div className="insights-findings-grid">
                    {agentReport.key_findings.map((finding, index) => (
                      <div
                        key={index}
                        className="insights-finding-card"
                        style={{ animationDelay: `${index * 0.1}s` }}
                      >
                        <div 
                          className="insights-finding-icon"
                          data-importance={finding.importance}
                        >
                          {finding.importance === 'high' ? '!' : '•'}
                        </div>
                        <h4 className="insights-finding-title">{finding.title}</h4>
                        <p className="insights-finding-desc">{finding.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 专业建议 */}
              {agentReport.recommendations && agentReport.recommendations.length > 0 && (
                <div className="insights-section insights-reveal">
                  <h3 className="insights-section-title">专业建议</h3>
                  <div className="insights-recommendations">
                    {agentReport.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className="insights-recommendation-card"
                        style={{ animationDelay: `${index * 0.1}s` }}
                      >
                        <div
                          className="insights-rec-priority"
                          data-priority={rec.priority}
                        >
                          {rec.priority}
                        </div>
                        <div className="insights-rec-content">
                          <div className="insights-rec-category">{rec.category}</div>
                          <h4 className="insights-rec-title">{rec.action}</h4>
                          <p className="insights-rec-desc">{rec.expected_impact}</p>
                          <div className="insights-rec-meta">
                            <span>{rec.timeline}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 决策逻辑 */}
              {agentReport.decision_logic && (
                <div className="insights-section insights-reveal">
                  <h3 className="insights-section-title">决策逻辑分析</h3>
                  <div className="insights-logic-card">
                    {agentReport.decision_logic.reasoning_path && (
                      <div className="insights-logic-block">
                        <h4 className="insights-logic-subtitle">推理路径</h4>
                        <ol className="insights-logic-steps">
                          {agentReport.decision_logic.reasoning_path.map((step, idx) => (
                            <li key={idx}>{step.description}</li>
                          ))}
                        </ol>
                      </div>
                    )}
                    {agentReport.decision_logic.influence_factors && 
                     Object.keys(agentReport.decision_logic.influence_factors).length > 0 && (
                      <div className="insights-logic-block">
                        <h4 className="insights-logic-subtitle">影响因素</h4>
                        <div className="insights-influence-bars">
                          {Object.entries(agentReport.decision_logic.influence_factors)
                            .sort(([, a], [, b]) => b - a)
                            .map(([factor, score]) => (
                              <div key={factor} className="insights-influence-item">
                                <span className="insights-influence-label">{factor}</span>
                                <div className="insights-influence-bar-bg">
                                  <div 
                                    className="insights-influence-bar-fill"
                                    style={{ width: `${score * 100}%` }}
                                  />
                                </div>
                                <span className="insights-influence-value">
                                  {(score * 100).toFixed(0)}%
                                </span>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 数据来源 */}
              <div className="insights-section insights-reveal">
                <h3 className="insights-section-title">数据来源</h3>
                <div className="insights-sources-grid">
                  <div className="insights-source-card">
                    <div className="insights-source-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                      </svg>
                    </div>
                    <div className="insights-source-name">RAG记忆系统</div>
                    <div className="insights-source-count">
                      {agentReport.data_sources.rag_nodes || 0} 个节点
                    </div>
                  </div>
                  <div className="insights-source-card">
                    <div className="insights-source-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <circle cx="12" cy="12" r="6"/>
                        <circle cx="12" cy="12" r="2"/>
                      </svg>
                    </div>
                    <div className="insights-source-name">Neo4j知识图谱</div>
                    <div className="insights-source-count">
                      {agentReport.data_sources.neo4j_nodes || 0} 个节点
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 错误状态 */}
          {error && (
            <div className="insights-error insights-reveal">
              <div className="insights-error-icon">!</div>
              <h2 className="insights-error-title">分析失败</h2>
              <p className="insights-error-message">{error}</p>
            </div>
          )}
        </div>

        {/* Agent对话弹窗 */}
        {chatAgent && token && (
          <AgentChatDialog
            agentType={chatAgent.type}
            agentName={chatAgent.name}
            agentColor={chatAgent.color}
            token={token}
            onClose={() => setChatAgent(null)}
          />
        )}

        {/* Agent导入资料弹窗 */}
        {importAgent && token && (
          <AgentDataImport
            agentType={importAgent.type}
            agentName={importAgent.name}
            agentColor={importAgent.color}
            token={token}
            onClose={() => setImportAgent(null)}
            onImportSuccess={() => {
              // 导入成功后可以刷新或显示提示
              console.log('资料导入成功');
            }}
          />
        )}
      </div>
    </AppShell>
  );
}
