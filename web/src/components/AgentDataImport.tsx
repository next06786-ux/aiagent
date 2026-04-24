import { useState } from 'react';
import { API_BASE_URL } from '../services/api';
import '../styles/AgentDataImport.css';

interface AgentDataImportProps {
  agentType: 'relationship' | 'education' | 'career';
  agentName: string;
  agentColor: string;
  token: string;
  onClose: () => void;
  onImportSuccess: () => void;
}

export function AgentDataImport({ 
  agentType, 
  agentName, 
  agentColor, 
  token, 
  onClose,
  onImportSuccess 
}: AgentDataImportProps) {
  const [importType, setImportType] = useState<'text' | 'file'>('text');
  const [textContent, setTextContent] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    message: string;
    count?: number;
  } | null>(null);

  const handleTextImport = async () => {
    if (!textContent.trim()) {
      alert('请输入要导入的内容');
      return;
    }

    setIsImporting(true);
    setImportResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/agent-import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          token: token,  // 添加token到请求体
          agent_type: agentType,
          import_type: 'text',
          content: textContent
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setImportResult({
          success: true,
          message: `成功导入 ${data.count} 条记忆`,
          count: data.count
        });
        setTextContent('');
        setTimeout(() => {
          onImportSuccess();
        }, 2000);
      } else {
        setImportResult({
          success: false,
          message: data.message || '导入失败'
        });
      }
    } catch (error) {
      console.error('导入失败:', error);
      setImportResult({
        success: false,
        message: '网络错误，请重试'
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileImport = async () => {
    if (!file) {
      alert('请选择文件');
      return;
    }

    setIsImporting(true);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('agent_type', agentType);
      formData.append('token', token);  // 添加token到FormData

      const response = await fetch(`${API_BASE_URL}/api/agent-import-file`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      
      if (data.success) {
        setImportResult({
          success: true,
          message: `成功导入 ${data.count} 条记忆`,
          count: data.count
        });
        setFile(null);
        setTimeout(() => {
          onImportSuccess();
        }, 2000);
      } else {
        setImportResult({
          success: false,
          message: data.message || '导入失败'
        });
      }
    } catch (error) {
      console.error('导入失败:', error);
      setImportResult({
        success: false,
        message: '网络错误，请重试'
      });
    } finally {
      setIsImporting(false);
    }
  };

  const getPlaceholder = () => {
    const placeholders = {
      relationship: `例如：
- 我的好友张三是计算机专业的，我们经常一起讨论技术
- 我的导师李教授在人工智能领域很有建树
- 我和室友关系很好，经常一起学习`,
      education: `例如：
- 我就读于985大学计算机科学与技术专业
- 我的GPA是3.8，专业排名前10%
- 我参加过ACM竞赛，获得过省级一等奖
- 我对机器学习和深度学习很感兴趣`,
      career: `例如：
- 我掌握Python、Java、C++等编程语言
- 我有2个月的互联网公司实习经验
- 我对算法工程师和后端开发岗位感兴趣
- 我希望在一线城市工作，期望薪资15-20K`
    };
    return placeholders[agentType];
  };

  const getSupportedFormats = () => {
    return '.txt, .md, .pdf, .docx';
  };

  return (
    <div className="agent-import-overlay" onClick={onClose}>
      <div className="agent-import-dialog" onClick={e => e.stopPropagation()}>
        {/* 头部 */}
        <div className="agent-import-header" style={{ background: agentColor }}>
          <div className="agent-import-header-info">
            <h3 className="agent-import-title">导入资料到 {agentName}</h3>
            <p className="agent-import-subtitle">增强Agent的个性化分析能力</p>
          </div>
          <button className="agent-import-close" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 导入类型选择 */}
        <div className="agent-import-type-selector">
          <button
            className={`import-type-btn ${importType === 'text' ? 'active' : ''}`}
            onClick={() => setImportType('text')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            文本导入
          </button>
          <button
            className={`import-type-btn ${importType === 'file' ? 'active' : ''}`}
            onClick={() => setImportType('file')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            文件上传
          </button>
        </div>

        {/* 导入内容区 */}
        <div className="agent-import-content">
          {importType === 'text' ? (
            <div className="import-text-area">
              <textarea
                className="import-textarea"
                placeholder={getPlaceholder()}
                value={textContent}
                onChange={e => setTextContent(e.target.value)}
                rows={12}
                disabled={isImporting}
              />
              <div className="import-tips">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4M12 8h.01" />
                </svg>
                <span>支持多行输入，每行一条信息，系统会自动分段存储</span>
              </div>
            </div>
          ) : (
            <div className="import-file-area">
              <div className="file-upload-zone">
                <input
                  type="file"
                  id="file-input"
                  className="file-input"
                  accept={getSupportedFormats()}
                  onChange={e => setFile(e.target.files?.[0] || null)}
                  disabled={isImporting}
                />
                <label htmlFor="file-input" className="file-upload-label">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <span className="upload-text">
                    {file ? file.name : '点击选择文件或拖拽到此处'}
                  </span>
                  <span className="upload-hint">
                    支持格式：{getSupportedFormats()}
                  </span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* 导入结果 */}
        {importResult && (
          <div className={`import-result ${importResult.success ? 'success' : 'error'}`}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {importResult.success ? (
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              ) : (
                <circle cx="12" cy="12" r="10" />
              )}
              {importResult.success ? (
                <polyline points="22 4 12 14.01 9 11.01" />
              ) : (
                <>
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </>
              )}
            </svg>
            <span>{importResult.message}</span>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="agent-import-actions">
          <button className="import-cancel-btn" onClick={onClose} disabled={isImporting}>
            取消
          </button>
          <button
            className="import-submit-btn"
            style={{ background: agentColor }}
            onClick={importType === 'text' ? handleTextImport : handleFileImport}
            disabled={isImporting || (importType === 'text' ? !textContent.trim() : !file)}
          >
            {isImporting ? (
              <>
                <span className="import-spinner" />
                导入中...
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                开始导入
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
