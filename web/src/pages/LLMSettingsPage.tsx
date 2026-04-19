/**
 * LLM 设置页面
 * 提供大模型切换和管理功能
 */
import React from 'react';
import { LLMSwitcher } from '../components/LLMSwitcher';
import '../styles/LLMSettingsPage.css';

export const LLMSettingsPage: React.FC = () => {
  return (
    <div className="llm-settings-page">
      <div className="page-header">
        <h1>⚙️ 大模型设置</h1>
        <p className="page-description">
          在云端 API 和自建基座模型之间灵活切换，满足不同场景需求
        </p>
      </div>

      <div className="page-content">
        <LLMSwitcher />
      </div>

      <div className="help-section">
        <h3>📖 使用说明</h3>
        
        <div className="help-item">
          <h4>☁️ 通义千问 API</h4>
          <p>
            阿里云提供的云端大模型服务，速度快、稳定性高，按量计费。
            适合生产环境和高并发场景。
          </p>
          <ul>
            <li>优点: 速度快、稳定、无需 GPU</li>
            <li>缺点: 需要 API Key、按量计费</li>
            <li>配置: 在 .env 文件中设置 DASHSCOPE_API_KEY</li>
          </ul>
        </div>

        <div className="help-item">
          <h4>🖥️ 远程基座模型</h4>
          <p>
            在自己的服务器上部署的量化模型，成本低、数据私密。
            适合对成本敏感或有数据隐私要求的场景。
          </p>
          <ul>
            <li>优点: 成本低、数据私密、可定制</li>
            <li>缺点: 需要 GPU 服务器、需要维护</li>
            <li>配置: 输入服务器地址（如 http://your-server-ip:8001）</li>
          </ul>
        </div>

        <div className="help-item">
          <h4>💻 本地量化模型</h4>
          <p>
            在本地运行的量化模型，完全离线可用。
            适合开发测试或无网络环境。
          </p>
          <ul>
            <li>优点: 完全离线、响应快、无成本</li>
            <li>缺点: 需要本地 GPU、占用资源</li>
            <li>配置: 需要下载模型文件到本地</li>
          </ul>
        </div>

        <div className="help-item">
          <h4>🤖 OpenAI API</h4>
          <p>
            OpenAI 提供的云端大模型服务，功能强大。
            适合需要最先进模型能力的场景。
          </p>
          <ul>
            <li>优点: 功能强大、生态完善</li>
            <li>缺点: 需要国际网络、费用较高</li>
            <li>配置: 在 .env 文件中设置 OPENAI_API_KEY</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
