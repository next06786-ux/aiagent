/**
 * 决策人格头像组件
 * 为每个人格提供独特的视觉标识
 */

interface PersonaAvatarProps {
  personaId: string;
  size?: number;
}

export function PersonaAvatar({ personaId, size = 60 }: PersonaAvatarProps) {
  const getPersonaIcon = () => {
    switch (personaId) {
      case 'rational_analyst':
        // 理性分析师 - 眼镜和图表
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="rational-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#0A59F7" />
                <stop offset="100%" stopColor="#6B48FF" />
              </linearGradient>
            </defs>
            {/* 头部轮廓 */}
            <circle cx="50" cy="40" r="25" fill="url(#rational-grad)" opacity="0.15" />
            {/* 眼镜 */}
            <ellipse cx="40" cy="38" rx="8" ry="6" fill="none" stroke="url(#rational-grad)" strokeWidth="2.5" />
            <ellipse cx="60" cy="38" rx="8" ry="6" fill="none" stroke="url(#rational-grad)" strokeWidth="2.5" />
            <line x1="48" y1="38" x2="52" y2="38" stroke="url(#rational-grad)" strokeWidth="2.5" />
            {/* 图表符号 */}
            <path d="M 35 70 L 40 60 L 50 65 L 60 55 L 65 60" fill="none" stroke="url(#rational-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="40" cy="60" r="2" fill="url(#rational-grad)" />
            <circle cx="50" cy="65" r="2" fill="url(#rational-grad)" />
            <circle cx="60" cy="55" r="2" fill="url(#rational-grad)" />
          </svg>
        );

      case 'adventurer':
        // 冒险家 - 山峰和指南针
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="adventurer-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FF6B35" />
                <stop offset="100%" stopColor="#F7931E" />
              </linearGradient>
            </defs>
            {/* 头部轮廓 */}
            <circle cx="50" cy="35" r="22" fill="url(#adventurer-grad)" opacity="0.15" />
            {/* 帽子 */}
            <path d="M 30 35 Q 50 20 70 35" fill="none" stroke="url(#adventurer-grad)" strokeWidth="2.5" strokeLinecap="round" />
            <line x1="30" y1="35" x2="70" y2="35" stroke="url(#adventurer-grad)" strokeWidth="2" />
            {/* 山峰 */}
            <path d="M 30 75 L 40 60 L 50 70 L 60 55 L 70 75" fill="none" stroke="url(#adventurer-grad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            {/* 旗帜 */}
            <line x1="60" y1="55" x2="60" y2="48" stroke="url(#adventurer-grad)" strokeWidth="1.5" />
            <path d="M 60 48 L 68 51 L 60 54" fill="url(#adventurer-grad)" />
          </svg>
        );

      case 'pragmatist':
        // 实用主义者 - 工具和齿轮
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="pragmatist-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10B981" />
                <stop offset="100%" stopColor="#059669" />
              </linearGradient>
            </defs>
            {/* 头部轮廓 */}
            <circle cx="50" cy="38" r="24" fill="url(#pragmatist-grad)" opacity="0.15" />
            {/* 安全帽 */}
            <path d="M 28 38 Q 50 25 72 38" fill="none" stroke="url(#pragmatist-grad)" strokeWidth="2.5" strokeLinecap="round" />
            <ellipse cx="50" cy="38" rx="22" ry="4" fill="url(#pragmatist-grad)" opacity="0.3" />
            {/* 齿轮 */}
            <circle cx="50" cy="68" r="10" fill="none" stroke="url(#pragmatist-grad)" strokeWidth="2" />
            <circle cx="50" cy="68" r="5" fill="url(#pragmatist-grad)" opacity="0.3" />
            {/* 齿轮齿 */}
            {[0, 60, 120, 180, 240, 300].map((angle, i) => {
              const rad = (angle * Math.PI) / 180;
              const x1 = 50 + 10 * Math.cos(rad);
              const y1 = 68 + 10 * Math.sin(rad);
              const x2 = 50 + 13 * Math.cos(rad);
              const y2 = 68 + 13 * Math.sin(rad);
              return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="url(#pragmatist-grad)" strokeWidth="2" />;
            })}
          </svg>
        );

      case 'conservative':
        // 保守派 - 盾牌和锁
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="conservative-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#64748B" />
                <stop offset="100%" stopColor="#475569" />
              </linearGradient>
            </defs>
            {/* 头部轮廓 */}
            <circle cx="50" cy="38" r="24" fill="url(#conservative-grad)" opacity="0.15" />
            {/* 领带 */}
            <path d="M 50 50 L 45 65 L 50 75 L 55 65 Z" fill="url(#conservative-grad)" opacity="0.4" />
            {/* 盾牌 */}
            <path d="M 50 25 Q 35 30 35 45 Q 35 60 50 70 Q 65 60 65 45 Q 65 30 50 25 Z" fill="none" stroke="url(#conservative-grad)" strokeWidth="2.5" />
            <path d="M 50 30 L 50 65" stroke="url(#conservative-grad)" strokeWidth="1.5" opacity="0.5" />
            <path d="M 40 45 L 60 45" stroke="url(#conservative-grad)" strokeWidth="1.5" opacity="0.5" />
          </svg>
        );

      case 'emotional_intuitive':
        // 情感直觉者 - 心形和波浪
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="emotional-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#EC4899" />
                <stop offset="100%" stopColor="#F43F5E" />
              </linearGradient>
            </defs>
            {/* 头部轮廓 */}
            <circle cx="50" cy="38" r="24" fill="url(#emotional-grad)" opacity="0.15" />
            {/* 眼睛 */}
            <circle cx="42" cy="36" r="3" fill="url(#emotional-grad)" />
            <circle cx="58" cy="36" r="3" fill="url(#emotional-grad)" />
            {/* 微笑 */}
            <path d="M 40 45 Q 50 50 60 45" fill="none" stroke="url(#emotional-grad)" strokeWidth="2" strokeLinecap="round" />
            {/* 心形 */}
            <path d="M 50 75 C 50 75 35 65 35 55 C 35 50 38 47 42 47 C 46 47 50 50 50 50 C 50 50 54 47 58 47 C 62 47 65 50 65 55 C 65 65 50 75 50 75 Z" fill="url(#emotional-grad)" opacity="0.6" />
          </svg>
        );

      case 'social_navigator':
        // 社交导向者 - 人群和连接
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="social-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#6366F1" />
              </linearGradient>
            </defs>
            {/* 中心人物 */}
            <circle cx="50" cy="40" r="12" fill="url(#social-grad)" opacity="0.3" />
            <circle cx="50" cy="40" r="8" fill="url(#social-grad)" opacity="0.5" />
            {/* 周围人物 */}
            <circle cx="30" cy="35" r="6" fill="url(#social-grad)" opacity="0.25" />
            <circle cx="70" cy="35" r="6" fill="url(#social-grad)" opacity="0.25" />
            <circle cx="35" cy="55" r="6" fill="url(#social-grad)" opacity="0.25" />
            <circle cx="65" cy="55" r="6" fill="url(#social-grad)" opacity="0.25" />
            {/* 连接线 */}
            <line x1="50" y1="40" x2="30" y2="35" stroke="url(#social-grad)" strokeWidth="1.5" opacity="0.4" />
            <line x1="50" y1="40" x2="70" y2="35" stroke="url(#social-grad)" strokeWidth="1.5" opacity="0.4" />
            <line x1="50" y1="40" x2="35" y2="55" stroke="url(#social-grad)" strokeWidth="1.5" opacity="0.4" />
            <line x1="50" y1="40" x2="65" y2="55" stroke="url(#social-grad)" strokeWidth="1.5" opacity="0.4" />
            {/* 对话气泡 */}
            <circle cx="50" cy="72" r="8" fill="none" stroke="url(#social-grad)" strokeWidth="2" />
            <circle cx="46" cy="70" r="1.5" fill="url(#social-grad)" />
            <circle cx="50" cy="70" r="1.5" fill="url(#social-grad)" />
            <circle cx="54" cy="70" r="1.5" fill="url(#social-grad)" />
          </svg>
        );

      case 'innovator':
        // 创新者 - 灯泡和火花
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="innovator-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FBBF24" />
                <stop offset="100%" stopColor="#F59E0B" />
              </linearGradient>
            </defs>
            {/* 头部轮廓 */}
            <circle cx="50" cy="38" r="24" fill="url(#innovator-grad)" opacity="0.15" />
            {/* 灯泡 */}
            <circle cx="50" cy="45" r="15" fill="none" stroke="url(#innovator-grad)" strokeWidth="2.5" />
            <path d="M 42 58 L 42 65 L 58 65 L 58 58" fill="none" stroke="url(#innovator-grad)" strokeWidth="2" strokeLinecap="round" />
            <line x1="45" y1="68" x2="55" y2="68" stroke="url(#innovator-grad)" strokeWidth="2.5" strokeLinecap="round" />
            {/* 灯丝 */}
            <path d="M 50 38 Q 45 45 50 52" fill="none" stroke="url(#innovator-grad)" strokeWidth="1.5" />
            {/* 火花 */}
            <path d="M 35 30 L 38 33 L 35 36" fill="none" stroke="url(#innovator-grad)" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M 65 30 L 62 33 L 65 36" fill="none" stroke="url(#innovator-grad)" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M 50 20 L 50 25" stroke="url(#innovator-grad)" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        );

      default:
        // 默认图标 - 简单的人形
        return (
          <svg viewBox="0 0 100 100" width={size} height={size}>
            <defs>
              <linearGradient id="default-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#94A3B8" />
                <stop offset="100%" stopColor="#64748B" />
              </linearGradient>
            </defs>
            <circle cx="50" cy="35" r="15" fill="url(#default-grad)" opacity="0.3" />
            <ellipse cx="50" cy="65" rx="20" ry="15" fill="url(#default-grad)" opacity="0.3" />
          </svg>
        );
    }
  };

  return (
    <div style={{
      width: size,
      height: size,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      {getPersonaIcon()}
    </div>
  );
}
