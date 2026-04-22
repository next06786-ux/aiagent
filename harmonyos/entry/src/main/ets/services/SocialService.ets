/**
 * 社交服务
 * 处理好友管理和树洞世界
 */
import { HttpClient } from '../utils/HttpClient';
import { ApiConstants } from '../constants/ApiConstants';
import { Friend, Post, Comment } from '../models/Social';
import {
  AddFriendRequest,
  RemoveFriendRequest,
  GetPostsParams,
  CreatePostRequest,
  CommentPostRequest,
  LikePostRequest
} from '../types/RequestInterfaces';

export class SocialService {
  private httpClient = HttpClient.getInstance();
  
  // ==================== 好友管理 ====================
  
  /**
   * 获取好友列表
   */
  async getFriendsList(userId: string): Promise<Friend[]> {
    const result = await this.httpClient.get<Friend[]>(
      `${ApiConstants.SOCIAL.FRIENDS_LIST}/${userId}`,
      {}
    );
    
    return result.data;
  }
  
  /**
   * 获取好友
   */
  async getFriends(): Promise<Friend[]> {
    const result = await this.httpClient.get<Friend[]>(
      ApiConstants.SOCIAL.FRIENDS_LIST,
      {}
    );
    
    return result.data || [];
  }
  
  /**
   * 添加好友
   */
  async addFriend(userId: string, friendId: string): Promise<void> {
    const requestData: AddFriendRequest = {
      user_id: userId,
      friend_id: friendId
    };
    
    await this.httpClient.post<Object>(
      ApiConstants.SOCIAL.FRIENDS_ADD,
      requestData
    );
  }
  
  /**
   * 删除好友
   */
  async removeFriend(userId: string, friendId: string): Promise<void> {
    const requestData: RemoveFriendRequest = {
      user_id: userId,
      friend_id: friendId
    };
    
    await this.httpClient.post<Object>(
      ApiConstants.SOCIAL.FRIENDS_REMOVE,
      requestData
    );
  }
  
  /**
   * 获取好友请求
   */
  async getFriendRequests(userId: string): Promise<Object[]> {
    const result = await this.httpClient.get<Object[]>(
      `${ApiConstants.SOCIAL.FRIENDS_REQUESTS}/${userId}`,
      {}
    );
    
    return result.data || [];
  }
  
  // ==================== 树洞世界 ====================
  
  /**
   * 获取树洞帖子列表
   */
  async getTreeHolePosts(page: number = 1, limit: number = 20): Promise<Post[]> {
    const paramsObj: Record<string, Object> = {};
    paramsObj['page'] = page.toString();
    paramsObj['limit'] = limit.toString();
    
    const result = await this.httpClient.get<Post[]>(
      ApiConstants.SOCIAL.TREE_HOLE_POSTS,
      paramsObj
    );
    
    return result.data || [];
  }
  
  /**
   * 发布树洞帖子
   */
  async postToTreeHole(
    userId: string,
    content: string,
    isAnonymous: boolean = false,
    tags: string[] = []
  ): Promise<Post> {
    const requestData: CreatePostRequest = {
      user_id: userId,
      content: content,
      is_anonymous: isAnonymous,
      tags: tags
    };
    
    const result = await this.httpClient.post<Post>(
      ApiConstants.SOCIAL.TREE_HOLE_POST,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 创建树洞帖子
   */
  async createTreeHolePost(content: string): Promise<Post> {
    const requestData: CreatePostRequest = {
      user_id: '',
      content: content,
      is_anonymous: false,
      tags: []
    };
    
    const result = await this.httpClient.post<Post>(
      ApiConstants.SOCIAL.TREE_HOLE_POST,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 获取帖子详情
   */
  async getPostDetail(postId: string): Promise<Post> {
    const result = await this.httpClient.get<Post>(
      `${ApiConstants.SOCIAL.TREE_HOLE_POST}/${postId}`,
      {}
    );
    
    return result.data;
  }
  
  /**
   * 评论帖子
   */
  async commentPost(
    postId: string,
    userId: string,
    content: string
  ): Promise<Comment> {
    const requestData: CommentPostRequest = {
      post_id: postId,
      user_id: userId,
      content: content
    };
    
    const result = await this.httpClient.post<Comment>(
      ApiConstants.SOCIAL.TREE_HOLE_COMMENT,
      requestData
    );
    
    return result.data;
  }
  
  /**
   * 点赞帖子
   */
  async likePost(postId: string, userId: string): Promise<void> {
    const requestData: LikePostRequest = {
      post_id: postId,
      user_id: userId
    };
    
    await this.httpClient.post<Object>(
      ApiConstants.SOCIAL.TREE_HOLE_LIKE,
      requestData
    );
  }
  
  /**
   * 取消点赞
   */
  async unlikePost(postId: string, userId: string): Promise<void> {
    const requestData: LikePostRequest = {
      post_id: postId,
      user_id: userId
    };
    
    await this.httpClient.post<Object>(
      `${ApiConstants.SOCIAL.TREE_HOLE_LIKE}/cancel`,
      requestData
    );
  }
}
