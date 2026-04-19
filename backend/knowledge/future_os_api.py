from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.decision.future_os_service import FutureOSService
from backend.vertical.general.general_decision_engine import (
    get_general_decision_engine,
    GeneralDecisionContext,
)

# 使用Neo4j版本的知识图谱（真实数据）
from backend.vertical.career.neo4j_career_kg import get_neo4j_career_kg, UserSkillProfile
from backend.vertical.education.neo4j_education_kg import get_neo4j_education_kg, EducationUserProfile
from backend.vertical.relationship.people_graph_builder import get_people_graph_builder, PeopleGraphRequest

# 初始化知识图谱实例
career_kg = get_neo4j_career_kg()
education_kg = get_neo4j_education_kg()
people_graph_builder = get_people_graph_builder()

print("[FutureOS API] 使用Neo4j知识图谱（真实数据）")


router = APIRouter(prefix="/api/v5/future-os", tags=["future-os"])
service = FutureOSService()
general_engine = get_general_decision_engine()


# ==================== 辅助函数 ====================

def _extract_skills_from_kg(user_id: str) -> Dict[str, Any]:
    """从用户知识图谱中提取技能数据"""
    try:
        from backend.knowledge.information_knowledge_graph import InformationKnowledgeGraph
        
        kg = InformationKnowledgeGraph(user_id)
        try:
            export = kg.export()
            info_nodes = export.get('information', [])
            
            # 提取技能节点（类型为 Skill 或 category 为 skill）
            mastered_skills = []
            partial_skills = []
            missing_skills = []
            target_direction = None
            
            for node in info_nodes:
                node_type = node.get('type', '').lower()
                category = node.get('category', '').lower()
                name = node.get('name', '')
                
                # 识别技能节点
                if node_type == 'skill' or category == 'skill' or 'skill' in category:
                    # 根据掌握程度分类
                    mastery = node.get('mastery', 0.0)  # 0-1 的掌握程度
                    confidence = node.get('confidence', 0.8)
                    
                    if mastery >= 0.7 or confidence >= 0.8:
                        mastered_skills.append(name)
                    elif mastery >= 0.3:
                        partial_skills.append(name)
                    else:
                        missing_skills.append(name)
                
                # 识别职业方向
                if node_type == 'career_goal' or category == 'career':
                    target_direction = name
            
            # 如果没有找到技能，返回空列表（新用户）
            return {
                'mastered': mastered_skills,
                'partial': partial_skills,
                'missing': missing_skills,
                'target_direction': target_direction or 'Python工程师'
            }
        finally:
            kg.close()
    
    except Exception as e:
        print(f"[提取技能失败] {e}")
        return {
            'mastered': [],
            'partial': [],
            'missing': [],
            'target_direction': 'Python工程师'
        }


# ==================== 请求模型 ====================
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


# 人物关系图谱相关请求模型
class PeopleGraphRequest(BaseModel):
    """人物关系图谱请求"""
    user_id: str
    question: str = ""                    # 用户问题/场景
    session_id: Optional[str] = None      # 会话ID


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


# ==================== 已废弃：通用知识图谱端点 ====================
# 该端点已被三个专用端点替代：
# - /people-graph: 人物关系图谱
# - /career-graph: 职业发展图谱  
# - /education-graph: 升学规划图谱
# 
# @router.get("/knowledge/{user_id}")
# async def get_future_os_knowledge_view(...):
#     """已废弃，请使用专用端点"""
#     pass


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
    """通用决策推演（使用独立的GeneralDecisionEngine）"""
    try:
        # 构建上下文
        context_data = service.build_context(
            request.user_id, 
            request.question, 
            request.session_id
        )
        
        # 创建GeneralDecisionContext
        context = GeneralDecisionContext(
            user_id=request.user_id,
            question=request.question,
            profile=context_data["profile"],
            top_people=context_data.get("top_people", []),
            top_education=context_data.get("top_education", []),
            top_career=context_data.get("top_career", []),
            recommended_view=context_data.get("recommended_view", "people"),
            session_id=request.session_id,
        )
        
        # 使用通用决策引擎进行推演
        payload = general_engine.simulate_decision(
            user_id=request.user_id,
            question=request.question,
            context=context,
            options=request.options,
        )
        
        return {"success": True, "data": payload}
    except Exception as exc:
        return {"success": False, "message": str(exc), "data": None}


