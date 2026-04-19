import React, { useEffect, useRef, useState } from 'react';
import Live2DManager from '../utils/Live2DManager';
import '../styles/Live2DAvatar.css';

interface Live2DAvatarProps {
  type: 'relationship' | 'education' | 'career';
  isHovered?: boolean;
  loadDelay?: number; // 添加延迟加载参数
}

// 模型路径配置
const MODEL_PATHS = {
  relationship: '/live2d/mao_pro_zh/runtime/mao_pro.model3.json',
  education: '/live2d/hiyori_pro_zh/runtime/hiyori_pro_t11.model3.json',
  career: '/live2d/miara_pro_en/runtime/miara_pro_t03.model3.json',
};

export const Live2DAvatar: React.FC<Live2DAvatarProps> = ({ 
  type, 
  isHovered = false,
  loadDelay = 0 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const modelIdRef = useRef<string>(`live2d-${type}-${Date.now()}`);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current || hasLoadedRef.current) return;

    const modelId = modelIdRef.current;
    const manager = Live2DManager.getInstance();

    const initModel = async () => {
      try {
        // 延迟加载，避免同时创建多个WebGL上下文
        if (loadDelay > 0) {
          await new Promise(resolve => setTimeout(resolve, loadDelay));
        }

        const modelPath = MODEL_PATHS[type];
        console.log(`[Live2DAvatar ${type}] Initializing with path: ${modelPath}`);
        
        await manager.loadModel(modelId, containerRef.current!, modelPath);
        
        hasLoadedRef.current = true;

        // 设置定期播放待机动画
        const idleInterval = setInterval(() => {
          manager.playIdleMotion(modelId);
        }, 15000);

        setIsLoading(false);

        return () => clearInterval(idleInterval);
      } catch (error) {
        console.error(`[Live2DAvatar ${type}] Load failed:`, error);
        setLoadError('模型加载失败: ' + (error as Error).message);
        setIsLoading(false);
      }
    };

    initModel();

    return () => {
      if (hasLoadedRef.current) {
        manager.destroyModel(modelId);
      }
    };
  }, [type, loadDelay]);

  // 悬停效果
  useEffect(() => {
    if (isHovered && hasLoadedRef.current) {
      const manager = Live2DManager.getInstance();
      manager.playMotion(modelIdRef.current, 'tap_body');
    }
  }, [isHovered]);

  return (
    <div className="live2d-avatar-container" ref={containerRef}>
      {isLoading && (
        <div className="live2d-loading">
          <div className="loading-spinner"></div>
          <p>加载中...</p>
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
