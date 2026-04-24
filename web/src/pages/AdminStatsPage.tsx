import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { API_BASE_URL } from '../services/api';
import '../styles/AdminStatsPage.css';

interface UserStats {
  total: number;
  active: number;
  inactive: number;
  new_7d: number;
  active_24h: number;
}

interface DecisionStats {
  total: number;
  today: number;
  this_week: number;
  by_category: Record<string, number>;
  avg_options: number;
}

interface SystemStats {
  users: UserStats;
  decisions: DecisionStats;
  timestamp: string;
}

export function AdminStatsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  const getToken = () => {
    const authData = localStorage.getItem('choicerealm.web.auth');
    if (!authData) return null;
    const auth = JSON.parse(authData);
    return auth.token;
  };

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    loadStats();
    
    // 每30秒刷新一次
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, [user, navigate]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const token = getToken();
      if (!token) {
        navigate('/auth');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/admin/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        setStats(result);
      } else if (response.status === 403) {
        alert('您没有管理员权限');
        navigate('/');
      }
    } catch (error) {
      if (import.meta.env.DEV) {
        console.log('加载统计数据失败:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN');
  };

  return (
    <div className="admin-stats-page">
      <div className="admin-stats-background">
        <div className="admin-stats-blob admin-stats-blob-1" />
        <div className="admin-stats-blob admin-stats-blob-2" />
      </div>

      <div className="admin-stats-header">
        <button className="admin-back-btn" onClick={() => navigate('/admin')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          返回管理中心
        </button>
        <h1 className="admin-stats-title">系统统计</h1>
        {stats && (
          <div className="admin-stats-time">
            最后更新: {formatTime(stats.timestamp)}
          </div>
        )}
      </div>

      {loading && !stats ? (
        <div className="admin-stats-loading">
          <div className="admin-loading-spinner" />
          <p>加载中...</p>
        </div>
      ) : stats ? (
        <div className="admin-stats-container">
          {/* 用户统计卡片 */}
          <div className="admin-stats-card">
            <div className="admin-stats-card-header">
              <h2>用户统计</h2>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>
            <div className="admin-stats-grid">
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">总用户数</div>
                <div className="admin-stats-item-value">{stats.users.total}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">活跃用户</div>
                <div className="admin-stats-item-value admin-stats-success">{stats.users.active}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">禁用用户</div>
                <div className="admin-stats-item-value admin-stats-danger">{stats.users.inactive}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">24小时活跃</div>
                <div className="admin-stats-item-value admin-stats-info">{stats.users.active_24h}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">7天新增</div>
                <div className="admin-stats-item-value admin-stats-warning">{stats.users.new_7d}</div>
              </div>
            </div>
          </div>

          {/* 决策统计卡片 */}
          <div className="admin-stats-card">
            <div className="admin-stats-card-header">
              <h2>决策统计</h2>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <div className="admin-stats-grid">
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">总决策数</div>
                <div className="admin-stats-item-value admin-stats-primary">{stats.decisions.total}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">今日决策</div>
                <div className="admin-stats-item-value admin-stats-success">{stats.decisions.today}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">本周决策</div>
                <div className="admin-stats-item-value admin-stats-info">{stats.decisions.this_week}</div>
              </div>
              <div className="admin-stats-item">
                <div className="admin-stats-item-label">平均选项数</div>
                <div className="admin-stats-item-value admin-stats-warning">{stats.decisions.avg_options}</div>
              </div>
            </div>
          </div>

          {/* 决策分类统计 */}
          {Object.keys(stats.decisions.by_category).length > 0 && (
            <div className="admin-stats-card admin-stats-card-wide">
              <div className="admin-stats-card-header">
                <h2>决策分类分布</h2>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
              </div>
              <div className="admin-category-list">
                {Object.entries(stats.decisions.by_category)
                  .sort(([, a], [, b]) => b - a)
                  .map(([category, count]) => {
                    const percentage = ((count / stats.decisions.total) * 100).toFixed(1);
                    return (
                      <div key={category} className="admin-category-row">
                        <div className="admin-category-info">
                          <span className="admin-category-name">{category}</span>
                          <span className="admin-category-count">{count} 次</span>
                        </div>
                        <div className="admin-category-bar-container">
                          <div 
                            className="admin-category-bar" 
                            style={{ width: `${percentage}%` }}
                          />
                          <span className="admin-category-percentage">{percentage}%</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* 快速操作 */}
          <div className="admin-stats-actions">
            <button 
              className="admin-stats-action-btn"
              onClick={() => navigate('/admin/users')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              管理用户
            </button>
            <button 
              className="admin-stats-action-btn"
              onClick={loadStats}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
              </svg>
              刷新数据
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
