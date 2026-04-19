import { useState } from 'react';
import { GlassCard } from '../common/GlassCard';
import { 
  drawCard, 
  submitChoice, 
  getProfile 
} from '../../services/parallelLifeService';
import './TarotGame.css';

type GamePhase = 'intro' | 'drawing' | 'choosing' | 'result';

interface CardData {
  card: string;
  card_key: string;
  dimension: string;
  dimension_key: string;
  scenario: string;
  options: Array<{
    id: string;
    text: string;
    tendency: 'left' | 'right';
  }>;
  icon?: string;
}

interface ProfileData {
  dimensions: Record<string, { value: number; count: number; confidence: number }>;
  patterns: string[];
  confidence: number;
  total_choices: number;
}

export function TarotGame() {
  const [phase, setPhase] = useState<GamePhase>('intro');
  const [currentCard, setCurrentCard] = useState<CardData | null>(null);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [progress, setProgress] = useState(0);
  const [isDrawing, setIsDrawing] = useState(false);
  const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || '2c2139f7-bab4-483d-9882-ae83ce8734cd';

  const handleStart = () => {
    setPhase('drawing');
    setTimeout(() => handleDrawCard(), 800);
  };

  const handleDrawCard = async () => {
    setIsDrawing(true);
    try {
      const data = await drawCard(userId);
      // 等待抽牌动画完成
      setTimeout(() => {
        setCurrentCard(data);
        setIsDrawing(false);
        setPhase('choosing');
      }, 2500);
    } catch (error) {
      console.error('抽牌失败:', error);
      setIsDrawing(false);
    }
  };

  const handleChoice = async (option: { id: string; text: string; tendency: 'left' | 'right' }) => {
    if (!currentCard) return;

    try {
      await submitChoice(
        userId,
        currentCard.card,
        currentCard.card_key,
        currentCard.dimension,
        currentCard.dimension_key,
        currentCard.scenario,
        option.text,
        option.tendency
      );

      setProgress(prev => prev + (100 / 21));

      if (progress + (100 / 21) >= 100) {
        const profileData = await getProfile(userId);
        setProfile(profileData);
        setPhase('result');
      } else {
        setPhase('drawing');
        setTimeout(() => handleDrawCard(), 800);
      }
    } catch (error) {
      console.error('提交选择失败:', error);
    }
  };

  const handleFinishEarly = async () => {
    try {
      const profileData = await getProfile(userId);
      setProfile(profileData);
      setPhase('result');
    } catch (error) {
      console.error('提前结束失败:', error);
    }
  };

  const handleRestart = () => {
    setProgress(0);
    setCurrentCard(null);
    setProfile(null);
    setPhase('intro');
  };

  return (
    <div className="tarot-game-container">
      {/* 星空背景 */}
      <div className="tarot-starfield">
        {[...Array(100)].map((_, i) => (
          <div
            key={i}
            className="tarot-star"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 3}s`,
            }}
          />
        ))}
      </div>

      <div className="tarot-content">
        {/* 介绍阶段 */}
        {phase === 'intro' && (
          <div className="tarot-intro">
            <h1 className="tarot-main-title">
              今日运势
              <br />
              <span className="tarot-main-title-sub">AI星座塔罗占卜</span>
            </h1>
            <p className="tarot-intro-badge">
              添加生日信息解读更准确
            </p>

            <div className="tarot-card-preview">
              <div className="tarot-card-back-large">
                <div className="tarot-card-glow" />
                <div className="tarot-card-pattern-large">
                  <svg viewBox="0 0 200 300" className="tarot-pattern-svg">
                    <circle cx="100" cy="150" r="60" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.6" />
                    <path d="M100 90 L120 140 L170 140 L130 170 L145 220 L100 190 L55 220 L70 170 L30 140 L80 140 Z" 
                          fill="none" stroke="currentColor" strokeWidth="2" />
                    <circle cx="100" cy="40" r="8" fill="currentColor" opacity="0.8" />
                    <circle cx="100" cy="260" r="8" fill="currentColor" opacity="0.8" />
                  </svg>
                </div>
              </div>
            </div>

            <button className="tarot-start-button-large" onClick={handleStart}>
              点击占卜揭示今日运势！
            </button>
          </div>
        )}

        {/* 抽牌阶段 */}
        {phase === 'drawing' && (
          <div className="tarot-drawing">
            <div className="tarot-progress-top">
              <span>进度 {Math.round(progress)}/100</span>
              <div className="tarot-progress-bar-top">
                <div 
                  className="tarot-progress-fill-top" 
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <div className="tarot-deck-area">
              <div className="tarot-deck-stack">
                {[...Array(7)].map((_, i) => (
                  <div
                    key={i}
                    className={`tarot-deck-card ${isDrawing && i === 6 ? 'drawing-card' : ''}`}
                    style={{
                      transform: `translateY(${-i * 3}px) translateX(${-i * 1.5}px) rotate(${-i * 1.5}deg)`,
                      zIndex: 7 - i,
                      animationDelay: `${i * 0.1}s`,
                    }}
                  >
                    <div className="tarot-card-back-deck">
                      <div className="tarot-card-glow-deck" />
                      <div className="tarot-card-pattern-deck">
                        <svg viewBox="0 0 200 300" className="tarot-pattern-svg">
                          <circle cx="100" cy="150" r="50" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.5" />
                          <path d="M100 100 L115 135 L155 135 L125 160 L138 195 L100 170 L62 195 L75 160 L45 135 L85 135 Z" 
                                fill="none" stroke="currentColor" strokeWidth="1.5" />
                        </svg>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="tarot-drawing-text">正在抽取塔罗牌...</p>
            </div>
          </div>
        )}

        {/* 选择阶段 */}
        {phase === 'choosing' && currentCard && (
          <div className="tarot-choosing">
            <div className="tarot-progress-top">
              <span>进度 {Math.round(progress)}/100 · {currentCard.dimension}</span>
              <div className="tarot-progress-bar-top">
                <div 
                  className="tarot-progress-fill-top" 
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <div className="tarot-revealed-card">
              <div className="tarot-card-front">
                <div className="tarot-card-glow-front" />
                <div className="tarot-card-border">
                  <div className="tarot-card-icon-large">
                    <svg viewBox="0 0 100 100" width="80" height="80" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="50" cy="50" r="45" stroke="url(#iconGradient)" strokeWidth="3" opacity="0.3"/>
                      <path d="M50 15 L60 40 L85 40 L65 55 L75 80 L50 65 L25 80 L35 55 L15 40 L40 40 Z" 
                            fill="url(#iconGradient)" opacity="0.8"/>
                      <defs>
                        <linearGradient id="iconGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#0A59F7"/>
                          <stop offset="100%" stopColor="#6B48FF"/>
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                  <h2 className="tarot-card-title">{currentCard.card}</h2>
                  <p className="tarot-card-dimension-text">{currentCard.dimension}</p>
                  <div className="tarot-card-divider" />
                  <p className="tarot-card-scenario-text">{currentCard.scenario}</p>
                </div>
              </div>
            </div>

            <div className="tarot-choices">
              {currentCard.options.map((option) => (
                <button
                  key={option.id}
                  className="tarot-choice-button"
                  onClick={() => handleChoice(option)}
                >
                  <span className="tarot-choice-icon">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                      {option.tendency === 'left' ? (
                        <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
                      ) : (
                        <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
                      )}
                    </svg>
                  </span>
                  <span className="tarot-choice-text">{option.text}</span>
                </button>
              ))}
            </div>

            <div className="tarot-finish-early">
              <button className="tarot-finish-early-button" onClick={handleFinishEarly}>
                <span className="tarot-finish-early-icon">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </span>
                <span className="tarot-finish-early-text">我今天不想继续了</span>
              </button>
            </div>
          </div>
        )}

        {/* 结果阶段 */}
        {phase === 'result' && profile && (
          <div className="tarot-result">
            <h2 className="tarot-result-title">
              你的决策画像
              <br />
              <span className="tarot-result-subtitle">Decision Profile</span>
            </h2>
            <p className="tarot-result-info">
              基于 {profile.total_choices} 次选择 · 置信度 {Math.round(profile.confidence * 100)}%
            </p>

            <div className="tarot-result-grid">
              {Object.entries(profile.dimensions).map(([name, data]) => (
                <div key={name} className="tarot-dimension-card">
                  <div className="tarot-dimension-header">
                    <span className="tarot-dimension-name">{name}</span>
                    <span className="tarot-dimension-confidence">
                      {Math.round(data.confidence * 100)}%
                    </span>
                  </div>
                  <div className="tarot-dimension-bar-container">
                    <div 
                      className="tarot-dimension-bar-fill"
                      style={{ width: `${((data.value + 1) / 2) * 100}%` }}
                    />
                  </div>
                  <div className="tarot-dimension-value-text">
                    倾向值: {data.value.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>

            {profile.patterns.length > 0 && (
              <div className="tarot-patterns-card">
                <h3>决策模式特征</h3>
                <ul className="tarot-patterns-list">
                  {profile.patterns.map((pattern, i) => (
                    <li key={i}>{pattern}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="tarot-result-actions">
              <button className="tarot-action-button primary" onClick={handleRestart}>
                重新开始
              </button>
              <button 
                className="tarot-action-button secondary"
                onClick={() => window.history.back()}
              >
                返回主页
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
