"""
知识图谱感知RAG集成模块
将 KnowledgeGraphAwareRAG 融入现有的 RAG 架构

使用方式:
1. 聊天时使用知识图谱上下文:
   kg_rag = KGRAGManager.get_system(user_id)
   result = kg_rag.query_with_context(query, llm_service)

2. 检索时使用混合检索:
   context = kg_rag.retrieve(query, mode=RetrievalMode.HYBRID)
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 延迟导入，避免循环依赖
_kgrag_instances: Dict[str, 'KnowledgeGraphAwareRAG'] = {}


def get_kg_rag_system(user_id: str) -> 'KnowledgeGraphAwareRAG':
    """获取用户的知识图谱感知RAG系统实例"""
    if user_id not in _kgrag_instances:
        from backend.learning.knowledge_graph_rag import KnowledgeGraphAwareRAG
        _kgrag_instances[user_id] = KnowledgeGraphAwareRAG(user_id)
    return _kgrag_instances[user_id]


def clear_kg_rag_instances():
    """清除所有实例（用于测试或重置）"""
    global _kgrag_instances
    _kgrag_instances.clear()


# ==================== 上下文构建工具 ====================

def build_rag_context_for_chat(
    user_id: str,
    query: str,
    max_nodes: int = 10,
    include_reasoning: bool = True
) -> Dict[str, Any]:
    """
    为聊天构建RAG上下文字典（用于API返回）

    Returns:
        {
            "context_text": "可读上下文文本",
            "nodes_count": 5,
            "influence_summary": {"人物": 0.4, "职业": 0.6},
            "reasoning": "推理路径描述"
        }
    """
    try:
        kg_rag = get_kg_rag_system(user_id)
        from backend.learning.knowledge_graph_rag import RetrievalMode

        context = kg_rag.retrieve(
            query=query,
            max_nodes=max_nodes,
            mode=RetrievalMode.HYBRID,
            include_reasoning=include_reasoning
        )

        # 构建可读文本
        context_text = context.to_prompt() if hasattr(context, 'to_prompt') else str(context)

        return {
            "context_text": context_text,
            "nodes_count": len(context.nodes),
            "influence_summary": context.influence_summary,
            "reasoning": context.reasoning_path,
            "relationships_count": len(context.relationships)
        }
    except Exception as e:
        print(f"构建RAG上下文失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "context_text": "",
            "nodes_count": 0,
            "influence_summary": {},
            "reasoning": f"上下文构建失败: {str(e)}",
            "relationships_count": 0
        }


def build_prompt_with_kg_context(
    user_id: str,
    query: str,
    system_instruction: str = ""
) -> str:
    """
    构建包含知识图谱上下文的完整Prompt

    Args:
        user_id: 用户ID
        query: 用户查询
        system_instruction: 系统指令（可选）

    Returns:
        完整的Prompt字符串
    """
    context_info = build_rag_context_for_chat(user_id, query)

    # 默认系统指令
    if not system_instruction:
        system_instruction = """你是一个基于用户个人知识图谱的AI助手。
