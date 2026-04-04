import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { StatusPill } from '../components/common/StatusPill';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import { getFutureOsHistory } from '../services/futureOs';
import type { DecisionHistoryRecord } from '../types/api';

function formatDate(value: string) {
  if (!value) {
    return '未知时间';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(
    2,
    '0',
  )}-${String(date.getDate()).padStart(2, '0')} ${String(
    date.getHours(),
  ).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

export function DecisionHistoryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [history, setHistory] = useState<DecisionHistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }

    let active = true;
    setIsLoading(true);
    setError('');

    getFutureOsHistory(user.user_id, 24)
      .then((items) => {
        if (active) {
          setHistory(items);
        }
      })
      .catch((loadError) => {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : '历史记录加载失败');
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [user]);

  const stats = useMemo(() => {
    const totalRuns = history.length;
    const totalBranches = history.reduce(
      (sum, item) => sum + (item.options_count || 0),
      0,
    );
    return {
      totalRuns,
      totalBranches,
      lastRun: history[0]?.created_at || '',
    };
  }, [history]);

  return (
    <AppShell>
      <div className="stack-layout">
        <section className="hero-card decision-history-hero">
          <div className="hero-copy">
            <p className="eyebrow">Future OS Replay</p>
            <h2>把每次推演都沉淀成可回放的未来分支地图。</h2>
            <p>
              历史页现在只保留统一的 Future OS 记录，不再区分旧副本和增强副本。
              每条记录都对应一次 AI 核心上下文构建、多 Agent 分支推演与图谱舞台结果。
            </p>
          </div>
          <div className="metrics-grid compact-grid">
            <MetricCard
              label="推演次数"
              value={String(stats.totalRuns)}
              helper="已保存的决策图谱"
              tone="primary"
            />
            <MetricCard
              label="累计分支"
              value={String(stats.totalBranches)}
              helper="多 Agent 分支总数"
              tone="secondary"
            />
            <MetricCard
              label="最近一次"
              value={stats.lastRun ? formatDate(stats.lastRun).slice(5, 16) : '--'}
              helper="最新回放时间"
              tone="accent"
            />
          </div>
        </section>

        <GlassCard
          title="回放列表"
          subtitle="重新打开任意一次推演，继续查看分支细节或进入平行人生。"
        >
          {isLoading ? (
            <div className="empty-state-block">
              <strong>正在同步历史记录</strong>
              <p>Future OS 正在读取你的决策图谱回放数据。</p>
            </div>
          ) : history.length === 0 ? (
            <div className="empty-state-block">
              <strong>还没有推演记录</strong>
              <p>先去决策副本发起一次问题建模，历史页就会自动出现可回放记录。</p>
              <button
                className="button button-primary"
                onClick={() => navigate('/decision')}
              >
                去发起推演
              </button>
            </div>
          ) : (
            <div className="history-grid">
              {history.map((record) => (
                <article key={record.simulation_id} className="history-card">
                  <div className="module-accent history-accent-primary" />
                  <div className="history-card-body">
                    <div className="history-card-top">
                      <StatusPill tone="primary">Future OS</StatusPill>
                      <span>{formatDate(record.created_at)}</span>
                    </div>
                    <h3>{record.question}</h3>
                    <p>{record.recommendation || '本次推演尚未形成明确推荐文案。'}</p>
                    <div className="history-meta-row">
                      <span>{record.options_count} 个分支</span>
                      <span>{record.simulation_id}</span>
                    </div>
                    <div className="history-card-foot">
                      <button
                        className="button button-primary"
                        onClick={() =>
                          navigate(
                            `/decision/simulation?simulationId=${encodeURIComponent(
                              record.simulation_id,
                            )}`,
                            {
                              state: {
                                mode: 'history',
                                simulationId: record.simulation_id,
                                question: record.question,
                                userId: user?.user_id || '',
                              },
                            },
                          )
                        }
                      >
                        打开回放
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {error ? <div className="form-error">{error}</div> : null}
        </GlassCard>
      </div>
    </AppShell>
  );
}
