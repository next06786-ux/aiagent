/**
 * 管理员服务
 * Admin Service
 */

const API_BASE = `${import.meta.env.VITE_API_BASE_URL || ''}/api/admin`;

export interface User {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface UserDetail extends User {
  phone?: string;
  updated_at?: string;
  stats?: {
    health_records_count: number;
    last_activity?: string;
  };
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface UsersResponse {
  users: User[];
  pagination: Pagination;
}

export interface SystemStats {
  users: {
    total: number;
    active: number;
    inactive: number;
    new_7d: number;
    active_24h: number;
  };
  timestamp: string;
}

export interface Activity {
  type: string;
  user_id: string;
  username: string;
  nickname: string;
  timestamp: string;
}

/**
 * 检查管理员权限
 */
export async function checkAdminPermission(token: string): Promise<{ is_admin: boolean; user_id: string }> {
  const response = await fetch(`${API_BASE}/check-permission`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('权限检查失败');
  }

  return response.json();
}

/**
 * 获取用户列表
 */
export async function getUsers(
  token: string,
  page: number = 1,
  pageSize: number = 20,
  search?: string
): Promise<UsersResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (search) {
    params.append('search', search);
  }

  const response = await fetch(`${API_BASE}/users?${params}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('获取用户列表失败');
  }

  return response.json();
}

/**
 * 获取用户详情
 */
export async function getUserDetail(token: string, userId: string): Promise<UserDetail> {
  const response = await fetch(`${API_BASE}/users/${userId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('获取用户详情失败');
  }

  return response.json();
}

/**
 * 更新用户状态
 */
export async function updateUserStatus(
  token: string,
  userId: string,
  isActive: boolean
): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/users/${userId}/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_active: isActive }),
  });

  if (!response.ok) {
    throw new Error('更新用户状态失败');
  }

  return response.json();
}

/**
 * 删除用户
 */
export async function deleteUser(token: string, userId: string): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`${API_BASE}/users/${userId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('删除用户失败');
  }

  return response.json();
}

/**
 * 获取系统统计
 */
export async function getSystemStats(token: string): Promise<SystemStats> {
  const response = await fetch(`${API_BASE}/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('获取系统统计失败');
  }

  return response.json();
}

/**
 * 获取最近活动
 */
export async function getRecentActivities(token: string, limit: number = 20): Promise<{ activities: Activity[] }> {
  const response = await fetch(`${API_BASE}/activities?limit=${limit}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('获取活动记录失败');
  }

  return response.json();
}
