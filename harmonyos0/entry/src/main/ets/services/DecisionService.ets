/**
 * 决策服务
 * 处理多人格决策推演的所有功能
 */
import { HttpClient } from '../utils/HttpClient';
import { WebSocketClient } from '../utils/WebSocketClient';
import { ApiConstants } from '../constants/ApiConstants';
import { SessionInfo, CollectionProgress, OptionsResult } from '../models/User';
import { Decision, Option } from '../models/Decision';
import { WebSocketEvent } from '../models/Agent';

export class DecisionService {
  private httpClient = HttpClient.getInstance();
  private wsClient: WebSocketClient | null = null;
  
  /**
   * 开始信息收集
   */
  async startCollection(
    userId: string,
    question: string,
    decisionType: string
  ): Promise<SessionInfo> {
    const result = await this.httpClient.post<SessionInfo>(
      ApiConstants.DECISION.START_COLLECTION,
      { user_id: userId, question, decision_type: decisionType }
    );
    
    return result.data;
  }
  
  /**
   * 继续信息收集
   */
  async continueCollection(
    sessionId: string,
    userId: string,
    userInput: string
  ): Promise<CollectionProgress> {
    const result = await this.httpClient.post<CollectionProgress>(
      ApiConstants.DECISION.CONTINUE_COLLECTION,
      { session_id: sessionId, user_id: userId, user_input: userInput }
    );
    
    return result.data;
  }
  
  /**
   * 生成AI推荐选项
   */
  async generateOptions(
    sessionId: string,
    userId: string
  ): Promise<OptionsResult> {
    const result = await this.httpClient.post<OptionsResult>(
      ApiConstants.DECISION.GENERATE_OPTIONS,
      { session_id: sessionId, user_id: userId }
    );
    
    return result.data;
  }
  
  /**
   * 获取会话信息
   */
  async getSession(sessionId: string): Promise<Decision> {
    const result = await this.httpClient.get<Decision>(
      `${ApiConstants.DECISION.SESSION}/${sessionId}`
    );
    
    return result.data;
  }
  
  /**
   * 更新决策结果
   */
  async updateOutcome(
    sessionId: string,
    userId: string,
    chosenOption: string,
    actualOutcome: string
  ): Promise<void> {
    await this.httpClient.post(
      ApiConstants.DECISION.UPDATE_OUTCOME,
      {
        session_id: sessionId,
        user_id: userId,
        chosen_option: chosenOption,
        actual_outcome: actualOutcome
      }
    );
  }
  
  /**
   * 开始WebSocket推演
   */
  async startSimulation(
    sessionId: string,
    userId: string,
    question: string,
    option: { title: string; description: string },
    optionIndex: number,
    collectedInfo: any,
    decisionType: string,
    onMessage: (event: WebSocketEvent) => void
  ): Promise<void> {
    // 创建WebSocket连接
    this.wsClient = new WebSocketClient(ApiConstants.WS.DECISION_SIMULATE);
    
    // 注册消息处理器
    this.wsClient.on('open', () => {
      console.log('决策推演WebSocket已连接');
      // 发送开始推演消息
      this.wsClient?.send({
        type: 'start_simulation',
        session_id: sessionId,
        user_id: userId,
        question,
        option,
        option_index: optionIndex,
        collected_info: collectedInfo,
        decision_type: decisionType
      });
    });
    
    // 注册所有消息类型的处理器
    this.wsClient.on('*', (event: WebSocketEvent) => {
      onMessage(event);
    });
    
    this.wsClient.on('error', (data) => {
      console.error('WebSocket错误:', data);
      onMessage({
        type: 'error',
        content: '连接错误，请检查网络'
      });
    });
    
    this.wsClient.on('close', () => {
      console.log('WebSocket连接已关闭');
    });
    
    // 连接WebSocket
    await this.wsClient.connect();
  }
  
  /**
   * 暂停推演
   */
  pauseSimulation(optionId: string, sessionId: string): void {
    if (this.wsClient) {
      this.wsClient.send({
        type: 'stop_simulation',
        option_id: optionId,
        session_id: sessionId
      });
    }
  }
  
  /**
   * 关闭WebSocket连接
   */
  closeSimulation(): void {
    if (this.wsClient) {
      this.wsClient.close();
      this.wsClient = null;
    }
  }
  
  /**
   * 检查WebSocket是否连接
   */
  isSimulationActive(): boolean {
    return this.wsClient !== null && this.wsClient.isConnected();
  }
}
