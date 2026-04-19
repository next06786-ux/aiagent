"""
管理员API路由
Admin API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from backend.auth.auth_service import get_current_user_id
from backend.admin.admin_service import get_admin_service


router = APIRouter(prefix="/api/admin", tags=["admin"])


class UpdateUserStatusRequest(BaseModel):
    """更新用户状态请求"""
    is_active: bool


# 管理员权限检查依赖
async def require_admin(user_id: str = Depends(get_current_user_id)) -> str:
    """要求管理员权限"""
    admin_service = get_admin_service()
    if not admin_service.is_admin(user_id):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user_id


@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    admin_id: str = Depends(require_admin)
):
    """
    获取用户列表
    
    需要管理员权限
    """
    admin_service = get_admin_service()
    result = admin_service.get_all_users(page, page_size, search)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('message', '获取用户列表失败'))
    
    return result  # 返回完整的result，包含success和data


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin_id: str = Depends(require_admin)
):
    """
    获取用户详细信息
    
    需要管理员权限
    """
    admin_service = get_admin_service()
    result = admin_service.get_user_detail(user_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('message', '用户不存在'))
    
    return result['data']


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequest,
    admin_id: str = Depends(require_admin)
):
    """
    更新用户状态（启用/禁用）
    
    需要管理员权限
    """
    admin_service = get_admin_service()
    result = admin_service.update_user_status(user_id, request.is_active)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('message', '更新失败'))
    
    return result


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_id: str = Depends(require_admin)
):
    """
    删除用户
    
    需要管理员权限
    """
    admin_service = get_admin_service()
    result = admin_service.delete_user(user_id)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('message', '删除失败'))
    
    return result


@router.get("/stats")
async def get_system_stats(admin_id: str = Depends(require_admin)):
    """
    获取系统统计信息
    
    需要管理员权限
    """
    admin_service = get_admin_service()
    result = admin_service.get_system_stats()
    
    if not result['success']:
        raise HTTPException(status_code=500, detail='获取统计信息失败')
    
    return result['data']


@router.get("/activities")
async def get_recent_activities(
    limit: int = Query(20, ge=1, le=100),
    admin_id: str = Depends(require_admin)
):
    """
    获取最近活动
    
    需要管理员权限
    """
    admin_service = get_admin_service()
    result = admin_service.get_recent_activities(limit)
    
    if not result['success']:
        raise HTTPException(status_code=500, detail='获取活动记录失败')
    
    return result['data']


@router.get("/check-permission")
async def check_admin_permission(user_id: str = Depends(get_current_user_id)):
    """
    检查当前用户是否有管理员权限
    """
    admin_service = get_admin_service()
    is_admin = admin_service.is_admin(user_id)
    
    return {
        'is_admin': is_admin,
        'user_id': user_id
    }
