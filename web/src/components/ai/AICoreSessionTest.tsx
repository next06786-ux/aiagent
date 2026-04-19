/**
 * AI核心会话同步测试组件
 * 用于验证主界面和悬浮球的对话同步
 */
import { useAICoreSession } from '../../hooks/useAICoreSession';
import { useAuth } from '../../hooks/useAuth';

export function AICoreSessionTest() {
  const { user } = useAuth();
  const { sessionId, messages, clearSession } = useAICoreSession(user?.user_id);

  return (
    <div style={{ 
      position: 'fixed', 
      bottom: '80px', 
      right: '20px', 
      background: 'white', 
      padding: '16px', 
      borderRadius: '12px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      maxWidth: '300px',
      zIndex: 9997
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>会话同步状态</h3>
      <div style={{ fontSize: '12px', color: '#666' }}>
        <div>会话ID: {sessionId.slice(0, 8)}...</div>
        <div>消息数: {messages.length}</div>
        <button 
          onClick={clearSession}
          style={{
            marginTop: '8px',
            padding: '6px 12px',
            background: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          清空会话
        </button>
      </div>
    </div>
  );
}
