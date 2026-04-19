/**
 * 智能日程推荐 - HarmonyOS 6 风格
 * 纯展示模式 - 所有交互通过AI核心完成
 */
import React, { useState, useEffect } from 'react';
import { scheduleService, DailySchedule, UserPatterns, TimeDecisionResult } from '../../services/scheduleService';
import { scheduleServiceExtended, TaskStatus } from '../../services/scheduleService';
import { AppShell } from '../shell/AppShell';
import { GlassCard } from '../common/GlassCard';
import { PageHeader } from '../common/PageHeader';
import { StatusPill } from '../common/StatusPill';
import './SmartSchedule-v2.css';

export const SmartScheduleV2: React.FC = () => {
  // 从AuthContext或localStorage获取真实用户ID
  const [userId] = useState(() => {
    // 1. 尝试从localStorage获取登录用户
    const storedUser = localStorage.getItem('current_user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        console.log('[智能日程] 从localStorage获取用户:', user.user_id);
        return user.user_id;
      } catch (e) {
        console.warn('[智能日程] 解析localStorage用户失败:', e);
      }
    }
    
    // 2. 尝试从sessionStorage获取
    const sessionUser = sessionStorage.getItem('user');
    if (sessionUser) {
      try {
        const user = JSON.parse(sessionUser);
        console.log('[智能日程] 从sessionStorage获取用户:', user.user_id);
        return user.user_id;
      } catch (e) {
        console.warn('[智能日程] 解析sessionStorage用户失败:', e);
      }
    }
    
    // 3. 使用默认用户ID（你的实际用户ID）
    console.log('[智能日程] 使用默认用户ID');
    return '2c2139f7-bab4-483d-9882-ae83ce8734cd';
  });
  const [schedule, setSchedule] = useState<DailySchedule | null>(null);
  const [patterns, setPatterns] = useState<UserPatterns | null>(null);
  const [decision, setDecision] = useState<TimeDecisionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState<'schedule' | 'decision' | 'patterns'>('schedule');
  
  // 任务状态
  const [scheduleTask, setScheduleTask] = useState<TaskStatus | null>(null);
  const [decisionTask, setDecisionTask] = useState<TaskStatus | null>(null);

  useEffect(() => {
    console.log('[智能日程] 组件加载，用户ID:', userId);
    loadInitialData();
    loadTaskData();
    // 每5秒检查一次任务状态（不重新加载 patterns）
    const interval = setInterval(loadTaskData, 5000);
    return () => clearInterval(interval);
  }, [userId]);

  const loadInitialData = async () => {
    // 只在初始加载时获取用户模式
    try {
      console.log('[智能日程] 加载用户模式...');
      const patternsData = await scheduleService.getUserPatterns(userId);
      setPatterns(patternsData);
      console.log('[智能日程] 用户模式加载完成');
    } catch (error) {
      console.error('[智能日程] 加载用户模式失败:', error);
    }
  };

  const loadTaskData = async () => {
    // 定期检查任务状态
    setLoading(true);
    try {
      console.log('[智能日程] 检查任务状态，用户ID:', userId);

      // 加载最新的日程任务
      const latestSchedule = await scheduleServiceExtended.getLatestSchedule(userId);
      console.log('[智能日程] 最新日程任务:', latestSchedule);
      
      if (latestSchedule.status !== 'no_data') {
        setScheduleTask(latestSchedule);
        if (latestSchedule.status === 'completed' && latestSchedule.result) {
          setSchedule(latestSchedule.result);
          console.log('[智能日程] 日程数据已更新');
        } else if (latestSchedule.status === 'running' || latestSchedule.status === 'pending') {
          console.log(`[智能日程] 任务进行中: ${latestSchedule.progress}% - ${latestSchedule.progress_message}`);
        }
      } else {
        console.log('[智能日程] 暂无日程数据');
      }

      // 加载最新的决策任务
      const latestDecision = await scheduleServiceExtended.getLatestDecision(userId);
      console.log('[智能日程] 最新决策任务:', latestDecision);
      
      if (latestDecision.status !== 'no_data') {
        setDecisionTask(latestDecision);
        if (latestDecision.status === 'completed' && latestDecision.result) {
          setDecision(latestDecision.result);
          console.log('[智能日程] 决策数据已更新');
        } else if (latestDecision.status === 'running' || latestDecision.status === 'pending') {
          console.log(`[智能日程] 决策任务进行中: ${latestDecision.progress}% - ${latestDecision.progress_message}`);
        }
      } else {
        console.log('[智能日程] 暂无决策数据');
      }
    } catch (error) {
      console.error('[智能日程] 加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTaskTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      work: '工作',
      study: '学习',
      exercise: '运动',
      social: '社交',
      rest: '休息',
    };
    return labels[type] || type;
  };

  const getPriorityLabel = (priority: string) => {
    const labels: Record<string, string> = {
      high: '高',
      medium: '中',
      low: '低',
    };
    return labels[priority] || priority;
  };

  const getOptionColor = (optionId: string) => {
    const colors: Record<string, string> = {
      aggressive: '#FF6B6B',
      balanced: '#0A59F7',
      conservative: '#34C759',
    };
    return colors[optionId] || '#666';
  };

  const getOptionLabel = (optionId: string) => {
    const labels: Record<string, string> = {
      aggressive: '激进方案',
      balanced: '平衡方案',
      conservative: '保守方案',
    };
    return labels[optionId] || optionId;
  };

  return (
    <AppShell>
      <PageHeader
        title="智能日程"
        subtitle="通过AI核心对话生成个性化日程安排"
      />

      {/* 提示卡片 */}
      <GlassCard>
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <div style={{ 
            width: '64px', 
            height: '64px', 
            margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #0A59F7, #6B48FF)',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '32px',
            color: 'white'
          }}>
            AI
          </div>
          <h3 style={{ marginBottom: '12px', color: '#1a1a1a' }}>与AI对话生成日程</h3>
          <p style={{ color: '#666', lineHeight: 1.6, marginBottom: '20px' }}>
            点击右下角的AI助手，告诉它你今天的任务和状态，<br />
            AI会为你生成最优的时间安排和决策建议
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <StatusPill tone="primary">"帮我安排今天的工作"</StatusPill>
            <StatusPill tone="success">"我今天压力很大，怎么安排？"</StatusPill>
            <StatusPill tone="warning">"给我一个高效的日程方案"</StatusPill>
          </div>
        </div>
      </GlassCard>

      {/* 视图切换 */}
      <div className="schedule-view-tabs">
        <button
          className={`schedule-tab ${activeView === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveView('schedule')}
        >
          今日日程
        </button>
        <button
          className={`schedule-tab ${activeView === 'decision' ? 'active' : ''}`}
          onClick={() => setActiveView('decision')}
        >
          时间决策
        </button>
        <button
          className={`schedule-tab ${activeView === 'patterns' ? 'active' : ''}`}
          onClick={() => setActiveView('patterns')}
        >
          时间模式
        </button>
      </div>

      {/* 今日日程视图 */}
      {activeView === 'schedule' && (
        <div className="stack-layout">
          {/* 生成进度显示 */}
          {scheduleTask && scheduleTask.status === 'running' && (
            <GlassCard>
              <div style={{ padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <div className="loading-spinner" style={{ 
                    width: '24px', 
                    height: '24px', 
                    border: '3px solid #f3f3f3',
                    borderTop: '3px solid #0A59F7',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <div>
                    <h4 style={{ margin: 0, color: '#1a1a1a' }}>正在生成日程...</h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#666' }}>
                      {scheduleTask.progress_message}
                    </p>
                  </div>
                </div>
                <div style={{ 
                  width: '100%', 
                  height: '8px', 
                  backgroundColor: '#f0f0f0', 
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${scheduleTask.progress}%`,
                    height: '100%',
                    backgroundColor: '#0A59F7',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>
                <p style={{ marginTop: '8px', fontSize: '12px', color: '#999', textAlign: 'right' }}>
                  {scheduleTask.progress}%
                </p>
              </div>
            </GlassCard>
          )}

          {schedule ? (
            <>
              <GlassCard
                title={`今日日程 - ${schedule.date}`}
                subtitle="基于你的习惯和生产力曲线优化"
              >
                <div className="schedule-timeline">
                  {schedule.timeline.map((item, index) => (
                    <div
                      key={index}
                      className={`schedule-timeline-item schedule-type-${item.type}`}
                    >
                      <div className="timeline-time">
                        <span className="time-start">{item.start}</span>
                        <span className="time-separator">-</span>
                        <span className="time-end">{item.end}</span>
                      </div>
                      <div className="timeline-content">
                        <h4>{item.title}</h4>
                        <div className="timeline-meta">
                          <StatusPill
                            tone={
                              item.priority === 'high'
                                ? 'danger'
                                : item.priority === 'medium'
                                  ? 'warning'
                                  : 'primary'
                            }
                          >
                            {getPriorityLabel(item.priority)}
                          </StatusPill>
                          <span className="timeline-duration">{item.duration}分钟</span>
                          <span className="timeline-type">{getTaskTypeLabel(item.type)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>

              <GlassCard title="日程摘要" subtitle="今日时间分配概览">
                <div className="schedule-summary-grid">
                  <div className="summary-stat">
                    <div className="stat-value">{schedule.summary.total_tasks}</div>
                    <div className="stat-label">总任务数</div>
                  </div>
                  <div className="summary-stat">
                    <div className="stat-value">{Math.round(schedule.summary.total_work_minutes / 60)}h</div>
                    <div className="stat-label">工作时长</div>
                  </div>
                  <div className="summary-stat">
                    <div className="stat-value">{schedule.summary.total_break_minutes}min</div>
                    <div className="stat-label">休息时长</div>
                  </div>
                  <div className="summary-stat">
                    <div className="stat-value">{schedule.summary.work_break_ratio.toFixed(1)}</div>
                    <div className="stat-label">工作/休息比</div>
                  </div>
                </div>

                {schedule.optimization_tips && schedule.optimization_tips.length > 0 && (
                  <div className="schedule-tips">
                    <h4>优化建议</h4>
                    <ul>
                      {schedule.optimization_tips.map((tip, index) => (
                        <li key={index}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </GlassCard>
            </>
          ) : (
            <GlassCard>
              <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                <div style={{ 
                  width: '80px', 
                  height: '80px', 
                  margin: '0 auto 16px',
                  background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.1), rgba(107, 72, 255, 0.1))',
                  borderRadius: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid rgba(10, 89, 247, 0.2)'
                }}>
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0A59F7" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                </div>
                <p>暂无今日日程</p>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>
                  通过AI助手生成你的个性化日程安排
                </p>
              </div>
            </GlassCard>
          )}
        </div>
      )}

      {/* 时间决策视图 */}
      {activeView === 'decision' && (
        <div className="stack-layout">
          {/* 决策进度显示 */}
          {decisionTask && decisionTask.status === 'running' && (
            <GlassCard>
              <div style={{ padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <div className="loading-spinner" style={{ 
                    width: '24px', 
                    height: '24px', 
                    border: '3px solid #f3f3f3',
                    borderTop: '3px solid #0A59F7',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <div>
                    <h4 style={{ margin: 0, color: '#1a1a1a' }}>正在生成决策...</h4>
                    <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#666' }}>
                      {decisionTask.progress_message}
                    </p>
                  </div>
                </div>
                <div style={{ 
                  width: '100%', 
                  height: '8px', 
                  backgroundColor: '#f0f0f0', 
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${decisionTask.progress}%`,
                    height: '100%',
                    backgroundColor: '#0A59F7',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>
                <p style={{ marginTop: '8px', fontSize: '12px', color: '#999', textAlign: 'right' }}>
                  {decisionTask.progress}%
                </p>
              </div>
            </GlassCard>
          )}

          {decision ? (
            <>
              <GlassCard 
                title="推荐方案" 
                subtitle={`决策置信度: ${(decision.confidence * 100).toFixed(0)}%`}
              >
                <div 
                  className="decision-option recommended"
                  style={{ borderColor: getOptionColor(decision.recommended_option.option_id) }}
                >
                  <div className="option-header">
                    <h3>{getOptionLabel(decision.recommended_option.option_id)}</h3>
                    <StatusPill tone="success">推荐</StatusPill>
                  </div>
                  
                  <p className="option-description">
                    {decision.recommended_option.description}
                  </p>

                  <div className="option-metrics">
                    <div className="metric">
                      <span className="metric-label">完成率</span>
                      <span className="metric-value">
                        {(decision.recommended_option.expected_completion_rate * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">效率</span>
                      <span className="metric-value">
                        {(decision.recommended_option.expected_efficiency * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">压力</span>
                      <span className="metric-value">
                        {(decision.recommended_option.expected_stress * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">风险</span>
                      <span className="metric-value">
                        {(decision.recommended_option.risk_level * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </GlassCard>

              <GlassCard title="决策推理" subtitle="为什么推荐这个方案">
                <div className="decision-reasoning">
                  <pre style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontFamily: 'inherit' }}>
                    {decision.reasoning}
                  </pre>
                </div>
              </GlassCard>

              <GlassCard title="备选方案" subtitle="其他可行的选择">
                <div className="alternative-options">
                  {decision.alternative_options.map((option) => (
                    <div 
                      key={option.option_id}
                      className="decision-option alternative"
                      style={{ borderColor: getOptionColor(option.option_id) }}
                    >
                      <div className="option-header">
                        <h4>{getOptionLabel(option.option_id)}</h4>
                      </div>
                      
                      <p className="option-description">{option.description}</p>

                      <div className="option-metrics compact">
                        <span>完成率 {(option.expected_completion_rate * 100).toFixed(0)}%</span>
                        <span>效率 {(option.expected_efficiency * 100).toFixed(0)}%</span>
                        <span>压力 {(option.expected_stress * 100).toFixed(0)}%</span>
                        <span>风险 {(option.risk_level * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>

              <GlassCard title="权衡分析" subtitle="不同方案的取舍">
                <div className="trade-offs">
                  {Object.entries(decision.trade_offs).map(([key, value]: [string, any]) => (
                    <div key={key} className="trade-off-item">
                      <h4>{value.description}</h4>
                      <ul>
                        {Object.entries(value).map(([strategy, desc]: [string, any]) => {
                          if (strategy === 'description') return null;
                          return (
                            <li key={strategy}>
                              <strong>{getOptionLabel(strategy)}:</strong> {desc}
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}
                </div>
              </GlassCard>
            </>
          ) : (
            <GlassCard>
              <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                <div style={{ 
                  width: '80px', 
                  height: '80px', 
                  margin: '0 auto 16px',
                  background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.1), rgba(107, 72, 255, 0.1))',
                  borderRadius: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid rgba(10, 89, 247, 0.2)'
                }}>
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0A59F7" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </div>
                <p>暂无决策结果</p>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>
                  告诉AI你的任务和状态，获取智能决策建议
                </p>
              </div>
            </GlassCard>
          )}
        </div>
      )}

      {/* 时间模式视图 */}
      {activeView === 'patterns' && (
        <div className="stack-layout">
          {patterns ? (
            <>
              <GlassCard title="生产力曲线" subtitle="你的24小时效率分布">
                <div className="schedule-productivity-chart">
                  {patterns.productivity_curve
                    .filter((p) => p.hour >= 6 && p.hour <= 23)
                    .map((pattern) => (
                      <div key={pattern.hour} className="productivity-bar-group">
                        <div className="bar-hour">{pattern.hour}:00</div>
                        <div className="bar-container">
                          <div
                            className="productivity-bar bar-productivity"
                            style={{ width: `${pattern.productivity * 100}%` }}
                            title={`生产力: ${(pattern.productivity * 100).toFixed(0)}%`}
                          />
                          <div
                            className="productivity-bar bar-focus"
                            style={{ width: `${pattern.focus * 100}%` }}
                            title={`专注度: ${(pattern.focus * 100).toFixed(0)}%`}
                          />
                          <div
                            className="productivity-bar bar-energy"
                            style={{ width: `${pattern.energy * 100}%` }}
                            title={`能量: ${(pattern.energy * 100).toFixed(0)}%`}
                          />
                        </div>
                      </div>
                    ))}
                </div>
                <div className="chart-legend">
                  <div className="legend-item">
                    <span className="legend-color bar-productivity"></span>
                    <span>生产力</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color bar-focus"></span>
                    <span>专注度</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color bar-energy"></span>
                    <span>能量</span>
                  </div>
                </div>
              </GlassCard>

              <GlassCard title="高效时段" subtitle="你的黄金工作时间">
                <div className="schedule-peak-hours">
                  {patterns.peak_hours.map((slot, index) => (
                    <div key={index} className="peak-hour-slot">
                      {slot.start_time} - {slot.end_time}
                    </div>
                  ))}
                </div>
              </GlassCard>

              <GlassCard title="典型作息" subtitle="你的日常时间安排">
                <div className="schedule-typical-grid">
                  <div className="typical-item">
                    <span className="typical-label">起床时间</span>
                    <span className="typical-value">{patterns.typical_schedule.wake_time}</span>
                  </div>
                  <div className="typical-item">
                    <span className="typical-label">睡觉时间</span>
                    <span className="typical-value">{patterns.typical_schedule.sleep_time}</span>
                  </div>
                  <div className="typical-item">
                    <span className="typical-label">工作时段</span>
                    <span className="typical-value">
                      {patterns.typical_schedule.work_start} - {patterns.typical_schedule.work_end}
                    </span>
                  </div>
                  <div className="typical-item">
                    <span className="typical-label">运动时间</span>
                    <span className="typical-value">{patterns.typical_schedule.exercise_time}</span>
                  </div>
                </div>
              </GlassCard>
            </>
          ) : (
            <GlassCard>
              <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                {loading ? (
                  <>
                    <div style={{ 
                      width: '80px', 
                      height: '80px', 
                      margin: '0 auto 16px',
                      background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.1), rgba(107, 72, 255, 0.1))',
                      borderRadius: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <div className="loading-spinner" style={{ 
                        width: '40px', 
                        height: '40px', 
                        border: '4px solid #f3f3f3',
                        borderTop: '4px solid #0A59F7',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }}></div>
                    </div>
                    <p>加载中...</p>
                  </>
                ) : (
                  <>
                    <div style={{ 
                      width: '80px', 
                      height: '80px', 
                      margin: '0 auto 16px',
                      background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.1), rgba(107, 72, 255, 0.1))',
                      borderRadius: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '2px solid rgba(10, 89, 247, 0.2)'
                    }}>
                      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0A59F7" strokeWidth="2">
                        <line x1="12" y1="20" x2="12" y2="10"></line>
                        <line x1="18" y1="20" x2="18" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="16"></line>
                      </svg>
                    </div>
                    <p>暂无时间模式数据</p>
                  </>
                )}
              </div>
            </GlassCard>
          )}
        </div>
      )}
    </AppShell>
  );
};
