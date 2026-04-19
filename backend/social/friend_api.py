"""
好友管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from backend.social.friend_service import get_friend_service

router = APIRouter(prefix="/api/social", tags=["social"])


class SearchUsersRequest(BaseModel):
    """搜索用户请求"""
    query: str
    user_id: str
    limit: int = 10


class SendFriendRequestRequest(BaseModel):
    """发送好友请求"""
    from_user_id: str
    to_user_id: str
    message: str = ""


class HandleFriendRequestRequest(BaseModel):
    """处理好友请求"""
    request_id: str
    user_id: str


class RemoveFriendRequest(BaseModel):
    """删除好友"""
    user_id: str
    friend_id: str


@router.post("/search-users")
async def search_users(request: SearchUsersRequest):
    """搜索用户"""
    try:
        service = get_friend_service()
        users = service.search_users(request.query, request.user_id, request.limit)
        
        return {
            "code": 200,
            "message": "搜索成功",
            "data": users
        }
    except Exception as e:
        print(f"搜索用户失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"搜索失败: {str(e)}",
            "data": None
        }


@router.post("/send-friend-request")
async def send_friend_request(request: SendFriendRequestRequest):
    """发送好友请求"""
    try:
        service = get_friend_service()
        result = service.send_friend_request(
            request.from_user_id,
            request.to_user_id,
            request.message
        )
        
        return {
            "code": 200 if result['success'] else 400,
            "message": result['message'],
            "data": None
        }
    except Exception as e:
        print(f"发送好友请求失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"发送失败: {str(e)}",
            "data": None
        }


@router.get("/friend-requests/{user_id}")
async def get_friend_requests(user_id: str):
    """获取好友请求列表"""
    try:
        service = get_friend_service()
        requests = service.get_friend_requests(user_id)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": requests
        }
    except Exception as e:
        print(f"获取好友请求失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }


@router.post("/accept-friend-request")
async def accept_friend_request(request: HandleFriendRequestRequest):
    """接受好友请求"""
    try:
        service = get_friend_service()
        result = service.accept_friend_request(request.request_id, request.user_id)
        
        return {
            "code": 200 if result['success'] else 400,
            "message": result['message'],
            "data": None
        }
    except Exception as e:
        print(f"接受好友请求失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"操作失败: {str(e)}",
            "data": None
        }


@router.post("/reject-friend-request")
async def reject_friend_request(request: HandleFriendRequestRequest):
    """拒绝好友请求"""
    try:
        service = get_friend_service()
        result = service.reject_friend_request(request.request_id, request.user_id)
        
        return {
            "code": 200 if result['success'] else 400,
            "message": result['message'],
            "data": None
        }
    except Exception as e:
        print(f"拒绝好友请求失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"操作失败: {str(e)}",
            "data": None
        }


@router.get("/friends/{user_id}")
async def get_friends(user_id: str):
    """获取好友列表"""
    try:
        service = get_friend_service()
        friends = service.get_friends(user_id)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": friends
        }
    except Exception as e:
        print(f"获取好友列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }


@router.post("/remove-friend")
async def remove_friend(request: RemoveFriendRequest):
    """删除好友"""
    try:
        service = get_friend_service()
        result = service.remove_friend(request.user_id, request.friend_id)
        
        return {
            "code": 200 if result['success'] else 400,
            "message": result['message'],
            "data": None
        }
    except Exception as e:
        print(f"删除好友失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"操作失败: {str(e)}",
            "data": None
        }
