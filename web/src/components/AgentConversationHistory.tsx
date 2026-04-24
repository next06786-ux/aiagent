import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../services/api';
import '../styles/AgentConversationHistory.css';

interface Conversation {
  conversation_id: string;
  agent_type: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface AgentConversationHistoryProps {
  agentType: 'relationship' | 'education' | 'career';
  token: string;
  onSelectConversation: (conversationId: string, messages: any[]) => void;
  onClose: () => void;
}

export function AgentConversationHistory({ 
  agentType, 
  token, 
  onSelectConversation,
  onClose 
}: AgentConversationHistoryProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadConversations();
  }, [agentType]);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/agent-conversations?token=${token}&agent_type=${agentType}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('获取对话历史失败');
      }

      const data = await response.json();
      
      if (data.success) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('加载对话历史失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = async (conversationId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/agent-conversation/${conversationId}?token=${token}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('获取对话详情失败');
      }

      const data = await response.json();
      
      if (data.success) {
        onSelectConversation(conversationId, data.messages);
      }
    } catch (error) {
      console.error('加载对话详情失败:', error);
    }
  };

  const handleDeleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('确定要删除这个对话吗？')) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/agent-conversation/${conversationId}`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ token })
        }
      );

      if (!response.ok) {
        throw new Error('删除对话失败');
      }

      const data = await response.json();
      
      if (data.success) {
        // 重新加载列表
        loadConversations();
      }
    } catch (error) {
      console.error('删除对话失败:', error);
      alert('删除失败，请重试');
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  return (
    <div className="conversation-history-overlay" onClick={onClose}>
      <div className="conversation-history-panel" onClick={e => e.stopPropagation()}>
        <div className="conversation-history-header">
          <h3>对话历史</h3>
          <button className="close-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="conversation-history-content">
          {isLoading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>加载中...</p>
            </div>
          ) : conversations.length === 0 ? (
            <div className="empty-state">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <p>还没有对话历史</p>
              <span>开始与Agent对话吧</span>
            </div>
          ) : (
            <div className="conversation-list">
              {conversations.map(conv => (
                <div
                  key={conv.conversation_id}
                  className="conversation-item"
                  onClick={() => handleSelectConversation(conv.conversation_id)}
                >
                  <div className="conversation-item-content">
                    <h4 className="conversation-title">{conv.title}</h4>
                    <div className="conversation-meta">
                      <span className="conversation-time">{formatDate(conv.updated_at)}</span>
                      <span className="conversation-count">{conv.message_count} 条消息</span>
                    </div>
                  </div>
                  <button
                    className="delete-btn"
                    onClick={(e) => handleDeleteConversation(conv.conversation_id, e)}
                    title="删除对话"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
