"""
知识图谱感知RAG API路由
将知识图谱深度融入RAG检索和对话系统

API端点:
- POST /api/kg-rag/query - 查询知识图谱上下文
- POST /api/kg-rag/chat - 知识图谱增强对话
- POST /api/kg-rag/enhance - 增强现有对话
- GET /api/kg-rag/stats/{user_id} - 获取统计信息
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from backend.learning.kg_rag_integration import (
    build_rag_context_for_chat,
    build_prompt_with_kg_context,
    enhance_conversation_with_kg,
    KGRAGContextMiddleware,
    get_kg_rag_system
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kg-rag", tags=["kg-rag"])


# ==================== 请求/响应模型 ====================

class KGContextRequest(BaseModel):
    """知识图谱上下文查询请求"""
    user_id: str
    query: str
    max_nodes: int = 10
    mode: str = "hybrid"  # hybrid, graph_first, vector_only, graph_only


class KGContextResponse(BaseModel):
    """知识图谱上下文查询响应"""
    success: bool
    context_text: str
    nodes_count: int
    influence_summary: Dict[str, float]
    reasoning: str
    relationships_count: int
    nodes: Optional[List[Dict[str, Any]]] = None


class KGChatRequest(BaseModel):
    """知识图谱增强对话请求"""
    user_id: str
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    use_kg_context: bool = True


class KGChatResponse(BaseModel):
    """知识图谱增强对话响应"""
    success: bool
    kg_context: Dict[str, Any]
    answer: str
    enhanced_prompt: str


class KGEnhanceRequest(BaseModel):
    """对话增强请求"""
    user_id: str
    query: str
    conversation_history: List[Dict[str, str]]


class KGEnhanceResponse(BaseModel):
    """对话增强响应"""
    success: bool
    enhanced_prompt: str
    kg_context: Dict[str, Any]
    summary: str


# ==================== API 端点 ====================

@router.post("/query", response_model=KGContextResponse)
async def query_kg_context(request: KGContextRequest):
    """
    查询知识图谱上下文

    使用知识图谱感知的RAG检索，返回结构化的图谱上下文
    """
    try:
        logger.info(f"查询知识图谱上下文: user={request.user_id}, query={request.query[:50]}...")

        # 获取上下文
        context_info = build_rag_context_for_chat(
            user_id=request.user_id,
            query=request.query,
            max_nodes=request.max_nodes,
            include_reasoning=True
        )

        # 获取节点详情
        nodes_detail = []
        try:
            retriever = get_kg_rag_system(request.user_id)
            context = retriever.retrieve_adaptive(
                query=request.query,
                max_results=request.max_nodes
            )
            nodes_detail = [
                {
                    "id": result.id,
                    "name": result.content[:50],
                    "type": result.node_type,
                    "category": result.category,
                    "confidence": result.confidence,
                    "influence_score": result.score,
                    "metadata": result.metadata
                }
                for result in context.results
            ]
        except Exception as e:
            logger.warning(f"获取节点详情失败: {e}")

        return KGContextResponse(
            success=True,
            context_text=context_info["context_text"],
            nodes_count=context_info["nodes_count"],
            influence_summary=context_info["influence_summary"],
            reasoning=context_info["reasoning"],
            relationships_count=context_info["relationships_count"],
            nodes=nodes_detail
        )

    except Exception as e:
        logger.error(f"查询知识图谱上下文失败: {e}")
        import traceback
        traceback.print_exc()
        return KGContextResponse(
            success=False,
            context_text="",
            nodes_count=0,
            influence_summary={},
            reasoning=f"查询失败: {str(e)}",
            relationships_count=0
        )


@router.post("/chat", response_model=KGChatResponse)
async def kg_enhanced_chat(request: KGChatRequest):
    """
    知识图谱增强对话

    结合知识图谱上下文进行对话，生成更贴合用户个人情况的回答
    """
    try:
        logger.info(f"知识图谱增强对话: user={request.user_id}, query={request.query[:50]}...")

        # 构建增强的prompt
        enhanced_prompt = build_prompt_with_kg_context(
            user_id=request.user_id,
            query=request.query
        )

        # 获取图谱上下文
        kg_context = build_rag_context_for_chat(
            user_id=request.user_id,
            query=request.query,
            max_nodes=10
        )

        # 如果提供了历史记录，增强对话
        if request.conversation_history:
            enhanced = enhance_conversation_with_kg(
                user_id=request.user_id,
                conversation_history=request.conversation_history,
                new_query=request.query
            )
            kg_context = enhanced["kg_context"]

        # 调用LLM生成回答
        answer = ""
        try:
            from backend.llm.llm_service import get_llm_service
            llm = get_llm_service()
            if llm:
                messages = [
                    {"role": "system", "content": """你是一个基于用户个人知识图谱的AI助手。
