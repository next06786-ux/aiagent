import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { API_BASE_URL } from '../services/api';
import '../styles/AdminUsersPage.css';

interface User {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export function AdminUsersPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [pagination, setPagination] = useState<Pagination>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // 获取token
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
    loadUsers();
  }, [pagination.page, search, user, navigate]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const token = getToken();
      if (!token) {
        navigate('/auth');
        return;
      }

      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.page_size.toString(),
      });
      
      if (search) {
        params.append('search', search);
      }

      const response = await fetch(
        `${API_BASE_URL}/api/admin/users?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('用户列表数据:', result);
        
        // 检查返回的数据结构
        if (result.success && result.data) {
          setUsers(result.data.users || []);
          setPagination(result.data.pagination || pagination);
        } else {
          console.error('数据格式错误:', result);
        }
      } else if (response.status === 403) {
        alert('您没有管理员权限');
        navigate('/');
      } else {
        console.log('加载用户列表失败，状态码:', response.status);
      }
    } catch (error) {
      // 静默处理连接错误
      if (import.meta.env.DEV) {
        console.log('加载用户列表失败（后端可能未启动）:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearch(value);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleToggleStatus = async (userId: string, currentStatus: boolean) => {
    try {
      const token = getToken();
      if (!token) return;

      const response = await fetch(
        `${API_BASE_URL}/api/admin/users/${userId}/status`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ is_active: !currentStatus }),
        }
      );

      if (response.ok) {
        loadUsers();
      }
    } catch (error) {
      console.error('更新用户状态失败:', error);
    }
  };

  const handleViewDetail = async (user: User) => {
    setSelectedUser(user);
    setShowDetailModal(true);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '从未';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  return (
    <div className="admin-users-page">
      <div className="admin-users-background">
        <div className="admin-users-blob admin-users-blob-1" />
        <div className="admin-users-blob admin-users-blob-2" />
      </div>

      <div className="admin-users-header">
        <button className="admin-back-btn" onClick={() => navigate('/admin')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          返回管理中心
        </button>
        <h1 className="admin-users-title">用户管理</h1>
      </div>

      <div className="admin-users-container">
        <div className="admin-users-toolbar">
          <div className="admin-search-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="搜索用户名、邮箱或昵称..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>
          <div className="admin-stats-mini">
            <div className="admin-stat-mini">
              <span className="admin-stat-mini-label">总用户</span>
              <span className="admin-stat-mini-value">{pagination.total}</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="admin-users-loading">
            <div className="admin-loading-spinner" />
            <p>加载中...</p>
          </div>
        ) : (
          <>
            <div className="admin-users-table-container">
              <table className="admin-users-table">
                <thead>
                  <tr>
                    <th>用户</th>
                    <th>邮箱</th>
                    <th>状态</th>
                    <th>注册时间</th>
                    <th>最后登录</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.user_id}>
                      <td>
                        <div className="admin-user-cell">
                          <div className="admin-user-avatar">
                            {user.avatar_url ? (
                              <img src={user.avatar_url} alt={user.username} />
                            ) : (
                              <span>{user.username.charAt(0).toUpperCase()}</span>
                            )}
                          </div>
                          <div className="admin-user-info">
                            <div className="admin-user-name">{user.nickname || user.username}</div>
                            <div className="admin-user-username">@{user.username}</div>
                          </div>
                        </div>
                      </td>
                      <td>{user.email}</td>
                      <td>
                        <span className={`admin-status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? '活跃' : '禁用'}
                        </span>
                      </td>
                      <td>{formatDate(user.created_at)}</td>
                      <td>{formatDate(user.last_login)}</td>
                      <td>
                        <div className="admin-actions">
                          <button
                            className="admin-action-btn admin-action-view"
                            onClick={() => handleViewDetail(user)}
                            title="查看详情"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                          </button>
                          <button
                            className={`admin-action-btn ${user.is_active ? 'admin-action-disable' : 'admin-action-enable'}`}
                            onClick={() => handleToggleStatus(user.user_id, user.is_active)}
                            title={user.is_active ? '禁用' : '启用'}
                          >
                            {user.is_active ? (
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                              </svg>
                            ) : (
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                <polyline points="22 4 12 14.01 9 11.01" />
                              </svg>
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pagination.total_pages > 1 && (
              <div className="admin-pagination">
                <button
                  className="admin-page-btn"
                  disabled={pagination.page === 1}
                  onClick={() => setPagination((prev) => ({ ...prev, page: prev.page - 1 }))}
                >
                  上一页
                </button>
                <div className="admin-page-info">
                  第 {pagination.page} / {pagination.total_pages} 页
                </div>
                <button
                  className="admin-page-btn"
                  disabled={pagination.page === pagination.total_pages}
                  onClick={() => setPagination((prev) => ({ ...prev, page: prev.page + 1 }))}
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {showDetailModal && selectedUser && (
        <div className="admin-modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
            <div className="admin-modal-header">
              <h2>用户详情</h2>
              <button className="admin-modal-close" onClick={() => setShowDetailModal(false)}>
                ✕
              </button>
            </div>
            <div className="admin-modal-body">
              <div className="admin-detail-section">
                <div className="admin-detail-avatar-large">
                  {selectedUser.avatar_url ? (
                    <img src={selectedUser.avatar_url} alt={selectedUser.username} />
                  ) : (
                    <span>{selectedUser.username.charAt(0).toUpperCase()}</span>
                  )}
                </div>
                <h3>{selectedUser.nickname || selectedUser.username}</h3>
                <p className="admin-detail-username">@{selectedUser.username}</p>
              </div>
              
              <div className="admin-detail-grid">
                <div className="admin-detail-item">
                  <label>用户ID</label>
                  <span className="admin-detail-id">{selectedUser.user_id}</span>
                </div>
                <div className="admin-detail-item">
                  <label>用户名</label>
                  <span>{selectedUser.username}</span>
                </div>
                <div className="admin-detail-item">
                  <label>昵称</label>
                  <span>{selectedUser.nickname || '未设置'}</span>
                </div>
                <div className="admin-detail-item">
                  <label>邮箱</label>
                  <span>{selectedUser.email}</span>
                </div>
                <div className="admin-detail-item">
                  <label>手机号</label>
                  <span>{selectedUser.phone || '未设置'}</span>
                </div>
                <div className="admin-detail-item">
                  <label>账号状态</label>
                  <span className={`admin-status-badge ${selectedUser.is_active ? 'active' : 'inactive'}`}>
                    {selectedUser.is_active ? '活跃' : '禁用'}
                  </span>
                </div>
                <div className="admin-detail-item">
                  <label>验证状态</label>
                  <span className={`admin-status-badge ${selectedUser.is_verified ? 'active' : 'inactive'}`}>
                    {selectedUser.is_verified ? '已验证' : '未验证'}
                  </span>
                </div>
                <div className="admin-detail-item">
                  <label>注册时间</label>
                  <span>{formatDate(selectedUser.created_at)}</span>
                </div>
                <div className="admin-detail-item">
                  <label>最后登录</label>
                  <span>{formatDate(selectedUser.last_login)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
