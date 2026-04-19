"""
树洞消息存储服务
使用 Neo4j 存储树洞和消息数据
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase
import os


class TreeHoleStorage:
    """树洞消息存储服务"""
    
    def __init__(self):
        self.driver = None
        self._connect()
    
    def _connect(self):
        """连接 Neo4j"""
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "lifeswarm123")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ 树洞存储连接成功")
        except Exception as e:
            print(f"❌ 树洞存储连接失败: {e}")
            print(f"   URI: {uri}")
            print(f"   用户名: {username}")
            print(f"   请检查 Neo4j 是否运行，以及 .env 中的密码是否正确")
    
    def create_tree_hole(self, hole_id: str, user_id: str, title: str, description: str) -> bool:
        """创建树洞（与用户绑定）"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (h:TreeHole {id: $hole_id})
                    SET h.title = $title,
                        h.description = $description,
                        h.user_id = $user_id,
                        h.created_at = datetime()
                """, hole_id=hole_id, user_id=user_id, title=title, description=description)
            return True
        except Exception as e:
            print(f"创建树洞失败: {e}")
            return False
    
    def add_message(
        self,
        message_id: str,
        tree_hole_id: str,
        user_id: str,
        content: str,
        is_anonymous: bool = True
    ) -> bool:
        """添加消息到树洞"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (h:TreeHole {id: $tree_hole_id})
                    CREATE (m:TreeHoleMessage {
                        id: $message_id,
                        user_id: $user_id,
                        content: $content,
                        is_anonymous: $is_anonymous,
                        created_at: datetime(),
                        likes: 0
                    })
                    CREATE (m)-[:POSTED_IN]->(h)
                """, 
                message_id=message_id,
                tree_hole_id=tree_hole_id,
                user_id=user_id,
                content=content,
                is_anonymous=is_anonymous)
            return True
        except Exception as e:
            print(f"添加消息失败: {e}")
            return False
    
    def get_user_tree_holes(self, user_id: str, hours: int = 168) -> List[Dict[str, Any]]:
        """获取用户的树洞列表"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:TreeHole {user_id: $user_id})
                    OPTIONAL MATCH (m:TreeHoleMessage)-[:POSTED_IN]->(h)
                    WHERE m.created_at >= datetime() - duration({hours: $hours})
                    WITH h, collect({
                        id: m.id,
                        content: m.content,
                        created_at: m.created_at,
                        likes: m.likes,
                        user_id: m.user_id,
                        is_anonymous: m.is_anonymous
                    }) as messages
                    RETURN h.id as id,
                           h.title as title,
                           h.description as description,
                           h.user_id as user_id,
                           h.created_at as created_at,
                           size([msg IN messages WHERE msg.content IS NOT NULL]) as message_count,
                           messages
                    ORDER BY h.created_at DESC
                """, user_id=user_id, hours=hours)
                
                tree_holes = []
                for record in result:
                    valid_messages = [
                        {
                            'id': msg['id'],
                            'content': msg['content'],
                            'created_at': msg['created_at'].isoformat() if msg['created_at'] else None,
                            'likes': msg['likes'] or 0,
                            'user_id': msg['user_id'] if not msg.get('is_anonymous') else None,
                            'is_anonymous': msg.get('is_anonymous', True)
                        }
                        for msg in record['messages']
                        if msg['content'] is not None
                    ]
                    
                    tree_holes.append({
                        'id': record['id'],
                        'title': record['title'],
                        'description': record['description'],
                        'user_id': record['user_id'],
                        'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                        'message_count': len(valid_messages),
                        'messages': valid_messages
                    })
                return tree_holes
        except Exception as e:
            print(f"获取用户树洞失败: {e}")
            return []
    
    def get_messages_by_tree_hole(
        self,
        tree_hole_id: str,
        limit: int = 100,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取树洞的消息"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (m:TreeHoleMessage)-[:POSTED_IN]->(h:TreeHole {id: $tree_hole_id})
                    WHERE m.created_at >= datetime() - duration({hours: $hours})
                    RETURN m.id as id,
                           m.content as content,
                           m.created_at as created_at,
                           m.likes as likes,
                           m.user_id as user_id,
                           m.is_anonymous as is_anonymous
                    ORDER BY m.created_at DESC
                    LIMIT $limit
                """, tree_hole_id=tree_hole_id, limit=limit, hours=hours)
                
                messages = []
                for record in result:
                    messages.append({
                        'id': record['id'],
                        'content': record['content'],
                        'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                        'likes': record['likes'],
                        'user_id': record['user_id'] if not record['is_anonymous'] else None,
                        'is_anonymous': record['is_anonymous']
                    })
                return messages
        except Exception as e:
            print(f"获取消息失败: {e}")
            return []
    
    def get_all_tree_holes_with_messages(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取所有树洞及其消息（用于热门分析）"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:TreeHole)
                    OPTIONAL MATCH (m:TreeHoleMessage)-[:POSTED_IN]->(h)
                    WHERE m.created_at >= datetime() - duration({hours: $hours})
                    WITH h, collect({
                        id: m.id,
                        content: m.content,
                        created_at: m.created_at,
                        likes: m.likes
                    }) as messages
                    RETURN h.id as id,
                           h.title as title,
                           h.description as description,
                           h.user_id as user_id,
                           size([msg IN messages WHERE msg.content IS NOT NULL]) as message_count,
                           messages
                """, hours=hours)
                
                tree_holes = []
                for record in result:
                    valid_messages = [
                        {
                            'id': msg['id'],
                            'content': msg['content'],
                            'created_at': msg['created_at'].isoformat() if msg['created_at'] else None,
                            'likes': msg['likes'] or 0
                        }
                        for msg in record['messages']
                        if msg['content'] is not None
                    ]
                    
                    tree_holes.append({
                        'id': record['id'],
                        'title': record['title'],
                        'description': record['description'],
                        'user_id': record['user_id'],
                        'message_count': len(valid_messages),
                        'messages': valid_messages
                    })
                return tree_holes
        except Exception as e:
            print(f"获取树洞列表失败: {e}")
            return []
    
    def like_message(self, message_id: str) -> bool:
        """点赞消息"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (m:TreeHoleMessage {id: $message_id})
                    SET m.likes = m.likes + 1
                """, message_id=message_id)
            return True
        except Exception as e:
            print(f"点赞失败: {e}")
            return False
    
    def delete_tree_hole(self, hole_id: str, user_id: str) -> bool:
        """删除树洞（仅所有者可删除）"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:TreeHole {id: $hole_id, user_id: $user_id})
                    OPTIONAL MATCH (m:TreeHoleMessage)-[:POSTED_IN]->(h)
                    DETACH DELETE h, m
                    RETURN count(h) as deleted
                """, hole_id=hole_id, user_id=user_id)
                
                record = result.single()
                return record and record['deleted'] > 0
        except Exception as e:
            print(f"删除树洞失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# 全局单例
_storage = None

def get_tree_hole_storage() -> TreeHoleStorage:
    """获取树洞存储单例"""
    global _storage
    if _storage is None:
        _storage = TreeHoleStorage()
    return _storage
