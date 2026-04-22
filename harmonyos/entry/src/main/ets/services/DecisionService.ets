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

/**
 * 选项信息接口
 */
export interface OptionInfo {
  title: string;
  description: string;
}

/**
 * 开始收集请求接口
 */
interface StartCollectionRequest {
  user_id: string;
  question: string;
  decision_type: string;
}

/**
 * 继续收集请求接口
 */
interface ContinueCollectionRequest {
  session_id: string;
  user_id: string;
  user_input: string;
}

/**
 * 生成选项请求接口
 */
interface GenerateOptionsRequest {
  session_id: string;
  user_id: string;
}

/**
 * 更新结果请求接口
 */
interface UpdateOutcomeRequest {
  session_id: string;
  user_id: string;
  chosen_option: string;
  actual_outcome: string;
}

/**
 * 开始推演请求接口
 */
interface StartSimulationRequest {
  type: string;
  session_id: string;
  user_id: string;
  question: string;
  option: Object;
  option_index: number;
  collected_info: Object;
  decision_type: string;
}

/**
 * 停止推演请求接口
 */
interface StopSimulationRequest {
  type: string;
  option_id: string;
  session_id: string;
}

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
    const requestData: StartCollectionRequest = {
      user_id: userId,
      question: question,
      decision_type: decisionType
    };
    
    const result = await this.httpClient.post<SessionInfo>(
      ApiConstants.DECISION.START_COLLECTION,
      requestData
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
    const requestData: ContinueCollectionRequest = {
      session_id: sessionId,
      user_id: userId,
      user_input: userInput
    };
    
    const result = await this.httpClient.post<CollectionProgress>(
      ApiConstants.DECISION.CONTINUE_COLLECTION,
      requestData
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
    const requestData: GenerateOptionsRequest = {
      session_id: sessionId,
      user_id: userId
    };
    
    const result = await this.httpClient.post<OptionsResult>(
      ApiConstants.DECISION.GENERATE_OPTIONS,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取会话信息
   */
  async getSession(sessionId: string): Promise<Decision> {
    const result = await this.httpClient.get<Decision>(
      `${ApiConstants.DECISION.SESSION}/${sessionId}`,
      {}
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
    const requestData: UpdateOutcomeRequest = {
      session_id: sessionId,
      user_id: userId,
      chosen_option: chosenOption,
      actual_outcome: actualOutcome
    };
    
    await this.httpClient.post<Object>(
      ApiConstants.DECISION.UPDATE_OUTCOME,
      requestData
    );
  }
  
  /**
   * 开始WebSocket推演
   */
  async startSimulation(
    sessionId: string,
    userId: string,
    question: string,
    option: OptionInfo,
    optionIndex: number,
    collectedInfo: Object,
    decisionType: string,
    onMessage: (event: WebSocketEvent) => void
  ): Promise<void> {
    // 创建WebSocket连接
    this.wsClient = new WebSocketClient(ApiConstants.WS.DECISION_SIMULATE);
    
    // 注册消息处理器
    this.wsClient.on('open', () => {
      console.log('决策推演WebSocket已连接');
      // 发送开始推演消息
      const startData: StartSimulationRequest = {
        type: 'start_simulation',
        session_id: sessionId,
        user_id: userId,
        question: question,
        option: option as Object,
        option_index: optionIndex,
        collected_info: collectedInfo,
        decision_type: decisionType
      };
      this.wsClient?.send(startData);
    });
    
    // 注册所有消息类型的处理器
    this.wsClient.on('*', (event: Object) => {
      onMessage(event as WebSocketEvent);
    });
    
    this.wsClient.on('error', (data: Object) => {
      console.error('WebSocket错误:', data);
      const errorEvent: WebSocketEvent = {
        type: 'error',
        content: '连接错误，请检查网络'
      };
      onMessage(errorEvent);
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
      const stopData: StopSimulationRequest = {
        type: 'stop_simulation',
        option_id: optionId,
        session_id: sessionId
      };
      this.wsClient.send(stopData);
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
