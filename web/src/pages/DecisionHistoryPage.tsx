import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { BackButton } from '../components/common/BackButton';
import { useAuth } from '../hooks/useAuth';
import { PersonaInteractionView } from '../components/decision/PersonaInteractionView';
import { DecisionReportModal } from '../components/decision/DecisionReportModal';
import { 
  getDecisionHistoryList, 
  getDecisionHistoryDetail, 
  deleteDecisionHistory, 
  DecisionHistoryListItem,
  DecisionHistory 
} from '../services/decisionHistory';

export function DecisionHistoryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [historyList, setHistoryList] = useState<DecisionHistoryListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  // 场景查看状态
  const [viewingHistory, setViewingHistory] = useState<DecisionHistory | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string>('option_1'); // 当前查看的选项
  const [showReportModal, setShowReportModal] = useState(false);

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
      const response = await getDecisionHistoryList(user.user_id);
      console.log('[历史] 加载成功:', response);
      setHistoryList(response.histories || []);
    } catch (err) {
      console.error('[历史] 加载失败:', err);
      setError('加载历史记录失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (historyId: string) => {
    if (!user?.user_id) return;
    if (!confirm('确定要删除这条历史记录吗？')) return;

    try {
      await deleteDecisionHistory(historyId, user.user_id);
      setHistoryList(prev => prev.filter(item => item.id !== historyId));
    } catch (err) {
      console.error('[历史] 删除失败:', err);
      alert('删除失败，请稍后重试');
    }
  };

  const handleView = async (item: DecisionHistoryListItem) => {
    console.log('[历史] 查看详情:', item);
    
    try {
      const response = await getDecisionHistoryDetail(item.id);
      console.log('[历史] API响应:', response);
      
      if (response.success && response.history) {
        console.log('[历史] 详情加载成功:', response.history);
        console.log('[历史] options_data:', response.history.options_data);
        
        setViewingHistory(response.history);
        
        // 检查数据结构，设置默认选项
        const optionsData = response.history.options_data;
        if (optionsData) {
          // 找到第一个可用的选项
          const firstOptionKey = Object.keys(optionsData).find(key => key.startsWith('option_'));
          if (firstOptionKey) {
            setSelectedOptionId(firstOptionKey);
          } else {
            // 旧格式数据，没有 option_1, option_2 这样的key
            setSelectedOptionId('legacy');
          }
        }
      } else {
        alert('加载历史详情失败');
      }
    } catch (err) {
      console.error('[历史] 加载详情失败:', err);
      alert('加载历史详情失败');
    }
  };

  const handleCloseViewer = () => {
    setViewingHistory(null);
    setShowReportModal(false);
    setSelectedOptionId('option_1');
  };

  // 获取当前选中选项的数据
  const getCurrentOptionData = () => {
    if (!viewingHistory?.options_data) return null;
    
    const optionsData = viewingHistory.options_data;
    
    console.log('[历史查看] getCurrentOptionData 被调用');
    console.log('[历史查看] selectedOptionId:', selectedOptionId);
    console.log('[历史查看] optionsData keys:', Object.keys(optionsData));
    
    // 新格式：多选项
    if (selectedOptionId !== 'legacy' && optionsData[selectedOptionId]) {
      const data = optionsData[selectedOptionId];
      console.log('[历史查看] 返回新格式数据:', data);
      console.log('[历史查看] 是否有report:', !!data.report);
      return data;
    }
    
    // 旧格式：单选项（兼容）
    if (optionsData.agents) {
      console.log('[历史查看] 返回旧格式数据');
      return optionsData;
    }
    
    console.log('[历史查看] 没有找到数据');
    return null;
  };

  // 获取所有可用的选项
  const getAvailableOptions = () => {
    if (!viewingHistory?.options_data) return [];
    
    const optionsData = viewingHistory.options_data;
    
    console.log('[历史查看] getAvailableOptions 被调用');
    console.log('[历史查看] optionsData:', optionsData);
    
    // 新格式：返回所有 option_X 的key
    const optionKeys = Object.keys(optionsData).filter(key => key.startsWith('option_'));
    
    console.log('[历史查看] 找到的 option keys:', optionKeys);
    
    if (optionKeys.length > 0) {
      const options = optionKeys.map(key => ({
        id: key,
        title: optionsData[key].option_title || key,
        data: optionsData[key]
      }));
      console.log('[历史查看] 返回的选项列表:', options);
      return options;
    }
    
    // 旧格式：返回单个选项
    if (optionsData.agents) {
      return [{
        id: 'legacy',
        title: optionsData.option_title || '决策选项',
        data: optionsData
      }];
    }
    
    return [];
  };

  return (
    <AppShell>
      <BackButton to="/decision/workbench" label="返回" />
      
      {/* 场景查看器 */}
      {viewingHistory && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 9998, // 降低一级，让报告弹窗在上面
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }} onClick={handleCloseViewer}>
          <div style={{
            width: '95%',
            height: '95%',
            background: 'white',
            borderRadius: 24,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          }} onClick={(e) => e.stopPropagation()}>
            {/* 头部 */}
            <div style={{
              padding: '24px 32px',
              borderBottom: '1px solid #E2E8F0',
              background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                <div>
                  <h2 style={{
                    fontSize: 24,
                    fontWeight: 700,
                    color: '#1a1a1a',
                    marginBottom: 4,
                  }}>
                    {viewingHistory.question}
                  </h2>
                  <p style={{ fontSize: 14, color: '#64748B' }}>
                    {new Date(viewingHistory.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  {getCurrentOptionData()?.report && (
                    <button
                      onClick={() => setShowReportModal(true)}
                      style={{
                        padding: '12px 24px',
                        borderRadius: 12,
                        border: 'none',
                        background: 'linear-gradient(135deg, #6B48FF 0%, #8B5CF6 100%)',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: 14,
                        fontWeight: 600,
                        boxShadow: '0 4px 12px rgba(107, 72, 255, 0.3)',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 6px 16px rgba(107, 72, 255, 0.4)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(107, 72, 255, 0.3)';
                      }}
                    >
                      查看报告
                    </button>
                  )}
                  <button
                    onClick={handleCloseViewer}
                    style={{
                      padding: '12px 24px',
                      borderRadius: 12,
                      border: '1px solid #E2E8F0',
                      background: 'white',
                      color: '#64748B',
                      cursor: 'pointer',
                      fontSize: 14,
                      fontWeight: 600,
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#F8FAFC';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white';
                    }}
                  >
                    关闭
                  </button>
                </div>
              </div>
              
              {/* 选项切换器 - 即使只有一个选项也显示 */}
              {getAvailableOptions().length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
                  <div style={{ fontSize: 13, color: '#64748B', marginRight: 8, display: 'flex', alignItems: 'center' }}>
                    选项:
                  </div>
                  {getAvailableOptions().map(option => (
                    <button
                      key={option.id}
                      onClick={() => {
                        console.log('[历史查看] 切换到选项:', option.id, option.title);
                        setSelectedOptionId(option.id);
                      }}
                      style={{
                        padding: '8px 16px',
                        borderRadius: 10,
                        border: selectedOptionId === option.id ? 'none' : '1px solid #E2E8F0',
                        background: selectedOptionId === option.id 
                          ? 'linear-gradient(135deg, #6B48FF 0%, #8B5CF6 100%)'
                          : 'white',
                        color: selectedOptionId === option.id ? 'white' : '#64748B',
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: 600,
                        transition: 'all 0.2s ease',
                        boxShadow: selectedOptionId === option.id 
                          ? '0 2px 8px rgba(107, 72, 255, 0.3)'
                          : 'none',
                      }}
                    >
                      {option.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            {/* 场景内容 */}
            <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
              {getCurrentOptionData()?.agents && (
                <PersonaInteractionView
                  personas={getCurrentOptionData().agents.map((a: any) => ({
                    id: a.id,
                    name: a.name,
                    status: 'complete' as const,
                    score: a.score,
                    stance: a.stance,
                    thinkingHistory: a.thinking_history || [],
                  }))}
                  interactions={[]}
                  optionTitle={getCurrentOptionData().option_title || ''}
                  currentMonth={getCurrentOptionData().current_round || 0}
                  isComplete={true}
                  totalScore={getCurrentOptionData().total_score || 0}
                />
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* 报告弹窗 */}
      {showReportModal && getCurrentOptionData()?.report && (
        <DecisionReportModal
          visible={showReportModal}
          report={getCurrentOptionData().report}
          optionTitle={getCurrentOptionData().option_title || ''}
          onClose={() => setShowReportModal(false)}
        />
      )}
      
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
                        {new Date(item.created_at).toLocaleString('zh-CN')}
                      </span>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: 8,
                        background: 'rgba(10, 89, 247, 0.08)',
                        fontSize: 12,
                        fontWeight: 600,
                        color: 'rgba(10, 89, 247, 0.9)',
                      }}>
                        {item.options_count} 个选项
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
