import React, { useEffect, useRef, useState } from 'react';
import Live2DManager from '../utils/Live2DManager';
import '../styles/Live2DAvatar.css';

interface CubismLive2DAvatarProps {
  type: 'relationship' | 'education' | 'career';
  isHovered?: boolean;
}

// 模型路径配置
const MODEL_PATHS = {
  relationship: '/live2d/shizuku/shizuku.model3.json',
  education: '/live2d/haru/haru_greeter_t03.model3.json',
  career: '/live2d/hiyori/hiyori_pro_t10.model3.json',
};

export const CubismLive2DAvatar: React.FC<CubismLive2DAvatarProps> = ({ type, isHovered = false }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const managerRef = useRef<typeof Live2DManager | null>(null);

  useEffect(() => {
    const initLive2D = async () => {
      if (!containerRef.current) return;

      try {
        setIsLoading(true);
        const manager = Live2DManager.getInstance();
        managerRef.current = manager;

        // 加载当前类型的模型
        const modelPath = MODEL_PATHS[type];
        await manager.loadModel(type, containerRef.current, modelPath);

        // 切换到当前模型
        manager.switchAgent(type);

        setIsLoading(false);
        console.log(`✓ Live2D model loaded: ${type}`);
      } catch (error) {
        console.error('Live2D加载失败:', error);
        setLoadError('模型加载失败: ' + (error as Error).message);
        setIsLoading(false);
      }
    };

    initLive2D();

    return () => {
      // 组件卸载时不销毁模型，保持在管理器中以便复用
      // 如果需要完全清理，可以调用 manager.destroyModel(type)
    };
  }, [type]);

  // 处理悬停交互
  useEffect(() => {
    if (isHovered && managerRef.current) {
      const manager = Live2DManager.getInstance();
      if (manager.getCurrentAgent() === type) {
        manager.playCurrentAgentMotion('tap_body');
      }
    }
  }, [isHovered, type]);

  return (
    <div className="live2d-avatar-container">
      <div ref={containerRef} className="live2d-wrapper" />
      {isLoading && (
        <div className="live2d-loading">
          <div className="loading-spinner"></div>
          <p>加载Live2D模型...</p>
        </div>
      )}
      {loadError && (
        <div className="live2d-error">
          <p>{loadError}</p>
        </div>
      )}
    </div>
  );
};
