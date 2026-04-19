import { useEffect, useRef, useState } from 'react';

interface ChatMessage {
  role: 'ai' | 'user' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
}

interface StreamingCollectionChatProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isProcessing: boolean;
  currentStatus?: string;
  progress?: {
    current: number;
    total: number;
    stage: string;
  };
}

export function StreamingCollectionChat({
  messages,
  onSendMessage,
  isProcessing,
  currentStatus,
  progress,
}: StreamingCollectionChatProps) {
  const [input, setInput] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!isProcessing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isProcessing]);

  const handleSend = () => {
    if (!input.trim() || isProcessing) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* 进度指示器 */}
      {progress && (
        <div style={{
          padding: '14px 18px',
          borderRadius: 16,
          background: 'linear-gradient(135deg, rgba(232, 213, 208, 0.12), rgba(220, 205, 195, 0.08))',
          border: '1px solid rgba(220, 210, 200, 0.25)',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 10,
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#7a6f65' }}>
              {progress.stage}
            </span>
            <span style={{ fontSize: 12, color: '#9a8f85' }}>
              {progress.current} / {progress.total}
            </span>
          </div>
          <div style={{
            height: 6,
            borderRadius: 999,
            background: 'rgba(220, 210, 200, 0.2)',
            overflow: 'hidden',
          }}>
            <div
              style={{
                height: '100%',
                borderRadius: 999,
                background: 'linear-gradient(90deg, rgba(232, 213, 208, 0.9), rgba(220, 205, 195, 0.9))',
                width: `${(progress.current / progress.total) * 100}%`,
                transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            />
          </div>
        </div>
      )}

      {/* 状态指示器 */}
      {currentStatus && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 14,
          background: 'rgba(232, 213, 208, 0.08)',
          border: '1px solid rgba(220, 210, 200, 0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <div style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #E8D5D0, #D4C4BF)',
            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          }} />
          <span style={{ fontSize: 13, color: '#7a6f65', fontWeight: 500 }}>
            {currentStatus}
          </span>
        </div>
      )}

      {/* 消息列表 */}
      <div style={{
        maxHeight: 480,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
        padding: '4px 0',
      }}>
        {messages.map((msg, i) => (
          <div
            key={`msg-${i}-${msg.timestamp}`}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              animation: 'fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            <div
              style={{
                maxWidth: '82%',
                padding: msg.role === 'system' ? '10px 16px' : '14px 20px',
                borderRadius: msg.role === 'system' ? 12 : 20,
                background:
                  msg.role === 'ai'
                    ? 'linear-gradient(135deg, rgba(232, 213, 208, 0.15), rgba(220, 205, 195, 0.12))'
                    : msg.role === 'user'
                    ? 'rgba(255, 255, 255, 0.12)'
                    : 'rgba(220, 210, 200, 0.08)',
                border: `1.5px solid ${
                  msg.role === 'ai'
                    ? 'rgba(220, 210, 200, 0.3)'
                    : msg.role === 'user'
                    ? 'rgba(255, 255, 255, 0.2)'
                    : 'rgba(220, 210, 200, 0.15)'
                }`,
                color: msg.role === 'system' ? '#9a8f85' : '#2a2520',
                fontSize: msg.role === 'system' ? 12 : 15,
                lineHeight: 1.7,
                fontWeight: msg.role === 'system' ? 500 : 400,
                boxShadow:
                  msg.role === 'ai'
                    ? '0 4px 12px rgba(220, 205, 195, 0.15)'
                    : msg.role === 'user'
                    ? '0 4px 12px rgba(0, 0, 0, 0.08)'
                    : 'none',
              }}
            >
              {msg.role === 'ai' && (
                <div
                  style={{
                    fontSize: 10,
                    opacity: 0.65,
                    marginBottom: 8,
                    letterSpacing: '0.08em',
                    color: '#B8A89D',
                    textTransform: 'uppercase',
                  }}
                >
                  系统
                </div>
              )}
              <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {msg.content}
                {msg.isStreaming && (
                  <span
                    style={{
                      display: 'inline-block',
                      width: 8,
                      height: 14,
                      marginLeft: 4,
                      background: '#D4C4BF',
                      animation: 'blink 1s step-end infinite',
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        ))}

        {/* 思考中指示器 */}
        {isProcessing && !currentStatus && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                padding: '12px 18px',
                borderRadius: 16,
                background: 'rgba(232, 213, 208, 0.08)',
                border: '1px solid rgba(220, 210, 200, 0.2)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}
            >
              <div style={{ display: 'flex', gap: 4 }}>
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: '#D4C4BF',
                      animation: `bounce 1.4s ease-in-out ${i * 0.2}s infinite`,
                    }}
                  />
                ))}
              </div>
              <span style={{ fontSize: 13, color: '#9a8f85' }}>思考中</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* 输入区域 */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
        <input
          ref={inputRef}
          type="text"
          className="input"
          style={{
            flex: 1,
            padding: '14px 18px',
            borderRadius: 16,
            fontSize: 14,
            border: '1.5px solid rgba(220, 210, 200, 0.25)',
            background: 'rgba(255, 255, 255, 0.92)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的回答，按 Enter 发送..."
          disabled={isProcessing}
        />
        <button
          className="button button-primary"
          onClick={handleSend}
          disabled={isProcessing || !input.trim()}
          style={{
            whiteSpace: 'nowrap',
            padding: '14px 24px',
            borderRadius: 16,
            background: isProcessing
              ? 'rgba(220, 210, 200, 0.3)'
              : 'linear-gradient(135deg, rgba(232, 213, 208, 0.95), rgba(220, 205, 195, 0.95))',
            color: isProcessing ? '#9a8f85' : '#5a5248',
            border: 'none',
            fontWeight: 600,
            fontSize: 14,
            cursor: isProcessing ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          {isProcessing ? '处理中...' : '发送'}
        </button>
      </div>

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.5;
            transform: scale(0.8);
          }
        }

        @keyframes blink {
          0%, 50% {
            opacity: 1;
          }
          51%, 100% {
            opacity: 0;
          }
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: translateY(0);
          }
          40% {
            transform: translateY(-8px);
          }
        }
      `}</style>
    </div>
  );
}
