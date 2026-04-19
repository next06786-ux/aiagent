import React from 'react';
import '../styles/SimpleLive2DAvatar.css';

interface SimpleLive2DAvatarProps {
  type: 'relationship' | 'education' | 'career';
  color: string;
  isHovered?: boolean;
}

export const SimpleLive2DAvatar: React.FC<SimpleLive2DAvatarProps> = ({ 
  type, 
  color, 
  isHovered = false 
}) => {
  return (
    <div className={`simple-live2d ${isHovered ? 'hovered' : ''}`}>
      <svg 
        width="180" 
        height="220" 
        viewBox="0 0 180 220" 
        className="character-svg"
        style={{ '--char-color': color } as React.CSSProperties}
      >
        {/* 定义渐变和滤镜 */}
        <defs>
          <radialGradient id={`skinGradient-${type}`} cx="30%" cy="30%">
            <stop offset="0%" stopColor="#ffe4c4" />
            <stop offset="50%" stopColor="#ffd4a3" />
            <stop offset="100%" stopColor="#ffb380" />
          </radialGradient>
          
          <radialGradient id={`bodyGradient-${type}`} cx="30%" cy="30%">
            <stop offset="0%" stopColor={color} stopOpacity="1" />
            <stop offset="100%" stopColor={color} stopOpacity="0.7" />
          </radialGradient>
          
          <filter id="shadow">
            <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
            <feOffset dx="0" dy="4" result="offsetblur"/>
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.3"/>
            </feComponentTransfer>
            <feMerge>
              <feMergeNode/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* 身体 */}
        <g className="body-group">
          <ellipse 
            cx="90" 
            cy="140" 
            rx="35" 
            ry="50" 
            fill={`url(#bodyGradient-${type})`}
            filter="url(#shadow)"
            className="body"
          />
          
          {/* 衣服装饰 */}
          {type === 'relationship' && (
            <text x="90" y="145" fontSize="24" textAnchor="middle" className="badge">❤️</text>
          )}
          {type === 'education' && (
            <text x="90" y="145" fontSize="24" textAnchor="middle" className="badge">📚</text>
          )}
          {type === 'career' && (
            <text x="90" y="145" fontSize="24" textAnchor="middle" className="badge">💼</text>
          )}
        </g>

        {/* 手臂 */}
        <g className="arms">
          <ellipse 
            cx="60" 
            cy="130" 
            rx="10" 
            ry="35" 
            fill={`url(#bodyGradient-${type})`}
            className="arm left-arm"
            transform="rotate(-20 60 130)"
          />
          <ellipse 
            cx="120" 
            cy="130" 
            rx="10" 
            ry="35" 
            fill={`url(#bodyGradient-${type})`}
            className="arm right-arm"
            transform="rotate(20 120 130)"
          />
          
          {/* 手 */}
          <circle cx="58" cy="160" r="8" fill="#ffe4c4" className="hand left-hand" />
          <circle cx="122" cy="160" r="8" fill="#ffe4c4" className="hand right-hand" />
        </g>

        {/* 头部 */}
        <g className="head-group">
          <circle 
            cx="90" 
            cy="60" 
            r="35" 
            fill={`url(#skinGradient-${type})`}
            filter="url(#shadow)"
            className="head"
          />
          
          {/* 头发/帽子 */}
          {type === 'relationship' && (
            <ellipse 
              cx="90" 
              cy="35" 
              rx="38" 
              ry="25" 
              fill="#2c3e50" 
              className="hair"
            />
          )}
          
          {type === 'education' && (
            <g className="graduation-cap">
              <rect x="55" y="25" width="70" height="8" rx="4" fill="#1a1a1a" />
              <ellipse cx="90" cy="35" rx="25" ry="15" fill="#2c2c2c" />
              <circle cx="90" cy="25" r="4" fill="#ffd700" />
              <line x1="95" y1="25" x2="105" y2="40" stroke="#ffd700" strokeWidth="2" className="tassel" />
              <circle cx="105" cy="40" r="3" fill="#ffd700" />
            </g>
          )}
          
          {type === 'career' && (
            <ellipse 
              cx="90" 
              cy="35" 
              rx="38" 
              ry="22" 
              fill="#1a1a1a" 
              className="hair"
            />
          )}
          
          {/* 脸部特征 */}
          <g className="face">
            {/* 眼睛 */}
            <g className="eyes">
              <ellipse cx="75" cy="55" rx="6" ry="8" fill="white" className="eye left-eye" />
              <ellipse cx="105" cy="55" rx="6" ry="8" fill="white" className="eye right-eye" />
              
              <circle cx="75" cy="56" r="4" fill="#4a90e2" className="iris left-iris" />
              <circle cx="105" cy="56" r="4" fill="#4a90e2" className="iris right-iris" />
              
              <circle cx="75" cy="56" r="2" fill="#1a1a1a" className="pupil" />
              <circle cx="105" cy="56" r="2" fill="#1a1a1a" className="pupil" />
              
              <circle cx="76" cy="54" r="1.5" fill="white" className="shine" />
              <circle cx="106" cy="54" r="1.5" fill="white" className="shine" />
            </g>
            
            {/* 眉毛 */}
            <line x1="68" y1="48" x2="82" y2="47" stroke="#8b6f47" strokeWidth="2" strokeLinecap="round" className="eyebrow" />
            <line x1="98" y1="47" x2="112" y2="48" stroke="#8b6f47" strokeWidth="2" strokeLinecap="round" className="eyebrow" />
            
            {/* 鼻子 */}
            <ellipse cx="90" cy="65" rx="3" ry="4" fill="rgba(255, 180, 128, 0.4)" />
            
            {/* 嘴巴 */}
            <path 
              d="M 80 72 Q 90 78 100 72" 
              stroke="#d4956c" 
              strokeWidth="2.5" 
              fill="none" 
              strokeLinecap="round"
              className="mouth"
            />
            
            {/* 脸颊红晕 */}
            <ellipse cx="70" cy="68" rx="8" ry="5" fill="rgba(255, 150, 150, 0.4)" className="blush" />
            <ellipse cx="110" cy="68" rx="8" ry="5" fill="rgba(255, 150, 150, 0.4)" className="blush" />
          </g>
        </g>

        {/* 腿部 */}
        <g className="legs">
          <ellipse cx="75" cy="190" rx="12" ry="30" fill={`url(#bodyGradient-${type})`} className="leg" />
          <ellipse cx="105" cy="190" rx="12" ry="30" fill={`url(#bodyGradient-${type})`} className="leg" />
          
          {/* 脚 */}
          <ellipse cx="75" cy="210" rx="14" ry="8" fill="#2c3e50" />
          <ellipse cx="105" cy="210" rx="14" ry="8" fill="#2c3e50" />
        </g>
      </svg>
    </div>
  );
};