请结合用户的知识图谱上下文，回答用户的问题。
你的回答应该：
1. 引用图谱中的具体节点和数据
2. 分析各因素对用户的影响
3. 给出有依据的建议
4. 如果信息不足，明确指出"""},
                    {"role": "user", "content": enhanced_prompt}
                ]
                answer = llm.chat(messages, temperature=0.3)
        except Exception as e:
            logger.warning(f"LLM生成失败: {e}")
            answer = "（知识图谱上下文已准备，但LLM生成失败）"

        return KGChatResponse(
            success=True,
            kg_context=kg_context,
            answer=answer,
            enhanced_prompt=enhanced_prompt
        )

    except Exception as e:
        logger.error(f"知识图谱增强对话失败: {e}")
        import traceback
        traceback.print_exc()
        return KGChatResponse(
            success=False,
            kg_context={},
            answer="",
            enhanced_prompt=f"请求失败: {str(e)}"
        )


@router.post("/enhance", response_model=KGEnhanceResponse)
async def enhance_existing_chat(request: KGEnhanceRequest):
    """
    增强现有对话

    将知识图谱上下文注入到对话历史中，用于后续的对话处理
    """
    try:
        logger.info(f"增强对话: user={request.user_id}, query={request.query[:50]}...")

        # 增强对话
        result = enhance_conversation_with_kg(
            user_id=request.user_id,
            conversation_history=request.conversation_history,
            new_query=request.query
        )

        return KGEnhanceResponse(
            success=True,
            enhanced_prompt=result["enhanced_history"][-1]["content"] if result["enhanced_history"] else "",
            kg_context=result["kg_context"],
            summary=result["summary"]
        )

    except Exception as e:
        logger.error(f"增强对话失败: {e}")
        return KGEnhanceResponse(
            success=False,
            enhanced_prompt="",
            kg_context={},
            summary=f"增强失败: {str(e)}"
        )


@router.get("/stats/{user_id}")
async def get_kg_rag_stats(user_id: str):
    """
    获取知识图谱RAG统计信息
    """
    try:
        kg_rag = get_kg_rag_system(user_id)
        stats = kg_rag.get_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {
            "success": False,
            "message": str(e)
        }


@router.get("/health")
async def kg_rag_health():
    """
    健康检查
    """
    return {"status": "ok", "service": "kg-rag"}


# ==================== 流式对话支持 ====================

@router.post("/stream")
async def kg_rag_stream(request: KGChatRequest):
    """
    知识图谱增强流式对话

    返回包含知识图谱上下文的流式响应
    """
    from fastapi.responses import StreamingResponse
    import json

    async def generate():
        try:
            # 1. 先发送上下文
            kg_context = build_rag_context_for_chat(
                user_id=request.user_id,
                query=request.query,
                max_nodes=10
            )
            yield f"event: context\ndata: {json.dumps(kg_context, ensure_ascii=False)}\n\n"

            # 2. 构建prompt
            enhanced_prompt = build_prompt_with_kg_context(
                user_id=request.user_id,
                query=request.query
            )

            # 3. 流式调用LLM
            try:
                from backend.llm.llm_service import get_llm_service
                llm = get_llm_service()
                if llm:
                    messages = [
                        {"role": "system", "content": """你是一个基于用户个人知识图谱的AI助手。
请结合用户的知识图谱上下文，回答用户的问题。
你的回答应该：
1. 引用图谱中的具体节点和数据
2. 分析各因素对用户的影响
3. 给出有依据的建议"""},
                        {"role": "user", "content": enhanced_prompt}
                    ]
                    # 这里需要LLM支持流式输出
                    # 简化版本：一次性返回
                    answer = llm.chat(messages, temperature=0.3)
                    yield f"event: answer\ndata: {json.dumps({'answer': answer}, ensure_ascii=False)}\n\n"
                else:
                    yield f"event: error\ndata: {json.dumps({'error': 'LLM服务不可用'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

            yield f"event: done\ndata: {json.dumps({}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
