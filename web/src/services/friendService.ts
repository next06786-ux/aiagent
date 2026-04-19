/**
 * 好友管理服务
 */

import { postJson, requestJson } from './api';

export interface Friend {
  user_id: string;
  username: string;
  nickname: string;
  avatar_url?: string;
  email?: string;
  status: 'online' | 'offline';
  lastSeen?: string;
  friend_since?: string;
}

export interface FriendRequest {
  request_id: string;
  from_user_id: string;
  from_username: string;
  from_nickname: string;
  from_avatar_url?: string;
  message: string;
  created_at: string;
}

export interface SearchResult {
  user_id: string;
  username: string;
  nickname: string;
  avatar_url?: string;
  email?: string;
  is_friend: boolean;
}

/**
 * 搜索用户
 */
export async function searchUsers(query: string, userId: string): Promise<SearchResult[]> {
  const response = await postJson<{ code: number; message: string; data: SearchResult[] }>(
    '/api/social/search-users',
    { query, user_id: userId, limit: 10 }
  );
  
  if (response.code === 200) {
    return response.data || [];
  } else {
    throw new Error(response.message || '搜索失败');
  }
}

/**
 * 发送好友请求
 */
export async function sendFriendRequest(fromUserId: string, toUserId: string, message: string = ''): Promise<void> {
  const response = await postJson<{ code: number; message: string }>(
    '/api/social/send-friend-request',
    { from_user_id: fromUserId, to_user_id: toUserId, message }
  );
  
  if (response.code !== 200) {
    throw new Error(response.message || '发送失败');
  }
}

/**
 * 获取好友请求列表
 */
export async function getFriendRequests(userId: string): Promise<FriendRequest[]> {
  const response = await requestJson<{ code: number; message: string; data: FriendRequest[] }>(
    `/api/social/friend-requests/${userId}`,
    { method: 'GET' }
  );
  
  if (response.code === 200) {
    return response.data || [];
  } else {
    throw new Error(response.message || '获取失败');
  }
}

/**
 * 接受好友请求
 */
export async function acceptFriendRequest(requestId: string, userId: string): Promise<void> {
  const response = await postJson<{ code: number; message: string }>(
    '/api/social/accept-friend-request',
    { request_id: requestId, user_id: userId }
  );
  
  if (response.code !== 200) {
    throw new Error(response.message || '操作失败');
  }
}

/**
 * 拒绝好友请求
 */
export async function rejectFriendRequest(requestId: string, userId: string): Promise<void> {
  const response = await postJson<{ code: number; message: string }>(
    '/api/social/reject-friend-request',
    { request_id: requestId, user_id: userId }
  );
  
  if (response.code !== 200) {
    throw new Error(response.message || '操作失败');
  }
}

/**
 * 获取好友列表
 */
export async function getFriends(userId: string): Promise<Friend[]> {
  const response = await requestJson<{ code: number; message: string; data: Friend[] }>(
    `/api/social/friends/${userId}`,
    { method: 'GET' }
  );
  
  if (response.code === 200) {
    return response.data || [];
  } else {
    throw new Error(response.message || '获取失败');
  }
}

/**
 * 删除好友
 */
export async function removeFriend(userId: string, friendId: string): Promise<void> {
  const response = await postJson<{ code: number; message: string }>(
    '/api/social/remove-friend',
    { user_id: userId, friend_id: friendId }
  );
  
  if (response.code !== 200) {
    throw new Error(response.message || '操作失败');
  }
}
