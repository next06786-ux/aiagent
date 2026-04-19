/**
 * LLM 提供者切换组件
 * 支持在 API 大模型和基座模型之间切换
 */
import React, { useState, useEffect } from 'react';
import {
  getLLMStatus,
  switchLLMProvider,
  testLLMProvider,
  getProviderDisplayName,
  getProviderIcon,
  type LLMStatus,
  type LLMProvider,
} from '../services/llmService';
import '../styles/LLMSwitcher.css';

export const LLMSwitcher: React.FC = () => {
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [remoteUrl, setRemoteUrl] = useState('');

  // 加载状态
  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLLMStatus();
      setStatus(data);
      setRemoteUrl(data.remote_model_url || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitch = async (provider: string) => {
    if (!status) return;

    try {
      setSwitching(true);
      setError(null);
      setSuccess(null);

      const request = {
        provider,
        remote_url: provider === 'remote_model' ? remoteUrl : undefined,
      };

      const result = await switchLLMProvider(request);
      setSuccess(result.message);
      
      // 重新加载状态
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : '切换失败');
    } finally {
      setSwitching(false);
    }
  };

  const handleTest = async (provider: string) => {
    try {
      setTesting(provider);
      setError(null);
      setSuccess(null);

      const request = {
        provider,
        remote_url: provider === 'remote_model' ? remoteUrl : undefined,
      };

      const result = await testLLMProvider(request);
      
      if (result.success) {
        setSuccess(`测试成功: ${result.response?.substring(0, 50)}...`);
      } else {
        setError(`测试失败: ${result.error}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '测试失败');
    } finally {
      setTesting(null);
    }
  };

  if (loading) {
    return (
      <div className="llm-switcher">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="llm-switcher">
        <div className="error">无法加载 LLM 状态</div>
      </div>
    );
  }

  return (
    <div className="llm-switcher">
      <div className="llm-switcher-header">
        <h3>🤖 大模型切换</h3>
        <button className="refresh-btn" onClick={loadStatus} disabled={loading}>
          🔄 刷新
        </button>
      </div>

      {error && (
        <div className="message error-message">
          ❌ {error}
        </div>
      )}

      {success && (
        <div className="message success-message">
          ✅ {success}
        </div>
      )}

      <div className="current-provider">
        <div className="label">当前使用:</div>
        <div className="value">
          {getProviderIcon(status.current_provider)}{' '}
          {getProviderDisplayName(status.current_provider)}
        </div>
      </div>

      <div className="providers-list">
        {Object.entries(status.available_providers).map(([key, provider]) => (
          <div
            key={key}
            className={`provider-card ${
              key === status.current_provider ? 'active' : ''
            } ${provider.available ? 'available' : 'unavailable'}`}
          >
            <div className="provider-header">
              <div className="provider-icon">{getProviderIcon(key)}</div>
              <div className="provider-info">
                <div className="provider-name">{provider.name}</div>
                <div className="provider-description">{provider.description}</div>
              </div>
            </div>

            <div className="provider-status">
              <span className={`status-badge ${provider.available ? 'available' : 'unavailable'}`}>
                {provider.status}
              </span>
            </div>

            {key === 'remote_model' && (
              <div className="remote-url-input">
                <input
                  type="text"
                  value={remoteUrl}
                  onChange={(e) => setRemoteUrl(e.target.value)}
                  placeholder="http://your-server-ip:8001"
                  disabled={switching || testing === key}
                />
              </div>
            )}

            <div className="provider-actions">
              <button
                className="test-btn"
                onClick={() => handleTest(key)}
                disabled={!provider.available || switching || testing !== null}
              >
                {testing === key ? '测试中...' : '测试'}
              </button>
              
              <button
                className="switch-btn"
                onClick={() => handleSwitch(key)}
                disabled={
                  !provider.available ||
                  key === status.current_provider ||
                  switching ||
                  testing !== null
                }
              >
                {switching ? '切换中...' : key === status.current_provider ? '当前' : '切换'}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="llm-switcher-footer">
        <p className="tip">
          💡 提示: 切换后会立即生效，所有新的对话将使用新的模型
        </p>
      </div>
    </div>
  );
};
