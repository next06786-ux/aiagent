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
        """多维度加权评分：后期事件权重更大，net_impact × probability 决定贡献值"""
        if not timeline:
            return 50.0
        main_chain = [e for e in timeline if not (
            hasattr(e, 'branch_group') and str(getattr(e, 'branch_group', '')).endswith('_fork')
        )]
        if not main_chain:
            main_chain = timeline
        total, weight_sum = 0.0, 0.0
        n = len(main_chain)
        for i, e in enumerate(main_chain):
            weight = 0.6 + 0.8 * (i / max(n - 1, 1))
            impact = getattr(e, 'impact', {}) if hasattr(e, 'impact') else {}
            net = sum(impact.values()) if isinstance(impact, dict) else 0.0
            prob = float(getattr(e, 'probability', 0.7))
            contribution = 50.0 + min(max(net * 80, -40), 40)
            total += contribution * prob * weight
            weight_sum += prob * weight
        if weight_sum == 0:
            return 50.0
        return round(min(95.0, max(10.0, total / weight_sum)), 1)

    def _calculate_risk_level(self, timeline) -> float:
        """主链负面 impact 绝对值均值，映射到 0~1"""
        if not timeline:
            return 0.5
        main_chain = [e for e in timeline if not (
            hasattr(e, 'branch_group') and str(getattr(e, 'branch_group', '')).endswith('_fork')
        )]
        if not main_chain:
            main_chain = timeline
        neg_sum, count = 0.0, 0
        for e in main_chain:
            impact = getattr(e, 'impact', {}) if hasattr(e, 'impact') else {}
            neg = sum(abs(v) for v in impact.values() if v < 0) if isinstance(impact, dict) else 0.0
            neg_sum += neg
            count += 1
        return round(min(1.0, (neg_sum / count) / 1.0), 2) if count else 0.5

    def _summarize_timeline(self, timeline) -> str:
        if not timeline:
            return '暂无推演数据'
        events = [e.event for e in timeline[:3] if hasattr(e, 'event')]
        return ' → '.join(events) if events else '暂无推演数据'

    async def simulate_decision(
        self,
        user_id: str,
        question: str,
        options: List[Dict[str, str]],
    ):
        """
        HTTP 模式的完整决策模拟（非流式）
        为每个选项生成时间线，然后生成推荐
        """
        from dataclasses import dataclass, asdict as _asdict

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
            timeline: list
            final_score: float
            risk_level: float
            risk_assessment: Optional[Dict] = None

        @dataclass
        class SimulationResult:
            simulation_id: str
            user_id: str
            question: str
            options: list
            recommendation: str
            created_at: str

        profile = None
        if self.personality_test:
            try:
                profile = self.personality_test.load_profile(user_id)
            except Exception:
                profile = None

        simulated_options = []

        for i, option in enumerate(options):
            option_branch = option.get('title', f'option_{i}').lower().replace(' ', '_')
            logger.info(f"[HTTP推演] 开始推演选项 {i+1}: {option.get('title')}")

            # 注入 PKF 上下文
            try:
                from backend.decision.personal_knowledge_fusion import (
                    PersonalFactExtractor, CausalReasoningGraph
                )
                extractor = PersonalFactExtractor(user_id)
                facts = extractor.extract_all()
                causal_graph = CausalReasoningGraph(question, option.get("title", ""), facts)
                causal_graph.build()
                causal_chains = causal_graph.get_chains()
                pkf_context = "个人事实：\n"
                for f in facts[:8]:
                    pkf_context += f"- {f.to_text()}\n"
                pkf_context += "\n因果推理链：\n"
                for chain in causal_chains[:4]:
                    chain_str = " -> ".join([e.cause for e in chain] + [chain[-1].effect])
                    pkf_context += f"- {chain_str}\n"
                self.lora_analyzer._pkf_context = pkf_context
            except Exception:
                self.lora_analyzer._pkf_context = ""

            # 生成时间线
            timeline = []
            timeline_data = await self.lora_analyzer.generate_timeline_with_lora(
                user_id=user_id,
                question=question,
                option=option,
                profile=profile,
                num_events=12
            )

            previous_event_id = None
            for idx, e in enumerate(timeline_data or []):
                negative_impact = sum(abs(v) for v in e.get('impact', {}).values() if v < 0)
                positive_impact = sum(v for v in e.get('impact', {}).values() if v > 0)
                node = TimelineEvent(
                    event_id=f"{option_branch}_node_{idx+1}",
                    parent_event_id=previous_event_id,
                    month=e.get('month', idx + 1),
                    event=e.get('event', ''),
                    impact=e.get('impact', {}),
                    probability=e.get('probability', 0.5),
                    event_type=self._infer_event_type(e.get('event', '')),
                    branch_group=option_branch,
                    node_level=idx + 1,
                    risk_tag="high" if negative_impact >= 0.5 else ("low" if negative_impact <= 0.1 else "medium"),
                    opportunity_tag="high" if positive_impact >= 0.5 else ("low" if positive_impact <= 0.1 else "medium"),
                    visual_weight=max(0.2, min(1.0, positive_impact + negative_impact))
                )
                previous_event_id = node.event_id
                timeline.append(node)

            final_score = self._calculate_final_score(timeline, profile)
            risk_level = self._calculate_risk_level(timeline)

            simulated_options.append(DecisionOption(
                option_id=f"option_{i+1}",
                title=option.get('title', f'选项{i+1}'),
                description=option.get('description', ''),
                timeline=timeline,
                final_score=final_score,
                risk_level=risk_level,
                risk_assessment=None
            ))

        # 生成推荐
        options_for_rec = [
            {
                "title": opt.title,
                "description": opt.description,
                "final_score": opt.final_score,
                "risk_level": opt.risk_level,
                "timeline_summary": self._summarize_timeline(opt.timeline)
            }
            for opt in simulated_options
        ]
        recommendation = ""
        try:
            rec_stream = ""
            async for chunk in self.lora_analyzer.stream_recommendation_generation(
                user_id=user_id, question=question, options=options_for_rec, profile=profile
            ):
                rec_stream += chunk
            recommendation = self.lora_analyzer._clean_recommendation(rec_stream)
        except Exception as e:
            logger.warning(f"推荐生成失败: {e}")
            recommendation = "暂无推荐"

        simulation_id = f"sim_{user_id}_{int(__import__('time').time())}"

        # 保存记录
        try:
            from backend.database.models import Database
            from backend.database.config import DatabaseConfig
            from datetime import datetime
            import sqlalchemy
            db = Database(DatabaseConfig.get_database_url())
            db_session = db.get_session()
            db_session.execute(
                sqlalchemy.text("""
                    INSERT IGNORE INTO decision_records
                    (simulation_id, user_id, question, options_count, recommendation, created_at)
                    VALUES (:sid, :uid, :q, :oc, :rec, :ca)
                """),
                {"sid": simulation_id, "uid": user_id, "q": question[:500],
                 "oc": len(options), "rec": recommendation[:1000],
                 "ca": datetime.now().isoformat()}
            )
            db_session.commit()
            db_session.close()
        except Exception as save_err:
            logger.warning(f"保存决策记录失败: {save_err}")

        return SimulationResult(
            simulation_id=simulation_id,
            user_id=user_id,
            question=question,
            options=simulated_options,
            recommendation=recommendation,
            created_at=__import__('datetime').datetime.now().isoformat()
        )


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
    """获取单条决策推演记录详情（含完整 timeline）"""
    try:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        import sqlalchemy
        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        row = db_session.execute(
            sqlalchemy.text("""
                SELECT simulation_id, user_id, question, options_count, recommendation, timeline_data, created_at
                FROM decision_records WHERE simulation_id = :sid
            """),
            {"sid": simulation_id}
        ).fetchone()
        db_session.close()
        if not row:
            return {"code": 404, "message": "记录不存在", "data": None}

        # 解析 timeline_data
        options = []
        if row[5]:
            try:
                options = json.loads(row[5])
            except Exception:
                options = []

        return {
            "code": 200,
            "data": {
                "simulation_id": row[0],
                "user_id": row[1],
                "question": row[2] or "",
                "options_count": row[3] or 0,
                "recommendation": row[4] or "",
                "options": options,
                "created_at": row[6] or "",
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
        from dataclasses import asdict as _safe_asdict
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
                        "timeline": [_safe_asdict(event) if hasattr(event, '__dataclass_fields__') else event for event in opt.timeline],
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
    统一选项规划接口
    
    不管用户是否提供了选项，都由大模型基于完整的信息收集结果来：
    1. 润色/扩展用户给出的粗略选项（如"考研" → 完整的选项描述）
    2. 补充用户没想到的合理选项
    3. 确保每个选项都是有意义的、可推演的决策方向
    
    最终输出 2-4 个结构化选项，每个都有清晰的标题和描述。
    """
    try:
        session = info_collector.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        from backend.llm.llm_service import get_llm_service
        llm_service = get_llm_service()
        
        collected_info = session.get("collected_info", {})
        initial_question = session.get("initial_question", "")
        options_mentioned = collected_info.get("options_mentioned", [])
        
        # 合并所有来源的选项线索：用户明确输入 + 信息收集阶段提取到的
        all_hints = list(set(request.user_options + options_mentioned))
        
        final_options = []
        
        if llm_service and llm_service.enabled:
            try:
                # 构建对话历史摘要
                conversation_summary = ""
                for msg in session.get("conversation_history", [])[-8:]:
                    role = "用户" if msg["role"] == "user" else "AI"
                    conversation_summary += f"{role}: {msg['content'][:150]}\n"
                
                prompt = f"""你是一个专业的决策分析师。用户正在面临一个重要决策，你需要根据收集到的完整信息，规划出 2-4 个真正有意义的决策选项。

## 用户的决策问题
{initial_question}

## 信息收集过程中的对话
{conversation_summary}

## 收集到的结构化信息
- 决策背景：{json.dumps(collected_info.get('decision_context', {}), ensure_ascii=False)}
- 约束条件：{json.dumps(collected_info.get('user_constraints', {}), ensure_ascii=False)}
- 优先级：{json.dumps(collected_info.get('priorities', {}), ensure_ascii=False)}
- 顾虑：{collected_info.get('concerns', [])}

## 用户提到过的选项线索
{', '.join(all_hints) if all_hints else '用户没有明确提出选项'}

## 你的任务
请输出 2-4 个决策选项，以 JSON 格式返回：
{{
  "options": [
    {{
      "title": "选项的简洁标题（8-15字，清晰表达方向）",
      "description": "对这个选项的具体说明（30-80字，包含关键行动和预期路径）"
    }}
  ]
}}

## 要求
1. 如果用户提到了选项线索（如"考研""工作"），必须基于这些线索来润色和扩展，不要忽略用户的意图。例如用户说"考研"，你应该输出类似"全力备考研究生 — 用一年时间冲刺目标院校，提升学历竞争力"。
2. 每个选项的 title 必须是一个完整的、有方向感的短句，不能只是一两个字。
3. 每个选项的 description 必须具体说明这条路怎么走、核心行动是什么。
4. 选项之间要有明显的差异性，代表不同的决策方向。
5. 可以在用户线索基础上补充 1-2 个用户没想到但合理的选项。
6. 总数控制在 2-4 个，不要超过 4 个。
7. 只返回 JSON，不要有其他内容。"""

                messages = [
                    {"role": "system", "content": "你是一个资深决策分析师。你的核心能力是把模糊的决策意向转化为清晰、可执行、可推演的决策选项。你输出的每个选项都应该让用户一看就明白这条路意味着什么。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = llm_service.chat(messages, temperature=0.7, response_format="json_object")
                
                logger.info(f"[选项规划] LLM响应: {response[:300] if response else '(空)'}")
                
                if response and response.strip():
                    result = json.loads(response)
                    if "options" in result and isinstance(result["options"], list):
                        for opt in result["options"][:4]:
                            title = opt.get("title", "").strip()
                            desc = opt.get("description", "").strip()
                            # 质量校验：标题至少4个字，描述至少10个字
                            if len(title) >= 4 and len(desc) >= 10:
                                final_options.append({"title": title, "description": desc})
                
            except Exception as e:
                logger.error(f"LLM选项规划失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 降级方案：如果大模型完全失败，基于用户线索构建基本选项
        if not final_options:
            if all_hints:
                for hint in all_hints[:3]:
                    hint = hint.strip()
                    if len(hint) >= 2:
                        final_options.append({
                            "title": f"选择{hint}方向",
                            "description": f"以{hint}为核心方向推进，评估这条路径的长期影响"
                        })
            # 始终补充一个兜底选项
            if len(final_options) < 2:
                final_options.append({
                    "title": "暂缓决定，先小范围试探",
                    "description": "不急于做最终决定，先用低成本方式试探各个方向，收集更多信息后再做判断"
                })
            if len(final_options) < 2:
                final_options.append({
                    "title": "按当前倾向果断行动",
                    "description": "选择内心最倾向的方向立即执行，在实践中调整和优化"
                })
        
        return {
            "code": 200,
            "message": "选项规划完成",
            "data": {
                "ai_options": final_options
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"选项规划失败: {e}")
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
                    # 在线程池中执行阻塞操作，避免阻塞事件循环导致 WS 超时
                    import concurrent.futures
                    loop = asyncio.get_event_loop()
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        profile = await loop.run_in_executor(
                            pool, simulator.personality_test.load_profile, user_id
                        )
                except Exception:
                    profile = None
            await websocket.send_json({
                "type": "status",
                "stage": "profile_loaded",
                "content": "用户画像已加载，准备提取个人知识..."
            })

            # ── PKF 只做一次，缓存给所有选项复用 ──
            pkf_context_cached = ""
            await websocket.send_json({
                "type": "status",
                "stage": "pkf_knowledge",
                "content": "正在分析你的个人背景和决策因果关系..."
            })

            heartbeat_active = True
            async def send_pkf_heartbeat():
                tick = 0
                stages = [
                    "正在提取个人事实...",
                    "正在构建因果推理图...",
                    "正在注入知识图谱上下文...",
                ]
                while heartbeat_active:
                    await asyncio.sleep(3)
                    if not heartbeat_active:
                        break
                    try:
                        await websocket.send_json({
                            "type": "status",
                            "stage": "preparing",
                            "content": stages[min(tick, len(stages) - 1)]
                        })
                    except Exception:
                        break
                    tick += 1

            heartbeat_task = asyncio.create_task(send_pkf_heartbeat())
            try:
                from backend.decision.personal_knowledge_fusion import (
                    PersonalFactExtractor, CausalReasoningGraph
                )
                import concurrent.futures
                loop = asyncio.get_event_loop()

                def _run_pkf_once():
                    extractor = PersonalFactExtractor(user_id)
                    facts = extractor.extract_all()
                    # 用第一个选项的标题构建因果图（个人事实是通用的）
                    first_title = options[0].get("title", "") if options else ""
                    cg = CausalReasoningGraph(question, first_title, facts)
                    cg.build()
                    chains = cg.get_chains()
                    return facts, chains

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    facts, causal_chains = await loop.run_in_executor(pool, _run_pkf_once)

                pkf_context_cached = "个人事实：\n"
                for f in facts[:8]:
                    pkf_context_cached += f"- {f.to_text()}\n"
                pkf_context_cached += "\n因果推理链：\n"
                for chain in causal_chains[:4]:
                    chain_str = " -> ".join([e.cause for e in chain] + [chain[-1].effect])
                    pkf_context_cached += f"- {chain_str}\n"

                await websocket.send_json({
                    "type": "status",
                    "stage": "pkf_ready",
                    "content": f"已提取 {len(facts)} 条个人事实，构建 {len(causal_chains)} 条因果链（所有选项共用）"
                })
                simulator.lora_analyzer._pkf_context = pkf_context_cached
            except Exception as pkf_err:
                logger.warning(f"PKF-DS 增强失败，降级为普通推演: {pkf_err}")
                simulator.lora_analyzer._pkf_context = ""
            finally:
                heartbeat_active = False
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            simulated_options = []

            async def generate_option_timeline(i: int, option: dict):
                """为单个选项生成时间线并流式推送节点（PKF 已缓存）"""
                await websocket.send_json({
                    "type": "option_start",
                    "option_id": f"option_{i+1}",
                    "title": option.get("title", f"选项{i+1}")
                })

                # PKF 上下文直接复用缓存，不再重新提取
                simulator.lora_analyzer._pkf_context = pkf_context_cached

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

                all_titles = [o.get("title", "") for o in options]
                async for chunk in simulator.lora_analyzer.stream_timeline_generation(
                    user_id=user_id,
                    question=question,
                    option=option,
                    profile=profile,
                    num_events=12,
                    all_option_titles=all_titles
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

                # 如果增量解析完全失败（timeline 为空），才用 fallback 一次性解析
                if not timeline and timeline_data:
                    previous_event_id = None
                    for idx, e in enumerate(timeline_data):
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
                elif not timeline:
                    # 完全没有数据，重试一次
                    retry_timeline = await simulator.lora_analyzer.generate_timeline_with_lora(
                        user_id=user_id, question=question, option=option, profile=profile, num_events=12
                    )
                    if retry_timeline:
                        previous_event_id = None
                        for idx, e in enumerate(retry_timeline):
                            negative_impact = sum(abs(v) for v in e['impact'].values() if v < 0)
                            positive_impact = sum(v for v in e['impact'].values() if v > 0)
                            risk_tag = "high" if negative_impact >= 0.5 else ("low" if negative_impact <= 0.1 else "medium")
                            node = TimelineEvent(
                                event_id=f"{option_branch}_node_{idx+1}",
                                parent_event_id=previous_event_id,
                                month=e['month'], event=e['event'], impact=e['impact'],
                                probability=e['probability'],
                                event_type=simulator._infer_event_type(e['event']),
                                branch_group=option_branch, node_level=idx + 1,
                                risk_tag=risk_tag
                            )
                            previous_event_id = node.event_id
                            timeline.append(node)
                            await websocket.send_json({
                                "type": "node", "option_id": f"option_{i+1}",
                                "option_title": option['title'], "node": asdict(node)
                            })
                # 如果增量解析已经成功（timeline 不为空），不再重复发送节点

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
                # ── 智能分支节点选取 ──────────────────────────────────────────
                # 只从主链（非 fork）中选，策略：高风险节点优先 + 均匀间隔覆盖全程
                main_chain_nodes = [
                    n for n in timeline
                    if not str(getattr(n, 'branch_group', '')).endswith('_fork')
                ]
                candidate_parents = []
                seen_months: set = set()

                # 1. 高风险节点（最值得岔路）
                for n in main_chain_nodes:
                    if getattr(n, 'risk_tag', '') == 'high' and n.month not in seen_months:
                        candidate_parents.append(n)
                        seen_months.add(n.month)
                        if len(candidate_parents) >= 2:
                            break

                # 2. 均匀间隔补充（覆盖早中晚三段）
                step = max(2, len(main_chain_nodes) // 3)
                for n in main_chain_nodes[1::step]:
                    if n.month not in seen_months and len(candidate_parents) < 5:
                        candidate_parents.append(n)
                        seen_months.add(n.month)

                # 至少保证 2 个分叉点
                if len(candidate_parents) < 2 and main_chain_nodes:
                    for n in main_chain_nodes[:3]:
                        if n.month not in seen_months:
                            candidate_parents.append(n)
                            seen_months.add(n.month)

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
                        CREATE TABLE IF NOT EXISTS decision_records (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            simulation_id VARCHAR(100) UNIQUE NOT NULL,
                            user_id VARCHAR(100) NOT NULL,
                            question TEXT,
                            options_count INT DEFAULT 0,
                            recommendation TEXT,
                            timeline_data LONGTEXT,
                            created_at VARCHAR(50),
                            INDEX idx_user_id (user_id)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """)
                )
                db_session.commit()

                # 序列化完整的 timeline 数据
                timeline_json = json.dumps([
                    {
                        "option_id": opt.option_id,
                        "title": opt.title,
                        "description": opt.description,
                        "final_score": opt.final_score,
                        "risk_level": opt.risk_level,
                        "timeline": [asdict(e) for e in opt.timeline]
                    }
                    for opt in simulated_options
                ], ensure_ascii=False)

                db_session.execute(
                    __import__('sqlalchemy').text("""
                        INSERT INTO decision_records 
                        (simulation_id, user_id, question, options_count, recommendation, timeline_data, created_at)
                        VALUES (:sid, :uid, :q, :oc, :rec, :td, :ca)
                        ON DUPLICATE KEY UPDATE
                        recommendation = VALUES(recommendation),
                        timeline_data = VALUES(timeline_data)
                    """),
                    {
                        "sid": simulation_id,
                        "uid": user_id,
                        "q": question[:500],
                        "oc": len(options),
                        "rec": recommendation[:2000] if recommendation else "",
                        "td": timeline_json,
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
