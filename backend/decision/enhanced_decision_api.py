"""
增强的决策API
集成信息收集（Qwen3.5-plus）和决策模拟（本地模型+LoRA）
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import asyncio

from backend.decision.decision_info_collector import DecisionInfoCollector
from backend.decision.parallel_universe_simulator import ParallelUniverseSimulator
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision/enhanced", tags=["enhanced-decision"])

# 全局实例
info_collector = DecisionInfoCollector()
simulator = ParallelUniverseSimulator()


class StartCollectionRequest(BaseModel):
    """开始信息收集请求"""
    user_id: str
    initial_question: str


class ContinueCollectionRequest(BaseModel):
    """继续信息收集请求"""
    session_id: str
    user_response: str


class SimulateWithCollectedInfoRequest(BaseModel):
    """使用收集的信息进行模拟"""
    session_id: str
    options: List[Dict[str, str]]  # [{"title": "选项A", "description": "..."}]
    use_lora: bool = True


@router.post("/collect/start")
async def start_info_collection(request: StartCollectionRequest) -> Dict[str, Any]:
    """
    开始决策信息收集
    
    使用 Qwen3.5-plus API 进行多轮对话，收集决策所需信息
    """
    try:
        logger.info(f"📥 收到信息收集请求 - user_id: {request.user_id}, question: {request.initial_question}")
        
        result = info_collector.start_collection(
            user_id=request.user_id,
            initial_question=request.initial_question
        )
        
        logger.info(f"✅ 信息收集会话创建成功 - session_id: {result['session_id']}")
        
        return {
            "code": 200,
            "message": "信息收集已开始",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"开始信息收集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/continue")
async def continue_info_collection(request: ContinueCollectionRequest) -> Dict[str, Any]:
    """
    继续信息收集
    
    用户回答AI的问题，继续收集信息
    """
    try:
        result = info_collector.continue_collection(
            session_id=request.session_id,
            user_response=request.user_response
        )
        
        return {
            "code": 200,
            "message": "继续收集" if not result.get("is_complete") else "信息收集完成",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"继续信息收集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collect/session/{session_id}")
async def get_collection_session(session_id: str) -> Dict[str, Any]:
    """
    获取信息收集会话
    
    查看当前收集进度和已收集的信息
    """
    try:
        session = info_collector.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "initial_question": session["initial_question"],
                "current_round": session["current_round"],
                "is_complete": session["is_complete"],
                "collected_info": session["collected_info"],
                "conversation_count": len(session["conversation_history"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate/with-collection")
async def simulate_with_collected_info(request: SimulateWithCollectedInfoRequest) -> Dict[str, Any]:
    """
    使用收集的信息进行决策模拟
    
    信息收集完成后，使用本地 Qwen3.5-9B + 用户 LoRA 进行个性化决策模拟
    """
    try:
        logger.info(f"📥 收到决策模拟请求 - session_id: {request.session_id}")
        
        # 1. 获取收集的信息
        session = info_collector.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        logger.info(f"📋 会话信息 - user_id: {session['user_id']}, question: {session['initial_question']}")
        
        if not session["is_complete"]:
            raise HTTPException(status_code=400, detail="信息收集未完成")
        
        # 2. 使用本地 Qwen3.5-9B + 用户 LoRA 进行决策模拟
        result = await simulator.simulate_decision(
            user_id=session["user_id"],
            question=session["initial_question"],
            options=request.options,
        )
        
        # 3. 转换为可序列化格式
        response_data = {
            "code": 200,
            "message": "决策模拟完成",
            "data": {
                "simulation_id": result.simulation_id,
                "user_id": result.user_id,
                "question": result.question,
                "collected_info_summary": session["collected_info"],
                "options": [
                    {
                        "option_id": opt.option_id,
                        "title": opt.title,
                        "description": opt.description,
                        "timeline": [asdict(event) for event in opt.timeline],
                        "final_score": opt.final_score,
                        "risk_level": opt.risk_level,
                        "risk_assessment": opt.risk_assessment
                    }
                    for opt in result.options
                ],
                "recommendation": result.recommendation,
                "created_at": result.created_at,
                "used_lora": True
            }
        }
        
        logger.info(f"决策模拟完成: {result.simulation_id}")
        return response_data
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404 if "LoRA" in str(e) else 400, detail=str(e))
    except RuntimeError as e:
        msg = str(e)
        if "正在训练中" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    except Exception as e:
        import traceback
        logger.error(f"决策模拟失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-process")
async def full_decision_process(
    user_id: str,
    initial_question: str,
    options: List[Dict[str, str]],
    use_lora: bool = True
) -> Dict[str, Any]:
    """
    完整决策流程（快速版）
    
    跳过多轮对话，直接使用初始问题进行模拟
    适合用户已经明确选项的情况
    """
    try:
        result = await simulator.simulate_decision(
            user_id=user_id,
            question=initial_question,
            options=options,
        )
        
        response_data = {
            "code": 200,
            "message": "决策模拟完成",
            "data": {
                "simulation_id": result.simulation_id,
                "user_id": result.user_id,
                "question": result.question,
                "options": [
                    {
                        "option_id": opt.option_id,
                        "title": opt.title,
                        "description": opt.description,
                        "timeline": [asdict(event) for event in opt.timeline],
                        "final_score": opt.final_score,
                        "risk_level": opt.risk_level,
                        "risk_assessment": opt.risk_assessment
                    }
                    for opt in result.options
                ],
                "recommendation": result.recommendation,
                "created_at": result.created_at,
                "used_lora": True
            }
        }
        
        return response_data
        
    except ValueError as e:
        raise HTTPException(status_code=404 if "LoRA" in str(e) else 400, detail=str(e))
    except RuntimeError as e:
        msg = str(e)
        if "正在训练中" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=500, detail=msg)
    except Exception as e:
        import traceback
        logger.error(f"快速决策模拟失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class GenerateOptionsRequest(BaseModel):
    """生成选项请求"""
    session_id: str
    user_options: List[str] = []


@router.post("/generate-options")
async def generate_ai_options(request: GenerateOptionsRequest) -> Dict[str, Any]:
    """
    生成 AI 建议选项
    
    根据收集的信息和用户已有选项，生成 1-2 个 AI 建议选项
    """
    try:
        # 获取会话信息
        session = info_collector.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 使用 LLM 生成建议选项
        from backend.llm.llm_service import get_llm_service
        llm_service = get_llm_service()
        
        ai_options = []
        
        if llm_service and llm_service.enabled:
            try:
                collected_info = session.get("collected_info", {})
                initial_question = session.get("initial_question", "")
                
                prompt = f"""基于以下信息，为用户推荐1-2个决策选项：

