"""
Agent对话路由
Agent Chat Routes
"""
from flask import Blueprint, request, jsonify
from backend.auth.auth_middleware import require_auth
from backend.llm.llm_service import get_llm_service
from backend.learning.rag_manager import RAGManager
from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval, QueryType
from typing import List, Dict, Any

agent_chat_bp = Blueprint('agent_chat', __name__)


# Agent系统提示词
AGENT_SYSTEM_PROMPTS = {
    'relationship': """你是一位专业的人际关系分析师Agent。你的专长包括：
- 社交网络分析
- 人际关系质量评估
- 沟通模式优化
- 社交技能提升
- 人际冲突处理

你的回答应该：
1. 基于用户的实际情况（从知识图谱和记忆系统中检索）
2. 提供具体、可操作的建议
3. 保持专业、友善的语气
4. 关注用户的情感需求
5. 每次回答控制在200字以内，简洁明了

记住：你是人际关系领域的专家，专注于帮助用户改善社交生活。""",

    'education': """你是一位专业的教育升学规划师Agent。你的专长包括：
- 升学路径规划（考研/就业/出国）
- 学校和专业选择建议
- 学习方法优化
- 学业竞争力提升
- 课程规划建议

你的回答应该：
1. 基于用户的学业背景和目标
2. 提供数据支持的分析
3. 给出清晰的行动步骤
4. 考虑用户的实际情况
5. 每次回答控制在200字以内，简洁明了

记住：你是教育规划领域的专家，专注于帮助学生做出明智的升学决策。""",

    'career': """你是一位专业的职业发展规划师Agent。你的专长包括：
- 职业方向选择
- 技能匹配分析
- 职业发展路径规划
- 求职策略建议
- 工作机会评估

你的回答应该：
1. 基于用户的技能和兴趣
2. 结合市场需求和趋势
3. 提供实用的职业建议
4. 关注长期职业发展
5. 每次回答控制在200字以内，简洁明了

记住：你是职业规划领域的专家，专注于帮助用户实现职业目标。"""
}


@agent_chat_bp.route('/api/agent-chat', methods=['POST'])
@require_auth
def agent_chat(current_user_id: str):
    """
    Agent对话接口
    
    请求体：
    {
        "agent_type": "relationship" | "education" | "career",
        "message": "用户消息",
        "conversation_history": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    try:
        data = request.get_json()
        agent_type = data.get('agent_type')
        user_message = data.get('message')
        conversation_history = data.get('conversation_history', [])
        
        if not agent_type or not user_message:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            return jsonify({
                'success': False,
                'message': '无效的Agent类型'
            }), 400
        
        # 1. 从RAG和知识图谱检索相关信息
        context = _retrieve_context(current_user_id, user_message, agent_type)
        
        # 2. 构建对话消息
        messages = _build_messages(
            agent_type=agent_type,
            user_message=user_message,
            conversation_history=conversation_history,
            context=context
        )
        
        # 3. 调用LLM生成回复
        llm_service = get_llm_service()
        if not llm_service or not llm_service.enabled:
            return jsonify({
                'success': False,
                'message': 'LLM服务不可用'
            }), 503
        
        response = llm_service.chat(
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'context_used': len(context) > 0
        })
        
    except Exception as e:
        print(f"❌ Agent对话失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'对话失败: {str(e)}'
        }), 500


def _retrieve_context(user_id: str, query: str, agent_type: str) -> str:
    """检索相关上下文信息"""
    try:
        # 使用混合检索系统
        retrieval = UnifiedHybridRetrieval(user_id=user_id)
        
        # 根据Agent类型确定查询类型和领域过滤
        query_type = QueryType.SEMANTIC
        domain_filter = None
        
        if agent_type == 'relationship':
            domain_filter = 'relationship'
        elif agent_type == 'education':
            domain_filter = 'education'
        elif agent_type == 'career':
            domain_filter = 'career'
        
        # 执行检索
        retrieval_context = retrieval.retrieve(
            query=query,
            query_type=query_type,
            max_results=5,
            domain_filter=domain_filter
        )
        
        # 提取相关内容
        if retrieval_context and retrieval_context.results:
            context_parts = []
            for result in retrieval_context.results[:3]:  # 最多3条
                context_parts.append(f"- {result.content}")
            
            return "\n".join(context_parts)
        
        return ""
        
    except Exception as e:
        print(f"⚠️ 上下文检索失败: {e}")
        return ""


def _build_messages(
    agent_type: str,
    user_message: str,
    conversation_history: List[Dict[str, str]],
    context: str
) -> List[Dict[str, str]]:
    """构建对话消息"""
    messages = []
    
    # 1. 系统提示词
    system_prompt = AGENT_SYSTEM_PROMPTS[agent_type]
    
    # 2. 如果有上下文，添加到系统提示词
    if context:
        system_prompt += f"\n\n用户相关信息：\n{context}"
    
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # 3. 添加历史对话（最多保留最近5轮）
    recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
    messages.extend(recent_history)
    
    # 4. 添加当前用户消息
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages
