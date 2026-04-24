"""
管理员服务
Admin Service
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database.models import User
from backend.database.db_manager import DatabaseManager


class AdminService:
    """管理员服务"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        # 管理员用户ID列表（可以从配置文件读取）
        self.admin_user_ids = [
            'admin-default-account',  # 默认管理员账号
            'admin-00000000-0000-0000-0000-000000000001',  # 其他管理员账号
        ]
    
    def is_admin(self, user_id: str) -> bool:
        """检查用户是否是管理员"""
        return user_id in self.admin_user_ids
    
    def get_all_users(self, page: int = 1, page_size: int = 20, 
                     search: Optional[str] = None) -> Dict[str, Any]:
        """
        获取所有用户列表
        
        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词（用户名或邮箱）
        
        Returns:
            用户列表和分页信息
        """
        session = self.db_manager.get_session()
        
        try:
            query = session.query(User)
            
            # 搜索过滤
            if search:
                query = query.filter(
                    (User.username.like(f'%{search}%')) |
                    (User.email.like(f'%{search}%')) |
                    (User.nickname.like(f'%{search}%'))
                )
            
            # 总数
            total = query.count()
            
            # 分页
            users = query.order_by(desc(User.created_at))\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()
            
            user_list = []
            for user in users:
                user_list.append({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                })
            
            return {
                'success': True,
                'data': {
                    'users': user_list,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size
                    }
                }
            }
            
        finally:
            session.close()
    
    def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """获取用户详细信息"""
        session = self.db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 获取用户的健康记录统计
            health_records = self.db_manager.get_health_records(user_id, limit=30)
            
            return {
                'success': True,
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname,
                    'avatar_url': user.avatar_url,
                    'phone': user.phone,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                    'stats': {
                        'health_records_count': len(health_records),
                        'last_activity': health_records[0].timestamp.isoformat() if health_records else None
                    }
                }
            }
            
        finally:
            session.close()
    
    def update_user_status(self, user_id: str, is_active: bool) -> Dict[str, Any]:
        """更新用户状态（启用/禁用）"""
        session = self.db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            user.is_active = is_active
            user.updated_at = datetime.now()
            session.commit()
            
            return {
                'success': True,
                'message': f'用户已{"启用" if is_active else "禁用"}',
                'data': {
                    'user_id': user_id,
                    'is_active': is_active
                }
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': f'更新失败: {str(e)}'
            }
        finally:
            session.close()
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """删除用户（软删除）"""
        session = self.db_manager.get_session()
        
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户不存在'
                }
            
            # 软删除：禁用账号
            user.is_active = False
            user.updated_at = datetime.now()
            session.commit()
            
            return {
                'success': True,
                'message': '用户已删除'
            }
            
        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'message': f'删除失败: {str(e)}'
            }
        finally:
            session.close()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息 - 包含决策相关数据"""
        session = self.db_manager.get_session()
        
        try:
            # 用户统计
            total_users = session.query(func.count(User.id)).scalar()
            active_users = session.query(func.count(User.id))\
                                 .filter(User.is_active == True).scalar()
            
            # 最近7天新增用户
            seven_days_ago = datetime.now() - timedelta(days=7)
            new_users_7d = session.query(func.count(User.id))\
                                 .filter(User.created_at >= seven_days_ago).scalar()
            
            # 最近24小时活跃用户
            one_day_ago = datetime.now() - timedelta(days=1)
            active_users_24h = session.query(func.count(User.id))\
                                     .filter(User.last_login >= one_day_ago).scalar()
            
            # 决策统计 - 从文件系统读取（因为决策历史存储在JSON文件中）
            decision_stats = self._get_decision_stats()
            
            return {
                'success': True,
                'data': {
                    'users': {
                        'total': total_users,
                        'active': active_users,
                        'inactive': total_users - active_users,
                        'new_7d': new_users_7d,
                        'active_24h': active_users_24h
                    },
                    'decisions': decision_stats,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        finally:
            session.close()
    
    def _get_decision_stats(self) -> Dict[str, Any]:
        """获取决策统计数据"""
        import os
        import json
        from pathlib import Path
        
        try:
            # 决策历史存储路径
            history_dir = Path('./data/decision_history')
            
            if not history_dir.exists():
                return {
                    'total': 0,
                    'today': 0,
                    'this_week': 0,
                    'by_category': {},
                    'avg_options': 0
                }
            
            total_decisions = 0
            today_decisions = 0
            week_decisions = 0
            category_count = {}
            total_options = 0
            
            today = datetime.now().date()
            week_ago = datetime.now() - timedelta(days=7)
            
            # 遍历所有用户的决策历史
            for user_dir in history_dir.iterdir():
                if not user_dir.is_dir():
                    continue
                
                history_file = user_dir / 'history.json'
                if not history_file.exists():
                    continue
                
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        histories = json.load(f)
                    
                    for history in histories:
                        total_decisions += 1
                        
                        # 统计选项数量
                        options_count = len(history.get('options_data', {}).get('options', []))
                        total_options += options_count
                        
                        # 统计分类
                        category = history.get('category', '未分类')
                        category_count[category] = category_count.get(category, 0) + 1
                        
                        # 统计时间
                        created_at_str = history.get('created_at', '')
                        if created_at_str:
                            try:
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                                if created_at.date() == today:
                                    today_decisions += 1
                                if created_at >= week_ago:
                                    week_decisions += 1
                            except:
                                pass
                
                except Exception as e:
                    print(f"读取决策历史失败 {history_file}: {e}")
                    continue
            
            avg_options = round(total_options / total_decisions, 1) if total_decisions > 0 else 0
            
            return {
                'total': total_decisions,
                'today': today_decisions,
                'this_week': week_decisions,
                'by_category': category_count,
                'avg_options': avg_options
            }
            
        except Exception as e:
            print(f"获取决策统计失败: {e}")
            return {
                'total': 0,
                'today': 0,
                'this_week': 0,
                'by_category': {},
                'avg_options': 0
            }
    
    def get_recent_activities(self, limit: int = 20) -> Dict[str, Any]:
        """获取最近活动"""
        session = self.db_manager.get_session()
        
        try:
            # 获取最近登录的用户
            recent_logins = session.query(User)\
                                  .filter(User.last_login.isnot(None))\
                                  .order_by(desc(User.last_login))\
                                  .limit(limit)\
                                  .all()
            
            activities = []
            for user in recent_logins:
                activities.append({
                    'type': 'login',
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'timestamp': user.last_login.isoformat() if user.last_login else None
                })
            
            return {
                'success': True,
                'data': {
                    'activities': activities
                }
            }
            
        finally:
            session.close()


# 全局管理员服务实例
_admin_service = None


def get_admin_service() -> AdminService:
    """获取管理员服务实例"""
    global _admin_service
    if _admin_service is None:
        _admin_service = AdminService()
    return _admin_service
