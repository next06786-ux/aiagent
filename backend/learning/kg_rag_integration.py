"""
知识图谱感知RAG集成模块
将 UnifiedHybridRetrieval 融入现有的 RAG 架构

使用方式:
1. 聊天时使用知识图谱上下文:
   retriever = get_kg_rag_system(user_id)
   context = retriever.retrieve_adaptive(query)

2. 检索时使用混合检索:
   context = retriever.retrieve(query, config)
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 延迟导入，避免循环依赖
_retriever_instances: Dict[str, 'UnifiedHybridRetrieval'] = {}


def get_kg_rag_system(user_id: str) -> 'UnifiedHybridRetrieval':
    """获取用户的统一混合检索系统实例"""
    if user_id not in _retriever_instances:
        from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
        _retriever_instances[user_id] = UnifiedHybridRetrieval(user_id)
    return _retriever_instances[user_id]


def clear_kg_rag_instances():
    """清除所有实例（用于测试或重置）"""
    global _retriever_instances
    _retriever_instances.clear()


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
        retriever = get_kg_rag_system(user_id)
        from backend.learning.unified_hybrid_retrieval import QueryType
        
        # 使用自适应检索
        context = retriever.retrieve_adaptive(
            query=query,
            max_results=max_nodes
        )
        
        # 构建可读文本
        context_text = _format_context_text(context)
        
        return {
            "context_text": context_text,
            "nodes_count": context.total_results,
            "influence_summary": _calculate_influence_summary(context.results),
            "reasoning": f"使用{context.strategy_used.value}策略检索",
            "relationships_count": sum(len(r.relations) for r in context.results)
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


def _format_context_text(context) -> str:
    """格式化上下文为可读文本"""
    lines = []
    
    if context.results:
        lines.append(f"## 检索结果 ({context.total_results} 个)")
        lines.append("")
        
        for i, result in enumerate(context.results[:10], 1):
            lines.append(f"{i}. [{result.node_type}] {result.content}")
            lines.append(f"   分数: {result.score:.3f}, 来源: {result.source}")
            if result.relations:
                lines.append(f"   关系: {len(result.relations)} 条")
            lines.append("")
    
    return "\n".join(lines)


def _calculate_influence_summary(results: List) -> Dict[str, float]:
    """计算影响力汇总"""
    summary = {}
    
    for result in results:
        category = result.category or 'unknown'
        if category not in summary:
            summary[category] = 0
        summary[category] += result.score
    
    # 归一化
    total = sum(summary.values())
    if total > 0:
        summary = {k: v / total for k, v in summary.items()}
    
    return summary


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
        self._retriever = None

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = get_kg_rag_system(self.user_id)
        return self._retriever

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
            context = self.retriever.retrieve_adaptive(
                query=query,
                max_results=self.max_context_nodes
            )

            if not context.results:
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

        # 影响力分析
        influence = _calculate_influence_summary(context.results)
        if influence:
            lines.append("## 因素影响力分析")
            sorted_inf = sorted(influence.items(), key=lambda x: x[1], reverse=True)
            for cat, score in sorted_inf[:5]:
                lines.append(f"- {cat}: {score:.1%}")
            lines.append("")

        # 相关节点
        if context.results:
            lines.append(f"## 相关节点 ({context.total_results} 个)")
            for result in context.results[:8]:
                lines.append(f"- [{result.node_type}] {result.content[:50]}... (分数:{result.score:.2f})")

        # 关系
        all_relations = []
        for result in context.results:
            all_relations.extend(result.relations)
        
        if all_relations:
            lines.append("")
            lines.append(f"## 关键关系 ({len(all_relations)} 条)")
            for rel in all_relations[:5]:
                target = rel.get('target', '')
                rel_type = rel.get('type', 'RELATED_TO')
                if target:
                    lines.append(f"- {rel_type} → {target}")

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
    mode: str = "adaptive"  # adaptive, graph_only, vector_only, hybrid_parallel
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
