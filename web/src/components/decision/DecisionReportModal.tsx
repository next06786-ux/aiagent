import React from 'react';
import './DecisionReportModal.css';
import { DecisionReport } from '../../services/decisionHistory';

interface DecisionReportModalProps {
  visible: boolean;
  onClose: () => void;
  report: DecisionReport | null;
  optionTitle: string;
}

export function DecisionReportModal({
  visible,
  onClose,
  report,
  optionTitle,
}: DecisionReportModalProps) {
  if (!visible || !report) return null;

  return (
    <div className="decision-report-modal-overlay" onClick={onClose}>
      <div className="decision-report-modal" onClick={(e) => e.stopPropagation()}>
        {/* 头部 */}
        <div className="report-header">
          <h2 className="report-title">决策分析报告</h2>
          <button className="close-button" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M18 6L6 18M6 6l12 12" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {/* 选项标题 */}
        <div className="report-option-title">
          <div className="option-label">分析选项</div>
          <div className="option-name">{optionTitle}</div>
        </div>

        {/* 综合评分 */}
        <div className="report-score-section">
          <div className="score-label">综合评分</div>
          <div className="score-value">{report.total_score.toFixed(1)}</div>
          <div className="score-bar">
            <div 
              className="score-fill" 
              style={{ width: `${Math.min(report.total_score, 100)}%` }}
            />
          </div>
        </div>

        {/* 报告内容 */}
        <div className="report-content">
          {/* 总体评价 */}
          {report.summary && (
            <div className="report-section">
              <h3 className="section-title">总体评价</h3>
              <p className="section-text">{report.summary}</p>
            </div>
          )}

          {/* 关键洞察 */}
          {report.key_insights && report.key_insights.length > 0 && (
            <div className="report-section">
              <h3 className="section-title">关键洞察</h3>
              <ul className="insights-list">
                {report.key_insights.map((insight, index) => (
                  <li key={index} className="insight-item">
                    <span className="insight-icon">💡</span>
                    <span className="insight-text">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 主要优势 */}
          {report.strengths && report.strengths.length > 0 && (
            <div className="report-section">
              <h3 className="section-title">主要优势</h3>
              <ul className="strengths-list">
                {report.strengths.map((strength, index) => (
                  <li key={index} className="strength-item">
                    <span className="strength-icon">✓</span>
                    <span className="strength-text">{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 潜在风险 */}
          {report.risks && report.risks.length > 0 && (
            <div className="report-section">
              <h3 className="section-title">潜在风险</h3>
              <ul className="risks-list">
                {report.risks.map((risk, index) => (
                  <li key={index} className="risk-item">
                    <span className="risk-icon">⚠</span>
                    <span className="risk-text">{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 综合建议 */}
          {report.recommendation && (
            <div className="report-section">
              <h3 className="section-title">综合建议</h3>
              <p className="section-text recommendation">{report.recommendation}</p>
            </div>
          )}

          {/* Agent 评估汇总 */}
          {report.agents_summary && report.agents_summary.length > 0 && (
            <div className="report-section">
              <h3 className="section-title">Agent 评估汇总</h3>
              <div className="agents-summary-grid">
                {report.agents_summary.map((agent, index) => (
                  <div key={index} className="agent-summary-card">
                    <div className="agent-name">{agent.name}</div>
                    <div className="agent-stance">{agent.stance}</div>
                    <div className="agent-metrics">
                      <span className="metric">
                        评分: <strong>{agent.score.toFixed(1)}</strong>
                      </span>
                      <span className="metric">
                        信心: <strong>{(agent.confidence * 100).toFixed(0)}%</strong>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 底部操作按钮 */}
        <div className="report-footer">
          <button className="btn-secondary" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
