"""
Agent对话路由 - 使用新的LangChain + Workflow + MCP架构
Agent Chat Routes - Using New LangChain + Workflow + MCP Architecture
"""
from flask import Blueprint, request, jsonify
from backend.auth.auth_middleware import require_auth
from backend.llm.llm_service import get_llm_service
from backend.learning.production_rag_system import ProductionRAGSystem
from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
from backend.agents.langchain_specialized_agents import create_langchain_agent
from backend.agents.mcp_integration import MCPHost
from backend.agents.specialized_mcp_servers import (
    WebSearchMCPServer,
    RelationshipMCPServer,
    EducationMCPServer
)
from typing import List, Dict, Any
import asyncio

agent_chat_bp = Blueprint('agent_chat', __name__)

# 全局Agent缓存（避免重复创建）
_agent_cache = {}

def _get_or_create_agent(user_id: str, agent_type: str):
    """获取或创建Agent实例（使用新架构 + MCP搜索）"""
    cache_key = f"{user_id}_{agent_type}"
    
    if cache_key in _agent_cache:
        return _agent_cache[cache_key]
    
    try:
        # 初始化服务
        llm_service = get_llm_service()
        if not llm_service or not llm_service.enabled:
            raise Exception("LLM服务不可用")
        
        # 初始化RAG系统（使用CPU模式）
        rag_system = ProductionRAGSystem(user_id, use_gpu=False)
        
        # 初始化检索系统
        retrieval_system = UnifiedHybridRetrieval(user_id)
        
        # ===== 创建MCP Host并注册工具 =====
        mcp_host = MCPHost(user_id=user_id)
        
        # 1. 注册联网搜索（所有Agent共享）
        mcp_host.register_server(WebSearchMCPServer())
        print(f"  ✓ 已注册联网搜索工具")
        
        # 2. 根据Agent类型注册专属工具
        if agent_type == 'relationship':
            mcp_host.register_server(RelationshipMCPServer())
            print(f"  ✓ 已注册人际关系专属工具")
        elif agent_type == 'education':
            mcp_host.register_server(EducationMCPServer())
            print(f"  ✓ 已注册教育规划专属工具")
        elif agent_type == 'career':
            # CareerMCPServer 待实现
            print(f"  ⚠ 职业发展专属工具待实现")
        
        # 创建Agent（传入MCP Host）
        agent = create_langchain_agent(
            agent_type=agent_type,
            user_id=user_id,
            llm_service=llm_service,
            rag_system=rag_system,
            retrieval_system=retrieval_system,
            use_workflow=True,  # 启用Workflow混合模式
            mcp_host=mcp_host   # 传入MCP Host
        )
        
        # 异步初始化Agent（发现MCP工具）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(agent.initialize())
        loop.close()
        
        # 缓存Agent
        _agent_cache[cache_key] = agent
        
        print(f"✅ 为用户 {user_id} 创建 {agent_type} Agent（已集成联网搜索）")
        return agent
        
    except Exception as e:
        print(f"❌ Agent创建失败: {e}")
        raise


@agent_chat_bp.route('/api/agent-chat', methods=['POST'])
@require_auth
def agent_chat(current_user_id: str):
    """
    Agent对话接口 - 使用新的LangChain + Workflow + MCP架构
    
    请求体：
    {
        "agent_type": "relationship" | "education" | "career",
        "message": "用户消息",
        "conversation_id": "会话ID（可选）",
        "conversation_title": "会话标题（可选）"
    }
    
    返回：
    {
        "success": true,
        "response": "Agent回复",
        "mode": "workflow_only" | "workflow_agent_hybrid" | "pure_agent",
        "agent_used": true/false,
        "execution_path": ["start", "memory_load", ...],
        "retrieval_stats": {
            "intent": "意图",
            "complexity": "simple/medium/complex",
            "context_window_size": 4
        }
    }
    """
    try:
        data = request.get_json()
        agent_type = data.get('agent_type')
        user_message = data.get('message')
        conversation_id = data.get('conversation_id')
        conversation_title = data.get('conversation_title')
        
        if not agent_type or not user_message:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        if agent_type not in ['relationship', 'education', 'career']:
            return jsonify({
                'success': False,
                'message': '无效的Agent类型'
            }), 400
        
        # 获取或创建Agent（使用新架构）
        agent = _get_or_create_agent(current_user_id, agent_type)
        
        # 使用Agent处理消息（自动使用Workflow + ReAct）
        result = agent.process(user_message)
        
        # 保存对话记录到数据库（可选）
        if conversation_id:
            _save_conversation(
                user_id=current_user_id,
                conversation_id=conversation_id,
                agent_type=agent_type,
                user_message=user_message,
                agent_response=result['response'],
                conversation_title=conversation_title
            )
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'mode': result['mode'],
            'agent_used': result['agent_used'],
            'execution_path': result.get('execution_path', []),
            'retrieval_stats': result.get('retrieval_stats', {}),
            'tool_calls': result.get('tool_calls', []),  # MCP工具调用信息
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        print(f"❌ Agent对话失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'对话失败: {str(e)}'
        }), 500


def _save_conversation(
    user_id: str,
    conversation_id: str,
    agent_type: str,
    user_message: str,
    agent_response: str,
    conversation_title: str = None
):
    """保存对话记录到数据库"""
    try:
        from backend.database.db_manager import db_manager
        
        # 保存到数据库（如果有对话表）
        # db_manager.save_agent_conversation(...)
        
        print(f"💾 对话已保存: {conversation_id}")
        
    except Exception as e:
        print(f"⚠️ 对话保存失败: {e}")


# ==================== 旧版API（兼容性保留） ====================
