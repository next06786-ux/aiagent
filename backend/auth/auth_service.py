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

from backend.database.models import User
from backend.database.db_manager import DatabaseManager


class AuthService:
    """用户认证服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        # 简单的token存储（生产环境应使用Redis）
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
        
        # 为演示用户创建永久mock token
        self._init_demo_token()
    
    def _init_demo_token(self):
        """初始化演示用户的mock token"""
        demo_user_id = '2c2139f7-bab4-483d-9882-ae83ce8734cd'
        demo_token = 'local-demo-token-permanent'
        
        # 创建一个永久有效的token（过期时间设为100年后）
        from datetime import timedelta
        self.active_tokens[demo_token] = {
            'user_id': demo_user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(days=36500)  # 100年
        }
        print(f"✅ 演示用户token已初始化: {demo_token}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码加密 - 使用bcrypt更安全"""
        import bcrypt
        # 使用bcrypt加密（自动加盐）
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码 - 使用bcrypt验证"""
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
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
        # 检查是否是mock token（本地演示token）- 永久有效
        if token.startswith('local-demo-token'):
            return '2c2139f7-bab4-483d-9882-ae83ce8734cd'
        
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
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        验证密码强度
        
        Returns:
            {
                'valid': bool,
                'message': str,
                'strength': str  # weak, medium, strong
            }
        """
        if len(password) < 6:
            return {
                'valid': False,
                'message': '密码长度不能少于6个字符',
                'strength': 'weak'
            }
        
        if len(password) < 8:
            return {
                'valid': True,
                'message': '密码强度较弱，建议使用8位以上并包含字母、数字和特殊字符',
                'strength': 'weak'
            }
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score >= 3 and len(password) >= 10:
            return {
                'valid': True,
                'message': '密码强度很好',
                'strength': 'strong'
            }
        elif strength_score >= 2 and len(password) >= 8:
            return {
                'valid': True,
                'message': '密码强度中等',
                'strength': 'medium'
            }
        else:
            return {
                'valid': True,
                'message': '密码强度较弱，建议包含大小写字母、数字和特殊字符',
                'strength': 'weak'
            }
    
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
            # 验证密码强度
            password_check = self.validate_password_strength(password)
            if not password_check['valid']:
                return {
                    'success': False,
                    'message': password_check['message']
                }
            
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
        # 【新增】检查是否是默认管理员账号
        if username_or_email == "admin" and password == "admin123":
            # 生成管理员token
            admin_user_id = "admin-default-account"
            token = self.generate_token(admin_user_id)
            
            return {
                'success': True,
                'message': '管理员登录成功',
                'data': {
                    'user_id': admin_user_id,
                    'username': 'admin',
                    'email': 'admin@lifeswarm.com',
                    'nickname': '系统管理员',
                    'avatar_url': None,
                    'is_admin': True,
                    'token': token
                }
            }
        
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
            
            # 检查是否是管理员
            from backend.admin.admin_service import get_admin_service
            admin_service = get_admin_service()
            is_admin = admin_service.is_admin(user.id)
            
            # 【新增】只有非管理员用户才异步加载系统（RAG、知识图谱）
            if not is_admin:
                import asyncio
                from backend.auth.login_state_manager import get_login_state_manager
                
                try:
                    # 在后台异步加载，不阻塞登录响应
                    try:
                        loop = asyncio.get_running_loop()
                        # 如果事件循环正在运行，创建任务
                        asyncio.create_task(
                            get_login_state_manager().check_and_load_user_systems(user.id)
                        )
                        print(f"🔄 用户 {user.id} 的系统正在后台加载...")
                    except RuntimeError:
                        # 没有运行的事件循环，使用线程池异步执行
                        import threading
                        def load_in_thread():
                            asyncio.run(
                                get_login_state_manager().check_and_load_user_systems(user.id)
                            )
                        thread = threading.Thread(target=load_in_thread, daemon=True)
                        thread.start()
                        print(f"🔄 用户 {user.id} 的系统正在后台线程加载...")
                except Exception as e:
                    print(f"⚠️ 用户系统加载触发失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 加载失败不影响登录
            else:
                print(f"👑 管理员 {user.id} 登录，跳过系统加载")
            
            return {
                'success': True,
                'message': '登录成功',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'is_admin': is_admin,
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
        # 获取用户ID
        user_id = self.verify_token(token)
        
        # 撤销令牌
        self.revoke_token(token)
        
        # 【新增】卸载用户系统
        if user_id:
            import asyncio
            from backend.auth.login_state_manager import get_login_state_manager
            
            try:
                # 在后台异步卸载
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(
                        get_login_state_manager().unload_user_systems(user_id)
                    )
                    print(f"🔄 用户 {user_id} 的系统正在后台卸载...")
                except RuntimeError:
                    # 没有运行的事件循环，使用线程池异步执行
                    import threading
                    def unload_in_thread():
                        asyncio.run(
                            get_login_state_manager().unload_user_systems(user_id)
                        )
                    thread = threading.Thread(target=unload_in_thread, daemon=True)
                    thread.start()
                    print(f"🔄 用户 {user_id} 的系统正在后台线程卸载...")
            except Exception as e:
                print(f"⚠️ 用户系统卸载触发失败: {e}")
                # 卸载失败不影响登出
        
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
        # 【新增】如果是默认管理员账号
        if user_id == "admin-default-account":
            return {
                'user_id': 'admin-default-account',
                'username': 'admin',
                'email': 'admin@lifeswarm.com',
                'nickname': '系统管理员',
                'avatar_url': None,
                'phone': None,
                'is_verified': True,
                'created_at': None,
                'last_login': None
            }
        
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

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# FastAPI依赖注入函数
from fastapi import Header, HTTPException


async def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    从请求头获取当前用户ID
    用于FastAPI的Depends依赖注入
    
    Args:
        authorization: Authorization header (Bearer token)
    
    Returns:
        用户ID
    
    Raises:
        HTTPException: 如果token无效或过期
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    # 解析Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="无效的认证令牌格式")
    
    token = parts[1]
    
    # 检查是否是mock token（本地演示token）
    if token.startswith('local-demo-token'):
        # 返回演示用户ID
        return '2c2139f7-bab4-483d-9882-ae83ce8734cd'
    
    # 验证真实token
    auth_service = get_auth_service()
    user_id = auth_service.verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="认证令牌无效或已过期")
    
    return user_id
