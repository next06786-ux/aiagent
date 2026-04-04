from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.decision.future_os_service import FutureOSService
from backend.vertical.career.career_knowledge_graph import career_kg, UserSkillProfile


router = APIRouter(prefix="/api/v5/future-os", tags=["future-os"])
service = FutureOSService()


class ContextRequest(BaseModel):
    user_id: str
    question: str
    session_id: Optional[str] = None


class RouteRequest(BaseModel):
    user_id: str
    message: str


class SimulateRequest(BaseModel):
    user_id: str
    question: str
    session_id: Optional[str] = None
    options: List[str] = Field(default_factory=list)


class BranchScenarioRequest(BaseModel):
    user_id: str
    simulation_id: str
    branch_id: str


class ParallelLifeCompleteRequest(BaseModel):
    user_id: str
    scenario_id: str
    simulation_id: str
    branch_id: str
    final_stats: Dict[str, float]
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    emotion_feedback: Optional[str] = None
    free_text: str = ""


# 职业知识图谱相关请求模型
class CareerGraphRequest(BaseModel):
    """职业知识图谱请求"""
    user_id: str
    mastered_skills: List[str] = Field(default_factory=list)  # 已掌握技能
    partial_skills: List[str] = Field(default_factory=list)   # 部分掌握技能
    missing_skills: List[str] = Field(default_factory=list)   # 缺失技能
    target_direction: str = "Python工程师"  # 求职方向


class UpdateSkillRequest(BaseModel):
    """更新技能请求"""
    user_id: str
    skill: str
    mastery: float  # 0-1


@router.get("/knowledge/{user_id}")
async def get_future_os_knowledge_view(
    user_id: str,
    view: str = "people",
    question: str = "",
    session_id: Optional[str] = None,
):
    try:
        payload = service.get_graph_view(user_id, view, question, session_id)
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": {"nodes": [], "links": [], "summary": {}}}


@router.delete("/knowledge/{user_id}/cache")
async def clear_knowledge_graph_cache(user_id: str):
    """清除知识图谱缓存"""
    try:
        import redis
        import os
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        
        # 清除该用户的所有知识图谱缓存
        pattern = f"kg_*:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            return {
                "success": True,
                "message": f"已清除 {len(keys)} 个缓存",
                "cleared_keys": len(keys)
            }
        else:
            return {
                "success": True,
                "message": "没有找到缓存",
                "cleared_keys": 0
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"清除缓存失败: {str(e)}"
        }


@router.post("/context")
async def build_future_os_context(request: ContextRequest):
    try:
        payload = service.build_context(request.user_id, request.question, request.session_id)
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": None}


@router.post("/route")
async def route_future_os_message(request: RouteRequest):
    try:
        payload = service.route_message(request.user_id, request.message)
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": None}


@router.post("/simulate")
async def simulate_future_os(request: SimulateRequest):
    try:
        payload = service.simulate_decision(
            user_id=request.user_id,
            question=request.question,
            options=request.options,
            session_id=request.session_id,
        )
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": None}


@router.get("/simulations/{simulation_id}")
async def get_future_os_simulation(simulation_id: str):
    payload = service.load_simulation(simulation_id)
    if not payload:
        return {"success": False, "message": "未找到对应的推演记录", "data": None}
    return {"success": True, "data": payload}


@router.get("/history/{user_id}")
async def list_future_os_history(user_id: str, limit: int = 20):
    try:
        payload = service.list_simulations(user_id, limit)
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": []}


@router.post("/parallel-life/branch")
async def create_branch_parallel_life(request: BranchScenarioRequest):
    try:
        payload = service.create_parallel_life_branch(
            user_id=request.user_id,
            simulation_id=request.simulation_id,
            branch_id=request.branch_id,
        )
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": None}


@router.post("/parallel-life/complete")
async def complete_branch_parallel_life(request: ParallelLifeCompleteRequest):
    try:
        payload = service.complete_parallel_life(
            user_id=request.user_id,
            scenario_id=request.scenario_id,
            simulation_id=request.simulation_id,
            branch_id=request.branch_id,
            final_stats=request.final_stats,
            choices=request.choices,
            emotion_feedback=request.emotion_feedback,
            free_text=request.free_text,
        )
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": None}



# ==================== 职业知识图谱 API ====================

@router.post("/career-graph")
async def get_career_knowledge_graph(request: CareerGraphRequest):
    """
    获取职业决策知识图谱
    
    返回3D可视化图谱数据：
    - 第一圈：技能层（按掌握度着色）
    - 第二圈：岗位层（真实岗位数据）
    - 第三圈：公司层（真实公司信息）
    """
    try:
        # 构建用户技能画像
        user_profile = UserSkillProfile(
            mastered_skills=request.mastered_skills,
            partial_skills=request.partial_skills,
            missing_skills=request.missing_skills,
            target_direction=request.target_direction
        )
        
        # 构建知识图谱
        graph_data = career_kg.build_career_graph(user_profile)
        
        return {
            "success": True,
            "data": graph_data,
            "message": f"已生成职业知识图谱，包含{graph_data['metadata']['total_nodes']}个节点"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/career-graph/learning-path")
async def get_learning_path(
    user_id: str,
    mastered_skills: List[str],
    partial_skills: List[str],
    target_skill: str,
    target_direction: str = "Python工程师"
):
    """
    获取学习路径
    
    返回从当前技能到目标技能的学习路径
    """
    try:
        user_profile = UserSkillProfile(
            mastered_skills=mastered_skills,
            partial_skills=partial_skills,
            missing_skills=[],
            target_direction=target_direction
        )
        
        path = career_kg.calculate_learning_path(user_profile, target_skill)
        
        return {
            "success": True,
            "data": {
                "target_skill": target_skill,
                "learning_path": path,
                "steps": len(path)
            },
            "message": f"需要学习{len(path)}个技能"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/career-graph/reachable-jobs")
async def get_reachable_jobs(
    user_id: str,
    mastered_skills: str,  # JSON字符串列表
    partial_skills: str,   # JSON字符串列表
    target_direction: str = "Python工程师",
    max_missing_skills: int = 3
):
    """
    获取可达岗位
    
    返回用户当前技能可以达到的岗位列表
    """
    try:
        import json
        mastered = json.loads(mastered_skills)
        partial = json.loads(partial_skills)
        
        user_profile = UserSkillProfile(
            mastered_skills=mastered,
            partial_skills=partial,
            missing_skills=[],
            target_direction=target_direction
        )
        
        reachable = career_kg.find_reachable_jobs(user_profile, max_missing_skills)
        
        return {
            "success": True,
            "data": {
                "reachable_jobs": reachable,
                "count": len(reachable)
            },
            "message": f"找到{len(reachable)}个可达岗位"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
        # 获取可达岗位
        reachable = career_kg.get_reachable_jobs(user_profile, jobs, min_match_score)
        
        return {
            "success": True,
            "data": {
                "reachable_jobs": [
                    {
                        "title": item["job"].title,
                        "company": item["job"].company,
                        "salary_range": f"{item['job'].salary_min}-{item['job'].salary_max}万",
                        "match_score": item["match_score"],
                        "missing_skills": item["missing_skills"]
                    }
                    for item in reachable
                ],
                "total": len(reachable)
            },
            "message": f"找到{len(reachable)}个可达岗位"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
