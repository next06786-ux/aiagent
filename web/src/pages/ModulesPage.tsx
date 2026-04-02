import { Link } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';
import { StatusPill } from '../components/common/StatusPill';
import { AppShell } from '../components/shell/AppShell';
import { featureModules } from '../data/features';

const groups = ['核心闭环', '图谱与洞察', '代理与成长'] as const;

export function ModulesPage() {
  return (
    <AppShell
      title="能力地图"
      subtitle="Web 端功能迁移清单，哪些已经可用，哪些仍在排期，一目了然。"
    >
      <div className="stack-layout">
        {groups.map((group) => (
          <GlassCard
            key={group}
            title={group}
            subtitle="按实际价值和迁移难度排序推进"
          >
            <div className="module-grid">
              {featureModules
                .filter((module) => module.group === group)
                .map((module) => (
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
                      <div className="module-footnote">
                        {module.route ? (
                          <Link className="text-link" to={module.route}>
                            打开当前 Web 版本
                          </Link>
                        ) : (
                          <span>该模块后续按 Harmony 页面逐步拆分迁移。</span>
                        )}
                      </div>
                    </div>
                  </article>
                ))}
            </div>
          </GlassCard>
        ))}
      </div>
    </AppShell>
  );
}
