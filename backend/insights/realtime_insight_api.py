"""
实时智慧洞察API - 多Agent协作模式
提供三个Agent的HTTP接口（全部基于多Agent协作系统）
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.auth.auth_service import get_current_user_id
from backend.insights.multi_agent_system import create_multi_agent_system
from backend.insights.collaborative_agents import create_collaborative_agents

router = APIRouter()


# ==================== 请求模型 ====================

class InsightRequest(BaseModel):
    """通用洞察请求"""
    query: str = "分析我的整体发展情况"
    agent_chain: List[str] = ["relationship", "education", "career"]  # Agent执行顺序
    initial_context: Optional[Dict[str, Any]] = None


class SingleAgentRequest(BaseModel):
    """单个Agent请求（仍使用协作系统，但只执行一个Agent）"""
    query: str
    context: Optional[Dict[str, Any]] = None


# ==================== API端点 ====================

@router.post("/multi-agent/insight")
async def generate_multi_agent_insight(
    request: InsightRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    多Agent协作生成洞察报告
    
    特点：
    - 共享记忆空间：所有Agent共用RAG+Neo4j混合检索数据
    - 任务链传递：一个Agent的输出自动成为下一个Agent的输入
    - 状态广播：Agent完成工作后通知相关方
    - 三层混合AI：每个Agent都具备规则引擎+机器学习+LLM
    
    示例请求:
    {
        "query": "分析我的整体发展情况",
        "agent_chain": ["relationship", "education", "career"],
        "initial_context": {"focus": "career_transition"}
    }
    """
    try:
        # 创建多Agent系统
        gateway = create_multi_agent_system(user_id)
        
        # 创建并注册所有Agent
        agents = create_collaborative_agents(user_id)
        for agent in agents.values():
            gateway.register_agent(agent)
        
        # 执行任务链
        results = gateway.execute_task_chain(
            query=request.query,
            agent_chain=request.agent_chain,
            initial_data=request.initial_context
        )
        
        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"多Agent协作失败: {str(e)}")


