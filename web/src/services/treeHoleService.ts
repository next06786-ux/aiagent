/**
 * 树洞服务 - API 调用
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6006';

export interface TrendingDecision {
  rank: number;
  decision: string;
  domain: 'career' | 'education' | 'relationship' | 'family' | 'finance' | 'health' | 'lifestyle' | 'other';
  type: 'problem' | 'success' | 'question';
  keywords: string[];
  sentiment: 'positive' | 'neutral' | 'negative';
  description: string;
  pain_point?: string;
  score: number;
  message_count: number;
  tree_holes: Array<{
    id: string;
    title: string;
  }>;
  trend: 'hot' | 'up' | 'down' | 'stable';
}

export interface TreeHole {
  id: string;
  title: string;
  description: string;
  message_count: number;
  messages?: Array<{
    id: string;
    content: string;
    created_at: string;
    likes: number;
    comments: number;
  }>;
  recommendation_score?: number;
}

/**
 * 获取热门决策排行榜
 */
export async function getTrendingDecisions(timeWindow: number = 24): Promise<TrendingDecision[]> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/trending-decisions?time_window=${timeWindow}`);
    const data = await response.json();
    
    if (data.code === 200) {
      return data.data.decisions;
    } else {
      console.error('获取热门决策失败:', data.message);
      return [];
    }
  } catch (error) {
    console.error('获取热门决策失败:', error);
    return [];
  }
}

/**
 * 获取推荐树洞
 */
export async function getRecommendedTreeHoles(userId: string, limit: number = 5): Promise<TreeHole[]> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/recommend?user_id=${userId}&limit=${limit}`);
    const data = await response.json();
    
    if (data.code === 200) {
      return data.data;
    } else {
      console.error('获取推荐树洞失败:', data.message);
      return [];
    }
  } catch (error) {
    console.error('获取推荐树洞失败:', error);
    return [];
  }
}

/**
 * 获取所有树洞列表（公共空间）
 */
export async function getAllTreeHoles(): Promise<TreeHole[]> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/tree-holes?hours=168`);
    
    if (!response.ok) {
      console.error('获取树洞列表失败: HTTP', response.status);
      return [];
    }
    
    const data = await response.json();
    
    if (data.code === 200 && data.data) {
      console.log('成功获取树洞列表:', data.data.length, '个树洞');
      return data.data;
    } else {
      console.error('获取树洞列表失败:', data.message);
      return [];
    }
  } catch (error) {
    console.error('获取树洞列表失败:', error);
    return [];
  }
}

/**
 * 获取用户创建的树洞列表
 */
export async function getUserTreeHoles(userId: string): Promise<TreeHole[]> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/user/${userId}?hours=168`);
    
    if (!response.ok) {
      console.error('获取用户树洞失败: HTTP', response.status);
      return [];
    }
    
    const data = await response.json();
    
    if (data.code === 200 && data.data) {
      console.log('成功获取用户树洞:', data.data.length, '个树洞');
      return data.data;
    } else {
      console.error('获取用户树洞失败:', data.message);
      return [];
    }
  } catch (error) {
    console.error('获取用户树洞失败:', error);
    return [];
  }
}

/**
 * 创建树洞
 */
export async function createTreeHole(userId: string, title: string, description: string = ''): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        title,
        description,
      }),
    });
    
    const data = await response.json();
    
    if (data.code === 200 && data.data) {
      console.log('成功创建树洞:', data.data.tree_hole_id);
      return data.data.tree_hole_id;
    } else {
      console.error('创建树洞失败:', data.message);
      return null;
    }
  } catch (error) {
    console.error('创建树洞失败:', error);
    return null;
  }
}

/**
 * 获取树洞的消息列表
 */
export async function getTreeHoleMessages(treeHoleId: string, limit: number = 100, hours: number = 168): Promise<Array<{
  id: string;
  content: string;
  created_at: string;
  likes: number;
  is_anonymous: boolean;
}>> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/messages/${treeHoleId}?limit=${limit}&hours=${hours}`);
    
    if (!response.ok) {
      console.error('获取树洞消息失败: HTTP', response.status);
      return [];
    }
    
    const data = await response.json();
    
    if (data.code === 200 && data.data) {
      console.log('成功获取树洞消息:', data.data.length, '条消息');
      return data.data;
    } else {
      console.error('获取树洞消息失败:', data.message);
      return [];
    }
  } catch (error) {
    console.error('获取树洞消息失败:', error);
    return [];
  }
}

/**
 * 发送消息到树洞
 */
export async function sendMessage(treeHoleId: string, userId: string, content: string, isAnonymous: boolean = true): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/tree-hole/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tree_hole_id: treeHoleId,
        user_id: userId,
        content,
        is_anonymous: isAnonymous,
      }),
    });
    
    const data = await response.json();
    
    if (data.code === 200) {
      console.log('成功发送消息');
      return true;
    } else {
      console.error('发送消息失败:', data.message);
      return false;
    }
  } catch (error) {
    console.error('发送消息失败:', error);
    return false;
  }
}
