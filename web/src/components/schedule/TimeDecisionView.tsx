/**
 * 时间决策视图 - 智能决策系统
 * 展示多个方案并推荐最佳选择
 */
import React, { useState } from 'react';
import { 
  scheduleService, 
  Task, 
  TimeDecisionRequest,
  TimeDecisionResult 
} from '../../services/scheduleService';
import { GlassCard } from '../common/GlassCard';
import { StatusPill } from '../common/StatusPill';
import './SmartSchedule-v2.css';

interface TimeDecisionViewProps {
  userId: string;
}

export const TimeDecisionView: React.FC<TimeDecisionViewProps> = ({ userId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [decision, setDecision] = useState<TimeDecisionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [energyLevel, setEnergyLevel] = useState(0.7);
  const [stressLevel, setStressLevel] = useState(0.3);
  const [availableHours, setAvailableHours] = useState(12);

  const addTask = () => {
    const newTask: Task = {
      task_id: `task_${Date.now()}`,
      title: '新任务',
      task_type: 'work',
      duration_minutes: 60,
      priority: 'medium',
      flexibility: 0.5,
      energy_required: 0.5,
      focus_required: 0.5,
    };
    setTasks([...tasks, newTask]);
  };

  const updateTask = (index: number, field: keyof Task, value: any) => {
    const newTasks = [...tasks];
    (newTasks[index] as any)[field] = value;
    setTasks(newTasks);
  };

  const removeTask = (index: number) => {
    setTasks(tasks.filter((_, i) => i !== index));
  };

  const makeDecision = async () => {
    if (tasks.length === 0) {
      alert('请先添加任务');
      return;
    }

    setLoading(true);
    try {
      const request: TimeDecisionRequest = {
        user_id: userId,
        tasks,
        available_hours: availableHours,
        current_energy: energyLevel,
        current_stress: stressLevel,
      };

      const result = await scheduleService.makeTimeDecision(request);
      setDecision(result);
    } catch (error) {
      console.error('时间决策失败:', error);
      alert('时间决策失败');
    } finally {
      setLoading(false);
    }
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
    <div className="time-decision-view stack-layout">
      {/* 任务列表 */}
      <GlassCard title="待决策任务" subtitle="添加需要安排的任务">
        <div className="schedule-task-section">
          <button className="schedule-add-btn" onClick={addTask}>
            <span className="btn-icon">+</span>
            添加任务
          </button>

          {tasks.length > 0 && (
            <div className="schedule-task-list">
              {tasks.map((task, index) => (
                <div key={task.task_id} className="schedule-task-item">
                  <div className="task-row">
                    <input
                      type="text"
                      className="task-input task-title"
                      value={task.title}
                      onChange={(e) => updateTask(index, 'title', e.target.value)}
                      placeholder="任务名称"
                    />
                    <select
                      className="task-select"
                      value={task.task_type}
                      onChange={(e) => updateTask(index, 'task_type', e.target.value)}
                    >
                      <option value="work">工作</option>
                      <option value="study">学习</option>
                      <option value="exercise">运动</option>
                      <option value="social">社交</option>
                      <option value="rest">休息</option>
                    </select>
                    <input
                      type="number"
                      className="task-input task-duration"
                      value={task.duration_minutes}
                      onChange={(e) => updateTask(index, 'duration_minutes', parseInt(e.target.value))}
                      placeholder="时长"
                      min="15"
                      step="15"
                    />
                    <select
                      className="task-select"
                      value={task.priority}
                      onChange={(e) => updateTask(index, 'priority', e.target.value)}
                    >
                      <option value="high">高优先级</option>
                      <option value="medium">中优先级</option>
                      <option value="low">低优先级</option>
                    </select>
                    <button
                      className="task-remove-btn"
                      onClick={() => removeTask(index)}
                      title="删除任务"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </GlassCard>

      {/* 状态设置 */}
      <GlassCard title="当前状态" subtitle="调整你的能量和压力水平">
        <div className="state-controls">
          <div className="state-control">
            <label>
              <span>能量水平</span>
              <div className="slider-container">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={energyLevel * 100}
                  onChange={(e) => setEnergyLevel(Number(e.target.value) / 100)}
                  className="state-slider"
                />
                <span className="slider-value">{(energyLevel * 100).toFixed(0)}%</span>
              </div>
            </label>
          </div>

          <div className="state-control">
            <label>
              <span>压力水平</span>
              <div className="slider-container">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={stressLevel * 100}
                  onChange={(e) => setStressLevel(Number(e.target.value) / 100)}
                  className="state-slider"
                />
                <span className="slider-value">{(stressLevel * 100).toFixed(0)}%</span>
              </div>
            </label>
          </div>

          <div className="state-control">
            <label>
              <span>可用时间（小时）</span>
              <div className="slider-container">
                <input
                  type="range"
                  min="4"
                  max="16"
                  value={availableHours}
                  onChange={(e) => setAvailableHours(Number(e.target.value))}
                  className="state-slider"
                />
                <span className="slider-value">{availableHours}h</span>
              </div>
            </label>
          </div>
        </div>

        <button
          onClick={makeDecision}
          disabled={loading || tasks.length === 0}
          className="button button-primary button-large"
          style={{ marginTop: '20px', width: '100%' }}
        >
          {loading ? '决策中...' : '开始智能决策'}
        </button>
      </GlassCard>

      {/* 决策结果 */}
      {decision && (
        <>
          {/* 推荐方案 */}
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

          {/* 决策推理 */}
          <GlassCard title="决策推理" subtitle="为什么推荐这个方案">
            <div className="decision-reasoning">
              <pre style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {decision.reasoning}
              </pre>
            </div>
          </GlassCard>

          {/* 备选方案 */}
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

          {/* 权衡分析 */}
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
      )}
    </div>
  );
};
