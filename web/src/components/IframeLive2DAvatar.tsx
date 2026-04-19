import React, { useRef, useEffect, useState } from 'react';
import '../styles/Live2DAvatar.css';

interface IframeLive2DAvatarProps {
  type: 'relationship' | 'education' | 'career';
  isHovered?: boolean;
  loadDelay?: number; // 延迟加载时间（毫秒）
}

// 模型路径配置
const MODEL_PATHS = {
  relationship: '/live2d/mao_pro_zh/runtime/mao_pro.model3.json',
  education: '/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json',
  career: '/live2d/miara_pro_en/runtime/miara_pro_t03.model3.json',
};

export const IframeLive2DAvatar: React.FC<IframeLive2DAvatarProps> = ({ 
  type, 
  isHovered = false,
  loadDelay = 0
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [shouldLoad, setShouldLoad] = useState(loadDelay === 0);
  const modelPath = MODEL_PATHS[type];

  // 延迟加载逻辑
  useEffect(() => {
    if (loadDelay > 0) {
      const timer = setTimeout(() => {
        setShouldLoad(true);
      }, loadDelay);
      return () => clearTimeout(timer);
    }
  }, [loadDelay]);

  // 悬停时播放动画
  useEffect(() => {
    if (isHovered && iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage(
        { type: 'playMotion', motionName: 'tap_body' },
        '*'
      );
    }
  }, [isHovered]);

  return (
    <div className="live2d-avatar-container">
      {shouldLoad ? (
        <iframe
          ref={iframeRef}
          src={`/live2d-viewer.html?model=${encodeURIComponent(modelPath)}`}
          className="live2d-iframe"
          title={`Live2D ${type}`}
          loading="lazy"
          style={{
            width: '300px',
            height: '380px',
            border: 'none',
            background: 'transparent',
          }}
        />
      ) : (
        <div 
          className="live2d-placeholder"
          style={{
            width: '300px',
            height: '380px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.02)',
            borderRadius: '12px',
          }}
        >
          <div style={{ 
            width: '32px', 
            height: '32px', 
            border: '3px solid rgba(0, 0, 0, 0.1)', 
            borderTopColor: '#0A59F7',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        </div>
      )}
    </div>
  );
};
