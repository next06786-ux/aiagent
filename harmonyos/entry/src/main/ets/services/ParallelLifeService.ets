/**
 * 平行人生服务
 * 处理塔罗牌决策游戏
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { StartGameRequest, SubmitChoiceRequest } from '../types/RequestInterfaces';

export class ParallelLifeService {
  private httpClient = HttpClient.getInstance();
  
  /**
   * 开始塔罗牌游戏
   */
  async startGame(userId: string): Promise<GameSession> {
    const requestData: StartGameRequest = {
      user_id: userId
    };
    
    const result = await this.httpClient.post<GameSession>(
      ApiConstants.PARALLEL_LIFE.START_GAME,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取塔罗牌阅读
   */
  async getTarotReading(userId: string): Promise<GameSession> {
    return this.startGame(userId);
  }
  
  /**
   * 提交选择
   */
  async submitChoice(
    gameId: string,
    userId: string,
    choiceId: string
  ): Promise<GameProgress> {
    const requestData: SubmitChoiceRequest = {
      game_id: gameId,
      user_id: userId,
      choice_id: choiceId
    };
    
    const result = await this.httpClient.post<GameProgress>(
      ApiConstants.PARALLEL_LIFE.SUBMIT_CHOICE,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取决策画像
   */
  async getDecisionProfile(userId: string): Promise<DecisionProfile> {
    const result = await this.httpClient.get<DecisionProfile>(
      `${ApiConstants.PARALLEL_LIFE.DECISION_PROFILE}/${userId}`,
      {}
    );
    
    return result.data;
  }
}

/**
 * 游戏会话
 */
export interface GameSession {
  game_id: string;
  scene: TarotScene;
}

/**
 * 塔罗牌场景选项
 */
export interface TarotOption {
  id: string;
  text: string;
  dimension: string;
}

/**
 * 塔罗牌场景
 */
export interface TarotScene {
  title: string;
  description: string;
  image?: string;
  options: TarotOption[];
}

/**
 * 游戏进度
 */
export interface GameProgress {
  next_scene?: TarotScene;
  is_complete: boolean;
  decision_profile?: DecisionProfile;
  current_scene_index: number;
  total_scenes: number;
}

/**
 * 决策画像
 */
export interface DimensionValue {
  value: number;
  count: number;
  confidence: number;
}

export interface DecisionProfile {
  dimensions: Record<string, DimensionValue>;
  patterns: string[];
  confidence: number;
  total_choices: number;
}
