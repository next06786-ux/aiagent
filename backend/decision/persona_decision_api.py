"""
决策人格API - 使用7个决策人格进行实时决策推演

替代原有的教育升学决策系统，使用更强大的人格化决策副本

核心特性：
1. 7个独立的决策人格（理性分析师、冒险家、实用主义者等）
2. 分层记忆系统（共享事实 + 私有解读）
3. 实时WebSocket推演
4. 人格间自由交互和辩论
5. 涌现演化能力

作者: AI System
版本: 1.0
日期: 2026-04-18
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
from datetime import datetime
from starlette.websockets import WebSocketDisconnect as StarletteWebSocketDisconnect

from backend.decision.decision_info_collector import DecisionInfoCollector
from backend.decision.decision_personas import PersonaCouncil

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision/persona", tags=["persona-decision"])

# 全局实例
info_collector = DecisionInfoCollector()

# ==================== 配置常量 ====================

# 推演轮数配置
ROUNDS_CONFIG = {
    "quick": 1,      # 快速决策: 1轮,适合简单日常选择
    "standard": 2,   # 标准决策: 2轮,平衡速度和深度
    "deep": 3        # 深度决策: 3轮,充分辩论重大决策
}

# 默认轮数(可通过环境变量覆盖)
DEFAULT_ROUNDS = ROUNDS_CONFIG["quick"]  # 默认快速模式

# 重大决策类型自动升级到标准模式
MAJOR_DECISION_TYPES = ["career", "education", "relationship", "investment", "health"]


# ==================== 请求模型 ====================

class StartCollectionRequest(BaseModel):
    """开始信息收集请求"""
    user_id: str
    initial_question: str
    decision_type: Optional[str] = "general"


class ContinueCollectionRequest(BaseModel):
    """继续信息收集请求"""
    session_id: str
    user_response: str


class GenerateOptionsRequest(BaseModel):
    """生成选项请求"""
    session_id: str
    user_options: List[str] = []


# ==================== API路由端点 ====================

@router.post("/collect/start")
async def start_info_collection(request: StartCollectionRequest) -> Dict[str, Any]:
    """
    开始决策信息收集
    
    使用LLM进行多轮对话，收集决策所需信息
    """
    try:
        result = info_collector.start_collection(
            user_id=request.user_id,
            initial_question=request.initial_question
        )
        
        return {
            "success": True,
            "data": {
                "session_id": result["session_id"],
                "message": result["message"],
                "phase": result.get("phase", "user_free_talk"),
                "round": result.get("round", 0)
            }
        }
    except Exception as e:
        logger.error(f"开始信息收集失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/collect/start-stream")
async def start_info_collection_stream(request: StartCollectionRequest):
    """
    开始决策信息收集（流式版本）
    
    实时推送状态：
    1. 连接知识图谱
    2. 检索用户历史
    3. 加载RAG记忆
    4. 生成初始问题
    """
    from fastapi.responses import StreamingResponse
    
    async def generate_stream():
        try:
            # 发送开始状态
            yield f"data: {json.dumps({'type': 'status', 'content': '正在连接决策引擎...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            
            # 发送知识图谱检索状态
            yield f"data: {json.dumps({'type': 'status', 'content': '正在从知识图谱检索背景信息...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.2)
            
            # 发送RAG检索状态
            yield f"data: {json.dumps({'type': 'status', 'content': '正在加载相关历史记忆...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.2)
            
            # 执行实际的信息收集
            result = await asyncio.to_thread(
                info_collector.start_collection,
                user_id=request.user_id,
                initial_question=request.initial_question
            )
            
            # 发送完成状态
            yield f"data: {json.dumps({'type': 'status', 'content': '初始化完成'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            
            # 发送结果
            yield f"data: {json.dumps({'type': 'complete', 'data': result}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式信息收集失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/collect/continue")
async def continue_info_collection(request: ContinueCollectionRequest) -> Dict[str, Any]:
    """
    继续信息收集
    
    根据用户回答继续收集信息，直到收集完成
    """
    try:
        result = info_collector.continue_collection(
            session_id=request.session_id,
            user_response=request.user_response
        )
        
        return {
            "success": True,
            "data": {
                "session_id": request.session_id,
                "ai_question": result.get("ai_question"),
                "phase": result.get("phase"),
                "round": result.get("round"),
                "is_complete": result.get("is_complete", False),
                "collected_info": result.get("collected_info") if result.get("is_complete") else None,
                "summary": result.get("summary")
            }
        }
    except Exception as e:
        logger.error(f"继续信息收集失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.get("/collect/session/{session_id}")
async def get_collection_session(session_id: str) -> Dict[str, Any]:
    """获取信息收集会话"""
    try:
        session = info_collector.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "message": "会话不存在",
                "data": None
            }
        
        return {
            "success": True,
            "data": session
        }
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.post("/generate-options")
async def generate_ai_options(request: GenerateOptionsRequest) -> Dict[str, Any]:
    """
    生成决策选项
    
    基于收集的信息，使用AI生成或优化决策选项
    """
    import asyncio
    
    try:
        session = info_collector.get_session(request.session_id)
        
        if not session:
            return {
                "success": False,
                "message": "会话不存在",
                "data": None
            }
        
        # 如果用户提供了选项，直接使用（快速路径）
        if request.user_options:
            options = [
                {"title": opt, "description": ""} 
                for opt in request.user_options
            ]
            
            return {
                "success": True,
                "data": {
                    "ai_options": options,
                    "session_id": request.session_id
                }
            }
        
        collected_info = session.get("collected_info", {})
        
        # 从collected_info中提取结构化信息
        user_background = collected_info.get("user_background", {})
        decision_scenario = collected_info.get("decision_scenario", {})
        constraints = collected_info.get("constraints", {})
        priorities = collected_info.get("priorities", {})
        concerns = collected_info.get("concerns", [])
        mentioned_options = collected_info.get("mentioned_options", [])
        
        # 构建详细的上下文描述（简化版，减少token消耗）
        context_parts = []
        
        if user_background:
            bg_items = []
            for key in ["school", "major", "grade", "gpa", "experience"]:
                if user_background.get(key):
                    bg_items.append(f"{key}: {user_background[key]}")
            if user_background.get("skills"):
                bg_items.append(f"skills: {', '.join(user_background['skills'][:3])}")  # 只取前3个技能
            if bg_items:
                context_parts.append("背景: " + "; ".join(bg_items))
        
        if decision_scenario:
            scenario_items = []
            for key in ["situation", "deadline", "external_factors"]:
                if decision_scenario.get(key):
                    scenario_items.append(str(decision_scenario[key]))
            if scenario_items:
                context_parts.append("场景: " + "; ".join(scenario_items))
        
        if concerns:
            context_parts.append(f"顾虑: {', '.join(concerns[:3])}")  # 只取前3个顾虑
        
        if mentioned_options:
            context_parts.append(f"提及选项: {', '.join(mentioned_options)}")
        
        # 组合所有上下文（限制长度）
        full_context = " | ".join(context_parts) if context_parts else "基于初始问题生成选项"
        if len(full_context) > 500:
            full_context = full_context[:500] + "..."
        
        logger.info(f"[选项生成] 上下文: {full_context}")
        
        # 格式化约束条件（简化）
        constraints_text = "; ".join([f"{k}: {v}" for k, v in list(constraints.items())[:3]]) if constraints else "无"
        
        # 格式化优先级（简化）
        priorities_text = priorities.get("most_important", "未明确") if priorities else "未明确"
        
        # 使用AI生成选项（带超时）
        from backend.llm.llm_service import get_llm_service
        llm = get_llm_service()
        
        if not llm or not llm.enabled:
            # LLM不可用，返回默认选项
            logger.warning("[选项生成] LLM不可用，返回默认选项")
            return {
                "success": True,
                "data": {
                    "ai_options": [
                        {"title": "选项1", "description": "第一个选择"},
                        {"title": "选项2", "description": "第二个选择"},
                        {"title": "选项3", "description": "第三个选择"}
                    ],
                    "session_id": request.session_id
                }
            }
        
        # 使用提示词管理器
        from backend.decision.prompts.prompt_manager import get_prompt
        
        # 从配置文件获取提示词
        prompt_data = get_prompt(
            "option_generation",
            "generate_options",
            variables={
                "initial_question": session['initial_question'],
                "decision_scenario": full_context,
                "constraints": constraints_text,
                "priorities": priorities_text
            }
        )
        
        messages = [
            {"role": "system", "content": prompt_data["system"]},
            {"role": "user", "content": prompt_data["user"]}
        ]
        
        # 设置90秒超时（LLM响应较慢）
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm.chat,
                    messages,
                    temperature=prompt_data["temperature"],
                    response_format=prompt_data["return_format"]
                ),
                timeout=90.0  # 90秒超时
            )
        except asyncio.TimeoutError:
            logger.error("[选项生成] LLM调用超时(90秒)")
            return {
                "success": False,
                "message": "AI生成选项超时，请稍后重试",
                "data": {
                    "ai_options": [
                        {"title": "选项1", "description": "第一个选择"},
                        {"title": "选项2", "description": "第二个选择"},
                        {"title": "选项3", "description": "第三个选择"}
                    ],
                    "session_id": request.session_id
                }
            }
        
        logger.info(f"[选项生成] LLM返回: {response[:200]}...")
        
        try:
            result = json.loads(response)
            options = result.get("options", [])
            
            # 验证选项数量
            if len(options) < 2:
                logger.warning(f"[选项生成] 生成的选项数量不足: {len(options)}")
                # 补充默认选项
                while len(options) < 3:
                    options.append({"title": f"选项{len(options) + 1}", "description": "待补充"})
            
            logger.info(f"[选项生成] ✅ 成功生成 {len(options)} 个选项")
            
        except Exception as e:
            logger.error(f"[选项生成] JSON解析失败: {e}, 原始响应: {response[:500]}")
            options = [
                {"title": "选项1", "description": "第一个选择"},
                {"title": "选项2", "description": "第二个选择"},
                {"title": "选项3", "description": "第三个选择"}
            ]
        
        return {
            "success": True,
            "data": {
                "ai_options": options,
                "session_id": request.session_id
            }
        }
    except Exception as e:
        logger.error(f"生成选项失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }



@router.websocket("/ws/simulate-option")
async def simulate_single_option(websocket: WebSocket):
    """
    WebSocket实时推演 - 单个选项的7人格分析
    
    用于：每个选项在独立界面中展示7个决策人格的推演过程
    
    适用场景：
    - 人际关系决策
    - 教育升学决策
    - 职业规划决策
    
    流程：
    1. 初始化7个决策人格和分层记忆系统
    2. 加载共享事实（RAG + Neo4j）
    3. 7个人格独立分析该选项
    4. 人格间交互和辩论
    5. 生成该选项的综合评估
    """
    await websocket.accept()
    print(f"[WS] WebSocket连接已接受，准备进入消息循环")
    logger.info(f"[WS] WebSocket连接已接受，准备进入消息循环")
    ws_connected = True
    
    async def safe_send(data: dict) -> bool:
        """安全发送WebSocket消息"""
        nonlocal ws_connected
        if not ws_connected:
            return False
        try:
            await websocket.send_json(data)
            return True
        except (WebSocketDisconnect, StarletteWebSocketDisconnect, RuntimeError) as e:
            logger.warning(f"WebSocket连接已断开: {e}")
            ws_connected = False
            return False
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            ws_connected = False
            return False
    
    try:
        while ws_connected:
            try:
                # 接收客户端消息
                print(f"[WS] 等待接收消息...")
                logger.info(f"[WS] 等待接收消息...")
                message = await websocket.receive_json()
                print(f"[WS] 收到消息: {message.get('type', 'unknown')}, 完整消息: {message}")
                logger.info(f"[WS] 收到消息: {message.get('type', 'unknown')}, 完整消息: {message}")
                
                msg_type = message.get("type")
                
                if msg_type == "start_simulation":
                    # 开始推演单个选项
                    session_id = message.get("session_id")
                    user_id = message.get("user_id")
                    question = message.get("question", "")
                    option = message.get("option", {})  # 单个选项
                    option_index = message.get("option_index", 0)
                    collected_info = message.get("collected_info", {})
                    decision_type = message.get("decision_type", "general")  # relationship/education/career
                    
                    # 🆕 获取轮数配置
                    persona_rounds = message.get("persona_rounds", None)
                    if persona_rounds is None:
                        # 智能轮数配置：根据决策复杂度动态调整
                        default_rounds = DEFAULT_ROUNDS
                        
                        # 重大决策类型自动升级到标准模式
                        if decision_type in MAJOR_DECISION_TYPES:
                            default_rounds = ROUNDS_CONFIG["standard"]
                            logger.info(f"[轮数配置] 检测到重大决策类型 '{decision_type}'，升级到标准模式({default_rounds}轮)")
                        
                        # 如果收集的信息很丰富,升级到标准模式
                        if collected_info:
                            concerns_count = len(collected_info.get("concerns", []))
                            constraints_count = len(collected_info.get("constraints", {}))
                            if concerns_count > 3 or constraints_count > 3:
                                default_rounds = max(default_rounds, ROUNDS_CONFIG["standard"])
                                logger.info(f"[轮数配置] 检测到复杂信息(担忧:{concerns_count}, 约束:{constraints_count})，升级到标准模式({default_rounds}轮)")
                        
                        persona_rounds = {
                            "rational_analyst": default_rounds,
                            "adventurer": default_rounds,
                            "pragmatist": default_rounds,
                            "idealist": default_rounds,
                            "conservative": default_rounds,
                            "social_navigator": default_rounds,
                            "innovator": default_rounds
                        }
                    else:
                        logger.info(f"[轮数配置] 使用客户端指定的轮数配置")
                    
                    logger.info(f"[决策人格推演] 开始 - 选项: {option.get('title')}, 类型: {decision_type}")
                    logger.info(f"[决策人格推演] 轮数配置: {persona_rounds}")
                    
                    # 发送开始消息
                    if not await safe_send({
                        "type": "start",
                        "session_id": session_id,
                        "user_id": user_id,
                        "question": question,
                        "decision_type": decision_type,
                        "option": option,
                        "persona_rounds": persona_rounds
                    }):
                        return
                    
                    # 生成决策ID
                    decision_id = f"decision_{decision_type}_{user_id}_{int(datetime.now().timestamp())}"
                    option_id = f"option_{option_index + 1}"
                    option_title = option.get("title", f"选项{option_index + 1}")
                    
                    # 发送初始化状态
                    if not await safe_send({
                        "type": "status",
                        "stage": "init",
                        "content": f"正在初始化7个决策人格分析【{option_title}】..."
                    }):
                        return
                    
                    # 创建决策人格委员会
                    council = PersonaCouncil(user_id)
                    
                    # 立即发送智能体列表（用于前端初始化显示）
                    if not await safe_send({
                        "type": "personas_init",
                        "option_id": option_id,
                        "personas": [
                            {
                                "id": pid,
                                "name": p.name,
                                "description": p.description,
                                "risk_tolerance": p.value_system.risk_tolerance
                            }
                            for pid, p in council.personas.items()
                        ]
                    }):
                        return
                    
                    if not await safe_send({
                        "type": "status",
                        "stage": "personas_created",
                        "content": f"✅ 已创建{len(council.personas)}个决策人格",
                        "personas": [
                            {
                                "id": pid,
                                "name": p.name,
                                "description": p.description,
                                "risk_tolerance": p.value_system.risk_tolerance
                            }
                            for pid, p in council.personas.items()
                        ]
                    }):
                        return
                    
                    # 初始化记忆系统
                    if not await safe_send({
                        "type": "status",
                        "stage": "memory_init",
                        "content": "正在加载分层记忆系统（RAG + Neo4j）..."
                    }):
                        return
                    
                    try:
                        await council.initialize_for_decision(
                            decision_id=decision_id,
                            question=question,
                            options=[option],  # 只传入当前选项
                            collected_info=collected_info
                        )
                        
                        if not await safe_send({
                            "type": "status",
                            "stage": "memory_loaded",
                            "content": "✅ 记忆系统加载完成"
                        }):
                            return
                        
                        # 发送共享事实摘要
                        if council.memory_system and council.memory_system.shared_facts:
                            facts_summary = council.memory_system.shared_facts.get_summary()
                            if not await safe_send({
                                "type": "shared_facts",
                                "content": facts_summary,
                                "facts_data": {
                                    "relationships_count": len(council.memory_system.shared_facts.relationships),
                                    "education_count": len(council.memory_system.shared_facts.education_history),
                                    "career_count": len(council.memory_system.shared_facts.career_history),
                                    "skills_count": len(council.memory_system.shared_facts.skills)
                                }
                            }):
                                return
                    
                    except Exception as e:
                        logger.error(f"记忆系统初始化失败: {e}")
                        if not await safe_send({
                            "type": "status",
                            "stage": "memory_error",
                            "content": f"⚠️ 记忆系统初始化失败，使用降级模式"
                        }):
                            return
                    
                    # 开始分析该选项
                    if not await safe_send({
                        "type": "status",
                        "stage": "analysis_start",
                        "content": f"开始7个人格分析【{option_title}】..."
                    }):
                        return
                    
                    # ============================================================
                    # 使用新的生命周期系统进行推演
                    # ============================================================
                    
                    try:
                        # 创建WebSocket状态回调函数
                        async def ws_status_callback(event_type: str, data: Dict[str, Any]):
                            """实时推送Agent状态到前端"""
                            try:
                                # 直接发送，不嵌套在agent_event中
                                await safe_send({
                                    "type": event_type,
                                    "option_id": option_id,
                                    **data
                                })
                            except Exception as e:
                                logger.error(f"WebSocket推送失败: {e}")
                        
                        # 准备决策上下文
                        decision_context = {
                            "question": question,
                            "collected_info": collected_info,
                            "option_title": option_title,
                            "decision_type": decision_type,
                            "user_decision_style": council.memory_system.current_decision.user_decision_style if council.memory_system else {},
                            "status_callback": ws_status_callback  # 传递WebSocket回调
                        }
                        
                        # 调用新的analyze_decision方法
                        logger.info(f"[决策推演] 使用生命周期系统，轮数配置: {persona_rounds}")
                        
                        result = await council.analyze_decision(
                            decision_context=decision_context,
                            options=[option],
                            persona_rounds=persona_rounds
                        )
                        
                        # 提取分析结果
                        option_analyses = result['all_analyses'].get('option_1', {}).get('final_analyses', {})
                        
                        # 发送所有Agent的最终结果
                        for persona_id, analysis in option_analyses.items():
                            persona = council.personas[persona_id]
                            
                            await safe_send({
                                "type": "persona_analysis",
                                "stage": "final",
                                "option_id": option_id,
                                "persona_id": persona_id,
                                "persona_name": persona.name,
                                "persona_data": {
                                    "id": persona_id,
                                    "name": persona.name,
                                    "stance": analysis.get('stance', '未知'),
                                    "score": analysis.get('score', 0),
                                    "confidence": analysis.get('confidence', 0.5),
                                    "emotion": persona.emotional_state.primary_emotion.value,
                                    "key_points": analysis.get('key_points', []),
                                    "reasoning": analysis.get('reasoning', '')
                                },
                                "content": f"推演完成"
                            })
                        
                        # 发送完成消息
                        if not await safe_send({
                            "type": "complete",
                            "option_id": option_id,
                            "session_id": session_id,
                            "analyses": option_analyses,
                            "recommendation": result.get('recommendation', {}),
                            "content": f"【{option_title}】分析完成"
                        }):
                            return
                        
                        logger.info(f"[决策推演] 完成 - 选项: {option_title}")
                        
                    except Exception as e:
                        logger.error(f"[决策推演] 失败: {e}")
                        import traceback
                        traceback.print_exc()
                        
                        await safe_send({
                            "type": "error",
                            "content": f"推演失败: {str(e)}"
                        })
                        return
                    
                    # ============================================================
                    # 记录到决策上下文层（第2层）
                    # ============================================================
                    if council.memory_system and council.memory_system.current_decision and option_analyses:
                        # 记录所有persona的初始观点
                        for persona_id, persona in council.personas.items():
                            if persona.current_interpretation:
                                # 记录其他persona的观点（用于后续参考）
                                for other_id, other_analysis in option_analyses.items():
                                    if other_id != persona_id:
                                        persona.current_interpretation.interactions.append({
                                            "with_persona": other_id,
                                            "their_stance": other_analysis.get('stance', '未知'),
                                            "their_score": other_analysis.get('score', 0),
                                            "timestamp": datetime.now().isoformat()
                                        })
                        
                        logger.info(f"✅ 已记录{len(council.personas)}个persona的交互历史到私有解读层")
                    
                    # ============================================================
                    # 生成综合评估
                    # ============================================================
                    if not await safe_send({
                        "type": "status",
                        "stage": "final_evaluation",
                        "content": f"正在生成【{option_title}】的综合评估..."
                    }):
                        return
                    
                    # 计算综合评分
                    persona_scores = {
                        pid: analysis.get('score', 50)
                        for pid, analysis in option_analyses.items()
                    }
                    
                    avg_score = sum(persona_scores.values()) / len(persona_scores) if persona_scores else 0
                    
                    # 统计立场分布
                    support_count = sum(1 for a in option_analyses.values() if '支持' in a.get('stance', ''))
                    oppose_count = sum(1 for a in option_analyses.values() if '反对' in a.get('stance', ''))
                    neutral_count = len(option_analyses) - support_count - oppose_count
                    
                    # 判断共识程度
                    if support_count >= len(option_analyses) * 0.7:
                        consensus = "强烈支持"
                    elif oppose_count >= len(option_analyses) * 0.7:
                        consensus = "强烈反对"
                    elif support_count > oppose_count:
                        consensus = "倾向支持"
                    elif oppose_count > support_count:
                        consensus = "倾向反对"
                    else:
                        consensus = "意见分歧"
                    
                    # 生成评估内容
                    evaluation_content = f"""
