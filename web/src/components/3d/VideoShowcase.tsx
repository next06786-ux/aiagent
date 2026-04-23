import { useEffect, useRef, useState } from 'react';
import './VideoShowcase.css';

interface VideoShowcaseProps {
  onClose?: () => void;
  isEmbedded?: boolean;
}

export function VideoShowcase({ onClose, isEmbedded = false }: VideoShowcaseProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (isEmbedded) {
      const handleScroll = () => {
        const element = containerRef.current;
        if (!element) return;
        
        const rect = element.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        
        // 计算元素相对于视口的位置
        // 当元素顶部进入视口底部时开始动画
        const scrollStart = windowHeight;
        const scrollEnd = windowHeight * 0.3;
        const elementProgress = 1 - (rect.top - scrollEnd) / (scrollStart - scrollEnd);
        const p = Math.min(1, Math.max(0, elementProgress));
        setProgress(p);
      };

      window.addEventListener('scroll', handleScroll, { passive: true });
      handleScroll();
      return () => window.removeEventListener('scroll', handleScroll);
    }
  }, [isEmbedded]);

  // 嵌入模式下的动画效果
  const scale = isEmbedded ? (progress < 1 ? 0.85 + progress * 0.15 : 1) : 1;
  const translateY = isEmbedded ? (progress < 1 ? (1 - progress) * 40 : 0) : 0;
  const opacity = isEmbedded ? (progress < 0.3 ? 0 : Math.min(1, (progress - 0.3) / 0.3)) : 1;
  const blur = isEmbedded ? (1 - progress) * 8 : 0;

  // 嵌入模式下不需要 translate(-50%, -50%)，用 margin:auto 居中
  const containerTransform = isEmbedded 
    ? `translateY(${translateY}px) scale(${scale})`
    : `translate(-50%, -50%) translateY(${translateY}px) scale(${scale})`;

  return (
    <div
      ref={containerRef}
      className={`video-showcase-container ${isEmbedded ? 'video-showcase-embedded' : ''}`}
      style={{
        transform: containerTransform,
        opacity,
        filter: `blur(${blur}px)`,
      }}
    >
      <div className="video-showcase-frame">
        <div className="video-showcase-inner-black">
          <div className="video-showcase-content">
            {/* 显示图片，如果图片不存在则显示占位符 */}
            <img 
              src="/images/showcase.png" 
              alt="系统演示"
              className="video-showcase-image"
              onError={(e) => {
                // 如果图片加载失败，显示占位符
                e.currentTarget.style.display = 'none';
                const placeholder = e.currentTarget.nextElementSibling as HTMLElement;
                if (placeholder) placeholder.style.display = 'flex';
              }}
            />
            <div className="video-placeholder-fallback" style={{ display: 'none' }}>
              <div className="video-placeholder-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
              <span className="video-placeholder-text">视频演示区域</span>
              <span className="video-placeholder-hint">请将图片命名为 showcase.png 并放在 web/public/images/ 目录下</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Close button */}
      {onClose && (
        <button className="video-showcase-close" onClick={onClose}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      )}
    </div>
  );
}