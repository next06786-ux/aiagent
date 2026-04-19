/**
 * 智能日程推荐组件
 */
import React, { useState, useEffect } from 'react';
import { scheduleService, Task, DailySchedule, UserPatterns } from '../../services/scheduleService';
import './SmartSchedule.css';

export const SmartSchedule: React.FC = () => {
  const [userId] = useState(() => {
    // 尝试从localStorage或sessionStorage获取用户ID
    const storedUser = localStorage.getItem('current_user') || sessionStorage.getItem('user');
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser);
        return user.user_id || '2c2139f7-bab4-483d-9882-ae83ce8734cd';
      } catch {
        return '2c2139f7-bab4-483d-9882-ae83ce8734cd';
      }
    }
    return '2c2139f7-bab4-483d-9882-ae83ce8734cd';
  });
  const [tasks, setTasks] = useState<Task[]>([]);
  const [schedule, setSchedule] = useState<DailySchedule | null>(null);
  const [patterns, setPatterns] = useState<UserPatterns | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'schedule' | 'patterns'>('schedule');

  // 加载用户模式
  useEffect(() => {
    loadUserPatterns();
  }, []);

  const loadUserPatterns = async () => {
    try {
      const data = await scheduleService.getUserPatterns(userId);
      setPatterns(data);
    } catch (error) {
      console.error('加载用户模式失败:', error);
    }
  };

  // 添加任务
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

  // 生成日程
  const generateSchedule = async () => {
    if (tasks.length === 0) {
      alert('请先添加任务');
      return;
    }

    setLoading(true);
    try {
      const data = await scheduleService.recommendDailySchedule(userId, tasks);
      setSchedule(data);
    } catch (error) {
      console.error('生成日程失败:', error);
      alert('生成日程失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="smart-schedule-container">
      <h1>🗓️ 智能日程推荐</h1>

      {/* 标签页 */}
      <div className="tabs">
        <button
          className={activeTab === 'schedule' ? 'active' : ''}
          onClick={() => setActiveTab('schedule')}
        >
          日程规划
        </button>
        <button
          className={activeTab === 'patterns' ? 'active' : ''}
          onClick={() => setActiveTab('patterns')}
        >
          时间模式
        </button>
      </div>

      {/* 日程规划 */}
      {activeTab === 'schedule' && (
        <div className="schedule-tab">
          <div className="task-input-section">
            <h2>任务列表</h2>
            <button onClick={addTask}>➕ 添加任务</button>

            <div className="task-list">
              {tasks.map((task, index) => (
                <div key={task.task_id} className="task-item">
                  <input
                    type="text"
                    value={task.title}
                    onChange={(e) => {
                      const newTasks = [...tasks];
                      newTasks[index].title = e.target.value;
                      setTasks(newTasks);
                    }}
                    placeholder="任务名称"
                  />
                  <select
                    value={task.task_type}
                    onChange={(e) => {
                      const newTasks = [...tasks];
                      newTasks[index].task_type = e.target.value as any;
                      setTasks(newTasks);
                    }}
                  >
                    <option value="work">工作</option>
                    <option value="study">学习</option>
                    <option value="exercise">运动</option>
                    <option value="social">社交</option>
                    <option value="rest">休息</option>
                  </select>
                  <input
                    type="number"
                    value={task.duration_minutes}
                    onChange={(e) => {
                      const newTasks = [...tasks];
                      newTasks[index].duration_minutes = parseInt(e.target.value);
                      setTasks(newTasks);
                    }}
                    placeholder="时长(分钟)"
                  />
                  <select
                    value={task.priority}
                    onChange={(e) => {
                      const newTasks = [...tasks];
                      newTasks[index].priority = e.target.value as any;
                      setTasks(newTasks);
                    }}
                  >
                    <option value="high">高</option>
                    <option value="medium">中</option>
                    <option value="low">低</option>
                  </select>
                  <button
                    onClick={() => {
                      setTasks(tasks.filter((_, i) => i !== index));
                    }}
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={generateSchedule}
              disabled={loading || tasks.length === 0}
              className="generate-btn"
            >
              {loading ? '生成中...' : '🎯 生成智能日程'}
            </button>
          </div>

          {/* 日程结果 */}
          {schedule && (
            <div className="schedule-result">
              <h2>📅 推荐日程 - {schedule.date}</h2>

              <div className="timeline">
                {schedule.timeline.map((item, index) => (
                  <div key={index} className={`timeline-item ${item.type}`}>
                    <div className="time">
                      {item.start} - {item.end}
                    </div>
                    <div className="content">
                      <h3>{item.title}</h3>
                      <span className={`priority ${item.priority}`}>
                        {item.priority === 'high' ? '高优先级' : item.priority === 'medium' ? '中优先级' : '低优先级'}
                      </span>
                      <span className="duration">{item.duration}分钟</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="summary">
                <h3>📊 日程摘要</h3>
                <p>总任务数: {schedule.summary.total_tasks}</p>
                <p>工作时长: {schedule.summary.total_work_minutes}分钟</p>
                <p>休息时长: {schedule.summary.total_break_minutes}分钟</p>
                <p>工作/休息比: {schedule.summary.work_break_ratio}</p>
              </div>

              {schedule.optimization_tips.length > 0 && (
                <div className="tips">
                  <h3>💡 优化建议</h3>
                  <ul>
                    {schedule.optimization_tips.map((tip, index) => (
                      <li key={index}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 时间模式 */}
      {activeTab === 'patterns' && patterns && (
        <div className="patterns-tab">
          <h2>📈 你的时间使用模式</h2>

          <div className="productivity-chart">
            <h3>生产力曲线</h3>
            <div className="chart">
              {patterns.productivity_curve
                .filter((p) => p.hour >= 6 && p.hour <= 23)
                .map((pattern) => (
                  <div key={pattern.hour} className="chart-bar">
                    <div className="bar-label">{pattern.hour}:00</div>
                    <div className="bars">
                      <div
                        className="bar productivity"
                        style={{ width: `${pattern.productivity * 100}%` }}
                        title={`生产力: ${(pattern.productivity * 100).toFixed(0)}%`}
                      />
                      <div
                        className="bar focus"
                        style={{ width: `${pattern.focus * 100}%` }}
                        title={`专注度: ${(pattern.focus * 100).toFixed(0)}%`}
                      />
                      <div
                        className="bar energy"
                        style={{ width: `${pattern.energy * 100}%` }}
                        title={`能量: ${(pattern.energy * 100).toFixed(0)}%`}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div className="peak-hours">
            <h3>⚡ 高效时段</h3>
            {patterns.peak_hours.map((slot, index) => (
              <div key={index} className="time-slot">
                {slot.start_time} - {slot.end_time}
              </div>
            ))}
          </div>

          <div className="typical-schedule">
            <h3>🏠 典型日程</h3>
            <p>起床: {patterns.typical_schedule.wake_time}</p>
            <p>睡觉: {patterns.typical_schedule.sleep_time}</p>
            <p>工作: {patterns.typical_schedule.work_start} - {patterns.typical_schedule.work_end}</p>
            <p>运动: {patterns.typical_schedule.exercise_time}</p>
            <p>学习: {patterns.typical_schedule.learning_time}</p>
          </div>

          <div className="habits">
            <h3>🎯 习惯分析</h3>
            <p>类型: {patterns.habits.morning_person ? '早起型' : '夜猫子型'}</p>
            <p>运动频率: {patterns.habits.exercise_frequency}</p>
            <p>学习频率: {patterns.habits.learning_frequency}</p>
            <p>偏好工作时长: {patterns.habits.preferred_work_duration}分钟</p>
          </div>
        </div>
      )}
    </div>
  );
};
