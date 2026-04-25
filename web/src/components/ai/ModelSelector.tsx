import { useEffect, useState } from 'react';
import { getLLMStatus, switchLLMProvider, getProviderDisplayName, getProviderIcon } from '../../services/llmService';
import './ModelSelector.css';

interface ModelSelectorProps {
  compact?: boolean;
}

export function ModelSelector({ compact = false }: ModelSelectorProps) {
  const [currentModel, setCurrentModel] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<Record<string, any>>({});
  const [isOpen, setIsOpen] = useState(false);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const status = await getLLMStatus();
      setCurrentModel(status.current_provider);
      setAvailableModels(status.available_providers);
    } catch (error) {
      console.error('加载模型状态失败:', error);
    }
  };

  const handleSwitch = async (provider: string) => {
    if (provider === currentModel || switching) return;

    try {
      setSwitching(true);
      await switchLLMProvider({ provider });
      setCurrentModel(provider);
      setIsOpen(false);
      
      // 强制重新加载状态
      await loadStatus();
      
      // 强制刷新页面以确保UI更新
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } catch (error) {
      console.error('切换模型失败:', error);
      alert('切换模型失败，请重试');
    } finally {
      setSwitching(false);
    }
  };

  if (compact) {
    return (
      <div className="model-selector-compact">
        <button
          className="model-selector-trigger"
          onClick={() => setIsOpen(!isOpen)}
          disabled={switching}
        >
          <span className="model-icon">{getProviderIcon(currentModel)}</span>
          <span className="model-name">{getProviderDisplayName(currentModel)}</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        {isOpen && (
          <>
            <div className="model-selector-backdrop" onClick={() => setIsOpen(false)} />
            <div className="model-selector-dropdown">
              {Object.entries(availableModels)
                .filter(([key, model]: [string, any]) => model.available) // 只显示可用的模型
                .map(([key, model]: [string, any]) => (
                <button
                  key={key}
                  className={`model-option ${key === currentModel ? 'active' : ''}`}
                  onClick={() => handleSwitch(key)}
                  disabled={switching}
                >
                  <span className="model-option-icon">{getProviderIcon(key)}</span>
                  <div className="model-option-info">
                    <div className="model-option-name">{model.name}</div>
                    <div className="model-option-desc">{model.description}</div>
                  </div>
                  {key === currentModel && (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
}