@router.post("/cross-domain/comprehensive-analysis")
async def generate_cross_domain_analysis(
    request: InsightRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    跨领域综合分析 - 真正的多Agent并行协作
    
    功能：
    1. 三个Agent并行执行，共享记忆空间
    2. Agent之间实时状态广播和信息交互
    3. 每个Agent的输出会影响其他Agent
    4. 最后由跨领域Agent整合所有结果
    
    执行流程：
    1. 初始化共享记忆空间（RAG + Neo4j混合检索）
    2. 并行启动3个Agent（relationship, education, career）
    3. Agent之间通过消息队列实时交互
    4. 等待所有Agent完成
    5. 跨领域Agent整合结果
    
    示例场景：
    - "我的人际关系如何影响职业发展？"
    - "教育背景和人脉资源如何协同提升职业竞争力？"
    - "如何平衡学业、人际关系和职业规划？"
    """
    try:
        # 创建多Agent系统
        gateway = create_multi_agent_system(user_id)
        
        # 创建并注册所有Agent
        agents = create_collaborative_agents(user_id)
        for agent in agents.values():
            gateway.register_agent(agent)
        
        # 使用并行执行模式：三个领域Agent同时工作
        parallel_agents = ["relationship", "education", "career"]
        
        # 并行执行三个Agent
        parallel_results = await gateway.execute_parallel_agents(
            query=request.query,
            agent_names=parallel_agents,
            initial_data=request.initial_context or {"analysis_type": "comprehensive"}
        )
        
        # 如果有跨领域Agent，串行执行它（需要等待前面的Agent完成）
        if "cross_domain" in agents:
            # 跨领域Agent使用前面三个Agent的输出
            cross_domain_input = {
                "query": request.query,
                "hybrid_data": gateway.shared_memory.hybrid_data,
                "prev_agent_outputs": {
                    "relationship": parallel_results["results"].get("relationship", {}),
                    "education": parallel_results["results"].get("education", {}),
                    "career": parallel_results["results"].get("career", {})
                },
                "context": gateway.shared_memory.task_chain_context
            }
            
            cross_domain_result = agents["cross_domain"].execute(cross_domain_input)
            parallel_results["results"]["cross_domain"] = cross_domain_result
        else:
            cross_domain_result = {}
        
        return {
            "status": "success",
            "query": request.query,
            "analysis_type": "cross_domain_comprehensive",
            "execution_mode": "parallel",
            "domain_results": {
                "relationship": parallel_results["results"].get("relationship", {}),
                "education": parallel_results["results"].get("education", {}),
                "career": parallel_results["results"].get("career", {})
            },
            "cross_domain_analysis": {
                "summary": cross_domain_result.get("summary", ""),
                "cross_domain_patterns": cross_domain_result.get("cross_domain_patterns", []),
                "synergies": cross_domain_result.get("synergies", []),
                "conflicts": cross_domain_result.get("conflicts", []),
                "strategic_recommendations": cross_domain_result.get("strategic_recommendations", []),
                "integrated_insights": cross_domain_result.get("integrated_insights", []),
                "action_plan": cross_domain_result.get("action_plan", {})
            },
            "execution_summary": {
                "total_agents": len(parallel_agents) + (1 if "cross_domain" in agents else 0),
                "execution_time": parallel_results.get("execution_time", 0),
                "shared_context_size": len(parallel_results.get("shared_context", {})),
                "message_count": len(gateway.message_queue)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"跨领域综合分析失败: {str(e)}")


@router.post("/relationship/insight")
async def generate_relationship_insight(
    request: SingleAgentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    生成人际关系洞察报告（使用协作系统，单Agent模式）
    """
    try:
        gateway = create_multi_agent_system(user_id)
        agents = create_collaborative_agents(user_id)
        gateway.register_agent(agents["relationship"])
        
        results = gateway.execute_task_chain(
            query=request.query,
            agent_chain=["relationship"],
            initial_data=request.context
        )
        
        return {
            "status": "success",
            "report": results["results"].get("relationship", {}),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.post("/education/insight")
async def generate_education_insight(
    request: SingleAgentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    生成教育升学洞察报告（使用协作系统，单Agent模式）
    """
    try:
        gateway = create_multi_agent_system(user_id)
        agents = create_collaborative_agents(user_id)
        gateway.register_agent(agents["education"])
        
        results = gateway.execute_task_chain(
            query=request.query,
            agent_chain=["education"],
            initial_data=request.context
        )
        
        return {
            "status": "success",
            "report": results["results"].get("education", {}),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.post("/career/insight")
async def generate_career_insight(
    request: SingleAgentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    生成职业规划洞察报告（使用协作系统，单Agent模式）
    """
    try:
        gateway = create_multi_agent_system(user_id)
        agents = create_collaborative_agents(user_id)
        gateway.register_agent(agents["career"])
        
        results = gateway.execute_task_chain(
            query=request.query,
            agent_chain=["career"],
            initial_data=request.context
        )
        
        return {
            "status": "success",
            "report": results["results"].get("career", {}),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.get("/agents/status")
async def get_agents_status(user_id: str = Depends(get_current_user_id)):
    """获取所有Agent的状态"""
    return {
        "status": "success",
        "mode": "multi_agent_collaboration",
        "agents": {
            "relationship": {
                "name": "人际关系洞察Agent",
                "description": "分析人际关系网络、社交模式、关系质量",
                "features": ["三层混合AI", "多Agent协作"],
                "available": True
            },
            "education": {
                "name": "教育升学洞察Agent",
                "description": "分析升学路径、学校选择、专业匹配",
                "features": ["三层混合AI", "多Agent协作"],
                "available": True
            },
            "career": {
                "name": "职业规划洞察Agent",
                "description": "分析职业发展路径、技能匹配、岗位选择",
                "features": ["三层混合AI", "多Agent协作"],
                "available": True
            },
            "cross_domain": {
                "name": "跨领域综合分析Agent",
                "description": "整合三个领域的洞察，发现跨领域关联，生成综合战略建议",
                "features": ["跨领域整合", "协同效应分析", "冲突识别", "战略规划"],
                "available": True,
                "highlight": "核心功能"
            }
        },
        "collaboration_features": {
            "shared_memory": "所有Agent共用RAG+Neo4j混合检索数据",
            "task_chain": "Agent输出自动传递给下一个Agent",
            "conflict_resolution": "Gateway协调资源访问",
            "status_broadcast": "Agent完成后通知相关方"
        },
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }
