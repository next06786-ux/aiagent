import React from 'react';
import '../styles/Agent3DAvatar.css';

interface Agent3DAvatarProps {
  type: 'relationship' | 'education' | 'career';
  color: string;
  isHovered?: boolean;
}

export const Agent3DAvatar: React.FC<Agent3DAvatarProps> = ({ type, color, isHovered = false }) => {
  // 根据类型选择不同的表情和装饰
  const getCharacterEmoji = () => {
    switch (type) {
      case 'relationship':
        return '👨‍🤝‍👨';
      case 'education':
        return '👨‍🎓';
      case 'career':
        return '👨‍💼';
      default:
        return '👤';
    }
  };

  return (
    <div className={`agent-avatar-3d ${isHovered ? 'is-hovered' : ''}`}>
      <div className="avatar-scene" style={{ '--theme-color': color } as React.CSSProperties}>
        {/* 3D人物容器 */}
        <div className="character-3d">
          {/* 头部 */}
          <div className="char-head">
            <div className="head-sphere">
              {/* 脸部 */}
              <div className="face">
                <div className="eyes">
                  <div className="eye left">
                    <div className="eyeball"></div>
                  </div>
                  <div className="eye right">
                    <div className="eyeball"></div>
                  </div>
                </div>
                <div className="nose"></div>
                <div className="mouth"></div>
              </div>
            </div>
            
            {/* 头发/帽子 */}
            {type === 'relationship' && (
              <div className="hair-style-1">
                <div className="hair-part"></div>
              </div>
            )}
            {type === 'education' && (
              <div className="graduation-hat">
                <div className="hat-board"></div>
                <div className="hat-cap"></div>
                <div className="tassel"></div>
              </div>
            )}
            {type === 'career' && (
              <div className="hair-style-2">
                <div className="hair-part"></div>
              </div>
            )}
          </div>

          {/* 身体 */}
          <div className="char-body">
            <div className="body-torso">
              {/* 衣服装饰 */}
              {type === 'relationship' && (
                <div className="badge heart-badge">❤️</div>
              )}
              {type === 'education' && (
                <div className="badge book-badge">📚</div>
              )}
              {type === 'career' && (
                <div className="badge tie-badge">👔</div>
              )}
            </div>
          </div>

          {/* 手臂 */}
          <div className="char-arms">
            <div className="arm left-arm"></div>
            <div className="arm right-arm"></div>
          </div>

          {/* 腿 */}
          <div className="char-legs">
            <div className="leg left-leg"></div>
            <div className="leg right-leg"></div>
          </div>
        </div>

        {/* 阴影 */}
        <div className="char-shadow"></div>
      </div>
    </div>
  );
};
