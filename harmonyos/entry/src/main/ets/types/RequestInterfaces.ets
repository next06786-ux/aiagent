/**
 * 通用请求接口定义
 * 用于所有服务的HTTP请求数据
 */

/**
 * 空对象接口 - 用于可选的context/params参数
 */
export class EmptyObject {
}

// ==================== Social Service ====================
export interface AddFriendRequest {
  user_id: string;
  friend_id: string;
}

export interface RemoveFriendRequest {
  user_id: string;
  friend_id: string;
}

export interface GetPostsParams {
  page: string;
  limit: string;
}

export interface CreatePostRequest {
  user_id: string;
  content: string;
  is_anonymous: boolean;
  tags: string[];
}

export interface CommentPostRequest {
  post_id: string;
  user_id: string;
  content: string;
}

export interface LikePostRequest {
  post_id: string;
  user_id: string;
}

// ==================== Knowledge Graph Service ====================
export interface AddInformationRequest {
  user_id: string;
  source_type: string;
  content: string;
  entities: Object[];
  relationships: Object[];
}

export interface QueryKnowledgeRequest {
  user_id: string;
  query: string;
  query_type: string;
}

// ==================== Schedule Service ====================
export interface GetSchedulesParams {
  date: string;
  start_time: string;
  end_time: string;
  start_date: string;
  end_date: string;
}

export interface AddScheduleRequest {
  user_id: string;
  title: string;
  start_time: string;
  end_time: string;
  description: string;
  location: string;
  priority: string;
}

export interface GetRecommendationsRequest {
  user_id: string;
  date: string;
  preferences: Object;
}

export interface AutoGenerateRequest {
  user_id: string;
  date_range: Object;
  goals: string[];
}

// ==================== Insights Service ====================
export interface GetInsightRequest {
  user_id: string;
  query: string;
  context: Object;
}

// ==================== Parallel Life Service ====================
export interface StartGameRequest {
  user_id: string;
}

export interface SubmitChoiceRequest {
  game_id: string;
  user_id: string;
  choice_id: string;
}

// ==================== AI Core Service ====================
export interface RecognizeIntentRequest {
  user_id: string;
  message: string;
  context: Object;
}

export interface NavigateRequest {
  user_id: string;
  intent: string;
  params: Object;
}

// ==================== Data Preloader ====================
export interface CacheData {
  career: Object;
  education: Object;
  relationship: Object;
  timestamp: number;
}

export interface ScheduleCacheData {
  schedules: Object;
  timestamp: number;
}

export interface FriendsCacheData {
  friends: Object;
  timestamp: number;
}

export interface ConversationsCacheData {
  conversations: Object[];
  timestamp: number;
}
