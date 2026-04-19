"""
管理员模块
Admin Module
"""
from backend.admin.admin_service import get_admin_service
from backend.admin.admin_api import router as admin_router

__all__ = ['get_admin_service', 'admin_router']
