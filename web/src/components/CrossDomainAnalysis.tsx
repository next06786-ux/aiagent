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
        <h2>🔗 跨领域综合分析</h2>
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
            <div className="step">📦 初始化共享记忆空间...</div>
            <div className="step">🤖 执行多Agent协作...</div>
            <div className="step">🔗 识别跨领域关联...</div>
            <div className="step">🎯 生成综合战略...</div>
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="error-message">
          ❌ {error}
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
              📊 综合摘要
            </button>
            <button 
              className={`tab ${selectedTab === 'patterns' ? 'active' : ''}`}
              onClick={() => setSelectedTab('patterns')}
            >
              🔗 跨领域模式
            </button>
            <button 
              className={`tab ${selectedTab === 'recommendations' ? 'active' : ''}`}
              onClick={() => setSelectedTab('recommendations')}
            >
              🎯 战略建议
            </button>
            <button 
              className={`tab ${selectedTab === 'action_plan' ? 'active' : ''}`}
              onClick={() => setSelectedTab('action_plan')}
            >
              📅 行动计划
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
                    <h3>🔍 整合洞察</h3>
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
                  <h3>🔗 跨领域模式 ({result.cross_domain_analysis.cross_domain_patterns.length})</h3>
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
                  <h3>⚡ 协同效应 ({result.cross_domain_analysis.synergies.length})</h3>
                  {result.cross_domain_analysis.synergies.map((synergy, index) => (
                    <div key={index} className="synergy-card">
                      <div className="synergy-title">{synergy.title}</div>
                      <div className="synergy-description">{synergy.description}</div>
                      <div className="synergy-benefit">
                        💡 潜在收益: {synergy.potential_benefit}
                      </div>
                    </div>
                  ))}
                  {result.cross_domain_analysis.synergies.length === 0 && (
                    <div className="empty-state">暂无协同效应</div>
                  )}
                </div>

                {/* 潜在冲突 */}
                <div className="section">
                  <h3>⚠️ 潜在冲突 ({result.cross_domain_analysis.conflicts.length})</h3>
                  {result.cross_domain_analysis.conflicts.map((conflict, index) => (
                    <div key={index} className={`conflict-card severity-${conflict.severity}`}>
                      <div className="conflict-header">
                        <span className="conflict-title">{conflict.title}</span>
                        <span className="conflict-severity">{conflict.severity}</span>
                      </div>
                      <div className="conflict-description">{conflict.description}</div>
                      <div className="conflict-resolution">
                        💡 解决建议: {conflict.resolution_suggestion}
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
                <h3>🎯 战略建议 ({result.cross_domain_analysis.strategic_recommendations.length})</h3>
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
                <h3>📅 分阶段行动计划</h3>
                
                <div className="plan-section">
                  <div className="plan-header">
                    <span className="plan-icon">🚀</span>
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
                    <span className="plan-icon">📈</span>
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
                    <span className="plan-icon">🎯</span>
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
