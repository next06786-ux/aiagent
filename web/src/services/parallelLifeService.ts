/**
 * 平行人生 - 塔罗牌决策游戏服务
 */

// 使用相对路径，由nginx代理到后端
const API_BASE_URL = '';

export interface TarotCard {
  card: string;
  card_key: string;
  dimension: string;
  dimension_key: string;
  scenario: string;
  options: Array<{
    id: string;
    text: string;
    tendency: 'left' | 'right';
  }>;
  timestamp: string;
}

export interface DecisionProfile {
  dimensions: Record<string, {
    value: number;
    count: number;
    confidence: number;
  }>;
  patterns: string[];
  confidence: number;
  total_choices: number;
}

export interface GameStats {
  total_cards_drawn: number;
  choices_made: number;
  profile_confidence: number;
  dimensions_analyzed: number;
}

class ParallelLifeService {
  /**
   * 抽取塔罗牌
   */
  async drawCard(userId: string, drawnCards?: string[]): Promise<TarotCard> {
    const response = await fetch(`${API_BASE_URL}/api/v5/parallel-life/draw-card`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        drawn_cards: drawnCards,
      }),
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '抽牌失败');
    }

    return result.data;
  }

  /**
   * 提交选择
   */
  async submitChoice(
    userId: string,
    card: string,
    cardKey: string,
    dimension: string,
    dimensionKey: string,
    scenario: string,
    choice: string,
    tendency: 'left' | 'right'
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v5/parallel-life/submit-choice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        card,
        card_key: cardKey,
        dimension,
        dimension_key: dimensionKey,
        scenario,
        choice,
        tendency,
      }),
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '提交失败');
    }

    return result.data;
  }

  /**
   * 获取决策画像
   */
  async getDecisionProfile(userId: string): Promise<DecisionProfile> {
    const response = await fetch(
      `${API_BASE_URL}/api/v5/parallel-life/decision-profile/${userId}`
    );

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '获取画像失败');
    }

    return result.data;
  }

  /**
   * 获取游戏统计
   */
  async getGameStats(userId: string): Promise<GameStats> {
    const response = await fetch(
      `${API_BASE_URL}/api/v5/parallel-life/game-stats/${userId}`
    );

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message || '获取统计失败');
    }

    return result.data;
  }
}

export const parallelLifeService = new ParallelLifeService();

// 导出便捷函数
export const drawCard = (userId: string, drawnCards?: string[]) => 
  parallelLifeService.drawCard(userId, drawnCards);

export const submitChoice = (
  userId: string,
  card: string,
  cardKey: string,
  dimension: string,
  dimensionKey: string,
  scenario: string,
  choice: string,
  tendency: 'left' | 'right'
) => parallelLifeService.submitChoice(userId, card, cardKey, dimension, dimensionKey, scenario, choice, tendency);

export const getProfile = (userId: string) => 
  parallelLifeService.getDecisionProfile(userId);

export const getGameStats = (userId: string) => 
  parallelLifeService.getGameStats(userId);
