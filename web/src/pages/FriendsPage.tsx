import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import * as friendService from '../services/friendService';

interface Friend {
  user_id: string;
  username: string;
  nickname: string;
  avatar_url?: string;
  status: 'online' | 'offline';
  lastSeen?: string;
}

interface FriendRequest {
  request_id: string;
  from_user_id: string;
  from_username: string;
  from_nickname: string;
  from_avatar_url?: string;
  message: string;
  created_at: string;
}

interface SearchResult {
  user_id: string;
  username: string;
  nickname: string;
  avatar_url?: string;
  email?: string;
  is_friend: boolean;
}

export function FriendsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [friendRequests, setFriendRequests] = useState<FriendRequest[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'friends' | 'requests' | 'search'>('friends');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载好友列表
  useEffect(() => {
    if (user?.user_id && activeTab === 'friends') {
      loadFriends();
    }
  }, [user?.user_id, activeTab]);

  // 加载好友请求
  useEffect(() => {
    if (user?.user_id && activeTab === 'requests') {
      loadFriendRequests();
    }
  }, [user?.user_id, activeTab]);

  const loadFriends = async () => {
    if (!user?.user_id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await friendService.getFriends(user.user_id);
      setFriends(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
      console.error('加载好友列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadFriendRequests = async () => {
    if (!user?.user_id) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await friendService.getFriendRequests(user.user_id);
      setFriendRequests(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
      console.error('加载好友请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!user?.user_id || !searchQuery.trim()) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await friendService.searchUsers(searchQuery.trim(), user.user_id);
      setSearchResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败');
      console.error('搜索用户失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendRequest = async (toUserId: string) => {
    if (!user?.user_id) return;
    
    try {
      setLoading(true);
      setError(null);
      await friendService.sendFriendRequest(user.user_id, toUserId);
      alert('好友请求已发送');
      // 重新搜索以更新状态
      await handleSearch();
    } catch (err) {
      alert(err instanceof Error ? err.message : '发送失败');
      console.error('发送好友请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRequest = async (requestId: string) => {
    if (!user?.user_id) return;
    
    try {
      setLoading(true);
      setError(null);
      await friendService.acceptFriendRequest(requestId, user.user_id);
      alert('已成为好友');
      await loadFriendRequests();
    } catch (err) {
      alert(err instanceof Error ? err.message : '操作失败');
      console.error('接受好友请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRejectRequest = async (requestId: string) => {
    if (!user?.user_id) return;
    
    try {
      setLoading(true);
      setError(null);
      await friendService.rejectFriendRequest(requestId, user.user_id);
      alert('已拒绝');
      await loadFriendRequests();
    } catch (err) {
      alert(err instanceof Error ? err.message : '操作失败');
      console.error('拒绝好友请求失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const initial = (name: string) => name.slice(0, 1).toUpperCase();

  return (
    <div className="ls-homepage" style={{ minHeight: '100vh', paddingBottom: 80 }}>
      {/* 动画背景 */}
      <div className="ls-background">
        <div className="ls-blob ls-blob-1" />
        <div className="ls-blob ls-blob-2" />
        <div className="ls-blob ls-blob-3" />
      </div>

      {/* 顶部导航 */}
      <div className="app-topnav">
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 12px',
            borderRadius: 12,
            transition: 'all 0.2s',
            color: 'var(--text-primary)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(10, 89, 247, 0.08)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span style={{ fontSize: 14, fontWeight: 600 }}>返回首页</span>
        </button>
        <div style={{ flex: 1 }} />
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>
          好友
        </div>
      </div>

      {/* 主内容容器 */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '80px 28px 40px' }}>
        {/* 英雄卡片 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 24, padding: '28px 32px',
          borderRadius: 28, marginBottom: 24,
          background: 'linear-gradient(135deg, rgba(10, 89, 247, 0.08) 0%, rgba(107, 72, 255, 0.06) 100%)',
          border: '1px solid rgba(10, 89, 247, 0.12)',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
        }}>
          {/* 微光效果 */}
          <div style={{
            position: 'absolute', top: 0, right: 0, width: '50%', height: '100%',
            background: 'radial-gradient(ellipse at 80% 50%, rgba(10, 89, 247, 0.08), transparent 60%)',
            pointerEvents: 'none',
          }}/>
          
          {/* 图标 */}
          <div style={{
            width: 80, height: 80, borderRadius: '50%', flexShrink: 0,
            background: 'linear-gradient(135deg, #B0D9FF 0%, #7DBDFF 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 32, fontWeight: 800, color: '#fff',
            boxShadow: '0 12px 32px rgba(10, 89, 247, 0.25)',
            position: 'relative',
          }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          
          {/* 标题信息 */}
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 6, color: '#1A1A1A' }}>
              好友
            </div>
            <div style={{ fontSize: 14, color: '#666', marginBottom: 12, letterSpacing: '0.02em' }}>
              管理你的好友关系
            </div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <div style={{
                padding: '4px 12px',
                borderRadius: 999,
                fontSize: 12,
                fontWeight: 600,
                background: 'rgba(10, 89, 247, 0.12)',
                color: '#0A59F7',
              }}>
                {friends.length} 位好友
              </div>
            </div>
          </div>
        </div>

        {/* 标签页 */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: 28,
          padding: '8px',
          marginBottom: 24,
          boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
          border: '1px solid rgba(0, 0, 0, 0.06)',
          display: 'flex',
          gap: 8,
        }}>
          {[
            { 
              id: 'friends', 
              label: '好友列表', 
              icon: (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              )
            },
            { 
              id: 'requests', 
              label: '好友请求', 
              icon: (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
              )
            },
            { 
              id: 'search', 
              label: '添加好友', 
              icon: (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
              )
            },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                flex: 1,
                padding: '12px 20px',
                borderRadius: 20,
                border: activeTab === tab.id ? '2px solid rgba(10, 89, 247, 0.3)' : '2px solid transparent',
                background: activeTab === tab.id 
                  ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(250, 252, 255, 0.95) 100%)'
                  : 'transparent',
                color: activeTab === tab.id ? 'rgba(0, 0, 0, 0.85)' : '#666',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.3s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                boxShadow: activeTab === tab.id 
                  ? '0 4px 12px rgba(10, 89, 247, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
                  : 'none',
                position: 'relative',
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* 树洞入口卡片 */}
        <div 
          onClick={() => navigate('/tree-hole')}
          style={{
            background: 'linear-gradient(135deg, rgba(176, 217, 255, 0.15) 0%, rgba(125, 189, 255, 0.1) 100%)',
            backdropFilter: 'blur(20px)',
            borderRadius: 28,
            padding: '24px 32px',
            marginBottom: 24,
            boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
            border: '1px solid rgba(10, 89, 247, 0.15)',
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            cursor: 'pointer',
            transition: 'all 0.3s',
            position: 'relative',
            overflow: 'hidden',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 24px 56px rgba(10, 89, 247, 0.15)';
            e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.3)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 18px 48px rgba(0, 0, 0, 0.04)';
            e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.15)';
          }}
        >
          {/* 背景装饰 */}
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '40%',
            height: '100%',
            background: 'radial-gradient(ellipse at 80% 50%, rgba(10, 89, 247, 0.08), transparent 70%)',
            pointerEvents: 'none',
          }}/>

          {/* 树洞图标 */}
          <div style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #B0D9FF 0%, #7DBDFF 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 32,
            flexShrink: 0,
            boxShadow: '0 8px 24px rgba(10, 89, 247, 0.2)',
            position: 'relative',
          }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
              <circle cx="12" cy="11" r="3"/>
              <path d="M12 14c-3.31 0-6 2.69-6 6h12c0-3.31-2.69-6-6-6z"/>
            </svg>
          </div>

          {/* 内容 */}
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{ 
              fontSize: 20, 
              fontWeight: 800, 
              color: '#1A1A1A', 
              marginBottom: 4,
              letterSpacing: '-0.01em',
            }}>
              树洞世界
            </div>
            <div style={{ fontSize: 14, color: '#666', lineHeight: 1.5 }}>
              匿名分享你的心情、秘密和梦想，探索2.5D树洞地图
            </div>
          </div>

          {/* 箭头 */}
          <div style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'rgba(10, 89, 247, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            transition: 'all 0.3s',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0A59F7" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </div>
        </div>

        {/* 好友列表 */}
        {activeTab === 'friends' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 28,
            padding: 32,
            boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
            border: '1px solid rgba(0, 0, 0, 0.06)',
          }}>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>我的好友</h2>
              <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>共 {friends.length} 位好友</p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {loading ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                  加载中...
                </div>
              ) : friends.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="1.5">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                      <circle cx="9" cy="7" r="4"/>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                  </div>
                  <p style={{ margin: 0, fontSize: 14, color: '#999' }}>
                    还没有好友，快去添加吧
                  </p>
                </div>
              ) : (
                friends.map(friend => (
                  <div
                    key={friend.user_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '16px 18px',
                      borderRadius: 18,
                      background: 'rgba(10, 89, 247, 0.02)',
                      border: '1px solid rgba(10, 89, 247, 0.08)',
                      transition: 'all 0.3s',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = 'rgba(10, 89, 247, 0.04)';
                      e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.15)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = 'rgba(10, 89, 247, 0.02)';
                      e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.08)';
                    }}
                  >
                    {/* 头像 */}
                    <div style={{
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #B0D9FF 0%, #7DBDFF 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 20,
                      fontWeight: 800,
                      color: '#fff',
                      position: 'relative',
                    }}>
                      {friend.avatar_url ? (
                        <img src={friend.avatar_url} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                      ) : (
                        initial(friend.nickname)
                      )}
                      {/* 在线状态 */}
                      <div style={{
                        position: 'absolute',
                        bottom: 0,
                        right: 0,
                        width: 14,
                        height: 14,
                        borderRadius: '50%',
                        background: friend.status === 'online' ? '#34C759' : '#999',
                        border: '2px solid #fff',
                      }}/>
                    </div>

                    {/* 信息 */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: '#1A1A1A', marginBottom: 4 }}>
                        {friend.nickname}
                      </div>
                      <div style={{ fontSize: 13, color: '#999' }}>
                        @{friend.username}
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    <button
                      style={{
                        padding: '8px 16px',
                        borderRadius: 12,
                        border: 'none',
                        background: 'linear-gradient(135deg, #0A59F7 0%, #6B48FF 100%)',
                        color: '#fff',
                        fontSize: 13,
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.3s',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.transform = 'scale(1)';
                      }}
                    >
                      发消息
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* 好友请求 */}
        {activeTab === 'requests' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 28,
            padding: 32,
            boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
            border: '1px solid rgba(0, 0, 0, 0.06)',
          }}>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>好友请求</h2>
              <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>共 {friendRequests.length} 条请求</p>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                加载中...
              </div>
            ) : friendRequests.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="1.5">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                </div>
                <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#1A1A1A', marginBottom: 8 }}>
                  暂无好友请求
                </h3>
                <p style={{ margin: 0, fontSize: 14, color: '#999' }}>
                  当有人向你发送好友请求时，会显示在这里
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {friendRequests.map(request => (
                  <div
                    key={request.request_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '16px 18px',
                      borderRadius: 18,
                      background: 'rgba(10, 89, 247, 0.02)',
                      border: '1px solid rgba(10, 89, 247, 0.08)',
                    }}
                  >
                    {/* 头像 */}
                    <div style={{
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #B0D9FF 0%, #7DBDFF 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 20,
                      fontWeight: 800,
                      color: '#fff',
                    }}>
                      {request.from_avatar_url ? (
                        <img src={request.from_avatar_url} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                      ) : (
                        initial(request.from_nickname)
                      )}
                    </div>

                    {/* 信息 */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: '#1A1A1A', marginBottom: 4 }}>
                        {request.from_nickname}
                      </div>
                      <div style={{ fontSize: 13, color: '#999', marginBottom: 4 }}>
                        @{request.from_username}
                      </div>
                      {request.message && (
                        <div style={{ fontSize: 13, color: '#666', fontStyle: 'italic' }}>
                          "{request.message}"
                        </div>
                      )}
                    </div>

                    {/* 操作按钮 */}
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => handleAcceptRequest(request.request_id)}
                        disabled={loading}
                        style={{
                          padding: '8px 16px',
                          borderRadius: 12,
                          border: 'none',
                          background: 'linear-gradient(135deg, #34C759 0%, #30D158 100%)',
                          color: '#fff',
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: loading ? 'not-allowed' : 'pointer',
                          opacity: loading ? 0.6 : 1,
                        }}
                      >
                        接受
                      </button>
                      <button
                        onClick={() => handleRejectRequest(request.request_id)}
                        disabled={loading}
                        style={{
                          padding: '8px 16px',
                          borderRadius: 12,
                          border: '1px solid rgba(0, 0, 0, 0.1)',
                          background: '#fff',
                          color: '#666',
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: loading ? 'not-allowed' : 'pointer',
                          opacity: loading ? 0.6 : 1,
                        }}
                      >
                        拒绝
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 添加好友 */}
        {activeTab === 'search' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 28,
            padding: 32,
            boxShadow: '0 18px 48px rgba(0, 0, 0, 0.04)',
            border: '1px solid rgba(0, 0, 0, 0.06)',
          }}>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#1A1A1A' }}>添加好友</h2>
              <p style={{ margin: '6px 0 0', fontSize: 14, color: '#666' }}>通过用户名搜索并添加好友</p>
            </div>

            <div style={{ position: 'relative', marginBottom: 24 }}>
              <input
                type="text"
                placeholder="输入用户名搜索..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && handleSearch()}
                style={{
                  width: '100%',
                  padding: '14px 48px 14px 20px',
                  borderRadius: 16,
                  border: '2px solid rgba(10, 89, 247, 0.15)',
                  fontSize: 15,
                  outline: 'none',
                  transition: 'all 0.3s',
                }}
                onFocus={e => {
                  e.currentTarget.style.borderColor = '#0A59F7';
                }}
                onBlur={e => {
                  e.currentTarget.style.borderColor = 'rgba(10, 89, 247, 0.15)';
                }}
              />
              <button
                onClick={handleSearch}
                disabled={loading || !searchQuery.trim()}
                style={{
                  position: 'absolute',
                  right: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  padding: '8px 16px',
                  borderRadius: 12,
                  border: 'none',
                  background: 'linear-gradient(135deg, #0A59F7 0%, #6B48FF 100%)',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: loading || !searchQuery.trim() ? 'not-allowed' : 'pointer',
                  opacity: loading || !searchQuery.trim() ? 0.6 : 1,
                }}
              >
                {loading ? '搜索中...' : '搜索'}
              </button>
            </div>

            {searchResults.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'center' }}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" strokeWidth="1.5">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.35-4.35"/>
                  </svg>
                </div>
                <p style={{ margin: 0, fontSize: 14, color: '#999' }}>
                  {searchQuery ? '未找到匹配的用户' : '输入用户名开始搜索'}
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {searchResults.map(result => (
                  <div
                    key={result.user_id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '16px 18px',
                      borderRadius: 18,
                      background: 'rgba(10, 89, 247, 0.02)',
                      border: '1px solid rgba(10, 89, 247, 0.08)',
                    }}
                  >
                    {/* 头像 */}
                    <div style={{
                      width: 52,
                      height: 52,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #B0D9FF 0%, #7DBDFF 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 20,
                      fontWeight: 800,
                      color: '#fff',
                    }}>
                      {result.avatar_url ? (
                        <img src={result.avatar_url} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
                      ) : (
                        initial(result.nickname)
                      )}
                    </div>

                    {/* 信息 */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: '#1A1A1A', marginBottom: 4 }}>
                        {result.nickname}
                      </div>
                      <div style={{ fontSize: 13, color: '#999' }}>
                        @{result.username}
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    {result.is_friend ? (
                      <div style={{
                        padding: '8px 16px',
                        borderRadius: 12,
                        background: 'rgba(52, 199, 89, 0.1)',
                        color: '#34C759',
                        fontSize: 13,
                        fontWeight: 600,
                      }}>
                        已是好友
                      </div>
                    ) : (
                      <button
                        onClick={() => handleSendRequest(result.user_id)}
                        disabled={loading}
                        style={{
                          padding: '8px 16px',
                          borderRadius: 12,
                          border: 'none',
                          background: 'linear-gradient(135deg, #0A59F7 0%, #6B48FF 100%)',
                          color: '#fff',
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: loading ? 'not-allowed' : 'pointer',
                          opacity: loading ? 0.6 : 1,
                        }}
                      >
                        添加好友
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
