/**
 * API类型定义
 * 对标 web/src/types/api.ts
 */

/**
 * API响应包装
 */
export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data?: T;
}

/**
 * 认证相关类型
 */
export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  nickname?: string;
}

export interface LoginResponse {
  token: string;
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  is_admin?: boolean;
}

export interface UserInfo {
  user_id: string;
  username: string;
  email: string;
  nickname: string;
  avatar_url?: string;
  is_verified?: boolean;
  created_at?: string;
  last_login?: string;
}

export interface UpdateProfilePayload {
  nickname?: string;
  email?: string;
  avatar_url?: string;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
}

/**
 * 决策相关类型
 */
export interface DecisionSession {
  session_id: string;
  user_id: string;
  decision_topic: string;
  status: 'collecting' | 'analyzing' | 'completed';
  created_at: string;
}

export interface PersonaData {
  id: string;
  name: string;
  score?: number;
  stance?: string;
  confidence?: number;
  key_points?: string[];
  reasoning?: string;
  round?: number;
}

export interface OptionData {
  option_id: string;
  title: string;
  description: string;
  score?: number;
  risk_level?: string;
}

/**
 * 知识图谱相关类型
 */
export interface KnowledgeNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, Object>;
}

export interface KnowledgeRelationship {
  from: string;
  to: string;
  type: string;
  properties?: Record<string, Object>;
}

/**
 * 洞察相关类型
 */
export interface InsightReport {
  insight_id: string;
  type: 'relationship' | 'education' | 'career';
  title: string;
  content: string;
  score?: number;
  recommendations?: string[];
  created_at: string;
}

/**
 * 平行人生相关类型
 */
export interface TarotCard {
  card_id: string;
  name: string;
  image_url?: string;
  meaning: string;
  reversed?: boolean;
}

export interface TarotReading {
  cards: TarotCard[];
  interpretation: string;
  advice: string;
}

/**
 * 社交相关类型
 */
export interface Friend {
  user_id: string;
  username: string;
  nickname: string;
  avatar_url?: string;
  status?: 'online' | 'offline';
  last_seen?: string;
}

export interface FriendRequest {
  request_id: string;
  from_user_id: string;
  from_username: string;
  from_nickname: string;
  from_avatar_url?: string;
  message?: string;
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

export interface TreeHolePost {
  post_id: string;
  user_id?: string;
  content: string;
  is_anonymous: boolean;
  tags?: string[];
  likes_count: number;
  comments_count: number;
  is_liked: boolean;
  created_at: string;
}

export interface TreeHoleComment {
  comment_id: string;
  post_id: string;
  user_id?: string;
  content: string;
  created_at: string;
}

/**
 * 日程相关类型
 */
export interface Schedule {
  schedule_id: string;
  user_id: string;
  title: string;
  description?: string;
  start_time: number;
  end_time: number;
  location?: string;
  reminder?: number;
  created_at: string;
}

/**
 * AI对话相关类型
 */
export interface ChatMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface ChatSession {
  session_id: string;
  user_id: string;
  messages: ChatMessage[];
  created_at: string;
}
