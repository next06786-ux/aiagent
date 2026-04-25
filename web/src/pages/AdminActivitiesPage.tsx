import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { API_BASE_URL } from '../services/api';
import '../styles/AdminActivitiesPage.css';

interface Activity {
  id: string;
  user_id: string;
  username: string;
  action: string;
  details: string;
  timestamp: string;
  ip_address?: string;
}

export function AdminActivitiesPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5); // 秒

  // 获取活动记录
  const fetchActivities = async () => {
    try {
      const authData = localStorage.getItem('choicerealm.web.auth');
      if (!authData) return;
      
      const auth = JSON.parse(authData);
      const token = auth.token;
      
      const response = await fetch(`${API_BASE_URL}/api/admin/activities?limit=50`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities || []);
      } else if (response.status === 403) {
        alert('您没有管理员权限');
        navigate('/');
      }
    } catch (error) {
      console.error('获取活动记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    
    fetchActivities();
  }, [user, navigate]);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchActivities();
    }, refreshInterval * 1000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) {
      return '刚刚';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)}小时前`;
    } else {
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  // 获取活动类型的图标和颜色
  const getActivityStyle = (action: string) => {
    const styles: Record<string, { icon: string; color: string }> = {
      'login': { icon: '🔐', color: '#10b981' },
      'logout': { icon: '👋', color: '#6b7280' },
      'register': { icon: '✨', color: '#0A59F7' },
      'create_decision': { icon: '🎯', color: '#6B48FF' },
      'update_profile': { icon: '👤', color: '#3b82f6' },
      'import_data': { icon: '📥', color: '#8B5CF6' },
      'export_data': { icon: '📤', color: '#ec4899' },
      'delete': { icon: '🗑️', color: '#ef4444' },
      'error': { icon: '⚠️', color: '#f59e0b' },
    };
    
    return styles[action] || { icon: '📝', color: '#6b7280' };
  };

  if (loading) {
    return (
      <div className="admin-activities-loading">
        <div className="loading-spinner" />
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="admin-activities-page">
      {/* 背景装饰 */}
      <div className="admin-activities-background">
        <div className="admin-activities-blob admin-activities-blob-1" />
        <div className="admin-activities-blob admin-activities-blob-2" />
      </div>

      {/* 头部 */}
      <header className="admin-activities-header">
        <button 
          className="admin-activities-back-btn"
          onClick={() => navigate('/admin')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        
        <div className="admin-activities-header-content">
          <h1 className="admin-activities-title">活动监控</h1>
          <p className="admin-activities-subtitle">实时监控系统活动</p>
        </div>

        <div className="admin-activities-controls">
          <div className="admin-activities-refresh-control">
            <label className="admin-activities-checkbox">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              <span>自动刷新</span>
            </label>
            
            {autoRefresh && (
              <select
                className="admin-activities-interval-select"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
              >
                <option value={3}>3秒</option>
                <option value={5}>5秒</option>
                <option value={10}>10秒</option>
                <option value={30}>30秒</option>
              </select>
            )}
          </div>
          
          <button
            className="admin-activities-refresh-btn"
            onClick={fetchActivities}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
            </svg>
            刷新
          </button>
        </div>
      </header>

      {/* 活动列表 */}
      <div className="admin-activities-container">
        {activities.length === 0 ? (
          <div className="admin-activities-empty">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <p>暂无活动记录</p>
          </div>
        ) : (
          <div className="admin-activities-timeline">
            {activities.map((activity) => {
              const style = getActivityStyle(activity.action);
              return (
                <div key={activity.id} className="admin-activity-item">
                  <div 
                    className="admin-activity-icon"
                    style={{ '--activity-color': style.color } as React.CSSProperties}
                  >
                    <span>{style.icon}</span>
                  </div>
                  
                  <div className="admin-activity-content">
                    <div className="admin-activity-header">
                      <span className="admin-activity-user">{activity.username}</span>
                      <span className="admin-activity-action">{activity.action}</span>
                      <span className="admin-activity-time">{formatTime(activity.timestamp)}</span>
                    </div>
                    
                    {activity.details && (
                      <div className="admin-activity-details">{activity.details}</div>
                    )}
                    
                    {activity.ip_address && (
                      <div className="admin-activity-meta">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="2" y1="12" x2="22" y2="12" />
                          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                        </svg>
                        {activity.ip_address}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
