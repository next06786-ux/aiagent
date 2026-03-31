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
from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
from dataclasses import asdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision/enhanced", tags=["enhanced-decision"])

# 全局实例
info_collector = DecisionInfoCollector()


class DecisionSimulator:
    """决策模拟器包装类"""
    def __init__(self):
        self.lora_analyzer = LoRADecisionAnalyzer()
        self.personality_test = None
        try:
            from backend.personality.personality_test import PersonalityTest
            self.personality_test = PersonalityTest()
        except Exception as e:
            print(f"PersonalityTest 初始化失败: {e}")
        try:
            from backend.decision.risk_assessment_engine import RiskAssessmentEngine
            self._risk_engine = RiskAssessmentEngine()
        except Exception:
            self._risk_engine = None

    def _infer_event_type(self, event_text: str) -> str:
        keywords = {'风险': 'risk', '机会': 'opportunity', '挑战': 'challenge', '成功': 'milestone', '失败': 'setback'}
        for k, v in keywords.items():
            if k in event_text:
                return v
        return 'normal'

    def _calculate_final_score(self, timeline, profile) -> float:
        if not timeline:
            return 50.0
        scores = [e.probability * 100 for e in timeline if hasattr(e, 'probability')]
        return sum(scores) / len(scores) if scores else 50.0

    def _calculate_risk_level(self, timeline) -> float:
        if not timeline:
            return 0.5
        risks = [1 - e.probability for e in timeline if hasattr(e, 'probability')]
        return sum(risks) / len(risks) if risks else 0.5

    def _summarize_timeline(self, timeline) -> str:
        if not timeline:
            return '暂无推演数据'
        events = [e.event for e in timeline[:3] if hasattr(e, 'event')]
        return ' → '.join(events) if events else '暂无推演数据'


simulator = DecisionSimulator()


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


@router.get("/record/{simulation_id}")
async def get_decision_record(simulation_id: str):
    """获取单条决策推演记录详情"""
    try:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        import sqlalchemy
        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        row = db_session.execute(
            sqlalchemy.text("""
                SELECT simulation_id, user_id, question, options_count, recommendation, created_at
                FROM decision_records WHERE simulation_id = :sid
            """),
            {"sid": simulation_id}
        ).fetchone()
        db_session.close()
        if not row:
            return {"code": 404, "message": "记录不存在", "data": None}
        return {
            "code": 200,
            "data": {
                "simulation_id": row[0],
                "user_id": row[1],
                "question": row[2] or "",
                "options_count": row[3] or 0,
                "recommendation": row[4] or "",
                "created_at": row[5] or "",
                "options": []  # 历史推演节点数据暂不存储，只显示推荐结论
            }
        }
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