问题：{initial_question}

用户已有选项：{', '.join(request.user_options) if request.user_options else '无'}

收集的信息：
- 背景：{collected_info.get('decision_context', {})}
- 约束：{collected_info.get('user_constraints', {})}
- 优先级：{collected_info.get('priorities', {})}
- 顾虑：{collected_info.get('concerns', [])}

请以JSON格式返回，格式如下：
{{
  "options": [
    {{"title": "选项名称", "description": "简短描述"}},
    {{"title": "选项名称", "description": "简短描述"}}
  ]
}}

要求：
1. 推荐的选项要与用户已有选项不同
2. 考虑用户的约束条件和优先级
3. 每个选项要有实际可行性
"""
                
                messages = [
                    {"role": "system", "content": "你是一个专业的决策顾问，擅长为用户提供合理的决策选项。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = llm_service.chat(messages, temperature=0.7, response_format="json_object")
                
                print(f"📝 LLM原始响应: {response[:200] if response else '(空响应)'}")
                
                if not response or not response.strip():
                    print("⚠️ LLM返回空响应")
                    raise ValueError("LLM返回空响应")
                
                result = json.loads(response)
                
                if "options" in result:
                    ai_options = result["options"][:2]  # 最多2个
                
            except Exception as e:
                logger.error(f"LLM生成选项失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 如果 LLM 失败或没有生成，使用更适合副本模拟的默认选项
        if not ai_options:
            if not request.user_options or len(request.user_options) < 2:
                ai_options = [
                    {"title": "直接行动", "description": "先按当前倾向执行，边做边调整"},
                    {"title": "小规模试错", "description": "先做低成本试验，再决定是否全面投入"}
                ]
            else:
                ai_options = [
                    {"title": "综合方案", "description": "结合多个选项的优势，先做阶段性组合尝试"}
                ]
        
        return {
            "code": 200,
            "message": "AI选项生成成功",
            "data": {
                "ai_options": ai_options
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成AI选项失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.websocket("/ws/simulate")
async def simulate_with_collection_ws(websocket: WebSocket):
    """
    WebSocket 实时决策模拟

    客户端发送:
    {
      "session_id": "...",
      "options": [{"title": "...", "description": "..."}]
    }

    服务端返回:
    {"type": "start", ...}
    {"type": "option_start", ...}
    {"type": "node", "node": {...}}
    {"type": "option_complete", ...}
    {"type": "recommendation", ...}
    {"type": "done", ...}
    """
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_text()
            request = json.loads(payload)
            session_id = request.get("session_id")
            options = request.get("options", [])

            if not session_id or not options:
                await websocket.send_json({"type": "error", "content": "session_id 和 options 不能为空"})
                continue

            session = info_collector.get_session(session_id)
            if not session:
                await websocket.send_json({"type": "error", "content": "会话不存在"})
                continue
            if not session.get("is_complete"):
                await websocket.send_json({"type": "error", "content": "信息收集未完成"})
                continue

            user_id = session["user_id"]
            question = session["initial_question"]
            await websocket.send_json({
                "type": "start",
                "session_id": session_id,
                "user_id": user_id,
                "question": question
            })
            await websocket.send_json({
                "type": "status",
                "stage": "init",
                "content": "已建立推演连接，正在读取用户画像与决策上下文"
            })

            profile = simulator.personality_test.load_profile(user_id)
            await websocket.send_json({
                "type": "status",
                "stage": "profile_loaded",
                "content": "用户画像已加载，准备逐个推演决策选项"
            })
            simulated_options = []

            # 并行为所有选项生成时间线（32GB 显存足够并行 2-3 个推理）
            async def generate_option_timeline(i: int, option: dict):
                """为单个选项生成时间线并流式推送节点"""
                await websocket.send_json({
                    "type": "option_start",
                    "option_id": f"option_{i+1}",
                    "title": option.get("title", f"选项{i+1}")
                })
                await websocket.send_json({
                    "type": "status",
                    "stage": "option_start",
                    "option_id": f"option_{i+1}",
                    "option_title": option.get("title", f"选项{i+1}"),
                    "content": f"开始推演 {option.get('title', f'选项{i+1}')} 的主时间线"
                })

                timeline_data = await simulator.lora_analyzer.generate_timeline_with_lora(
                    user_id=user_id,
                    question=question,
                    option=option,
                    profile=profile,
                    num_events=8
                )

                timeline = []
                option_branch = option['title'].lower().replace(' ', '_')
                previous_event_id = None
                from backend.decision.parallel_universe_simulator import TimelineEvent, DecisionOption
                for idx, e in enumerate(timeline_data):
                    await websocket.send_json({
                        "type": "thinking",
                        "stage": "timeline_event",
                        "option_id": f"option_{i+1}",
                        "option_title": option['title'],
                        "content": f"正在生成 {option['title']} 的第 {idx + 1} 个关键事件"
                    })
                    negative_impact = sum(abs(v) for v in e['impact'].values() if v < 0)
                    positive_impact = sum(v for v in e['impact'].values() if v > 0)
                    risk_tag = "high" if negative_impact >= 0.5 else ("low" if negative_impact <= 0.1 else "medium")
                    opportunity_tag = "high" if positive_impact >= 0.5 else ("low" if positive_impact <= 0.1 else "medium")
                    node = TimelineEvent(
                        event_id=f"{option_branch}_node_{idx+1}",
                        parent_event_id=previous_event_id,
                        month=e['month'],
                        event=e['event'],
                        impact=e['impact'],
                        probability=e['probability'],
                        event_type=simulator._infer_event_type(e['event']),
                        branch_group=option_branch,
                        node_level=idx + 1,
                        risk_tag=risk_tag,
                        opportunity_tag=opportunity_tag,
                        visual_weight=max(0.2, min(1.0, positive_impact + negative_impact))
                    )
                    previous_event_id = node.event_id
                    timeline.append(node)
                    await websocket.send_json({
                        "type": "node",
                        "option_id": f"option_{i+1}",
                        "option_title": option['title'],
                        "node": asdict(node)
                    })

                final_score = simulator._calculate_final_score(timeline, profile) if timeline else 50.0
                risk_level = simulator._calculate_risk_level(timeline) if timeline else 0.5

                # 生成分支事件并流式推送
                await websocket.send_json({
                    "type": "thinking",
                    "stage": "branch_generation",
                    "option_id": f"option_{i+1}",
                    "option_title": option['title'],
                    "content": f"正在扩展 {option['title']} 的风险与机遇分支"
                })
                branch_nodes = simulator._generate_branch_events(timeline, option_branch)
                for bnode in branch_nodes:
                    timeline.append(bnode)
                    await websocket.send_json({
                        "type": "node",
                        "option_id": f"option_{i+1}",
                        "option_title": option['title'],
                        "node": asdict(bnode)
                    })

                await websocket.send_json({
                    "type": "status",
                    "stage": "option_scoring",
                    "option_id": f"option_{i+1}",
                    "option_title": option['title'],
                    "content": f"{option['title']} 主线与分支已生成，正在计算得分与风险"
                })
                await websocket.send_json({
                    "type": "option_complete",
                    "option_id": f"option_{i+1}",
                    "title": option['title'],
                    "final_score": final_score,
                    "risk_level": risk_level
                })

                return DecisionOption(
                    option_id=f"option_{i+1}",
                    title=option['title'],
                    description=option.get('description', ''),
                    timeline=timeline,
                    final_score=final_score,
                    risk_level=risk_level,
                    risk_assessment=None
                )

            # 串行执行（共享同一个 LoRA 模型实例，并行会冲突）
            for i, option in enumerate(options):
                opt_result = await generate_option_timeline(i, option)
                simulated_options.append(opt_result)

            options_for_rec = [
                {
                    "title": opt.title,
                    "description": opt.description,
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "timeline_summary": simulator._summarize_timeline(opt.timeline)
                }
                for opt in simulated_options
            ]
            await websocket.send_json({
                "type": "status",
                "stage": "recommendation",
                "content": "所有选项推演完成，正在生成个性化推荐结论"
            })
            recommendation = await simulator.lora_analyzer.generate_personalized_recommendation(
                user_id=user_id,
                question=question,
                options=options_for_rec,
                profile=profile
            )

            await websocket.send_json({
                "type": "recommendation",
                "content": recommendation
            })

            simulation_id = f"sim_{user_id}_{int(__import__('time').time())}"
            await websocket.send_json({
                "type": "status",
                "stage": "completed",
                "content": "推荐结论已生成，正在整理最终结果"
            })
            await websocket.send_json({
                "type": "done",
                "simulation_id": simulation_id,
                "user_id": user_id,
                "question": question
            })

    except WebSocketDisconnect:
        logger.info("决策模拟 WebSocket 已断开")
    except Exception as e:
        logger.error(f"决策模拟 WebSocket 失败: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
