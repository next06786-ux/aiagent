/**
 * AI对话服务 - 轮询版本（备用方案）
 * 如果SSE不工作，使用这个版本
 */
import { HttpUtil } from '../utils/HttpUtil';
import { ApiConfig } from '../config/ApiConfig';

export class ChatRequest {
  user_id: string = '';
  message: string = '';
  context: Record<string, string> | null = null;
}

/**
 * 使用轮询方式实现流式效果
 */
export async function chatStreamPolling(
  userId: string,
  message: string,
  onProgress: (progress: string) => void,
  onThinking: (thinking: string) => void,
  onAnswer: (answer: string) => void,
  onComplete: () => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    // 1. 启动对话
    console.info('[Polling] 启动对话');
    const startRequest = new ChatRequest();
    startRequest.user_id = userId;
    startRequest.message = message;
    
    const startResponse = await HttpUtil.post('/api/chat/stream/start', startRequest);
    
    if (startResponse.responseCode !== 200) {
      throw new Error(`启动失败: ${startResponse.responseCode}`);
    }
    
    const startResult = JSON.parse(startResponse.result as string) as Record<string, Object>;
    const sessionId = (startResult.data as Record<string, string>).session_id;
    console.info(`[Polling] 会话ID: ${sessionId}`);
    
    // 2. 轮询获取结果
    let isComplete = false;
    let pollCount = 0;
    const maxPolls = 600; // 最多轮询10分钟
    
    while (!isComplete && pollCount < maxPolls) {
      pollCount++;
      
      // 等待一小段时间再轮询
      await new Promise<void>(resolve => setTimeout(() => resolve(), 500));
      
      try {
        const pollResponse = await HttpUtil.get(`/api/chat/stream/poll/${sessionId}`);
        
        if (pollResponse.responseCode === 200) {
          const pollResult = JSON.parse(pollResponse.result as string) as Record<string, Object>;
          const data = pollResult.data as Record<string, string>;
          
          const status = data.status;
          const progress = data.progress || '';
          const thinking = data.thinking || '';
          const answer = data.answer || '';
          
          console.info(`[Polling] 状态: ${status}, 进度: ${progress}`);
          
          // 更新UI
          if (progress) {
            onProgress(progress);
          }
          if (thinking) {
            onThinking(thinking);
          }
          if (answer) {
            onAnswer(answer);
          }
          
          // 检查是否完成
          if (status === 'completed') {
            isComplete = true;
            onComplete();
          } else if (status === 'error') {
            const error = data.error || '未知错误';
            onError(error);
            return;
          }
        }
      } catch (pollErr) {
        console.error('[Polling] 轮询错误:', pollErr);
        // 继续轮询
      }
    }
    
    if (!isComplete) {
      throw new Error('轮询超时');
    }
    
  } catch (err) {
    const error = err as Error;
    console.error('[Polling] 错误:', error.message);
    onError(error.message);
  }
}