@router.get("/simulations/{simulation_id}")
async def get_future_os_simulation(simulation_id: str):
    """加载决策推演结果（使用GeneralDecisionEngine）"""
    payload = general_engine.load_simulation(simulation_id)
    if not payload:
        return {"success": False, "message": "未找到对应的推演记录", "data": None}
    return {"success": True, "data": payload}


@router.get("/history/{user_id}")
async def list_future_os_history(user_id: str, limit: int = 20):
    """列出决策推演历史（使用GeneralDecisionEngine）"""
    try:
        payload = general_engine.list_simulations(user_id, limit)
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



# ==================== 人物关系图谱 API ====================

@router.post("/people-graph")
async def get_people_knowledge_graph(request: PeopleGraphRequest):
    """
    获取人物关系知识图谱（基于用户个人数据 + 三级缓存）
    
    基于用户个人知识图谱中的人物关系数据构建3D可视化图谱
    """
    try:
        print(f"[PeopleGraph API] 收到请求 - user_id: {request.user_id}, session_id: {request.session_id}")
        
        # 加载用户的知识图谱数据
        export = service._load_graph_export(request.user_id)
        info_nodes = list(export.get("information") or [])
        relationships = list(export.get("relationships") or [])
        
        print(f"[PeopleGraph API] 加载数据 - 节点数: {len(info_nodes)}, 关系数: {len(relationships)}")
        
        # 使用people图谱构建器
        graph_data = people_graph_builder.build_people_graph(
            user_id=request.user_id,
            info_nodes=info_nodes,
            relationships=relationships,
            question=request.question,
            session_id=request.session_id
        )
        
        return {
            "success": True,
            "data": graph_data,
            "message": f"已生成人物关系图谱，包含{graph_data['summary']['node_count']}个节点"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 职业知识图谱 API ====================

@router.post("/career-graph")
async def get_career_knowledge_graph(request: CareerGraphRequest):
    """
    获取职业决策知识图谱（基于用户数据）
    
    返回3D可视化图谱数据：
    - 第一圈：技能层（用户已掌握/部分掌握/缺失的技能）
    - 第二圈：岗位层（根据用户技能匹配的真实岗位）
    - 第三圈：公司层（真实公司信息）
    """
    try:
        # 从用户的知识图谱中查询技能数据
        mastered_skills = request.mastered_skills or []
        partial_skills = request.partial_skills or []
        missing_skills = request.missing_skills or []
        target_direction = request.target_direction or "Python工程师"
        
        # 如果前端没有传递技能数据，从用户知识图谱中查询
        if not mastered_skills and not partial_skills:
            print(f"[CareerGraph API] 前端未传递技能数据，从知识图谱查询用户 {request.user_id} 的技能")
            skills_from_kg = _extract_skills_from_kg(request.user_id)
            mastered_skills = skills_from_kg.get('mastered', [])
            partial_skills = skills_from_kg.get('partial', [])
            missing_skills = skills_from_kg.get('missing', [])
            target_direction = skills_from_kg.get('target_direction', target_direction)
            print(f"[CareerGraph API] 从知识图谱提取技能 - 掌握: {len(mastered_skills)}, 部分: {len(partial_skills)}, 缺失: {len(missing_skills)}")
        
        # 构建用户技能画像
        user_profile = UserSkillProfile(
            mastered_skills=mastered_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            target_direction=target_direction,
            user_id=request.user_id  # 传递 user_id 用于缓存隔离
        )
        
        # 构建知识图谱（基于用户技能数据）
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
    获取教育升学决策知识图谱（基于用户数据）
    
    - 第一圈：学业层（用户的GPA、排名、标化成绩、科研经历）
    - 第二圈：目标学校层（根据用户成绩匹配的冲刺/匹配/保底院校）
    - 第三圈：规划行动层（个性化的备考任务、申请策略）
    """
    try:
        # 构建用户学业档案
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
        
        # 构建知识图谱（基于用户学业数据）
        graph_data = education_kg.build_education_graph(
            user_profile=user_profile,
            search_keyword=request.search_keyword,
            location=request.location
        )
        
        return {
            "success": True,
            "data": graph_data,
            "message": f"已生成教育升学知识图谱，包含{graph_data['metadata']['total_nodes']}个节点"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
