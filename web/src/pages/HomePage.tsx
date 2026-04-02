import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { MetricCard } from '../components/common/MetricCard';
import { StatusPill } from '../components/common/StatusPill';
import { AppShell } from '../components/shell/AppShell';
import { featureModules } from '../data/features';
import { useAuth } from '../hooks/useAuth';
import { listConversations } from '../services/chat';
import { getDecisionHistory, getLoraStatus } from '../services/decision';

interface PentagramNode {
  id: string;
  title: string;
  subtitle: string;
  route?: string;
  top: string;
  left: string;
  gradient: [string, string];
  status: 'live' | 'preview' | 'planned';
}

export function HomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [predictionCount, setPredictionCount] = useState(0);
  const [conversationCount, setConversationCount] = useState(0);
  const [loraLoaded, setLoraLoaded] = useState(false);
  const [trainingSamples, setTrainingSamples] = useState(0);

  useEffect(() => {
    if (!user?.user_id) {
      return;
    }

    let active = true;
    Promise.allSettled([
      getDecisionHistory(user.user_id),
      listConversations(user.user_id),
      getLoraStatus(user.user_id),
    ]).then((results) => {
      if (!active) {
        return;
      }

      const [historyResult, chatResult, loraResult] = results;

      if (historyResult.status === 'fulfilled') {
        setPredictionCount(historyResult.value.length);
      }
      if (chatResult.status === 'fulfilled') {
        setConversationCount(chatResult.value.length);
      }
      if (loraResult.status === 'fulfilled') {
        setLoraLoaded(Boolean(loraResult.value.is_loaded));
        setTrainingSamples(Number(loraResult.value.training_data_size || 0));
      }
    });

    return () => {
      active = false;
    };
  }, [user]);

  const pentagramNodes = useMemo<PentagramNode[]>(
    () => [
      {
        id: 'decision',
        title: '决策副本',
        subtitle: '推演入口',
        route: '/decision',
        top: '5%',
        left: '50%',
        gradient: ['#0A59F7', '#6B48FF'],
        status: 'live',
      },
      {
        id: 'history',
        title: '预测历史',
        subtitle: '回访校准',
        route: '/decision/history',
        top: '24%',
        left: '84%',
        gradient: ['#7B61FF', '#9F7BFF'],
        status: 'live',
      },
      {
        id: 'chat',
        title: 'AI 对话',
        subtitle: '实时协作',
        route: '/chat',
        top: '79%',
        left: '70%',
        gradient: ['#4FACFE', '#00F2FE'],
        status: 'live',
      },
      {
        id: 'profile',
        title: '个人中心',
        subtitle: '身份画像',
        route: '/profile',
        top: '79%',
        left: '30%',
        gradient: ['#43C6AC', '#A8E063'],
        status: 'live',
      },
      {
        id: 'knowledge-graph',
        title: '知识星图',
        subtitle: '记忆星空',
        route: '/knowledge-graph',
        top: '24%',
        left: '16%',
        gradient: ['#667EEA', '#764BA2'],
        status: 'live',
      },
    ],
    [],
  );

  return (
    <AppShell
      title="Web 中枢"
      subtitle="把 Harmony 端首页的仪式感主视觉迁到 Web，中间是 AI 核心，周围是能力球体。"
      actions={
        <>
          <button className="button button-secondary" onClick={() => navigate('/chat')}>
            打开 AI 对话
          </button>
          <button className="button button-primary" onClick={() => navigate('/decision')}>
            开始决策副本
          </button>
        </>
      }
    >
      <section className="hero-card pentagram-hero">
        <div className="hero-copy">
          <p className="eyebrow">AI Ritual Interface</p>
          <h2>以 AI 核心为中心，把主要能力组织成“五角法阵”式的首页中枢。</h2>
          <p>
            中心承载智能核心，外圈五个球体分别映射高频功能。视觉上更贴近鸿蒙端的仪式感、
            神秘感和系统中控台气质，交互上仍然保持一键直达真实页面。
          </p>

          <div className="hero-actions">
            <button className="button button-primary" onClick={() => navigate('/decision')}>
              激活决策副本
            </button>
            <button className="button button-ghost" onClick={() => navigate('/modules')}>
              查看全部能力
            </button>
          </div>
        </div>

        <div className="hero-side">
          <div className="pentagram-stage">
            <div className="pentagram-aura pentagram-aura-primary" />
            <div className="pentagram-aura pentagram-aura-secondary" />
            <div className="pentagram-energy-web" aria-hidden="true">
              <svg viewBox="0 0 100 100" className="pentagram-energy-svg">
                <defs>
                  <filter id="pentagramGlow">
                    <feGaussianBlur stdDeviation="1.2" result="coloredBlur" />
                    <feMerge>
                      <feMergeNode in="coloredBlur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>
                <line x1="50" y1="50" x2="50" y2="5" className="energy-line energy-line-primary" />
                <line x1="50" y1="50" x2="84" y2="24" className="energy-line energy-line-secondary" />
                <line x1="50" y1="50" x2="70" y2="79" className="energy-line energy-line-accent" />
                <line x1="50" y1="50" x2="30" y2="79" className="energy-line energy-line-mint" />
                <line x1="50" y1="50" x2="16" y2="24" className="energy-line energy-line-warm" />
              </svg>
            </div>
            <div className="pentagram-ring pentagram-ring-outer" />
            <div className="pentagram-ring pentagram-ring-inner" />
            <div className="pentagram-star" aria-hidden="true">
              <svg viewBox="0 0 100 100" className="pentagram-star-svg">
                <polygon points="50,5 70,79 16,24 84,24 30,79" />
              </svg>
            </div>

            {pentagramNodes.map((node) => (
              <button
                key={node.id}
                className={`pentagram-node is-${node.status}`}
                style={
                  {
                    '--node-top': node.top,
                    '--node-left': node.left,
                    '--node-start': node.gradient[0],
                    '--node-end': node.gradient[1],
                  } as CSSProperties
                }
                onClick={() => node.route && navigate(node.route)}
                type="button"
              >
                <span className="pentagram-node-orbit" />
                <span className="pentagram-node-core">
                  <small>{node.subtitle}</small>
                  <strong>{node.title}</strong>
                </span>
              </button>
            ))}

            <button
              className="pentagram-core"
              onClick={() => navigate('/chat')}
              type="button"
              aria-label="打开 AI 核心"
            >
              <span className="pentagram-core-halo" />
              <span className="pentagram-core-ring pentagram-core-ring-outer" />
              <span className="pentagram-core-ring pentagram-core-ring-inner" />
              <span className="pentagram-core-spark pentagram-core-spark-a" />
              <span className="pentagram-core-spark pentagram-core-spark-b" />
              <span className="pentagram-core-shell">
                <span className="pentagram-core-shell-gloss" />
                <span className="pentagram-core-shell-grid" />
                <span className="pentagram-core-shell-pulse" />
                <small>Central Engine</small>
                <strong>AI 核心</strong>
                <span>感知 / 推演 / 校准</span>
              </span>
            </button>
          </div>
        </div>
      </section>

      <section className="metrics-grid">
        <MetricCard
          label="预测记录"
          value={String(predictionCount)}
          helper="增强决策副本历史"
          tone="primary"
        />
        <MetricCard
          label="对话会话"
          value={String(conversationCount)}
          helper="复用 /ws/chat 与 V4 对话历史"
          tone="secondary"
        />
        <MetricCard
          label="个性模型储备"
          value={loraLoaded ? '已就绪' : '未训练'}
          helper={loraLoaded ? '已保留，当前主链默认仍走云端推演' : '当前仍走云端推演'}
          tone="accent"
        />
        <MetricCard
          label="训练样本"
          value={String(trainingSamples)}
          helper="来自对话与行为数据"
          tone="warning"
        />
      </section>

      <section className="two-column-grid">
        <GlassCard
          title="核心法阵入口"
          subtitle="五个球体都对应真实功能，不是装饰性的静态图。"
        >
          <div className="summary-groups">
            <div>
              <strong>中央 AI 核心</strong>
              <p>作为首页的认知中心，承接对话、推演、追踪与校准的统一入口。</p>
            </div>
            <div>
              <strong>五角功能球</strong>
              <p>决策副本、预测历史、AI 对话、个人中心、知识星图沿法阵分布，形成鸿蒙化主视觉。</p>
            </div>
            <div>
              <strong>视觉方向</strong>
              <p>保留蓝紫高光、玻璃流体感、光晕扩散和中控式结构，而不是传统卡片门户页。</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard title="Web 化原则" subtitle="继续按 Harmony 端的价值判断推进。">
          <ul className="plain-list">
            <li>首页先做品牌感和结构辨识度，让用户一眼知道这是 AI 中枢而不是普通后台。</li>
            <li>功能球必须可点击并直达真实模块，不做只有概念没有落点的展示。</li>
            <li>视觉上延续柔和高光、玻璃卡片、环形能量场和大圆角，不另起一套设计语言。</li>
            <li>后续再继续把决策详情、历史页和能力页的细节往 Harmony 风格拉齐。</li>
          </ul>
        </GlassCard>
      </section>

      <GlassCard
        title="能力地图"
        subtitle="Harmony 端已有功能会分批迁移，先把真实高频链路做扎实，再补其他模块。"
        action={
          <button className="button button-ghost" onClick={() => navigate('/modules')}>
            查看全部
          </button>
        }
      >
        <div className="module-grid">
          {featureModules.map((module) => (
            <article key={module.slug} className="module-card">
              <div
                className="module-accent"
                style={{
                  backgroundImage: `linear-gradient(135deg, ${module.gradient[0]}, ${module.gradient[1]})`,
                }}
              />
              <div className="module-content">
                <div className="module-header">
                  <h3>{module.title}</h3>
                  <StatusPill
                    tone={
                      module.status === 'live'
                        ? 'success'
                        : module.status === 'preview'
                          ? 'primary'
                          : 'warning'
                    }
                  >
                    {module.status === 'live'
                      ? '已上线'
                      : module.status === 'preview'
                        ? '预备迁移'
                        : '规划中'}
                  </StatusPill>
                </div>
                <p>{module.summary}</p>
                {module.route ? (
                  <Link className="text-link" to={module.route}>
                    进入模块
                  </Link>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </GlassCard>
    </AppShell>
  );
}
