import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { API_BASE_URL } from '../services/api';
import '../styles/AdminSettingsPage.css';

interface SystemSettings {
  site_name: string;
  site_description: string;
  allow_registration: boolean;
  require_email_verification: boolean;
  max_users: number;
  session_timeout: number;
  enable_logging: boolean;
  log_level: string;
  maintenance_mode: boolean;
  maintenance_message: string;
}

export function AdminSettingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [settings, setSettings] = useState<SystemSettings>({
    site_name: 'LifeSwarm',
    site_description: '智能决策辅助系统',
    allow_registration: true,
    require_email_verification: false,
    max_users: 10000,
    session_timeout: 7200,
    enable_logging: true,
    log_level: 'INFO',
    maintenance_mode: false,
    maintenance_message: '系统维护中，请稍后再试',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    
    // 模拟加载设置
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, [user, navigate]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      // 模拟保存
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setMessage({ type: 'success', text: '设置已保存' });
      
      // 3秒后清除消息
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('确定要重置为默认设置吗？')) {
      setSettings({
        site_name: 'LifeSwarm',
        site_description: '智能决策辅助系统',
        allow_registration: true,
        require_email_verification: false,
        max_users: 10000,
        session_timeout: 7200,
        enable_logging: true,
        log_level: 'INFO',
        maintenance_mode: false,
        maintenance_message: '系统维护中，请稍后再试',
      });
      setMessage({ type: 'success', text: '已重置为默认设置' });
      setTimeout(() => setMessage(null), 3000);
    }
  };

  if (loading) {
    return (
      <div className="admin-settings-loading">
        <div className="loading-spinner" />
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="admin-settings-page">
      {/* 背景装饰 */}
      <div className="admin-settings-background">
        <div className="admin-settings-blob admin-settings-blob-1" />
        <div className="admin-settings-blob admin-settings-blob-2" />
      </div>

      {/* 头部 */}
      <header className="admin-settings-header">
        <button 
          className="admin-settings-back-btn"
          onClick={() => navigate('/admin')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          返回
        </button>
        
        <div className="admin-settings-header-content">
          <h1 className="admin-settings-title">系统设置</h1>
          <p className="admin-settings-subtitle">配置系统参数和行为</p>
        </div>

        <div className="admin-settings-actions">
          <button
            className="admin-settings-reset-btn"
            onClick={handleReset}
            disabled={saving}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
            </svg>
            重置
          </button>
          
          <button
            className="admin-settings-save-btn"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>
                <div className="button-spinner" />
                保存中...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                  <polyline points="17 21 17 13 7 13 7 21" />
                  <polyline points="7 3 7 8 15 8" />
                </svg>
                保存设置
              </>
            )}
          </button>
        </div>
      </header>

      {/* 消息提示 */}
      {message && (
        <div className={`admin-settings-message admin-settings-message-${message.type}`}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {message.type === 'success' ? (
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3" />
            ) : (
              <circle cx="12" cy="12" r="10" />
            )}
          </svg>
          {message.text}
        </div>
      )}

      {/* 设置内容 */}
      <div className="admin-settings-container">
        {/* 基本设置 */}
        <section className="admin-settings-section">
          <div className="admin-settings-section-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <h2>基本设置</h2>
          </div>

          <div className="admin-settings-group">
            <div className="admin-settings-field">
              <label>站点名称</label>
              <input
                type="text"
                value={settings.site_name}
                onChange={(e) => setSettings({ ...settings, site_name: e.target.value })}
                placeholder="输入站点名称"
              />
            </div>

            <div className="admin-settings-field">
              <label>站点描述</label>
              <textarea
                value={settings.site_description}
                onChange={(e) => setSettings({ ...settings, site_description: e.target.value })}
                placeholder="输入站点描述"
                rows={3}
              />
            </div>
          </div>
        </section>

        {/* 用户管理 */}
        <section className="admin-settings-section">
          <div className="admin-settings-section-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <h2>用户管理</h2>
          </div>

          <div className="admin-settings-group">
            <div className="admin-settings-toggle">
              <div className="admin-settings-toggle-info">
                <label>允许用户注册</label>
                <p>关闭后新用户将无法注册账号</p>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.allow_registration}
                  onChange={(e) => setSettings({ ...settings, allow_registration: e.target.checked })}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="admin-settings-toggle">
              <div className="admin-settings-toggle-info">
                <label>要求邮箱验证</label>
                <p>新用户注册后需要验证邮箱才能使用</p>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.require_email_verification}
                  onChange={(e) => setSettings({ ...settings, require_email_verification: e.target.checked })}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="admin-settings-field">
              <label>最大用户数</label>
              <input
                type="number"
                value={settings.max_users}
                onChange={(e) => setSettings({ ...settings, max_users: parseInt(e.target.value) || 0 })}
                min="0"
              />
              <p className="admin-settings-field-hint">0 表示不限制</p>
            </div>

            <div className="admin-settings-field">
              <label>会话超时时间（秒）</label>
              <input
                type="number"
                value={settings.session_timeout}
                onChange={(e) => setSettings({ ...settings, session_timeout: parseInt(e.target.value) || 0 })}
                min="300"
                step="300"
              />
              <p className="admin-settings-field-hint">用户无操作后自动登出的时间</p>
            </div>
          </div>
        </section>

        {/* 系统日志 */}
        <section className="admin-settings-section">
          <div className="admin-settings-section-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            <h2>系统日志</h2>
          </div>

          <div className="admin-settings-group">
            <div className="admin-settings-toggle">
              <div className="admin-settings-toggle-info">
                <label>启用日志记录</label>
                <p>记录系统运行日志和用户操作</p>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={settings.enable_logging}
                  onChange={(e) => setSettings({ ...settings, enable_logging: e.target.checked })}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="admin-settings-field">
              <label>日志级别</label>
              <select
                value={settings.log_level}
                onChange={(e) => setSettings({ ...settings, log_level: e.target.value })}
                disabled={!settings.enable_logging}
              >
                <option value="DEBUG">DEBUG - 调试信息</option>
                <option value="INFO">INFO - 一般信息</option>
                <option value="WARNING">WARNING - 警告信息</option>
                <option value="ERROR">ERROR - 错误信息</option>
                <option value="CRITICAL">CRITICAL - 严重错误</option>
              </select>
            </div>
          </div>
        </section>

        {/* 维护模式 */}
        <section className="admin-settings-section admin-settings-section-danger">
          <div className="admin-settings-section-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <h2>维护模式</h2>
          </div>

          <div className="admin-settings-group">
            <div className="admin-settings-toggle">
              <div className="admin-settings-toggle-info">
                <label>启用维护模式</label>
                <p>启用后普通用户将无法访问系统</p>
              </div>
              <label className="toggle-switch toggle-switch-danger">
                <input
                  type="checkbox"
                  checked={settings.maintenance_mode}
                  onChange={(e) => setSettings({ ...settings, maintenance_mode: e.target.checked })}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="admin-settings-field">
              <label>维护提示信息</label>
              <textarea
                value={settings.maintenance_message}
                onChange={(e) => setSettings({ ...settings, maintenance_message: e.target.value })}
                placeholder="输入维护提示信息"
                rows={3}
                disabled={!settings.maintenance_mode}
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
