import { useLocation, useOutlet } from 'react-router-dom';
import { useRef, useLayoutEffect, useState } from 'react';

/**
 * KeepAlive 组件 - 保持路由组件的状态
 * 用于底部导航栏切换时保持页面状态和滚动位置
 */
export function KeepAlive() {
  const location = useLocation();
  const outlet = useOutlet();
  const cacheRef = useRef<Map<string, { outlet: JSX.Element; scrollY: number }>>(new Map());
  const [, forceUpdate] = useState({});
  const currentPath = location.pathname;

  // 使用 useLayoutEffect 在渲染前缓存
  useLayoutEffect(() => {
    if (outlet) {
      const existing = cacheRef.current.get(currentPath);
      if (!existing) {
        cacheRef.current.set(currentPath, { outlet, scrollY: 0 });
        forceUpdate({});
      }
    }
  }, [currentPath, outlet]);

  // 恢复滚动位置
  useLayoutEffect(() => {
    const cached = cacheRef.current.get(currentPath);
    if (cached) {
      window.scrollTo(0, cached.scrollY);
    }

    // 保存滚动位置
    return () => {
      const scrollY = window.scrollY;
      const cached = cacheRef.current.get(currentPath);
      if (cached) {
        cached.scrollY = scrollY;
      }
    };
  }, [currentPath]);

  // 渲染缓存的页面或当前outlet
  const cachedEntry = cacheRef.current.get(currentPath);
  
  return (
    <>
      {Array.from(cacheRef.current.entries()).map(([path, { outlet: cachedOutlet }]) => (
        <div
          key={path}
          style={{
            display: path === currentPath ? 'block' : 'none',
          }}
        >
          {path === currentPath && outlet ? outlet : cachedOutlet}
        </div>
      ))}
      {!cachedEntry && outlet && (
        <div style={{ display: 'block' }}>
          {outlet}
        </div>
      )}
    </>
  );
}