@router.get("/history/{user_id}")
async def get_decision_history(user_id: str):
    """获取用户的决策历史记录（从数据库读取，持久化）"""
    try:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        import sqlalchemy
        db = Database(DatabaseConfig.get_database_url())
        
        # 确保表存在
        engine = db.engine
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS decision_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    simulation_id VARCHAR(100) UNIQUE NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    question TEXT,
                    options_count INT DEFAULT 0,
                    recommendation TEXT,
                    created_at VARCHAR(50),
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            conn.commit()
        
        db_session = db.get_session()
        rows = db_session.execute(
            sqlalchemy.text("""
                SELECT simulation_id, question, options_count, recommendation, created_at
                FROM decision_records
                WHERE user_id = :uid
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"uid": user_id}
        ).fetchall()
        db_session.close()
        
        records = [
            {
                "session_id": row[0],
                "question": row[1] or "",
                "options_count": row[2] or 0,
                "recommendation": row[3] or "",
                "created_at": row[4] or ""
            }
            for row in rows
        ]
        return {"code": 200, "data": records}
    except Exception as e:
        logger.warning(f"获取决策历史失败: {e}")
        return {"code": 200, "data": []}


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

            profile = None
            if simulator.personality_test:
                try:
                    profile = simulator.personality_test.load_profile(user_id)
                except Exception:
                    profile = None
            await websocket.send_json({
                "type": "status",
                "stage": "profile_loaded",
                "content": "用户画像已加载，准备逐个推演决策选项"
            })
            simulated_options = []

            # 并行为所有选项生成时间线（32GB 显存足够并行 2-3 个推理）
            async def generate_option_timeline(i: int, option: dict):
                """为单个选项生成时间线并流式推送节点（PKF-DS 增强版）"""
                await websocket.send_json({
                    "type": "option_start",
                    "option_id": f"option_{i+1}",
                    "title": option.get("title", f"选项{i+1}")
                })

                # ── PKF-DS 阶段 1-2：抽取个人事实 + 构建因果图 ──
                await websocket.send_json({
                    "type": "status",
                    "stage": "pkf_knowledge",
                    "option_id": f"option_{i+1}",
                    "content": "正在分析你的个人背景和决策因果关系..."
                })
                try:
                    from backend.decision.personal_knowledge_fusion import (
                        PersonalFactExtractor, CausalReasoningGraph
                    )
                    extractor = PersonalFactExtractor(user_id)
                    facts = extractor.extract_all()
                    causal_graph = CausalReasoningGraph(
                        question, option.get("title", ""), facts
                    )
                    causal_edges = causal_graph.build()
                    causal_chains = causal_graph.get_chains()

                    # 把个人事实和因果链注入到 LoRA 的 life_context
                    pkf_context = "个人事实：\n"
                    for f in facts[:8]:
                        pkf_context += f"- {f.to_text()}\n"
                    pkf_context += "\n因果推理链：\n"
                    for chain in causal_chains[:4]:
                        chain_str = " -> ".join([e.cause for e in chain] + [chain[-1].effect])
                        pkf_context += f"- {chain_str}\n"

                    await websocket.send_json({
                        "type": "status",
                        "stage": "pkf_ready",
                        "option_id": f"option_{i+1}",
                        "content": f"已提取 {len(facts)} 条个人事实，构建 {len(causal_chains)} 条因果链"
                    })
                    # 把 PKF 上下文注入 LoRA analyzer 的 life_context
                    simulator.lora_analyzer._pkf_context = pkf_context
                except Exception as pkf_err:
                    logger.warning(f"PKF-DS 增强失败，降级为普通推演: {pkf_err}")
                    simulator.lora_analyzer._pkf_context = ""

                await websocket.send_json({
                    "type": "status",
                    "stage": "option_start",
                    "option_id": f"option_{i+1}",
                    "option_title": option.get("title", f"选项{i+1}"),
                    "content": f"开始推演 {option.get('title', f'选项{i+1}')} 的主时间线（快速模式）"
                })

                stream_buffer = ""
                emitted_months = []
                timeline = []
                option_branch = option['title'].lower().replace(' ', '_')
                previous_event_id = None
                from dataclasses import dataclass

                @dataclass
                class TimelineEvent:
                    event_id: str
                    parent_event_id: Optional[str]
                    month: int
                    event: str
                    impact: Dict[str, float]
                    probability: float
                    event_type: str = "general"
                    branch_group: str = "main"
                    node_level: int = 1
                    risk_tag: str = "medium"
                    opportunity_tag: str = "medium"
                    visual_weight: float = 0.5

                @dataclass
                class DecisionOption:
                    option_id: str
                    title: str
                    description: str
                    timeline: List[TimelineEvent]
                    final_score: float
                    risk_level: float
                    risk_assessment: Optional[Dict] = None

                async for chunk in simulator.lora_analyzer.stream_timeline_generation(
                    user_id=user_id,
                    question=question,
                    option=option,
                    profile=profile,
                    num_events=12
                ):
                    stream_buffer += chunk
                    await websocket.send_json({
                        "type": "thinking_chunk",
                        "stage": "timeline_generation_stream",
                        "option_id": f"option_{i+1}",
                        "option_title": option.get("title", f"选项{i+1}"),
                        "content": chunk
                    })

                    incremental_events = simulator.lora_analyzer.extract_incremental_events(stream_buffer, emitted_months)
                    for e in incremental_events:
                        idx = len(timeline)
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

                timeline_data = simulator.lora_analyzer._parse_timeline_json(stream_buffer)
                if not timeline_data:
                    retry_timeline = await simulator.lora_analyzer.generate_timeline_with_lora(
                        user_id=user_id,
                        question=question,
                        option=option,
                        profile=profile,
                        num_events=12
                    )
                    timeline_data = retry_timeline

                if not timeline:
                    previous_event_id = None
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
                branch_nodes = []
                candidate_parents = timeline[:1]
                for parent in candidate_parents:
                    parent_payload = {
                        "month": parent.month,
                        "event": parent.event,
                        "impact": parent.impact,
                        "probability": parent.probability
                    }
                    generated_branches = await simulator.lora_analyzer.generate_branch_events_with_lora(
                        user_id=user_id,
                        question=question,
                        option=option,
                        parent_event=parent_payload,
                        profile=profile
                    )
                    for branch_idx, b in enumerate(generated_branches):
                        negative_impact = sum(abs(v) for v in b['impact'].values() if v < 0)
                        positive_impact = sum(v for v in b['impact'].values() if v > 0)
                        branch_node = TimelineEvent(
                            event_id=f"{option_branch}_fork_{parent.node_level}_{branch_idx + 1}",
                            parent_event_id=parent.event_id,
                            month=b['month'],
                            event=b['event'],
                            impact=b['impact'],
                            probability=b['probability'],
                            event_type=simulator._infer_event_type(b['event']),
                            branch_group=f"{option_branch}_fork",
                            node_level=parent.node_level + 1,
                            risk_tag="high" if negative_impact >= 0.5 else ("low" if negative_impact <= 0.1 else "medium"),
                            opportunity_tag="high" if positive_impact >= 0.5 else ("low" if positive_impact <= 0.1 else "medium"),
                            visual_weight=max(0.2, min(1.0, positive_impact + negative_impact))
                        )
                        branch_nodes.append(branch_node)
                        timeline.append(branch_node)
                        await websocket.send_json({
                            "type": "node",
                            "option_id": f"option_{i+1}",
                            "option_title": option['title'],
                            "node": asdict(branch_node)
                        })

                await websocket.send_json({
                    "type": "status",
                    "stage": "option_scoring",
                    "option_id": f"option_{i+1}",
                    "option_title": option['title'],
                    "content": f"{option['title']} 主链已完成，正在补充分支与评分细节"
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
                "content": "主链推演已完成，正在汇总各选项并生成最终推荐"
            })
            recommendation_stream = ""
            async for chunk in simulator.lora_analyzer.stream_recommendation_generation(
                user_id=user_id,
                question=question,
                options=options_for_rec,
                profile=profile
            ):
                recommendation_stream += chunk
                await websocket.send_json({
                    "type": "recommendation_chunk",
                    "content": chunk
                })
            recommendation = simulator.lora_analyzer._clean_recommendation(recommendation_stream)

            await websocket.send_json({
                "type": "recommendation",
                "content": recommendation
            })

            simulation_id = f"sim_{user_id}_{int(__import__('time').time())}"
            
            # 保存决策记录到数据库
            try:
                from backend.database.models import Database
                from backend.database.config import DatabaseConfig
                from sqlalchemy import Column, String, Integer, Text, DateTime
                from sqlalchemy.ext.declarative import declarative_base
                from datetime import datetime
                db = Database(DatabaseConfig.get_database_url())
                db_session = db.get_session()
                # 用原生SQL插入，避免模型定义问题
                db_session.execute(
                    __import__('sqlalchemy').text("""
                        INSERT IGNORE INTO decision_records 
                        (simulation_id, user_id, question, options_count, recommendation, created_at)
                        VALUES (:sid, :uid, :q, :oc, :rec, :ca)
                    """),
                    {
                        "sid": simulation_id,
                        "uid": user_id,
                        "q": question[:500],
                        "oc": len(options),
                        "rec": recommendation[:1000] if recommendation else "",
                        "ca": datetime.now().isoformat()
                    }
                )
                db_session.commit()
                db_session.close()
                logger.info(f"决策记录已保存: {simulation_id}")
            except Exception as save_err:
                logger.warning(f"保存决策记录失败: {save_err}")
            
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


# ── 推演纠错反馈（受 GenSim 纠错机制启发）──────────────────────────────────

# 内存存储用户对推演事件的反馈，用于后续推演时注入 prompt
_simulation_feedback: Dict[str, List[Dict[str, str]]] = {}


class TimelineFeedbackRequest(BaseModel):
    """用户对推演时间线事件的反馈"""
    user_id: str
    simulation_id: str
    event_month: int
    event_text: str
    feedback_type: str  # "unlikely" | "accurate" | "comment"
    comment: str = ""


@router.post("/timeline-feedback")
async def submit_timeline_feedback(req: TimelineFeedbackRequest) -> Dict[str, Any]:
    """
    用户对推演时间线中某个事件给出反馈。
    反馈会被存储，在后续推演（如分支推演或重新推演）时注入 prompt，
    让模型根据用户的真实判断调整推演方向。

    参考：GenSim (NAACL 2025) 的纠错机制思路——
    当仿真结果偏离用户认知时，通过反馈修正后续生成。
    """
    key = f"{req.user_id}_{req.simulation_id}"
    if key not in _simulation_feedback:
        _simulation_feedback[key] = []

    _simulation_feedback[key].append({
        "event": req.event_text,
        "type": req.feedback_type,
        "comment": req.comment,
        "month": req.event_month
    })

    logger.info(f"[纠错反馈] 用户 {req.user_id} 对第 {req.event_month} 月事件反馈: {req.feedback_type}")

    # 同时存入数据库作为 LoRA 训练数据
    try:
        from backend.database.connection import db_connection
        from backend.database.models import ConversationHistory
        from datetime import datetime

        if req.feedback_type == "unlikely":
            user_msg = f"你之前推演说第{req.event_month}个月会'{req.event_text}'，我觉得这不太可能发生。"
            ai_msg = f"感谢你的反馈。我会调整对你的理解，在后续推演中降低类似事件的概率。"
        elif req.feedback_type == "accurate":
            user_msg = f"你推演的第{req.event_month}个月'{req.event_text}'，我觉得很准确。"
            ai_msg = f"很高兴这个推演符合你的预期，这说明我对你的决策风格理解得比较到位。"
        else:
            user_msg = f"关于第{req.event_month}个月的推演'{req.event_text}'，我想说：{req.comment}"
            ai_msg = f"收到你的反馈，我会在后续推演中考虑你的意见。"

        db = db_connection.get_session()
        now = datetime.utcnow()
        db.add(ConversationHistory(
            user_id=req.user_id, role="user", content=user_msg,
            timestamp=now, session_id=f"feedback_{req.simulation_id}"
        ))
        db.add(ConversationHistory(
            user_id=req.user_id, role="assistant", content=ai_msg,
            timestamp=now, session_id=f"feedback_{req.simulation_id}"
        ))
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"保存反馈训练数据失败: {e}")

    return {
        "success": True,
        "message": "反馈已记录，将影响后续推演",
        "feedback_count": len(_simulation_feedback[key])
    }


@router.get("/timeline-feedback/{user_id}/{simulation_id}")
async def get_timeline_feedback(user_id: str, simulation_id: str) -> Dict[str, Any]:
    """获取用户对某次推演的所有反馈"""
    key = f"{user_id}_{simulation_id}"
    feedbacks = _simulation_feedback.get(key, [])
    return {"success": True, "data": feedbacks}


def get_user_feedback_for_prompt(user_id: str, simulation_id: str) -> List[Dict[str, str]]:
    """供 lora_decision_analyzer 调用，获取用户反馈用于注入 prompt"""
    key = f"{user_id}_{simulation_id}"
    return _simulation_feedback.get(key, [])
