"""
好友关系管理服务
"""
import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from neo4j import GraphDatabase


class FriendService:
    """好友关系管理服务"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print(f"✅ 好友服务连接成功: {uri}")
        except Exception as e:
            print(f"❌ Neo4j 连接失败: {e}")
            raise
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def search_users(self, query: str, current_user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索用户（通过用户名或昵称）
        
        Args:
            query: 搜索关键词
            current_user_id: 当前用户ID
            limit: 返回结果数量限制
            
        Returns:
            用户列表
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User)
                WHERE (u.username CONTAINS $query OR u.nickname CONTAINS $query)
                  AND u.user_id <> $current_user_id
                OPTIONAL MATCH (current:User {user_id: $current_user_id})-[r:FRIEND]->(u)
                RETURN u.user_id AS user_id,
                       u.username AS username,
                       u.nickname AS nickname,
                       u.avatar_url AS avatar_url,
                       u.email AS email,
                       CASE WHEN r IS NOT NULL THEN true ELSE false END AS is_friend
                LIMIT $limit
            """, query=query, current_user_id=current_user_id, limit=limit)
            
            users = []
            for record in result:
                users.append({
                    'user_id': record['user_id'],
                    'username': record['username'],
                    'nickname': record['nickname'],
                    'avatar_url': record['avatar_url'],
                    'email': record['email'],
                    'is_friend': record['is_friend']
                })
            
            return users
    
    def send_friend_request(self, from_user_id: str, to_user_id: str, message: str = "") -> Dict[str, Any]:
        """
        发送好友请求
        
        Args:
            from_user_id: 发送者用户ID
            to_user_id: 接收者用户ID
            message: 附加消息
            
        Returns:
            操作结果
        """
        with self.driver.session() as session:
            # 检查是否已经是好友
            check_result = session.run("""
                MATCH (from:User {user_id: $from_user_id})-[r:FRIEND]-(to:User {user_id: $to_user_id})
                RETURN r
            """, from_user_id=from_user_id, to_user_id=to_user_id)
            
            if check_result.single():
                return {'success': False, 'message': '你们已经是好友了'}
            
            # 检查是否已经发送过请求
            request_check = session.run("""
                MATCH (from:User {user_id: $from_user_id})-[r:FRIEND_REQUEST]->(to:User {user_id: $to_user_id})
                WHERE r.status = 'pending'
                RETURN r
            """, from_user_id=from_user_id, to_user_id=to_user_id)
            
            if request_check.single():
                return {'success': False, 'message': '已经发送过好友请求，请等待对方回应'}
            
            # 创建好友请求
            session.run("""
                MATCH (from:User {user_id: $from_user_id})
                MATCH (to:User {user_id: $to_user_id})
                CREATE (from)-[r:FRIEND_REQUEST {
                    status: 'pending',
                    message: $message,
                    created_at: datetime(),
                    request_id: randomUUID()
                }]->(to)
            """, from_user_id=from_user_id, to_user_id=to_user_id, message=message)
            
            return {'success': True, 'message': '好友请求已发送'}
    
    def get_friend_requests(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取收到的好友请求列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            好友请求列表
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (from:User)-[r:FRIEND_REQUEST]->(to:User {user_id: $user_id})
                WHERE r.status = 'pending'
                RETURN r.request_id AS request_id,
                       from.user_id AS from_user_id,
                       from.username AS from_username,
                       from.nickname AS from_nickname,
                       from.avatar_url AS from_avatar_url,
                       r.message AS message,
                       r.created_at AS created_at
                ORDER BY r.created_at DESC
            """, user_id=user_id)
            
            requests = []
            for record in result:
                requests.append({
                    'request_id': record['request_id'],
                    'from_user_id': record['from_user_id'],
                    'from_username': record['from_username'],
                    'from_nickname': record['from_nickname'],
                    'from_avatar_url': record['from_avatar_url'],
                    'message': record['message'],
                    'created_at': record['created_at'].isoformat() if record['created_at'] else None
                })
            
            return requests
    
    def accept_friend_request(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """
        接受好友请求
        
        Args:
            request_id: 请求ID
            user_id: 当前用户ID（接收者）
            
        Returns:
            操作结果
        """
        with self.driver.session() as session:
            # 更新请求状态并创建好友关系
            result = session.run("""
                MATCH (from:User)-[r:FRIEND_REQUEST]->(to:User {user_id: $user_id})
                WHERE r.request_id = $request_id AND r.status = 'pending'
                SET r.status = 'accepted', r.accepted_at = datetime()
                WITH from, to
                CREATE (from)-[:FRIEND {created_at: datetime()}]->(to)
                CREATE (to)-[:FRIEND {created_at: datetime()}]->(from)
                RETURN from.user_id AS from_user_id, to.user_id AS to_user_id
            """, request_id=request_id, user_id=user_id)
            
            record = result.single()
            if record:
                return {'success': True, 'message': '已成为好友'}
            else:
                return {'success': False, 'message': '请求不存在或已处理'}
    
    def reject_friend_request(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """
        拒绝好友请求
        
        Args:
            request_id: 请求ID
            user_id: 当前用户ID（接收者）
            
        Returns:
            操作结果
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (from:User)-[r:FRIEND_REQUEST]->(to:User {user_id: $user_id})
                WHERE r.request_id = $request_id AND r.status = 'pending'
                SET r.status = 'rejected', r.rejected_at = datetime()
                RETURN r
            """, request_id=request_id, user_id=user_id)
            
            if result.single():
                return {'success': True, 'message': '已拒绝好友请求'}
            else:
                return {'success': False, 'message': '请求不存在或已处理'}
    
    def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取好友列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            好友列表
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:FRIEND]->(friend:User)
                RETURN friend.user_id AS user_id,
                       friend.username AS username,
                       friend.nickname AS nickname,
                       friend.avatar_url AS avatar_url,
                       friend.email AS email,
                       r.created_at AS friend_since
                ORDER BY r.created_at DESC
            """, user_id=user_id)
            
            friends = []
            for record in result:
                friends.append({
                    'user_id': record['user_id'],
                    'username': record['username'],
                    'nickname': record['nickname'],
                    'avatar_url': record['avatar_url'],
                    'email': record['email'],
                    'friend_since': record['friend_since'].isoformat() if record['friend_since'] else None,
                    'status': 'offline',  # TODO: 实现在线状态
                    'lastSeen': '未知'
                })
            
            return friends
    
    def remove_friend(self, user_id: str, friend_id: str) -> Dict[str, Any]:
        """
        删除好友
        
        Args:
            user_id: 当前用户ID
            friend_id: 要删除的好友ID
            
        Returns:
            操作结果
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r1:FRIEND]-(friend:User {user_id: $friend_id})
                DELETE r1
                RETURN count(r1) AS deleted_count
            """, user_id=user_id, friend_id=friend_id)
            
            record = result.single()
            if record and record['deleted_count'] > 0:
                return {'success': True, 'message': '已删除好友'}
            else:
                return {'success': False, 'message': '好友关系不存在'}


# 全局单例
_friend_service = None

def get_friend_service() -> FriendService:
    """获取好友服务单例"""
    global _friend_service
    if _friend_service is None:
        _friend_service = FriendService()
    return _friend_service
