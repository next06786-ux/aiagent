import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { BackButton } from '../components/common/BackButton';
import { useAuth } from '../hooks/useAuth';
import { getDecisionHistoryList, deleteDecisionHistory, DecisionHistoryItem } from '../services/decisionHistory';

export function DecisionHistoryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [historyList, setHistoryList] = useState<DecisionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.user_id) {
      loadHistory();
    }
  }, [user]);

  const loadHistory = async () => {
    if (!user?.user_id) return;
    
    setIsLoading(true);
    setError('');
    try {
      const list = await getDecisionHistoryList(user.user_id);
      setHistoryList(list);
    } catch (err) {
      console.error('[历史] 加载失败:', err);
      setError('加载历史记录失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (historyId: string) => {
    if (!confirm('确定要删除这条历史记录吗？')) return;

    try {
      await deleteDecisionHistory(historyId);
      setHistoryList(prev => prev.filter(item => item.id !== historyId));
    } catch (err) {
      console.error('[历史] 删除失败:', err);
      alert('删除失败，请稍后重试');
    }
  };

  const handleView = (item: DecisionHistoryItem) => {
    // TODO: 实现场景还原功能
    console.log('[历史] 查看详情:', item);
    alert('场景还原功能开发中...');
  };

  return (
    <AppShell>
      <BackButton to="/decision/workbench" label="返回" />
      
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
        <div style={{
          marginBottom: 32,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <h1 style={{
              fontSize: 32,
              fontWeight: 700,
              background: 'linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: 8,
            }}>
              历史决策
            </h1>
            <p style={{ fontSize: 15, color: '#64748B' }}>
              查看和管理你的决策分析历史记录
            </p>
          </div>
        </div>

        {isLoading ? (
          <div style={{
            textAlign: 'center',
            padding: 60,
            color: '#94A3B8',
          }}>
            <div style={{
              width: 40,
              height: 40,
              border: '3px solid rgba(10, 89, 247, 0.1)',
              borderTopColor: 'rgba(10, 89, 247, 0.6)',
              borderRadius: '50%',
              margin: '0 auto 16px',
              animation: 'spin 1s linear infinite',
            }} />
            <p>加载中...</p>
          </div>
        ) : error ? (
          <div style={{
            textAlign: 'center',
            padding: 60,
            color: '#EF4444',
          }}>
            <p>{error}</p>
            <button
              onClick={loadHistory}
              style={{
                marginTop: 16,
                padding: '10px 20px',
                borderRadius: 12,
                border: '1px solid #E2E8F0',
                background: 'white',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              重试
            </button>
          </div>
        ) : historyList.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: 60,
            color: '#94A3B8',
          }}>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 16px', opacity: 0.3 }}>
              <path d="M9 11l3 3L22 4"/>
              <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
            </svg>
            <p>暂无历史记录</p>
            <button
              onClick={() => navigate('/decision/workbench')}
              style={{
                marginTop: 16,
                padding: '10px 20px',
                borderRadius: 12,
                border: 'none',
                background: 'linear-gradient(135deg, #6B48FF 0%, #8B5CF6 100%)',
                color: 'white',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
                boxShadow: '0 4px 12px rgba(107, 72, 255, 0.3)',
              }}
            >
              开始新的决策分析
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 16 }}>
            {historyList.map(item => (
              <div
                key={item.id}
                style={{
                  padding: 24,
                  borderRadius: 16,
                  background: 'white',
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.05)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
                onClick={() => handleView(item)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{
                      fontSize: 18,
                      fontWeight: 600,
                      color: '#1a1a1a',
                      marginBottom: 8,
                    }}>
                      {item.question}
                    </h3>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                      <span style={{
                        fontSize: 13,
                        color: '#64748B',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"/>
                          <polyline points="12 6 12 12 16 14"/>
                        </svg>
                        {new Date(item.createdAt).toLocaleString('zh-CN')}
                      </span>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: 8,
                        background: 'rgba(10, 89, 247, 0.08)',
                        fontSize: 12,
                        fontWeight: 600,
                        color: 'rgba(10, 89, 247, 0.9)',
                      }}>
                        {item.optionTitle}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(item.id);
                    }}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 8,
                      border: '1px solid #FEE2E2',
                      background: 'white',
                      color: '#EF4444',
                      cursor: 'pointer',
                      fontSize: 13,
                      fontWeight: 600,
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#FEE2E2';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white';
                    }}
                  >
                    删除
                  </button>
                </div>
                
                {item.report && (
                  <div style={{
                    marginTop: 16,
                    padding: 16,
                    borderRadius: 12,
                    background: '#F8FAFC',
                    fontSize: 14,
                    color: '#475569',
                    lineHeight: 1.6,
                  }}>
                    {item.report.summary.substring(0, 150)}
                    {item.report.summary.length > 150 && '...'}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </AppShell>
  );
}
