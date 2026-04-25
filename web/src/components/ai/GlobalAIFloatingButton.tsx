import { useState } from 'react';
import { AICoreModal } from './AICoreModal';
import './GlobalAIFloatingButton.css';

interface GlobalAIFloatingButtonProps {
  disableNavigation?: boolean;
  disableQuickActions?: boolean;
}

export function GlobalAIFloatingButton({ 
  disableNavigation = false, 
  disableQuickActions = false 
}: GlobalAIFloatingButtonProps = {}) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      {/* 悬浮按钮 */}
      <button
        className="global-ai-floating-button"
        onClick={() => setIsModalOpen(true)}
        aria-label="打开AI核心"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          <circle cx="9" cy="10" r="1" fill="currentColor" />
          <circle cx="15" cy="10" r="1" fill="currentColor" />
        </svg>
        <span className="ai-badge">AI</span>
      </button>

      {/* AI核心弹窗 */}
      {isModalOpen && (
        <AICoreModal 
          onClose={() => setIsModalOpen(false)} 
          disableNavigation={disableNavigation}
          disableQuickActions={disableQuickActions}
        />
      )}
    </>
  );
}
