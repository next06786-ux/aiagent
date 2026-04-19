import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import '../styles/AbilityIslands.css';

interface Ability {
  id: string;
  name: string;
  route: string;
  description: string;
  position: { x: number; y: number };
  color: string;
}

const abilities: Ability[] = [
  { 
    id: 'ai-core', 
    name: 'AI核心', 
    route: '/chat', 
    description: '智能对话与理解',
    position: { x: 55, y: 45 },
    color: '#3b82f6'
  },
  { 
    id: 'decision', 
    name: '决策副本', 
    route: '/decision', 
    description: '决策模拟与推演',
    position: { x: 40, y: 55 },
    color: '#8b5cf6'
  },
  { 
    id: 'knowledge-graph', 
    name: '知识星图', 
    route: '/knowledge-graph', 
    description: '三维知识网络',
    position: { x: 50, y: 25 },
    color: '#06b6d4'
  },
  { 
    id: 'insights', 
    name: '智慧洞察', 
    route: '/insights', 
    description: '深度分析洞见',
    position: { x: 70, y: 35 },
    color: '#f59e0b'
  },
  { 
    id: 'parallel-life', 
    name: '平行人生', 
    route: '/parallel-life', 
    description: '多维人生模拟',
    position: { x: 80, y: 60 },
    color: '#ec4899'
  },
  { 
    id: 'schedule', 
    name: '智能日程', 
    route: '/smart-schedule', 
    description: '时间智能管理',
    position: { x: 65, y: 70 },
    color: '#10b981'
  },
  { 
    id: 'friends', 
    name: '社交', 
    route: '/friends', 
    description: '智能社交网络',
    position: { x: 25, y: 40 },
    color: '#f43f5e'
  },
  { 
    id: 'tree-hole', 
    name: '树洞', 
    route: '/tree-hole', 
    description: '匿名情感空间',
    position: { x: 15, y: 65 },
    color: '#14b8a6'
  },
  { 
    id: 'meta-agent', 
    name: '元代理', 
    route: '/meta-agent', 
    description: '智能体进化',
    position: { x: 35, y: 75 },
    color: '#6366f1'
  },
  { 
    id: 'learning', 
    name: '学习进度', 
    route: '/learning-progress', 
    description: '知识成长轨迹',
    position: { x: 75, y: 20 },
    color: '#eab308'
  },
];

