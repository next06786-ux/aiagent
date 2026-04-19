"""
Future OS API - 知识星图系统
提供人物关系、职业发展、教育升学三大知识星图的API端点
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 使用Neo4j版本的知识图谱（基于新架构）
from backend.vertical.career.neo4j_career_kg import (
    Neo4jCareerKnowledgeGraph,
    UserSkillProfile,
    get_neo4j_career_kg
)
from backend.vertical.education.neo4j_education_kg import (
    Neo4jEducationKnowledgeGraph,
    EducationUserProfile,
    get_neo4j_education_kg
)
from backend.vertical.relationship.neo4j_relationship_kg import (
    Neo4jRelationshipKnowledgeGraph,
    RelationshipUserProfile,
    get_neo4j_relationship_kg
)

print("[FutureOS API] 使用Neo4j知识图谱（基于3.0架构规范）")

router = APIRouter(prefix="/api/v5/future-os", tags=["future-os"])

# 初始化知识图谱实例（使用单例模式）
career_kg = get_neo4j_career_kg()
education_kg = get_neo4j_education_kg()
relationship_kg = get_neo4j_relationship_kg()


# ==================== 辅助函数 ====================

def _extract_skills_from_kg(user_id: str) -> Dict[str, Any]:
    """从用户知识图谱中提取技能数据（使用统一查询系统）"""
    try:
        from backend.database.connection import neo4j_connection
        
        driver = neo4j_connection.get_driver()
        
        query = """
        MATCH (u:User {user_id: $user_id})-[r]->(s)
        WHERE s:Skill OR (s:Concept AND s.type = 'Skill')
        RETURN s.name AS skill, 
               COALESCE(s.level, r.level, 'intermediate') AS level,
               COALESCE(s.confidence, r.confidence, 0.8) AS confidence
        ORDER BY confidence DESC
        LIMIT 50
        """
        
        with driver.session() as session:
            result = session.run(query, user_id=user_id)
            skills = []
            for record in result:
                skills.append({
                    'name': record['skill'],
                    'level': record.get('level', 'intermediate'),
                    'confidence': record.get('confidence', 0.8)
                })
        
        # 根据level分类技能
        mastered_skills = [s['name'] for s in skills if s['level'] in ['高级', 'advanced', 'expert', 'master']]
        partial_skills = [s['name'] for s in skills if s['level'] in ['中级', 'intermediate', 'medium']]
        missing_skills = []
        
        return {
            'mastered': mastered_skills,
            'partial': partial_skills,
            'missing': missing_skills,
            'target_direction': 'Python工程师'
        }
    
    except Exception as e:
        print(f"[提取技能失败] {e}")
        import traceback
        traceback.print_exc()
        return {
            'mastered': [],
            'partial': [],
            'missing': [],
            'target_direction': 'Python工程师'
        }


# ==================== 请求模型 ====================

class PeopleGraphRequest(BaseModel):
    """人物关系图谱请求"""
    user_id: str
    question: str = ""
    session_id: Optional[str] = None


class CareerGraphRequest(BaseModel):
    """职业知识图谱请求"""
    user_id: str
    mastered_skills: List[str] = Field(default_factory=list)
    partial_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    target_direction: str = "Python工程师"


class EducationGraphRequest(BaseModel):
    """教育升学知识图谱请求"""
    user_id: str
    gpa: float = 3.5
    gpa_max: float = 4.0
    ranking_percent: float = 0.2
    sat_act: float = 0.0
    research_experience: float = 0.5
    publications: int = 0
    target_major: str = ""
    target_level: str = "master"
    search_keyword: str = ""
    location: str = ""


# ==================== 人物关系图谱 API ====================

@router.post("/people-graph")
async def get_people_knowledge_graph(request: PeopleGraphRequest):
    """
    获取人物关系知识图谱（基于Neo4j 3.0架构）
    
    从用户的知识图谱中查询人物关系数据，构建3D可视化图谱
    """
    try:
        print(f"[PeopleGraph API] 收到请求 - user_id: {request.user_id}")
        
        # 构建用户画像
        user_profile = RelationshipUserProfile(
            user_id=request.user_id,
            name="我",
            question=request.question or "",
            session_id=request.session_id
        )
        
        # 使用Neo4j关系图谱构建器
        graph_data = relationship_kg.build_relationship_graph(
            user_profile=user_profile,
            use_hybrid=True
        )
        
        return {
            "success": True,
            "data": graph_data,
            "message": f"已生成人物关系图谱，包含{graph_data['metadata']['total_nodes']}个节点"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 职业知识图谱 API ====================

@router.post("/career-graph")
async def get_career_knowledge_graph(request: CareerGraphRequest):
    """
    获取职业决策知识图谱（基于Neo4j 3.0架构）
    
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
            print(f"[CareerGraph API] 从知识图谱查询用户 {request.user_id} 的技能")
            skills_from_kg = _extract_skills_from_kg(request.user_id)
            mastered_skills = skills_from_kg.get('mastered', [])
            partial_skills = skills_from_kg.get('partial', [])
            missing_skills = skills_from_kg.get('missing', [])
            target_direction = skills_from_kg.get('target_direction', target_direction)
        
        # 构建用户技能画像
        user_profile = UserSkillProfile(
            mastered_skills=mastered_skills,
            partial_skills=partial_skills,
            missing_skills=missing_skills,
            target_direction=target_direction,
            user_id=request.user_id
        )
        
        # 构建知识图谱（基于用户技能数据）
        graph_data = career_kg.build_career_graph(user_profile, use_hybrid=True)
        
        return {
            "success": True,
            "data": graph_data,
            "message": f"已生成职业知识图谱，包含{graph_data['metadata']['total_nodes']}个节点"
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 教育知识图谱 API ====================

@router.post("/education-graph")
async def get_education_knowledge_graph(request: EducationGraphRequest):
    """
    获取教育升学决策知识图谱（基于Neo4j 3.0架构）
    
    - 第一圈：学业层（用户的GPA、排名、标化成绩、科研经历）
    - 第二圈：目标学校层（根据用户成绩匹配的冲刺/匹配/保底院校）
    - 第三圈：规划行动层（个性化的备考任务、申请策略）
    """
    try:
        # 构建用户学业档案
        user_profile = EducationUserProfile(
            student_id=request.user_id,
            gpa=request.gpa,
            gpa_max=request.gpa_max,
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
            location=request.location,
            use_hybrid=True
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


print("Future OS API 已加载")
print("   - POST /api/v5/future-os/people-graph - 人物关系图谱")
print("   - POST /api/v5/future-os/career-graph - 职业发展图谱")
print("   - POST /api/v5/future-os/education-graph - 教育升学图谱")
