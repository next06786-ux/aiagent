import { useEffect, useState } from 'react';

interface SimulationProgressProps {
  stage: string;
  content: string;
  optionsCount: number;
  currentOption?: number;
}

export function SimulationProgress({
  stage,
  content,
  optionsCount,
  currentOption,
}: SimulationProgressProps) {
  const [progress, setProgress] = useState(0);
  const [dotCount, setDotCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState(Date.now());

  useEffect(() => {
    // 根据阶段计算进度
    const stageProgress: Record<string, number> = {
      init: 5,
      profile_loaded: 10,
      calibration_profile: 15,
      pkf_knowledge: 20,
      pkf_ready: 25,
      career_agent_init: 15,
      career_algorithm: 20,
      agent_initializing: 22,
      agent_evolving: 25,
      agent_interaction: 28,
      month_simulation: 30,
      agent_evaluation: 35,
      month_summary: 38,
      option_start: 30 + (currentOption || 0) * (60 / Math.max(optionsCount, 1)),
      timeline_generation_stream: 40 + (currentOption || 0) * (60 / Math.max(optionsCount, 1)),
      branch_generation: 50 + (currentOption || 0) * (60 / Math.max(optionsCount, 1)),
      option_scoring: 60 + (currentOption || 0) * (60 / Math.max(optionsCount, 1)),
      option_complete: 70 + (currentOption || 0) * (60 / Math.max(optionsCount, 1)),
      recommendation: 90,
      completed: 100,
    };

    const targetProgress = stageProgress[stage] || progress;
    setProgress(targetProgress);
    setLastUpdate(Date.now());
  }, [stage, currentOption, optionsCount, content]);

  // 动态加载动画
  useEffect(() => {
    const interval = setInterval(() => {
      setDotCount(prev => (prev + 1) % 4);
    }, 400);
    return () => clearInterval(interval);
  }, []);

  // 计算等待时间
  const waitTime = Math.round((Date.now() - lastUpdate) / 1000);

  const getStageLabel = (stage: string): string => {
    const careerLabels: Record<string, string> = {
      career_agent_init: '初始化职业决策引擎',
      career_algorithm: '职业决策算法分析',
      month_simulation: '月度模拟推演',
      agent_evaluation: '多Agent评估',
      month_summary: '月度综合评估',
      agent_initializing: '初始化Agent',
      agent_evolving: 'Agent状态演化',
      agent_interaction: 'Agent交互检测',
    };

    const labels: Record<string, string> = {
      init: '初始化推演环境',
      profile_loaded: '加载用户画像',
      calibration_profile: '载入历史校准',
      pkf_knowledge: '提取个人知识',
      pkf_ready: '知识图谱就绪',
      option_start: '开始选项推演',
      timeline_generation_stream: '生成时间线',
      branch_generation: '扩展分支节点',
      option_scoring: '计算选项评分',
      option_complete: '选项推演完成',
      recommendation: '生成推荐结论',
      completed: '推演完成',
      ...careerLabels,
    };

    return labels[stage] || stage;
  };

  const dots = '.'.repeat(dotCount);
  const isWorking = waitTime < 3;

  return (
    <div style={{
      background: '#ffffff',
      borderRadius: 16,
      padding: 20,
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.06)',
      border: '1px solid #e2e8f0',
    }}>
      {/* 顶部状态行 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#1e293b', marginBottom: 4 }}>
            {getStageLabel(stage)}
          </div>
          <div style={{ fontSize: 13, color: isWorking ? '#3b82f6' : '#94a3b8', lineHeight: 1.5 }}>
            {content || '处理中'}{dots}
          </div>
        </div>
        <div style={{
          width: 12,
          height: 12,
          borderRadius: '50%',
          background: isWorking ? '#3b82f6' : '#cbd5e1',
          marginLeft: 16,
          marginTop: 4,
          animation: isWorking ? 'pulse 1.5s ease-in-out infinite' : 'none',
          flexShrink: 0,
        }} />
      </div>

      {/* 进度条 */}
      <div style={{
        height: 6,
        background: '#e2e8f0',
        borderRadius: 3,
        overflow: 'hidden',
        marginBottom: 12,
      }}>
        <div style={{
          height: '100%',
          background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
          borderRadius: 3,
          width: `${progress}%`,
          transition: 'width 0.4s ease-out',
        }} />
      </div>

      {/* 底部状态栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 12, color: '#64748b' }}>
          {currentOption !== undefined && optionsCount > 0 ? (
            <span>选项 {currentOption + 1} / {optionsCount}</span>
          ) : (
            <span>{waitTime > 5 ? `等待中 (${waitTime}s)` : '处理中'}</span>
          )}
        </div>
        <div style={{
          fontSize: 18,
          fontWeight: 700,
          color: '#3b82f6',
        }}>
          {Math.round(progress)}%
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.15); }
        }
      `}</style>
    </div>
  );
}
