import { useEffect, useRef, useState } from 'react';

interface ThinkingStreamProps {
  content: string;
  optionTitle?: string;
  isActive: boolean;
}

export function ThinkingStream({ content, optionTitle, isActive }: ThinkingStreamProps) {
  const [displayLines, setDisplayLines] = useState<string[]>([]);
  const contentRef = useRef<HTMLDivElement>(null);
  const lineQueueRef = useRef<string[]>([]);

  useEffect(() => {
    if (content && isActive) {
      const lines = content.split('\n').filter(l => l.trim());
      lineQueueRef.current = [...lineQueueRef.current, ...lines];

      const showNextLine = () => {
        if (lineQueueRef.current.length > 0) {
          const nextLine = lineQueueRef.current.shift()!;
          setDisplayLines(prev => [...prev.slice(-30), nextLine]);
          setTimeout(showNextLine, 80 + Math.random() * 100);
        }
      };

      if (lineQueueRef.current.length === lines.length) {
        showNextLine();
      }
    }
  }, [content, isActive]);

  useEffect(() => {
    if (contentRef.current && isActive) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [displayLines, isActive]);

  if (!isActive) return null;

  return (
    <div style={{
      background: '#ffffff',
      borderRadius: 12,
      border: '1px solid #e2e8f0',
      overflow: 'hidden',
    }}>
      {/* 头部 */}
      <div style={{
        padding: '10px 14px',
        background: '#f8fafc',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <div style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: '#3b82f6',
          animation: 'pulse 1.5s ease-in-out infinite',
        }} />
        <span style={{ fontSize: 12, fontWeight: 600, color: '#1e293b' }}>
          {optionTitle ? `${optionTitle} - AI思考中` : 'AI思考中'}
        </span>
      </div>

      {/* 内容区 */}
      <div
        ref={contentRef}
        style={{
          padding: 12,
          minHeight: 100,
          maxHeight: 250,
          overflowY: 'auto',
          fontFamily: 'monospace',
          fontSize: 12,
          lineHeight: 1.6,
        }}
      >
        {displayLines.length > 0 ? (
          displayLines.map((line, idx) => (
            <div
              key={idx}
              style={{
                color: idx === displayLines.length - 1 ? '#1e293b' : '#64748b',
                fontWeight: idx === displayLines.length - 1 ? 500 : 400,
                marginBottom: 2,
              }}
            >
              {line.startsWith('=') ? (
                <div style={{ borderBottom: '1px solid #e2e8f0', margin: '6px 0' }} />
              ) : (
                line
              )}
            </div>
          ))
        ) : (
          <div style={{ color: '#94a3b8', fontSize: 12 }}>
            等待AI响应...
          </div>
        )}

        {isActive && displayLines.length > 0 && (
          <span
            style={{
              display: 'inline-block',
              width: 2,
              height: 12,
              background: '#3b82f6',
              marginLeft: 2,
              animation: 'blink 1s infinite',
              verticalAlign: 'middle',
            }}
          />
        )}
      </div>

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
