"""
三维垂直决策系统API
整合职业、关系、升学三个垂直领域的决策引擎
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

from backend.vertical.unified_decision_workflow import (
    UnifiedDecisionWorkflow,
    DecisionDomain,
    DecisionStage
)

router = APIRouter(prefix="/api/vertical-decision", tags=["vertical-decision"])

# 全局工作流实例
workflow = UnifiedDecisionWorkflow()


class DecisionDomainEnum(str, Enum):
    """决策领域枚举"""
    CAREER = "career"
    RELATIONSHIP = "relationship"
    EDUCATION = "education"


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    user_id: str
    question: str
    domain: Optional[DecisionDomainEnum] = None


class ModelingRequest(BaseModel):
    """建模请求"""
    session_id: str
    options: List[str]
    assumptions: List[str]
    constraints: Dict[str, Any]
    goals: Dict[str, Any]


class CollectingRequest(BaseModel):
    """信息收集请求"""
    session_id: str
    collected_info: Dict[str, Any]


class AnalyzingRequest(BaseModel):
    """分析请求"""
    session_id: str


class ExecutingRequest(BaseModel):
    """执行请求"""
    session_id: str
    selected_option: str
    action_plan: List[Dict[str, Any]]


class ProgressUpdateRequest(BaseModel):
    """进度更新请求"""
    session_id: str
    progress_update: Dict[str, Any]


@router.post("/session/create")
async def create_decision_session(request: CreateSessionRequest):
    """
    创建决策会话
    
    自动识别决策领域（职业/关系/升学）
    """
    try:
        domain = DecisionDomain[request.domain.value.upper()] if request.domain else None
        session = workflow.create_session(
            user_id=request.user_id,
            question=request.question,
            domain=domain
        )
        
        return {
            "success": True,
            "session": session.to_dict(),
            "message": f"已创建{session.domain.value}决策会话"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage/modeling")
async def modeling_stage(request: ModelingRequest):
    """
    决策建模阶段
    
    定义问题、列举选项、识别假设、明确约束和目标
    """
    try:
        result = workflow.modeling_stage(
            session_id=request.session_id,
            options=request.options,
            assumptions=request.assumptions,
            constraints=request.constraints,
            goals=request.goals
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage/collecting")
async def collecting_stage(request: CollectingRequest):
    """
    信息收集阶段
    
    收集真实数据，验证关键假设
    """
    try:
        result = workflow.collecting_stage(
            session_id=request.session_id,
            collected_info=request.collected_info
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage/analyzing")
async def analyzing_stage(request: AnalyzingRequest):
    """
    方案分析阶段
    
    基于真实数据分析各选项的可行性、收益、风险
    """
    try:
        result = workflow.analyzing_stage(
            session_id=request.session_id
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage/executing")
async def executing_stage(request: ExecutingRequest):
    """
    决策执行阶段
    
    制定行动计划，开始执行
    """
    try:
        result = workflow.executing_stage(
            session_id=request.session_id,
            selected_option=request.selected_option,
            action_plan=request.action_plan
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress/update")
async def update_progress(request: ProgressUpdateRequest):
    """
    更新执行进度
    
    记录执行过程中的进展和问题
    """
    try:
        result = workflow.track_progress(
            session_id=request.session_id,
            progress_update=request.progress_update
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    获取会话详情
    """
    try:
        session = workflow.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "success": True,
            "session": session.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/sessions")
async def list_user_sessions(user_id: str):
    """
    列出用户的所有决策会话
    """
    try:
        sessions = workflow.list_user_sessions(user_id)
        
        return {
            "success": True,
            "count": len(sessions),
            "sessions": [session.to_dict() for session in sessions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domain/identify")
async def identify_domain(question: str):
    """
    识别决策领域
    
    根据问题内容自动判断属于职业/关系/升学哪个领域
    """
    try:
        domain = workflow.identify_decision_domain(question)
        
        return {
            "success": True,
            "question": question,
            "domain": domain.value,
            "confidence": 0.85  # 简化版，实际可以返回置信度
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "vertical-decision-api",
        "engines": {
            "career": "active",
            "relationship": "active",
            "education": "active"
        }
    }
