from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.decision.future_os_service import FutureOSService
from backend.vertical.career.career_knowledge_graph import career_kg, UserSkillProfile
from backend.vertical.education.education_knowledge_graph import education_kg, EducationUserProfile


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


# 教育知识图谱相关请求模型
class EducationGraphRequest(BaseModel):
    """教育升学知识图谱请求"""
    user_id: str
    gpa: float = 3.5                      # 当前GPA
    gpa_max: float = 4.0                  # GPA满分
    ranking_percent: float = 0.2          # 年级排名百分比
    sat_act: float = 0.0                  # SAT/ACT成绩
    research_experience: float = 0.5      # 科研经历 (0-1)
    publications: int = 0                 # 发表论文数
    target_major: str = ""                # 目标专业
    target_level: str = "master"          # 目标学历：bachelor/master/phd
    search_keyword: str = ""              # 搜索关键词
    location: str = ""                    # 地理位置


@router.get("/knowledge/{user_id}")
async def get_future_os_knowledge_view(
    user_id: str,
    view: str = "people",
    question: str = "",
    session_id: Optional[str] = None,
):
    """获取知识星图视图（三级缓存架构）"""
    import time
    start_time = time.time()
    print(f"[KG API] 📥 收到请求 - user_id={user_id}, view={view}, question={question or '(空)'}, session_id={session_id or '(空)'}")
    
    try:
        view_start = time.time()
        payload = service.get_graph_view(user_id, view, question, session_id)
        view_time = time.time() - view_start
        
        total_time = time.time() - start_time
        print(f"[KG API] ✅ 请求完成 - 视图耗时={view_time:.3f}s, 总耗时={total_time:.3f}s, 节点数={len(payload.get('nodes', []))}")
        
        return {"success": True, "data": payload}
    except Exception as exc:
        error_time = time.time() - start_time
        print(f"[KG API] ❌ 请求失败 - 错误={str(exc)}, 耗时={error_time:.3f}s")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(exc), "data": {"nodes": [], "links": [], "summary": {}}}


@router.delete("/knowledge/{user_id}/cache")
async def clear_knowledge_graph_cache(user_id: str):
    """清除知识图谱缓存"""
    try:
        # 清除L1内存缓存
        from backend.decision.future_os_service import _l1_cache
        _l1_cache.clear()
        
        # 清除L2 Redis缓存
        from backend.decision.future_os_service import _get_redis_client
        redis_client = _get_redis_client()
        if redis_client:
            # 删除该用户的所有视图缓存
            pattern = f"kg_view:{user_id}:*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        
        return {"success": True, "message": f"已清除用户 {user_id} 的所有缓存"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    try:
        from backend.decision.future_os_service import _l1_cache, _get_redis_client
        
        # L1统计
        l1_stats = _l1_cache.stats()
        
        # L2统计
        l2_stats = {"status": "unavailable"}
        try:
            redis_client = _get_redis_client()
            if redis_client:
                info = redis_client.info("stats")
                l2_stats = {
                    "status": "connected",
                    "total_commands": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
                if l2_stats["keyspace_hits"] + l2_stats["keyspace_misses"] > 0:
                    hit_rate = l2_stats["keyspace_hits"] / (l2_stats["keyspace_hits"] + l2_stats["keyspace_misses"])
                    l2_stats["hit_rate"] = f"{hit_rate:.2%}"
        except Exception as e:
            l2_stats = {"status": "error", "message": str(e)}
        
        return {
            "success": True,
            "data": {
                "l1_memory_cache": l1_stats,
                "l2_redis_cache": l2_stats,
                "architecture": "三级缓存：L1(内存) → L2(Redis) → L3(计算)"
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
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


@router.post("/education-graph")
async def get_education_knowledge_graph(request: EducationGraphRequest):
    """
    获取教育升学决策知识图谱
    - 第一圈：学业层（GPA、排名、标化）
    - 第二圈：目标学校层（冲刺/匹配/保底）
    - 第三圈：规划行动层（备考任务、申请策略）
    """
    try:
        user_profile = EducationUserProfile(
            student_id=request.user_id,
            gpa=request.gpa, gpa_max=request.gpa_max,
            ranking_percent=request.ranking_percent,
            sat_act=request.sat_act,
            research_experience=request.research_experience,
            publications=request.publications,
            target_major=request.target_major,
            target_level=request.target_level
        )
        graph_data = education_kg.build_education_graph(
            user_profile=user_profile,
            search_keyword=request.search_keyword,
            location=request.location
        )
        return {
            "success": True,
            "data": graph_data,
            "message": "已生成教育升学知识图谱"
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