你的回答应该：
1. 结合用户知识图谱中的具体信息
2. 分析各因素对用户的影响
3. 给出有依据的建议"""

    prompt_parts = [
        system_instruction,
        "",
        "=" * 50,
        "【用户知识图谱上下文】",
        "=" * 50,
    ]

    if context_info["context_text"]:
        prompt_parts.append(context_info["context_text"])
    else:
        prompt_parts.append("（当前没有相关的知识图谱数据）")

    prompt_parts.extend([
        "",
        "=" * 50,
        f"【用户问题】: {query}",
        "=" * 50,
    ])

    return "\n".join(prompt_parts)


# ==================== RAG上下文中间件 ====================

class KGRAGContextMiddleware:
    """
    RAG上下文中间件
    自动为对话添加知识图谱上下文

    使用方式:
    middleware = KGRAGContextMiddleware(user_id)
    enhanced_messages = middleware.enhance_messages(messages)
    """

    def __init__(self, user_id: str, max_context_nodes: int = 10):
        self.user_id = user_id
        self.max_context_nodes = max_context_nodes
        self._kg_rag = None

    @property
    def kg_rag(self):
        if self._kg_rag is None:
            self._kg_rag = get_kg_rag_system(self.user_id)
        return self._kg_rag

    def enhance_messages(
        self,
        messages: List[Dict[str, str]],
        last_query: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        增强消息列表，在适当位置插入知识图谱上下文

        Args:
            messages: 原始消息列表 [{"role": "user", "content": "..."}]
            last_query: 最近的查询（用于检索上下文）

        Returns:
            增强后的消息列表
        """
        if not messages:
            return messages

        # 获取最后一条用户消息作为查询
        query = last_query
        if not query:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    query = msg.get("content", "")
                    break

        if not query:
            return messages

        # 检索知识图谱上下文
        try:
            from backend.learning.knowledge_graph_rag import RetrievalMode
            context = self.kg_rag.retrieve(
                query=query,
                max_nodes=self.max_context_nodes,
                mode=RetrievalMode.HYBRID,
                include_reasoning=False  # 简洁模式
            )

            if not context.nodes:
                return messages

            # 构建上下文消息
            context_text = self._build_context_message(context)

            # 在最后一条用户消息后插入系统上下文
            enhanced = []
            messages_added = False

            for i, msg in enumerate(messages):
                enhanced.append(msg)
                # 在用户消息后添加上下文
                if msg.get("role") == "user" and not messages_added:
                    enhanced.append({
                        "role": "system",
                        "content": f"【知识图谱上下文】\n{context_text}\n\n请结合上述上下文回答用户问题。"
                    })
                    messages_added = True

            return enhanced

        except Exception as e:
            print(f"增强消息失败: {e}")
            return messages

    def _build_context_message(self, context) -> str:
        """构建上下文消息文本"""
        lines = []

        if context.influence_summary:
            lines.append("## 因素影响力分析")
            sorted_inf = sorted(context.influence_summary.items(), key=lambda x: x[1], reverse=True)
            for cat, score in sorted_inf[:5]:
                lines.append(f"- {cat}: {score:.1%}")
            lines.append("")

        if context.nodes:
            lines.append(f"## 相关节点 ({len(context.nodes)} 个)")
            for node in context.nodes[:8]:
                lines.append(f"- [{node.node_type}] {node.name} (影响:{node.influence_score:.2f})")

        if context.relationships:
            lines.append("")
            lines.append(f"## 关键关系 ({len(context.relationships)} 条)")
            for rel in context.relationships[:5]:
                src = rel.get('source', '')
                tgt = rel.get('target', '')
                if src and tgt:
                    lines.append(f"- {src} → {tgt}")

        return "\n".join(lines)


# ==================== 对话历史增强 ====================

def enhance_conversation_with_kg(
    user_id: str,
    conversation_history: List[Dict[str, Any]],
    new_query: str
) -> Dict[str, Any]:
    """
    增强对话历史，添加知识图谱分析

    Returns:
        {
            "enhanced_history": [...],  # 增强后的历史
            "kg_context": {...},       # 知识图谱上下文
            "summary": "..."           # 基于图谱的对话摘要
        }
    """
    middleware = KGRAGContextMiddleware(user_id)

    # 增强消息
    enhanced_history = middleware.enhance_messages(
        [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in conversation_history[-10:]  # 最近10条
        ],
        last_query=new_query
    )

    # 获取图谱上下文摘要
    kg_context = build_rag_context_for_chat(user_id, new_query)

    # 生成摘要
    summary = ""
    if kg_context["influence_summary"]:
        top_factors = sorted(kg_context["influence_summary"].items(), key=lambda x: x[1], reverse=True)
        if top_factors:
            summary = f"基于知识图谱分析，主要影响因素包括: {', '.join([f'{k}({v:.0%})' for k, v in top_factors[:3]])}"

    return {
        "enhanced_history": enhanced_history,
        "kg_context": kg_context,
        "summary": summary
    }


# ==================== API 模型 ====================

from pydantic import BaseModel
from typing import Optional


class KGRAGQueryRequest(BaseModel):
    """知识图谱RAG查询请求"""
    user_id: str
    query: str
    max_nodes: int = 10
    mode: str = "hybrid"  # vector_only, graph_only, hybrid, graph_first
    include_reasoning: bool = True


class KGRAGQueryResponse(BaseModel):
    """知识图谱RAG查询响应"""
    success: bool
    context_text: str
    nodes_count: int
    influence_summary: Dict[str, float]
    reasoning: str
    relationships_count: int
    error: Optional[str] = None


class KGEnhancedChatRequest(BaseModel):
    """知识图谱增强聊天请求"""
    user_id: str
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class KGEnhancedChatResponse(BaseModel):
    """知识图谱增强聊天响应"""
    success: bool
    prompt: str  # 增强后的prompt
    kg_context: Dict[str, Any]
    answer: Optional[str] = None
    error: Optional[str] = None
