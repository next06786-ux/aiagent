import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import { completeParallelLifeBranch } from '../services/futureOs';
import type {
  ParallelLifeChoiceOption,
  ParallelLifeCompletionResult,
  ParallelLifeScenario,
} from '../types/api';

type GamePhase = 'empty' | 'intro' | 'playing' | 'result';

interface Stats {
  emotion: number;
  finance: number;
  social: number;
  health: number;
  growth: number;
  confidence: number;
  stress: number;
}

const INITIAL_STATS: Stats = {
  emotion: 50,
  finance: 50,
  social: 50,
  health: 50,
  growth: 50,
  confidence: 50,
  stress: 30,
};

const STAT_META: Array<{ key: keyof Stats; label: string; tone: string }> = [
  { key: 'emotion', label: '情绪', tone: 'primary' },
  { key: 'finance', label: '财务', tone: 'warning' },
  { key: 'social', label: '社交', tone: 'secondary' },
  { key: 'health', label: '健康', tone: 'success' },
  { key: 'growth', label: '成长', tone: 'accent' },
  { key: 'confidence', label: '自信', tone: 'primary' },
  { key: 'stress', label: '压力', tone: 'warning' },
];

function clamp(value: number) {
  return Math.max(0, Math.min(100, value));
}

function parseScenarioFromState(state: unknown): ParallelLifeScenario | null {
  const routeState = state as { scenario?: ParallelLifeScenario } | null;
  return routeState?.scenario || null;
}

function pickEnding(scenario: ParallelLifeScenario, stats: Stats) {
  if (stats.growth >= 60 && stats.confidence >= 60 && stats.stress <= 55) {
    return scenario.endings[0] || null;
  }
  return scenario.endings[1] || scenario.endings[0] || null;
}

