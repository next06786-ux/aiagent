"""
用户认证服务
User Authentication Service
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from database.models import User
from database.db_manager import DatabaseManager


class AuthService:
    """用户认证服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        # 简单的token存储（生产环境应使用Redis）
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密"""
        # 使用SHA256加盐哈希
        salt = "lifeswarm_salt_2024"  # 生产环境应使用随机盐
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        return AuthService.hash_password(password) == password_hash
    
    def generate_token(self, user_id: str) -> str:
        """生成访问令牌"""
        token = secrets.token_urlsafe(32)
        self.active_tokens[token] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=7)  # 7天有效期
        }
        return token
    
    def verify_token(self, token: str) -> Optional[str]:
        """验证令牌并返回用户ID"""
        if token not in self.active_tokens:
            return None
        
        token_data = self.active_tokens[token]
        
        # 检查是否过期
        if datetime.now() > token_data['expires_at']:
            del self.active_tokens[token]
            return None
        
        return token_data['user_id']
    
    def revoke_token(self, token: str):
        """撤销令牌（登出）"""
        if token in self.active_tokens:
            del self.active_tokens[token]
    
    def register(self, username: str, email: str, password: str, 
                nickname: Optional[str] = None) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称（可选）
        
        Returns:
            注册结果
        """
        session = self.db_manager.get_session()
        
        try:
            # 检查用户名是否已存在
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    return {
                        'success': False,
                        'message': '用户名已存在'
                    }
                else:
                    return {
                        'success': False,
                        'message': '邮箱已被注册'
                    }
            
            # 创建新用户
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            
            new_user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                nickname=nickname or username,
                is_active=True,
                is_verified=False
            )
            
            session.add(new_user)
            session.commit()
            
            # 生成令牌
            token = self.generate_token(user_id)
            
            return {
                'success': True,
                'message': '注册成功',
                'data': {
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'nickname': nickname or username,
                    'token': token
                }
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }
        finally:
            session.close()
    
    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
        
        Returns:
            登录结果
        """
        session = self.db_manager.get_session()
        
        try:
            # 查找用户（支持用户名或邮箱登录）
            user = session.query(User).filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email)
            ).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 验证密码
            if not self.verify_password(password, user.password_hash):
                return {
                    'success': False,
                    'message': '密码错误'
                }
            
            # 检查账号状态
            if not user.is_active:
                return {
                    'success': False,
                    'message': '账号已被禁用'
                }
            
            # 更新最后登录时间
            user.last_login = datetime.now()
            session.commit()
            
            # 生成令牌
            token = self.generate_token(user.id)
            
            return {
                'success': True,
                'message': '登录成功',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'token': token
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'登录失败: {str(e)}'
            }
        finally:
            session.close()
    
    def logout(self, token: str) -> Dict[str, Any]:
        """
        用户登出
        
        Args:
            token: 访问令牌
        
        Returns:
            登出结果
        """
        self.revoke_token(token)
        return {
            'success': True,
            'message': '登出成功'
        }
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息
        """
        session = self.db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return None
            
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'phone': user.phone,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
        finally:
            session.close()
    
    def update_user_info(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段
        
        Returns:
            更新结果
        """
        session = self.db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 更新允许的字段
            allowed_fields = ['nickname', 'avatar_url', 'phone']
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.now()
            session.commit()
            
            return {
                'success': True,
                'message': '更新成功',
                'data': self.get_user_info(user_id)
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': f'更新失败: {str(e)}'
            }
        finally:
            session.close()
    
    def change_password(self, user_id: str, old_password: str, 
                       new_password: str) -> Dict[str, Any]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            修改结果
        """
        session = self.db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 验证旧密码
            if not self.verify_password(old_password, user.password_hash):
                return {
                    'success': False,
                    'message': '旧密码错误'
                }
            
            # 更新密码
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.now()
            session.commit()
            
            return {
                'success': True,
                'message': '密码修改成功'
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': f'密码修改失败: {str(e)}'
            }
        finally:
            session.close()


# 全局认证服务实例
_auth_service = None


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