=================================================
【{option_title}】综合评估
=================================================

平均评分: {avg_score:.1f}/100
共识程度: {consensus}
立场分布: 支持{support_count}人 | 中立{neutral_count}人 | 反对{oppose_count}人

各人格最终立场：
"""
                    
                    for pid, analysis in option_analyses.items():
                        persona = council.personas[pid]
                        evaluation_content += f"\n【{persona.name}】{analysis.get('stance', '未知')} ({analysis.get('score', 0)}分)"
                        if analysis.get('recommendation'):
                            evaluation_content += f"\n  建议: {analysis.get('recommendation')}"
                    
                    evaluation_content += f"\n\n{'='*60}"
                    
                    if not await safe_send({
                        "type": "final_evaluation",
                        "option_id": option_id,
                        "option_title": option_title,
                        "evaluation_data": {
                            "avg_score": avg_score,
                            "consensus": consensus,
                            "support_count": support_count,
                            "oppose_count": oppose_count,
                            "neutral_count": neutral_count,
                            "persona_analyses": {
                                pid: {
                                    "name": council.personas[pid].name,
                                    "stance": analysis.get('stance'),
                                    "score": analysis.get('score'),
                                    "confidence": analysis.get('confidence')
                                }
                                for pid, analysis in option_analyses.items()
                            }
                        },
                        "content": evaluation_content
                    }):
                        return
                    
                    # 发送完成消息
                    if not await safe_send({
                        "type": "complete",
                        "decision_id": decision_id,
                        "session_id": session_id,
                        "option_id": option_id
                    }):
                        return
                    
                    # ============================================================
                    # 持久化记忆系统（第2层和第3层）
                    # ============================================================
                    if council.memory_system:
                        try:
                            # 更新决策结果到决策上下文层
                            council.memory_system.update_decision_outcome(
                                decision_id=decision_id,
                                chosen_option=option_title,
                                rationale=f"综合评分{avg_score:.1f}分，{consensus}",
                                outcome=None,  # 实际结果需要用户后续反馈
                                success=None
                            )
                            
                            # 持久化到存储
                            council.memory_system.persist_to_storage(decision_id)
                            
                            logger.info(f"✅ 记忆系统已持久化: {decision_id}")
                            logger.info(f"   - 决策上下文层: 已保存")
                            logger.info(f"   - 私有解读层: 已保存{len(council.personas)}个persona的解读")
                            
                        except Exception as e:
                            logger.error(f"持久化记忆系统失败: {e}")
                    
                    logger.info(f"[决策人格推演] 完成 - option: {option_title}")
                
                elif msg_type == "stop_simulation":
                    # 停止推演
                    option_id = message.get("option_id", "")
                    session_id = message.get("session_id", "")
                    logger.info(f"[决策人格推演] 收到停止信号 - option_id: {option_id}, session_id: {session_id}")
                    
                    # 发送停止确认
                    await safe_send({
                        "type": "stopped",
                        "option_id": option_id,
                        "session_id": session_id,
                        "content": "推演已停止"
                    })
                    
                    # 设置标志位停止推演（如果正在进行中）
                    ws_connected = False
                    logger.info(f"[决策人格推演] 已设置停止标志，关闭WebSocket")
                    break
                
                elif msg_type == "ping":
                    await safe_send({"type": "pong"})
                
            except WebSocketDisconnect:
                logger.info("[WS] 客户端主动断开连接")
                ws_connected = False
                break
            except Exception as e:
                logger.error(f"[WS] 处理消息时出错: {e}")
                import traceback
                traceback.print_exc()
                await safe_send({
                    "type": "error",
                    "message": str(e)
                })
                break
    
    except Exception as e:
        logger.error(f"[WS] WebSocket错误: {e}")
        import traceback
        logger.error(f"[WS] 错误堆栈: {traceback.format_exc()}")
        traceback.print_exc()
    finally:
        if ws_connected:
            try:
                await websocket.close()
            except:
                pass
        logger.info("[WS] WebSocket连接已关闭")


print("决策人格API已加载")
print("   - POST /api/decision/persona/collect/start - 开始信息收集")
print("   - POST /api/decision/persona/collect/continue - 继续信息收集")
print("   - POST /api/decision/persona/generate-options - 生成决策选项")
print("   - WS   /api/decision/persona/ws/simulate-option - 单个选项的7人格推演（用于独立界面）")
print("   - POST /api/decision/persona/update-outcome - 更新决策结果（用于学习）")


# ==================== 决策结果反馈和学习 ====================

class UpdateOutcomeRequest(BaseModel):
    """更新决策结果请求"""
    decision_id: str
    user_id: str
    chosen_option: str
    outcome: str  # 实际发生的结果
    success: bool  # 是否成功
    lessons_learned: Optional[str] = None  # 用户的反思


@router.post("/update-outcome")
async def update_decision_outcome(request: UpdateOutcomeRequest) -> Dict[str, Any]:
    """
    更新决策结果并让persona学习
    
    这是三层记忆系统的关键环节：
    1. 更新决策上下文层的结果
    2. 让每个persona从结果中学习（更新私有解读层）
    3. 持久化学习成果
    """
    try:
        from backend.decision.persona_memory_system import LayeredMemorySystem
        from backend.decision.decision_personas import create_persona_council
        
        # 重新加载记忆系统
        memory_system = LayeredMemorySystem(user_id=request.user_id)
        
        # 尝试从存储加载决策上下文
        import os
        import json
        
        storage_dir = "./backend/data/persona_memories"
        decision_file = os.path.join(storage_dir, f"decision_{request.decision_id}.json")
        
        if not os.path.exists(decision_file):
            return {
                "success": False,
                "message": f"决策记录不存在: {request.decision_id}"
            }
        
        # 更新决策结果
        memory_system.update_decision_outcome(
            decision_id=request.decision_id,
            chosen_option=request.chosen_option,
            rationale=f"用户选择了: {request.chosen_option}",
            outcome=request.outcome,
            success=request.success
        )
        
        # 让每个persona学习
        council = create_persona_council(request.user_id)
        
        for persona_id, persona in council.personas.items():
            # 加载该persona的解读
            persona_file = os.path.join(storage_dir, f"persona_{persona_id}_{request.decision_id}.json")
            
            if os.path.exists(persona_file):
                with open(persona_file, 'r', encoding='utf-8') as f:
                    interpretation_data = json.load(f)
                
                # 根据结果生成学习内容
                my_stance = interpretation_data.get('option_stances', {}).get(request.chosen_option, {}).get('stance', '未知')
                my_score = interpretation_data.get('option_stances', {}).get(request.chosen_option, {}).get('score', 0)
                
                # 判断预测是否准确
                if request.success:
                    if '支持' in my_stance and my_score >= 60:
                        lesson = f"✅ 我支持这个选项({my_score}分)，结果证明是正确的。{request.lessons_learned or ''}"
                    elif '反对' in my_stance:
                        lesson = f"⚠️ 我反对这个选项({my_score}分)，但结果是成功的。我需要重新审视我的判断标准。{request.lessons_learned or ''}"
                    else:
                        lesson = f"📝 我持中立态度({my_score}分)，结果是成功的。{request.lessons_learned or ''}"
                else:
                    if '支持' in my_stance and my_score >= 60:
                        lesson = f"❌ 我支持这个选项({my_score}分)，但结果失败了。我高估了某些因素。{request.lessons_learned or ''}"
                    elif '反对' in my_stance:
                        lesson = f"✅ 我反对这个选项({my_score}分)，结果证明我的担忧是对的。{request.lessons_learned or ''}"
                    else:
                        lesson = f"📝 我持中立态度({my_score}分)，结果失败了。{request.lessons_learned or ''}"
                
                # 更新解读文件
                interpretation_data.setdefault('learned_lessons', []).append(lesson)
                
                with open(persona_file, 'w', encoding='utf-8') as f:
                    json.dump(interpretation_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ {persona.name} 已学习: {lesson}")
        
        # 持久化更新后的决策上下文
        memory_system.persist_to_storage(request.decision_id)
        
        return {
            "success": True,
            "message": f"决策结果已更新，{len(council.personas)}个persona已学习",
            "data": {
                "decision_id": request.decision_id,
                "outcome": request.outcome,
                "success": request.success,
                "personas_learned": len(council.personas)
            }
        }
        
    except Exception as e:
        logger.error(f"更新决策结果失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": str(e)
        }


# ==================== 向后兼容端点 ====================

@router.get("/enhanced/ai-core/warmup-status/{session_id}")
async def get_warmup_status_compat(session_id: str):
    """向后兼容：AI核心预热状态（已废弃，返回完成状态）"""
    return {
        "success": True,
        "data": {
            "status": "completed",
            "message": "新的决策人格系统已就绪"
        }
    }


@router.get("/enhanced/history/{session_id}")
async def get_decision_history_compat(session_id: str):
    """向后兼容：获取决策历史"""
    try:
        session = info_collector.get_session(session_id)
        if not session:
            return {
                "success": False,
                "message": "会话不存在",
                "data": None
            }
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "conversation_history": session.get("conversation_history", []),
                "collected_info": session.get("collected_info", {}),
                "is_complete": session.get("is_complete", False)
            }
        }
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


# 注册兼容路由到 /api/decision/enhanced 前缀
compat_router = APIRouter(prefix="/api/decision/enhanced", tags=["decision-compat"])

def convert_to_legacy_format(result: Dict[str, Any]) -> Dict[str, Any]:
    """将新格式转换为旧格式 {success: true} -> {code: 200}"""
    if result.get("success"):
        return {
            "code": 200,
            "message": result.get("message", "success"),
            "data": result.get("data")
        }
    else:
        return {
            "code": 500,
            "message": result.get("message", "操作失败"),
            "data": result.get("data")
        }

@compat_router.post("/collect/start")
async def start_collection_compat(request: StartCollectionRequest):
    """向后兼容：开始信息收集"""
    result = await start_info_collection(request)
    return convert_to_legacy_format(result)

@compat_router.post("/collect/continue")
async def continue_collection_compat(request: ContinueCollectionRequest):
    """向后兼容：继续信息收集"""
    result = await continue_info_collection(request)
    return convert_to_legacy_format(result)

@compat_router.post("/collect/continue-stream")
async def continue_collection_stream_compat(request: ContinueCollectionRequest):
    """向后兼容：继续信息收集（流式）"""
    from fastapi.responses import StreamingResponse
    
    async def generate_stream():
        try:
            # 发送开始状态
            yield f"data: {json.dumps({'type': 'status', 'content': '正在分析你的回答...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)
            
            # 调用信息收集器
            result = info_collector.continue_collection(
                session_id=request.session_id,
                user_response=request.user_response
            )
            
            # 发送AI回复（如果有）
            if result.get("ai_question"):
                ai_question = result["ai_question"]
                
                # 清除状态，开始发送消息
                yield f"data: {json.dumps({'type': 'status', 'content': ''}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                
                # 分块发送AI消息，模拟打字效果
                chunk_size = 12
                for i in range(0, len(ai_question), chunk_size):
                    chunk = ai_question[i:i+chunk_size]
                    yield f"data: {json.dumps({'type': 'message', 'content': chunk}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.04)  # 打字效果延迟
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'data': result}, ensure_ascii=False)}\n\n"
            
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"流式信息收集失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@compat_router.post("/generate-options")
async def generate_options_compat(request: GenerateOptionsRequest):
    """向后兼容：生成选项"""
    result = await generate_ai_options(request)
    return convert_to_legacy_format(result)

@compat_router.get("/ai-core/warmup-status/{session_id}")
async def warmup_status_compat(session_id: str):
    result = await get_warmup_status_compat(session_id)
    return convert_to_legacy_format(result)

@compat_router.get("/history/{session_id}")
async def history_compat(session_id: str):
    result = await get_decision_history_compat(session_id)
    return convert_to_legacy_format(result)

@compat_router.get("/collect/session/{session_id}")
async def get_session_compat(session_id: str):
    """向后兼容：获取会话"""
    result = await get_collection_session(session_id)
    return convert_to_legacy_format(result)


print("   - 向后兼容端点已加载:")
print("     POST /api/decision/enhanced/collect/start")
print("     POST /api/decision/enhanced/collect/continue")
print("     POST /api/decision/enhanced/collect/continue-stream (流式)")
print("     POST /api/decision/enhanced/generate-options")
print("     GET  /api/decision/enhanced/ai-core/warmup-status/{session_id}")
print("     GET  /api/decision/enhanced/history/{session_id}")
print("     GET  /api/decision/enhanced/collect/session/{session_id}")