export function AbilityIslandsPage() {
  const navigate = useNavigate();
  const [selectedAbility, setSelectedAbility] = useState<string | null>(null);
  const [hoveredAbility, setHoveredAbility] = useState<string | null>(null);

  const handleMarkerClick = (abilityId: string) => {
    setSelectedAbility(selectedAbility === abilityId ? null : abilityId);
  };

  const handleAbilityNavigate = (route: string) => {
    console.log('Navigating to:', route);
    navigate(route);
  };

  const selectedAbilityData = abilities.find(a => a.id === selectedAbility);

  return (
    <AppShell>
      <div className="ability-map-container">
        <div className="map-header">
          <h1 className="map-title">能力地图</h1>
          <p className="map-subtitle">探索你的智能世界</p>
        </div>

        <div className="map-scene">
          {/* 地图背景 */}
          <div className="map-background">
            {/* 网格 */}
            <div className="map-grid"></div>
            
            {/* 地形层 */}
            <div className="terrain-layer">
              <div className="terrain-patch terrain-1"></div>
              <div className="terrain-patch terrain-2"></div>
              <div className="terrain-patch terrain-3"></div>
              <div className="terrain-patch terrain-4"></div>
              <div className="terrain-patch terrain-5"></div>
            </div>

            {/* 道路 */}
            <svg className="map-roads" viewBox="0 0 100 100" preserveAspectRatio="none">
              {/* 主干道 */}
              <path d="M 25 40 Q 40 45 55 45" stroke="rgba(255,255,255,0.5)" strokeWidth="0.4" fill="none" strokeLinecap="round" />
              <path d="M 55 45 Q 60 40 70 35" stroke="rgba(255,255,255,0.5)" strokeWidth="0.4" fill="none" strokeLinecap="round" />
              <path d="M 55 45 Q 50 50 40 55" stroke="rgba(255,255,255,0.5)" strokeWidth="0.4" fill="none" strokeLinecap="round" />
              
              {/* 支路 */}
              <path d="M 50 25 Q 60 30 70 35" stroke="rgba(255,255,255,0.4)" strokeWidth="0.3" fill="none" strokeLinecap="round" />
              <path d="M 70 35 Q 75 25 75 20" stroke="rgba(255,255,255,0.4)" strokeWidth="0.3" fill="none" strokeLinecap="round" />
              <path d="M 40 55 Q 35 65 35 75" stroke="rgba(255,255,255,0.4)" strokeWidth="0.3" fill="none" strokeLinecap="round" />
              <path d="M 40 55 Q 30 60 15 65" stroke="rgba(255,255,255,0.4)" strokeWidth="0.3" fill="none" strokeLinecap="round" />
              <path d="M 55 45 Q 70 55 80 60" stroke="rgba(255,255,255,0.4)" strokeWidth="0.3" fill="none" strokeLinecap="round" />
              <path d="M 80 60 Q 75 65 65 70" stroke="rgba(255,255,255,0.4)" strokeWidth="0.3" fill="none" strokeLinecap="round" />
              
              {/* 小路 */}
              <path d="M 25 40 Q 20 50 15 65" stroke="rgba(255,255,255,0.3)" strokeWidth="0.2" fill="none" strokeLinecap="round" strokeDasharray="1,1" />
              <path d="M 50 25 Q 52 35 55 45" stroke="rgba(255,255,255,0.3)" strokeWidth="0.2" fill="none" strokeLinecap="round" strokeDasharray="1,1" />
            </svg>

            {/* 装饰云朵 */}
            <div className="map-cloud cloud-1">☁️</div>
            <div className="map-cloud cloud-2">☁️</div>
            <div className="map-cloud cloud-3">☁️</div>
          </div>

          {/* 能力标记点 */}
          <div className="markers-layer">
            {abilities.map((ability) => (
              <div
                key={ability.id}
                className={`ability-marker ${selectedAbility === ability.id ? 'marker-selected' : ''} ${hoveredAbility === ability.id ? 'marker-hovered' : ''}`}
                style={{
                  left: `${ability.position.x}%`,
                  top: `${ability.position.y}%`,
                }}
                onClick={() => handleMarkerClick(ability.id)}
                onMouseEnter={() => setHoveredAbility(ability.id)}
                onMouseLeave={() => setHoveredAbility(null)}
              >
                {/* 标记点脉冲效果 */}
                <div className="marker-pulse"></div>
                
                {/* 标记点主体 */}
                <div className="marker-pin">
                  <div className="pin-dot"></div>
                </div>

                {/* 能力卡片预览 */}
                <div className="ability-preview-card">
                  <div className="preview-image" style={{ background: `linear-gradient(135deg, ${ability.color}15 0%, ${ability.color}30 100%)` }}>
                    <div className="preview-content">
                      <div className="preview-title">{ability.name}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 选中的能力卡片 */}
          {selectedAbilityData && (
            <div 
              className="ability-detail-card"
              style={{
                left: `${selectedAbilityData.position.x}%`,
                top: `${selectedAbilityData.position.y}%`,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="card-content">
                <div className="card-header">
                  <div className="card-color-badge" style={{ background: selectedAbilityData.color }}></div>
                  <div className="card-title-section">
                    <h3 className="card-title">{selectedAbilityData.name}</h3>
                    <p className="card-description">{selectedAbilityData.description}</p>
                  </div>
                  <button 
                    className="card-close"
                    onClick={() => setSelectedAbility(null)}
                  >
                    ✕
                  </button>
                </div>
                <button 
                  className="card-action-btn"
                  style={{ background: `linear-gradient(135deg, ${selectedAbilityData.color} 0%, ${selectedAbilityData.color}dd 100%)` }}
                  onClick={() => handleAbilityNavigate(selectedAbilityData.route)}
                >
                  进入体验 →
                </button>
              </div>
              <div className="card-pointer"></div>
            </div>
          )}
        </div>

        {/* 提示信息 */}
        <div className="map-hint">
          <p>📍 点击地图标记探索能力</p>
        </div>
      </div>
    </AppShell>
  );
}
