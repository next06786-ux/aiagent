"""
树洞 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from backend.social.topic_trending import get_trending_service
from backend.social.tree_hole_storage import get_tree_hole_storage

router = APIRouter(prefix="/api/tree-hole", tags=["tree-hole"])


class TreeHoleCreate(BaseModel):
    """创建树洞请求"""
    user_id: str
    title: str
    description: str = ""


class MessageCreate(BaseModel):
    """创建消息请求"""
    tree_hole_id: str
    user_id: str
    content: str
    is_anonymous: bool = True


@router.post("/create")
async def create_tree_hole(request: TreeHoleCreate):
    """创建树洞"""
    try:
        storage = get_tree_hole_storage()
        hole_id = str(uuid.uuid4())
        
        success = storage.create_tree_hole(
            hole_id=hole_id,
            user_id=request.user_id,
            title=request.title,
            description=request.description
        )
        
        if success:
            return {
                "code": 200,
                "message": "创建成功",
                "data": {"tree_hole_id": hole_id}
            }
        else:
            return {
                "code": 500,
                "message": "创建失败",
                "data": None
            }
    except Exception as e:
        print(f"创建树洞失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"创建失败: {str(e)}",
            "data": None
        }


@router.get("/tree-holes")
async def get_all_tree_holes(hours: int = 168):
    """获取所有树洞列表（公共空间，所有用户可见）"""
    try:
        storage = get_tree_hole_storage()
        tree_holes = storage.get_all_tree_holes_with_messages(hours=hours)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": tree_holes
        }
    except Exception as e:
        print(f"获取树洞列表失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }


@router.get("/user/{user_id}")
async def get_user_tree_holes(user_id: str, hours: int = 168):
    """获取用户创建的树洞列表"""
    try:
        storage = get_tree_hole_storage()
        tree_holes = storage.get_user_tree_holes(user_id, hours)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": tree_holes
        }
    except Exception as e:
        print(f"获取用户树洞失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }


@router.post("/messages")
async def create_message(message: MessageCreate):
    """发布消息到树洞"""
    try:
        storage = get_tree_hole_storage()
        message_id = str(uuid.uuid4())
        
        success = storage.add_message(
            message_id=message_id,
            tree_hole_id=message.tree_hole_id,
            user_id=message.user_id,
            content=message.content,
            is_anonymous=message.is_anonymous
        )
        
        if success:
            return {
                "code": 200,
                "message": "发布成功",
                "data": {"message_id": message_id}
            }
        else:
            return {
                "code": 500,
                "message": "发布失败",
                "data": None
            }
    except Exception as e:
        print(f"发布消息失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"发布失败: {str(e)}",
            "data": None
        }


@router.get("/messages/{tree_hole_id}")
async def get_tree_hole_messages(tree_hole_id: str, limit: int = 100, hours: int = 168):
    """获取树洞的消息列表"""
    try:
        storage = get_tree_hole_storage()
        messages = storage.get_messages_by_tree_hole(tree_hole_id, limit, hours)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": messages
        }
    except Exception as e:
        print(f"获取消息失败: {e}")
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }


@router.delete("/delete/{tree_hole_id}")
async def delete_tree_hole(tree_hole_id: str, user_id: str):
    """删除树洞"""
    try:
        storage = get_tree_hole_storage()
        success = storage.delete_tree_hole(tree_hole_id, user_id)
        
        if success:
            return {
                "code": 200,
                "message": "删除成功",
                "data": None
            }
        else:
            return {
                "code": 403,
                "message": "无权删除或树洞不存在",
                "data": None
            }
    except Exception as e:
        print(f"删除树洞失败: {e}")
        return {
            "code": 500,
            "message": f"删除失败: {str(e)}",
            "data": None
        }


@router.get("/trending-decisions")
async def get_trending_decisions(time_window: int = 24):
    """
    获取热门决策排行榜（从真实树洞消息中分析）
    
    Args:
        time_window: 时间窗口（小时），默认24小时
    """
    try:
        storage = get_tree_hole_storage()
        service = get_trending_service()
        
        # 从数据库获取真实树洞数据
        tree_holes = storage.get_all_tree_holes_with_messages(hours=time_window)
        
        print(f"\n{'='*60}")
        print(f"[热门决策] 开始分析")
        print(f"{'='*60}")
        print(f"[热门决策] 时间窗口: {time_window} 小时")
        print(f"[热门决策] 获取到 {len(tree_holes)} 个树洞")
        
        total_messages = 0
        for i, hole in enumerate(tree_holes, 1):
            msg_count = hole.get('message_count', 0)
            total_messages += msg_count
            print(f"  [{i}] {hole.get('title')}: {msg_count} 条消息")
        
        print(f"[热门决策] 总消息数: {total_messages}")
        
        # 如果没有真实数据，返回空列表
        if not tree_holes or total_messages == 0:
            print(f"[热门决策] ❌ 没有消息数据")
            print(f"[热门决策] 建议: 运行 python backend/social/init_tree_hole_data.py 初始化示例数据")
            print(f"{'='*60}\n")
            return {
                "code": 200,
                "message": "暂无数据",
                "data": {
                    "decisions": [],
                    "time_window": time_window,
                    "updated_at": datetime.now().isoformat(),
                    "note": "树洞中还没有消息"
                }
            }
        
        # 分析热门决策
        print(f"[热门决策] 开始LLM分析...")
        decisions = service.get_trending_decisions(tree_holes, time_window)
        
        print(f"[热门决策] ✅ 分析完成，提取到 {len(decisions)} 个决策")
        for i, decision in enumerate(decisions[:5], 1):
            print(f"  [{i}] {decision.get('decision')} (热度: {decision.get('score')})")
        print(f"{'='*60}\n")
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "decisions": decisions,
                "time_window": time_window,
                "updated_at": datetime.now().isoformat(),
                "total_messages": total_messages
            }
        }
    except Exception as e:
        print(f"[热门决策] ❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }
