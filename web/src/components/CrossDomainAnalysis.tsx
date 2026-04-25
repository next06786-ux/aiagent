/**
 * 跨领域综合分析组件
 * 多Agent协作 - 智慧洞察的核心功能
 */
import React, { useState } from 'react'
import { 
  generateCrossDomainAnalysis, 
  CrossDomainAnalysisResult 
} from '../services/agentInsightsService'
import '../styles/CrossDomainAnalysis.css'

interface CrossDomainAnalysisProps {
  token: string
}

export const CrossDomainAnalysis: React.FC<CrossDomainAnalysisProps> = ({ token }) => {
  const [query, setQuery] = useState('综合分析我的人际关系、教育背景和职业发展，给出整体战略建议')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CrossDomainAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedTab, setSelectedTab] = useState<'summary' | 'patterns' | 'recommendations' | 'action_plan'>('summary')

  const handleAnalyze = async () => {
    if (!query.trim()) {
      setError('请输入分析查询')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await generateCrossDomainAnalysis(token, query)
      setResult(data)
    } catch (err: any) {
      setError(err.message || '分析失败')
      console.error('跨领域分析失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const quickQueries = [
    '综合分析我的人际关系、教育背景和职业发展',
    '我的人际关系如何影响职业发展？',
    '教育背景和人脉资源如何协同提升职业竞争力？',
    '如何平衡学业、人际关系和职业规划？'
  ]

  return (
    <div className="cross-domain-analysis">
      <div className="analysis-header">
        <h2>跨领域综合分析</h2>
        <p className="subtitle">多Agent协作 · 发现跨领域关联 · 生成综合战略</p>
      </div>

      {/* 查询输入 */}
      <div className="query-section">
        <div className="query-input-group">
          <textarea
            className="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入你的综合分析需求..."
            rows={3}
          />
          <button 
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? '分析中...' : '开始分析'}
          </button>
        </div>

        {/* 快捷查询 */}
        <div className="quick-queries">
          <span className="quick-label">快捷查询：</span>
          {quickQueries.map((q, index) => (
            <button
              key={index}
              className="quick-query-btn"
              onClick={() => setQuery(q)}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* 加载状态 */}
      {loading && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <div className="loading-steps">
            <div className="step">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              </svg>
              <span>初始化共享记忆空间...</span>
            </div>
            <div className="step">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              <span>执行多Agent协作...</span>
            </div>
            <div className="step">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              <span>识别跨领域关联...</span>
            </div>
            <div className="step">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <circle cx="12" cy="12" r="6"/>
                <circle cx="12" cy="12" r="2"/>
              </svg>
              <span>生成综合战略...</span>
            </div>
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="error-message">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* 分析结果 */}
      {result && (
        <div className="analysis-result">
          {/* 执行摘要 */}
          <div className="execution-summary">
            <div className="summary-item">
              <span className="label">执行Agent:</span>
              <span className="value">{result.execution_summary.total_agents} 个</span>
            </div>
            <div className="summary-item">
              <span className="label">执行时间:</span>
              <span className="value">{result.execution_summary.execution_time.toFixed(2)}秒</span>
            </div>
            <div className="summary-item">
              <span className="label">分析类型:</span>
              <span className="value">{result.analysis_type}</span>
            </div>
          </div>

          {/* 标签页 */}
          <div className="tabs">
            <button 
              className={`tab ${selectedTab === 'summary' ? 'active' : ''}`}
              onClick={() => setSelectedTab('summary')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
              <span>综合摘要</span>
            </button>
            <button 
              className={`tab ${selectedTab === 'patterns' ? 'active' : ''}`}
              onClick={() => setSelectedTab('patterns')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              <span>跨领域模式</span>
            </button>
            <button 
              className={`tab ${selectedTab === 'recommendations' ? 'active' : ''}`}
              onClick={() => setSelectedTab('recommendations')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <circle cx="12" cy="12" r="6"/>
                <circle cx="12" cy="12" r="2"/>
              </svg>
              <span>战略建议</span>
            </button>
            <button 
              className={`tab ${selectedTab === 'action_plan' ? 'active' : ''}`}
              onClick={() => setSelectedTab('action_plan')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              <span>行动计划</span>
            </button>
          </div>

          {/* 标签页内容 */}
          <div className="tab-content">
            {selectedTab === 'summary' && (
              <div className="summary-content">
                <div className="summary-text">
                  {result.cross_domain_analysis.summary}
                </div>

                {/* 整合洞察 */}
                {result.cross_domain_analysis.integrated_insights.length > 0 && (
                  <div className="integrated-insights">
                    <h3>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '8px', color: '#0A59F7'}}>
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.35-4.35"/>
                      </svg>
                      整合洞察
                    </h3>
                    {result.cross_domain_analysis.integrated_insights.map((insight, index) => (
                      <div key={index} className={`insight-card importance-${insight.importance}`}>
                        <div className="insight-header">
                          <span className="insight-title">{insight.title}</span>
                          <span className="insight-domains">
                            {insight.domains.map(d => (
                              <span key={d} className="domain-tag">{d}</span>
                            ))}
                          </span>
                        </div>
                        <div className="insight-description">{insight.description}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {selectedTab === 'patterns' && (
              <div className="patterns-content">
                {/* 跨领域模式 */}
                <div className="section">
                  <h3>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '8px', color: '#0A59F7'}}>
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                    跨领域模式 ({result.cross_domain_analysis.cross_domain_patterns.length})
                  </h3>
                  {result.cross_domain_analysis.cross_domain_patterns.map((pattern, index) => (
                    <div key={index} className={`pattern-card strength-${pattern.strength}`}>
                      <div className="pattern-header">
                        <span className="pattern-title">{pattern.title}</span>
                        <span className="pattern-strength">{pattern.strength}</span>
                      </div>
                      <div className="pattern-description">{pattern.description}</div>
                      <div className="pattern-domains">
                        涉及领域: {pattern.domains.join(' × ')}
                      </div>
                    </div>
                  ))}
                  {result.cross_domain_analysis.cross_domain_patterns.length === 0 && (
                    <div className="empty-state">暂无跨领域模式</div>
                  )}
                </div>

                {/* 协同效应 */}
                <div className="section">
                  <h3>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '8px', color: '#10b981'}}>
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                    </svg>
                    协同效应 ({result.cross_domain_analysis.synergies.length})
                  </h3>
                  {result.cross_domain_analysis.synergies.map((synergy, index) => (
                    <div key={index} className="synergy-card">
                      <div className="synergy-title">{synergy.title}</div>
                      <div className="synergy-description">{synergy.description}</div>
                      <div className="synergy-benefit">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '6px', color: '#10b981'}}>
                          <circle cx="12" cy="12" r="10"/>
                          <path d="M12 16v-4"/>
                          <path d="M12 8h.01"/>
                        </svg>
                        潜在收益: {synergy.potential_benefit}
                      </div>
                    </div>
                  ))}
                  {result.cross_domain_analysis.synergies.length === 0 && (
                    <div className="empty-state">暂无协同效应</div>
                  )}
                </div>

                {/* 潜在冲突 */}
                <div className="section">
                  <h3>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '8px', color: '#f59e0b'}}>
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                      <line x1="12" y1="9" x2="12" y2="13"/>
                      <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    潜在冲突 ({result.cross_domain_analysis.conflicts.length})
                  </h3>
                  {result.cross_domain_analysis.conflicts.map((conflict, index) => (
                    <div key={index} className={`conflict-card severity-${conflict.severity}`}>
                      <div className="conflict-header">
                        <span className="conflict-title">{conflict.title}</span>
                        <span className="conflict-severity">{conflict.severity}</span>
                      </div>
                      <div className="conflict-description">{conflict.description}</div>
                      <div className="conflict-resolution">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '6px', color: '#f59e0b'}}>
                          <circle cx="12" cy="12" r="10"/>
                          <path d="M12 16v-4"/>
                          <path d="M12 8h.01"/>
                        </svg>
                        解决建议: {conflict.resolution_suggestion}
                      </div>
                    </div>
                  ))}
                  {result.cross_domain_analysis.conflicts.length === 0 && (
                    <div className="empty-state">暂无潜在冲突</div>
                  )}
                </div>
              </div>
            )}

            {selectedTab === 'recommendations' && (
              <div className="recommendations-content">
                <h3>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '8px', color: '#0A59F7'}}>
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="12" cy="12" r="6"/>
                    <circle cx="12" cy="12" r="2"/>
                  </svg>
                  战略建议 ({result.cross_domain_analysis.strategic_recommendations.length})
                </h3>
                {result.cross_domain_analysis.strategic_recommendations.map((rec, index) => (
                  <div key={index} className={`recommendation-card priority-${rec.priority}`}>
                    <div className="rec-header">
                      <span className="rec-number">{index + 1}</span>
                      <span className="rec-priority">{rec.priority}</span>
                      <span className="rec-category">{rec.category}</span>
                    </div>
                    <div className="rec-action">{rec.action}</div>
                    <div className="rec-details">
                      <div className="rec-detail">
                        <span className="label">预期影响:</span>
                        <span className="value">{rec.expected_impact}</span>
                      </div>
                      <div className="rec-detail">
                        <span className="label">时间线:</span>
                        <span className="value">{rec.timeline}</span>
                      </div>
                      <div className="rec-detail">
                        <span className="label">涉及领域:</span>
                        <span className="value">{rec.involved_domains.join(', ')}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedTab === 'action_plan' && (
              <div className="action-plan-content">
                <h3>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: '8px', color: '#0A59F7'}}>
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                  分阶段行动计划
                </h3>
                
                <div className="plan-section">
                  <div className="plan-header">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{color: '#0A59F7'}}>
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                    </svg>
                    <span className="plan-title">短期行动 (1-3个月)</span>
                  </div>
                  <ul className="plan-list">
                    {result.cross_domain_analysis.action_plan.short_term.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>

                <div className="plan-section">
                  <div className="plan-header">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{color: '#10b981'}}>
                      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                      <polyline points="17 6 23 6 23 12"/>
                    </svg>
                    <span className="plan-title">中期行动 (3-6个月)</span>
                  </div>
                  <ul className="plan-list">
                    {result.cross_domain_analysis.action_plan.medium_term.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>

                <div className="plan-section">
                  <div className="plan-header">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{color: '#6B48FF'}}>
                      <circle cx="12" cy="12" r="10"/>
                      <circle cx="12" cy="12" r="6"/>
                      <circle cx="12" cy="12" r="2"/>
                    </svg>
                    <span className="plan-title">长期行动 (6-12个月)</span>
                  </div>
                  <ul className="plan-list">
                    {result.cross_domain_analysis.action_plan.long_term.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
