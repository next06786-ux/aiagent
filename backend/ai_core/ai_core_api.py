"""
AI核心API - 智能路由和功能导航
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.ai_core.intent_router import intent_router


router = APIRouter(prefix="/api/v5/ai-core", tags=["ai-core"])


class IntentAnalysisRequest(BaseModel):
    """意图分析请求"""
    user_id: str
    message: str


class IntentAnalysisResponse(BaseModel):
    """意图分析响应"""
    has_navigation_intent: bool
    suggested_routes: list
    primary_route: Optional[dict]
    navigation_prompt: Optional[str]


@router.post("/analyze-intent", response_model=IntentAnalysisResponse)
async def analyze_user_intent(request: IntentAnalysisRequest):
    """
    分析用户消息的意图，识别是否需要导航到特定功能
    
    示例：
    - "我的人际关系图谱咋样了" → 建议跳转到知识星图（人际关系视图）
    - "我最近的有关人际关系的问题" → 建议跳转到知识星图
    - "我应该跳槽吗" → 建议跳转到决策推演
    """
    # 分析意图
    intent_result = intent_router.analyze_intent(request.message)
    
    # 生成导航提示
    navigation_prompt = None
    if intent_result["has_navigation_intent"]:
        navigation_prompt = intent_router.generate_navigation_prompt(intent_result)
    
    return IntentAnalysisResponse(
        has_navigation_intent=intent_result["has_navigation_intent"],
        suggested_routes=intent_result["suggested_routes"],
        primary_route=intent_result["primary_route"],
        navigation_prompt=navigation_prompt
    )


@router.get("/quick-actions")
async def get_quick_actions():
    """
    获取快捷功能列表
    """
    return {
        "success": True,
        "actions": [
            {
                "id": "knowledge_graph",
                "name": "知识星图",
                "icon": "🌟",
                "path": "/knowledge-graph",
                "description": "查看你的知识星图"
            },
            {
                "id": "decision",
                "name": "决策推演",
                "icon": "🎯",
                "path": "/decision",
                "description": "进行决策推演"
            },
            {
                "id": "parallel_life",
                "name": "平行人生",
                "icon": "🌈",
                "path": "/parallel-life",
                "description": "模拟平行人生"
            },
            {
                "id": "emergence",
                "name": "涌现洞察",
                "icon": "💡",
                "path": "/emergence-dashboard",
                "description": "查看涌现洞察"
            },
            {
                "id": "smart_schedule",
                "name": "智能日程",
                "icon": "📅",
                "path": "/smart-schedule",
                "description": "智能日程推荐"
            }
        ]
    }