export default function ParallelLifePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const scenario = useMemo(() => parseScenarioFromState(location.state), [location.state]);
  const [phase, setPhase] = useState<GamePhase>(scenario ? 'intro' : 'empty');
  const [currentNodeId, setCurrentNodeId] = useState('');
  const [stats, setStats] = useState<Stats>(INITIAL_STATS);
  const [freeText, setFreeText] = useState('');
  const [emotionFeedback, setEmotionFeedback] = useState('');
  const [choices, setChoices] = useState<Array<Record<string, unknown>>>([]);
  const [completion, setCompletion] = useState<ParallelLifeCompletionResult | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [countdown, setCountdown] = useState(20);
  const timerRef = useRef<number | null>(null);
  const nodeStartRef = useRef<number>(0);

  const currentNode = useMemo(() => {
    if (!scenario || !currentNodeId) {
      return null;
    }
    return scenario.nodes.find((item) => item.id === currentNodeId) || null;
  }, [currentNodeId, scenario]);

  const ending = useMemo(
    () => (scenario ? pickEnding(scenario, stats) : null),
    [scenario, stats],
  );

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!currentNode || currentNode.type !== 'choice' || phase !== 'playing') {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    setCountdown(20);
    nodeStartRef.current = Date.now();

    timerRef.current = window.setInterval(() => {
      setCountdown((value) => {
        if (value <= 1) {
          if (timerRef.current) {
            window.clearInterval(timerRef.current);
            timerRef.current = null;
          }
          if (currentNode.options[0]) {
            void handleChoice(currentNode.options[0]);
          }
          return 20;
        }
        return value - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [currentNode, phase]);

  function startScenario() {
    if (!scenario || scenario.nodes.length === 0) {
      return;
    }

    setStats(INITIAL_STATS);
    setChoices([]);
    setCompletion(null);
    setFreeText('');
    setEmotionFeedback('');
    setCurrentNodeId(scenario.nodes[0].id);
    nodeStartRef.current = Date.now();
    setPhase('playing');
  }

  async function handleChoice(option: ParallelLifeChoiceOption) {
    if (!currentNode || !scenario) {
      return;
    }

    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setChoices((current) => [
      ...current,
      {
        node_id: currentNode.id,
        option_id: option.id,
        choice_time_ms: Date.now() - nodeStartRef.current,
      },
    ]);

    setStats((current) => ({
      emotion: clamp(current.emotion + (option.delta.emotion || 0)),
      finance: clamp(current.finance + (option.delta.finance || 0)),
      social: clamp(current.social + (option.delta.social || 0)),
      health: clamp(current.health + (option.delta.health || 0)),
      growth: clamp(current.growth + (option.delta.growth || 0)),
      confidence: clamp(current.confidence + (option.delta.confidence || 0)),
      stress: clamp(current.stress + (option.delta.stress || 0)),
    }));

    if (option.next === 'ending' || !scenario.nodes.find((item) => item.id === option.next)) {
      await finishScenario();
      return;
    }

    setCurrentNodeId(option.next);
    nodeStartRef.current = Date.now();
  }

  async function handleFreeInputSubmit() {
    if (!currentNode || !scenario) {
      return;
    }

    setChoices((current) => [
      ...current,
      {
        node_id: currentNode.id,
        option_id: 'free_input',
        choice_time_ms: Date.now() - nodeStartRef.current,
      },
    ]);

    if (!currentNode.next || currentNode.next === 'ending') {
      await finishScenario();
      return;
    }

    setCurrentNodeId(currentNode.next);
    nodeStartRef.current = Date.now();
  }

  async function finishScenario() {
    if (!scenario || !user?.user_id) {
      setPhase('result');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const result = await completeParallelLifeBranch({
        user_id: user.user_id,
        scenario_id: scenario.scenario_id,
        simulation_id: scenario.simulation_id,
        branch_id: scenario.branch_id,
        final_stats: { ...stats },
        choices,
        emotion_feedback: emotionFeedback,
        free_text: freeText,
      });
      setCompletion(result);
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : '平行人生结果提交失败',
      );
    } finally {
      setIsSubmitting(false);
      setPhase('result');
    }
  }

  return (
    <AppShell
      actions={
        <button className="button button-ghost" onClick={() => navigate(-1)}>
          返回
        </button>
      }
    >
      <div className="stack-layout">
        {phase === 'empty' || !scenario ? (
          <GlassCard
            title="等待分支注入"
            subtitle="平行人生现在优先由决策图谱舞台发起，不再单独承担主入口。"
          >
            <div className="empty-state-block">
              <strong>还没有可体验的分支</strong>
              <p>
                请先在决策图谱舞台里选择一个分支，再把它送入平行人生。这样采集到的行为信号才能精确回写到同一条路径。
              </p>
              <button
                className="button button-primary"
                onClick={() => navigate('/decision')}
              >
                去决策副本
              </button>
            </div>
          </GlassCard>
        ) : phase === 'intro' ? (
          <>
            <section className="hero-card">
              <div className="hero-copy">
                <p className="eyebrow">Parallel Life Branch</p>
                <h2>{scenario.title}</h2>
                <p>{scenario.intro}</p>
              </div>
              <div className="metrics-grid compact-grid">
                <MetricCard
                  label="分支策略"
                  value={scenario.subtitle || '当前分支'}
                  helper="来自决策图谱舞台"
                  tone="primary"
                />
                <MetricCard
                  label="剧情节点"
                  value={String(scenario.nodes.length)}
                  helper="用于行为采集"
                  tone="secondary"
                />
                <MetricCard
                  label="来源推演"
                  value={scenario.simulation_id.slice(0, 12)}
                  helper="回写到同一条记录"
                  tone="accent"
                />
              </div>
            </section>

            <GlassCard
              title="玩法说明"
              subtitle="你会顺着这条分支做出几次取舍，系统会记录你的节奏、偏好和反应。"
            >
              <div className="chip-cloud">
                {(scenario.branch_context?.key_people || []).map((item) => (
                  <span key={item} className="graph-chip">
                    {item}
                  </span>
                ))}
              </div>
              <div className="composer-actions">
                <button className="button button-primary" onClick={startScenario}>
                  开始体验
                </button>
                <button className="button button-ghost" onClick={() => navigate(-1)}>
                  回到图谱
                </button>
              </div>
            </GlassCard>
          </>
        ) : phase === 'playing' ? (
          <>
            <div className="metrics-grid">
              {STAT_META.map((item) => (
                <MetricCard
                  key={item.key}
                  label={item.label}
                  value={String(stats[item.key])}
                  helper={item.key === 'stress' ? '越低越稳' : '越高越强'}
                  tone={item.tone as never}
                />
              ))}
            </div>

            {currentNode ? (
              <GlassCard
                title={currentNode.type === 'choice' ? '做出你的选择' : '写下真实想法'}
                subtitle={
                  currentNode.type === 'choice'
                    ? `倒计时 ${countdown} 秒，系统会记录你的决策速度`
                    : '自由输入会作为分支反思信号回写到画像'
                }
              >
                <div className="stack-layout compact-stack">
                  <p className="parallel-scene-copy">{currentNode.text}</p>

                  {currentNode.type === 'choice' ? (
                    <div className="parallel-choice-list">
                      {currentNode.options.map((option) => (
                        <button
                          key={option.id}
                          className="parallel-choice-card"
                          onClick={() => void handleChoice(option)}
                        >
                          <strong>{option.text}</strong>
                          <span>{option.sub}</span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="form-stack">
                      <textarea
                        className="textarea"
                        rows={5}
                        value={freeText}
                        onChange={(event) => setFreeText(event.target.value)}
                        placeholder="写下这条路真正让你担心和想守住的东西。"
                      />
                      <button
                        className="button button-primary"
                        onClick={() => void handleFreeInputSubmit()}
                      >
                        继续
                      </button>
                    </div>
                  )}
                </div>
              </GlassCard>
            ) : null}
          </>
        ) : (
          <>
            <section className="hero-card">
              <div className="hero-copy">
                <p className="eyebrow">Result Sync</p>
                <h2>{ending?.title || '本轮平行人生已结束'}</h2>
                <p>{ending?.text || '这次体验已经完成，行为信号已准备回写到 Future OS。'}</p>
                {completion?.next_hint ? <p>{completion.next_hint}</p> : null}
              </div>
              <div className="metrics-grid compact-grid">
                <MetricCard
                  label="成长"
                  value={String(stats.growth)}
                  helper="最终状态"
                  tone="primary"
                />
                <MetricCard
                  label="执行稳定"
                  value={
                    completion
                      ? `${Math.round(
                          Number(completion.updated_profile.execution_stability) * 100,
                        )}%`
                      : '--'
                  }
                  helper="回写后的画像"
                  tone="secondary"
                />
                <MetricCard
                  label="风险承受"
                  value={
                    completion
                      ? `${Math.round(
                          Number(completion.updated_profile.risk_tolerance) * 100,
                        )}%`
                      : '--'
                  }
                  helper="行为校准后"
                  tone="accent"
                />
              </div>
            </section>

            <GlassCard
              title="这轮体验给你的感受"
              subtitle="可选，把主观感受一起回写给 AI 核心。"
            >
              <div className="form-stack">
                <textarea
                  className="textarea"
                  rows={4}
                  value={emotionFeedback}
                  onChange={(event) => setEmotionFeedback(event.target.value)}
                  placeholder="例如：这条路让我兴奋，但现实阻力也比我想象得更大。"
                />
                <div className="composer-actions">
                  <button
                    className="button button-secondary"
                    onClick={() => navigate('/decision/simulation', {
                      state: {
                        mode: 'history',
                        simulationId: scenario.simulation_id,
                        question: scenario.source_question,
                        userId: user?.user_id || '',
                      },
                    })}
                  >
                    回到决策图谱
                  </button>
                  <button
                    className="button button-primary"
                    onClick={startScenario}
                    disabled={isSubmitting}
                  >
                    再体验一次
                  </button>
                </div>
              </div>
            </GlassCard>
          </>
        )}

        {error ? <div className="form-error">{error}</div> : null}
      </div>
    </AppShell>
  );
}
