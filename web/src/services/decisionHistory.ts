/**
 * 决策历史记录服务
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface DecisionHistory {
  id: string;
  user_id: string;
  session_id: string;
  question: string;
  decision_type: string;
  options_data: any;
  created_at: string;
  completed_at: string;
}

export interface DecisionHistoryListItem {
  id: string;
  session_id: string;
  question: string;
  decision_type: string;
  created_at: string;
  completed_at: string;
  options_count: number;
}

export interface DecisionReport {
  summary: string;
  key_insights: string[];
  strengths: string[];
  risks: string[];
  recommendation: string;
  agents_summary: Array<{
    name: string;
    stance: string;
    score: number;
    confidence: number;
  }>;
  total_score: number;
  full_text?: string;
}

/**
 * 保存决策历史
 */
export async function saveDecisionHistory(data: {
  user_id: string;
  session_id: string;
  question: string;
  decision_type: string;
  options_data: any;
}): Promise<{ success: boolean; history_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/decision/history/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('保存决策历史失败');
  }

  return response.json();
}

/**
 * 获取决策历史列表
 */
export async function getDecisionHistoryList(
  userId: string,
  limit: number = 20,
  offset: number = 0
): Promise<{
  success: boolean;
  histories: DecisionHistoryListItem[];
  total: number;
}> {
  const response = await fetch(
    `${API_BASE_URL}/api/decision/history/list?user_id=${userId}&limit=${limit}&offset=${offset}`
  );

  if (!response.ok) {
    throw new Error('获取决策历史列表失败');
  }

  return response.json();
}

/**
 * 获取决策历史详情
 */
export async function getDecisionHistoryDetail(
  historyId: string
): Promise<{ success: boolean; history: DecisionHistory }> {
  const response = await fetch(
    `${API_BASE_URL}/api/decision/history/detail/${historyId}`
  );

  if (!response.ok) {
    throw new Error('获取决策历史详情失败');
  }

  return response.json();
}

/**
 * 删除决策历史
 */
export async function deleteDecisionHistory(
  historyId: string,
  userId: string
): Promise<{ success: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/api/decision/history/delete/${historyId}?user_id=${userId}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    throw new Error('删除决策历史失败');
  }

  return response.json();
}

/**
 * 生成决策报告
 */
export async function generateDecisionReport(data: {
  question: string;
  option_title: string;
  option_description: string;
  agents_data: any[];
  total_score: number;
}): Promise<{ success: boolean; report: DecisionReport }> {
  const response = await fetch(`${API_BASE_URL}/api/decision/generate-report`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('生成决策报告失败');
  }

  return response.json();
}
