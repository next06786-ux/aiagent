import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { StatusPill } from '../components/common/StatusPill';
import { AppShell } from '../components/shell/AppShell';
import { useAuth } from '../hooks/useAuth';
import { getDecisionHistory, listLegacyDungeons } from '../services/decision';
import type { DecisionHistoryRecord, LegacyDungeonRecord } from '../types/api';

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
  const [legacy, setLegacy] = useState<LegacyDungeonRecord[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }

    Promise.allSettled([
      getDecisionHistory(user.user_id),
      listLegacyDungeons(user.user_id),
    ]).then((results) => {
      const [enhancedResult, legacyResult] = results;

      if (enhancedResult.status === 'fulfilled') {
        setHistory(enhancedResult.value);
      }
      if (legacyResult.status === 'fulfilled') {
        setLegacy(legacyResult.value);
      }
      if (enhancedResult.status === 'rejected' && legacyResult.status === 'rejected') {
        setError('历史记录加载失败，请稍后重试。');
      }
    });
  }, [user]);

  const stats = useMemo(() => {
    const totalEnhanced = history.length;
    const totalLegacy = legacy.length;
    const totalOptions = history.reduce((sum, item) => sum + item.options_count, 0);
    return { totalEnhanced, totalLegacy, totalOptions };
  }, [history, legacy]);

  return (
    <AppShell
      title="预测历史"
      subtitle="增强版历史回放优先保留，Legacy 副本入口继续兼容，方便你对比不同阶段的推演产物。"
    >
      <div className="stack-layout">
        <section className="hero-card decision-history-hero">
          <div className="hero-copy">
            <p className="eyebrow">Replay Center</p>
            <h2>把每一次推演当成可以回放、校准和复盘的长期资产。</h2>
            <p>
              这里会同时保存增强版推演记录与 Legacy 副本数据。前者更完整，后者用于兼容旧链路，
              两者都能继续进入详情页查看。
            </p>
          </div>
          <div className="hero-side">
            <div className="metrics-grid compact-grid">
              <MetricCard label="增强推演" value={String(stats.totalEnhanced)} helper="含 prediction trace" tone="primary" />
              <MetricCard label="Legacy 副本" value={String(stats.totalLegacy)} helper="兼容旧链路" tone="warning" />
              <MetricCard label="累计选项" value={String(stats.totalOptions)} helper="增强版记录内统计" tone="secondary" />
            </div>
          </div>
        </section>

        <GlassCard
          title="增强版推演记录"
          subtitle="支持 prediction trace、verifiability report 和 follow-up summary。"
        >
          {history.length === 0 ? (
            <div className="empty-state-block">
              <strong>还没有增强版记录</strong>
              <p>完成一次新的决策推演后，这里会出现可回放的完整记录。</p>
            </div>
          ) : (
            <div className="history-grid">
              {history.map((record) => (
                <article key={record.session_id} className="history-card">
                  <div className="module-accent history-accent-primary" />
                  <div className="history-card-body">
                    <div className="history-card-top">
                      <StatusPill tone="primary">增强版</StatusPill>
                      <span>{formatDate(record.created_at)}</span>
                    </div>
                    <h3>{record.question}</h3>
                    <p>{record.recommendation || '暂无 recommendation 文本'}</p>
                    <div className="history-meta-row">
                      <span>{record.options_count} 个选项</span>
                      <span>session: {record.session_id}</span>
                    </div>
                    <div className="history-card-foot">
                      <button
                        className="button button-primary"
                        onClick={() =>
                          navigate(
                            `/decision/simulation?simulationId=${encodeURIComponent(
                              record.session_id,
                            )}`,
                            {
                              state: {
                                mode: 'history',
                                simulationId: record.session_id,
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
        </GlassCard>

        <GlassCard title="Legacy 副本记录" subtitle="用于兼容 create-dungeon 时代的旧副本数据。">
          {legacy.length === 0 ? (
            <div className="empty-state-block">
              <strong>还没有 Legacy 记录</strong>
              <p>如果旧接口生成过副本，这里会自动聚合出来。</p>
            </div>
          ) : (
            <div className="history-grid">
              {legacy.map((record) => (
                <article key={record.dungeon_id} className="history-card">
                  <div className="module-accent history-accent-warning" />
                  <div className="history-card-body">
                    <div className="history-card-top">
                      <StatusPill tone="warning">Legacy</StatusPill>
                      <span>{formatDate(record.created_at)}</span>
                    </div>
                    <h3>{record.title}</h3>
                    <p>{record.description || '暂无描述'}</p>
                    <div className="history-meta-row">
                      <span>{record.options_count} 个选项</span>
                      <span>dungeon: {record.dungeon_id}</span>
                    </div>
                    <div className="history-card-foot">
                      <button
                        className="button button-secondary"
                        onClick={() =>
                          navigate(
                            `/decision/simulation?dungeonId=${encodeURIComponent(
                              record.dungeon_id,
                            )}`,
                            {
                              state: {
                                mode: 'legacy',
                                dungeonId: record.dungeon_id,
                                question: record.title,
                                userId: user?.user_id || '',
                              },
                            },
                          )
                        }
                      >
                        查看副本
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
