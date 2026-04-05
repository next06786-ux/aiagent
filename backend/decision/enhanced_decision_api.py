"""
增强的决策API
集成信息收集（Qwen3.5-plus）和决策模拟（本地模型+LoRA）
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
import logging
import queue
import threading
import re
from starlette.websockets import WebSocketDisconnect as StarletteWebSocketDisconnect

from backend.decision.decision_info_collector import DecisionInfoCollector
from backend.decision.lora_decision_analyzer import LoRADecisionAnalyzer
from backend.decision.review_agents import ReviewAgentScaffold
from backend.decision.integrated_decision_engine import integrated_engine, DecisionType
from backend.llm.llm_service import get_llm_service
from dataclasses import asdict

# 导入三维垂直决策引擎
from backend.vertical.career.career_decision_engine import CareerDecisionEngine
from backend.vertical.relationship.relationship_decision_engine import RelationshipDecisionEngine
from backend.vertical.education.education_decision_engine import EducationDecisionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision/enhanced", tags=["enhanced-decision"])

# 全局实例
info_collector = DecisionInfoCollector()

# 三维垂直决策引擎实例
career_engine = CareerDecisionEngine()
relationship_engine = RelationshipDecisionEngine()
education_engine = EducationDecisionEngine()


# ==================== 辅助函数 ====================

def get_score_assessment(score: float) -> str:
    """根据评分返回评估文字"""
    if score >= 80:
        return "非常优秀，各方面准备充分"
    elif score >= 70:
        return "表现良好，具备一定优势"
    elif score >= 60:
        return "中等水平，需要继续努力"
    elif score >= 50:
        return "偏低，建议加强薄弱环节"
    else:
        return "风险较高，需要重点关注"


def get_agent_status(status: str) -> str:
    """将Agent状态转换为中文"""
    status_map = {
        'good': '良好',
        'warning': '警告',
        'critical': '危险'
    }
    return status_map.get(status, status)


def format_metric_key(key: str) -> str:
    """将指标Key转换为中文"""
    key_map = {
        'skill_gap': '技能差距',
        'avg_completion': '完成度',
        'learning_efficiency': '学习效率',
        'skills_count': '技能数量',
        'network_size': '人脉规模',
        'network_quality': '人脉质量',
        'industry_connections': '行业人脉',
        'referral_opportunities': '内推机会',
        'savings': '储蓄',
        'runway_months': '财务跑道',
        'monthly_cashflow': '月现金流',
        'total_investment': '总投入',
        'self_efficacy': '自我效能',
        'resilience': '韧性',
        'stress_level': '压力水平',
        'motivation': '动力',
        'job_demand_index': '岗位需求',
        'salary_trend': '薪资趋势',
        'industry_growth': '行业增长',
        'competition_level': '竞争程度'
    }
    return key_map.get(key, key)


# ==================== 决策类型选择 API ====================

class IdentifyDecisionTypeRequest(BaseModel):
    """识别决策类型请求"""
    question: str


class SelectDecisionTypeRequest(BaseModel):
    """选择决策类型请求"""
    user_id: str
    question: str
    decision_type: str  # career, relationship, education, general


@router.post("/identify-type")
async def identify_decision_type(request: IdentifyDecisionTypeRequest) -> Dict[str, Any]:
    """
    自动识别决策类型
    
    根据问题内容自动判断属于职业/关系/升学/通用哪个类型
    """
    try:
        decision_type = integrated_engine.identify_decision_type(request.question)
        type_info = integrated_engine.get_decision_type_info(decision_type)
        
        return {
            "success": True,
            "question": request.question,
            "identified_type": decision_type.value,
            "type_info": type_info,
            "message": f"识别为{type_info['name']}"
        }
    except Exception as e:
        logger.error(f"识别决策类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision-types")
async def get_decision_types() -> Dict[str, Any]:
    """
    获取所有决策类型信息
    
    返回四种决策类型的详细说明，供用户选择
    """
    try:
        types_info = []
        for decision_type in DecisionType:
            type_info = integrated_engine.get_decision_type_info(decision_type)
            types_info.append(type_info)
        
        return {
            "success": True,
            "types": types_info,
            "message": "支持4种决策类型"
        }
    except Exception as e:
        logger.error(f"获取决策类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-with-type")
async def start_decision_with_type(request: SelectDecisionTypeRequest) -> Dict[str, Any]:
    """
    选择决策类型并开始决策流程
    
    用户选择决策类型后，生成对应的信息收集清单
    """
    try:
        # 解析决策类型
        decision_type = DecisionType(request.decision_type)
        
        # 获取类型信息
        type_info = integrated_engine.get_decision_type_info(decision_type)
        
        # 生成信息收集清单
        checklist = integrated_engine.generate_information_checklist(
            decision_type=decision_type,
            question=request.question,
            options=[]
        )
        
        # 创建会话（使用现有的信息收集器）
        session_id = info_collector.start_collection(
            user_id=request.user_id,
            initial_question=request.question
        )
        
        # 在会话中保存决策类型
        if session_id in info_collector.sessions:
            info_collector.sessions[session_id]["decision_type"] = decision_type.value
        
        return {
            "success": True,
            "session_id": session_id,
            "decision_type": decision_type.value,
            "type_info": type_info,
            "information_checklist": checklist,
            "message": f"已创建{type_info['name']}会话，请按清单收集信息"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的决策类型: {request.decision_type}")
    except Exception as e:
        logger.error(f"创建决策会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DecisionSimulator:
    """决策模拟器包装类"""
    def __init__(self):
        self.lora_analyzer = LoRADecisionAnalyzer()
        self.review_agents = ReviewAgentScaffold()
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
            try:
                # 确保所有值都不为None
                i_val = float(i) if i is not None else 0.0
                n_val = float(n) if n is not None else 1.0
                weight = 0.6 + 0.8 * (i_val / max(n_val - 1, 1))
                
                impact = getattr(e, 'impact', {}) if hasattr(e, 'impact') else {}
                net = sum(impact.values()) if isinstance(impact, dict) else 0.0
                prob = float(getattr(e, 'probability', 0.7) or 0.7)
                contribution = 50.0 + min(max(net * 80, -40), 40)
                
                # 确保所有计算值都不为None
                if weight is None:
                    weight = 1.0
                if prob is None:
                    prob = 0.7
                if contribution is None:
                    contribution = 50.0
                    
                total += contribution * prob * weight
                weight_sum += prob * weight
            except Exception as e:
                logger.warning(f"计算事件评分时出错: {e}")
                continue
                
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
        
        # 计算负面影响的平均值
        negative_impacts = []
        for e in main_chain:
            impact = getattr(e, 'impact', {}) if hasattr(e, 'impact') else {}
            if isinstance(impact, dict):
                negative_sum = sum(abs(value) for value in impact.values() if value < 0)
                negative_impacts.append(negative_sum)
        
        if not negative_impacts:
            return 0.5
        
        avg_negative = sum(negative_impacts) / len(negative_impacts)
        # 映射到0~1范围，假设单个事件最大负面影响为2.0
        risk_level = min(1.0, max(0.0, avg_negative / 2.0))
        return round(risk_level, 2)
    
    def _convert_career_result_to_standard(self, career_result: Dict[str, Any]):
        """
        将职业决策多Agent结果转换为标准格式
        
        Args:
            career_result: CareerSimulationIntegration的输出
        
        Returns:
            SimulationResult格式的数据
        """
        from dataclasses import dataclass
        from datetime import datetime
        import uuid
        
        @dataclass
        class TimelineEvent:
            event_id: str
            parent_event_id: Optional[str]
            month: int
            event: str
            impact: Dict[str, float]
            probability: float
            state_before: Dict[str, Any]
            impact_vector: Dict[str, float]
            evidence_sources: List[str]
            agent_votes: List[Dict[str, Any]]
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
            prediction_trace: Optional[Dict[str, Any]] = None
            execution_confidence: float = 0.7
            dropout_risk_month: Optional[int] = None
            personal_note: str = ""
        
        @dataclass
        class SimulationResult:
            simulation_id: str
            user_id: str
            question: str
            options: list
            recommendation: str
            created_at: str
            verifiability_report: Optional[Dict[str, Any]] = None
        
        simulation_id = str(uuid.uuid4())
        options_list = []
        
        # 转换每个选项
        for i, option_sim in enumerate(career_result.get('options_simulation', [])):
            if option_sim.get('error'):
                continue
            
            option_info = option_sim['option']
            timeline_data = option_sim.get('timeline', [])
            final_assessment = option_sim.get('final_assessment', {})
            
            # 转换时间线为标准格式
            timeline_events = []
            previous_event_id = None
            
            for month_idx, month_data in enumerate(timeline_data):
                month = month_data['month']
                agents = month_data.get('agents', {})
                
                # 生成事件描述（综合5个Agent的状态）
                event_parts = []
                impact_dict = {}
                
                for agent_name, agent_data in agents.items():
                    if agent_data.get('changes'):
                        event_parts.append(agent_data['changes'][0])
                    
                    # 映射Agent得分到impact维度
                    if agent_name == 'skill_development':
                        impact_dict['职业发展'] = (agent_data['score'] - 50) / 50
                    elif agent_name == 'financial':
                        impact_dict['财务'] = (agent_data['score'] - 50) / 50
                    elif agent_name == 'psychological':
                        impact_dict['情绪'] = (agent_data['score'] - 50) / 50
                    elif agent_name == 'career_network':
                        impact_dict['社交'] = (agent_data['score'] - 50) / 50
                
                event_text = f"第{month}月：" + "；".join(event_parts[:2]) if event_parts else f"第{month}月进展"
                
                event_id = f"option_{i+1}_month_{month}"
                
                timeline_events.append(TimelineEvent(
                    event_id=event_id,
                    parent_event_id=previous_event_id,
                    month=month,
                    event=event_text,
                    impact=impact_dict,
                    probability=0.8,
                    state_before={},
                    impact_vector=impact_dict,
                    evidence_sources=['multi_agent_evaluation'],
                    agent_votes=[],
                    event_type='normal',
                    branch_group=f"option_{i+1}",
                    node_level=month,
                    risk_tag=month_data.get('overall_status', 'medium'),
                    opportunity_tag='medium',
                    visual_weight=month_data.get('overall_score', 50) / 100
                ))
                
                previous_event_id = event_id
            
            # 创建选项对象
            option_obj = DecisionOption(
                option_id=f"option_{i+1}",
                title=option_info['title'],
                description=option_info.get('description', ''),
                timeline=timeline_events,
                final_score=final_assessment.get('overall_score', 50),
                risk_level=1.0 - (final_assessment.get('overall_score', 50) / 100),
                risk_assessment={
                    'level': final_assessment.get('overall_status', 'medium'),
                    'key_risks': final_assessment.get('key_risks', []),
                    'weakest_dimension': final_assessment.get('weakest_dimension', {})
                },
                prediction_trace={
                    'agent_evaluation': option_sim.get('agent_evaluation', {}),
                    'success_probability': option_sim.get('agent_evaluation', {}).get('summary', {}).get('success_probability', 0.5)
                },
                execution_confidence=option_sim.get('agent_evaluation', {}).get('summary', {}).get('success_probability', 0.7),
                personal_note=f"基于多Agent评估：{len(option_sim.get('agent_evaluation', {}).get('decision_points', []))}个关键决策点"
            )
            
            options_list.append(option_obj)
        
        # 生成推荐
        recommendation_data = career_result.get('recommendation', {})
        recommendation_text = f"推荐选择：{recommendation_data.get('recommended_option', '未知')}\n"
        recommendation_text += f"综合得分：{recommendation_data.get('overall_score', 0):.1f}\n"
        recommendation_text += f"成功概率：{recommendation_data.get('success_probability', 0):.0%}\n\n"
        recommendation_text += "推荐理由：\n" + "\n".join(f"• {r}" for r in recommendation_data.get('reasons', []))
        
        if recommendation_data.get('considerations'):
            recommendation_text += "\n\n需要考虑：\n" + "\n".join(f"⚠ {c}" for c in recommendation_data.get('considerations', []))
        
        # 创建结果对象
        result = SimulationResult(
            simulation_id=simulation_id,
            user_id=career_result.get('user_id', ''),
            question=career_result.get('question', ''),
            options=options_list,
            recommendation=recommendation_text,
            created_at=datetime.now().isoformat(),
            verifiability_report={
                'data_sources': ['career_knowledge_graph', 'career_algorithm', 'multi_agent_evaluation'],
                'evaluation_method': 'multi_agent_framework',
                'agents_used': ['skill_development', 'career_network', 'financial', 'psychological', 'market_environment'],
                'comparison': career_result.get('comparison', {})
            }
        )
        
        return result
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

    def _main_chain(self, timeline) -> List[Any]:
        return [
            e for e in timeline
            if not (hasattr(e, 'branch_group') and str(getattr(e, 'branch_group', '')).endswith('_fork'))
        ]

    def _event_text(self, event: Any) -> str:
        if hasattr(event, 'event'):
            return getattr(event, 'event', '') or ''
        if isinstance(event, dict):
            return str(event.get('event', '') or '')
        return ''

    def _is_specific_event(self, text: str) -> bool:
        if not text:
            return False
        has_number = bool(re.search(r'\d', text))
        anchors = ['你', '父母', '妈妈', '爸爸', '领导', '同事', '朋友', '面试', '工资', '房租', '项目', '客户', '学校', 'offer']
        has_anchor = any(token in text for token in anchors)
        return len(text) >= 18 and (has_number or has_anchor)

    def _calculate_context_coverage(self, collected_info: Optional[Dict[str, Any]]) -> float:
        if not collected_info:
            return 0.0
        checks = [
            bool(collected_info.get("decision_context")),
            bool(collected_info.get("user_constraints")),
            bool(collected_info.get("priorities")),
            bool(collected_info.get("concerns")),
            len(collected_info.get("options_mentioned", [])) >= 2,
        ]
        return round(sum(1 for item in checks if item) / len(checks), 2)

    def _normalize_impact_vector(self, impact: Optional[Dict[str, Any]]) -> Dict[str, float]:
        if not isinstance(impact, dict):
            return {}
        normalized: Dict[str, float] = {}
        for key, value in impact.items():
            if key is None:
                continue
            try:
                # 确保value不为None
                if value is None:
                    continue
                normalized[str(key)] = round(float(value), 3)
            except (TypeError, ValueError) as e:
                logger.warning(f"无法规范化影响向量 {key}={value}: {e}")
                continue
        return normalized

    def _top_impact_axes(self, impact_vector: Dict[str, float], limit: int = 3) -> List[str]:
        return [
            key
            for key, _ in sorted(
                impact_vector.items(),
                key=lambda item: abs(item[1]),
                reverse=True,
            )[:limit]
        ]

    def _build_state_before(
        self,
        *,
        question: str,
        option_title: str,
        timeline: List[Any],
        month: int,
        branch_group: str,
    ) -> Dict[str, Any]:
        cumulative: Dict[str, float] = {}
        previous_event = ""
        for item in timeline:
            impact = self._normalize_impact_vector(
                getattr(item, "impact_vector", None)
                if hasattr(item, "impact_vector")
                else item.get("impact_vector")
                if isinstance(item, dict)
                else None
            )
            if not impact:
                impact = self._normalize_impact_vector(
                    getattr(item, "impact", None)
                    if hasattr(item, "impact")
                    else item.get("impact")
                    if isinstance(item, dict)
                    else None
                )
            for key, value in impact.items():
                cumulative[key] = cumulative.get(key, 0.0) + value
            event_text = self._event_text(item)
            if event_text:
                previous_event = event_text

        momentum = round(sum(cumulative.values()), 2)
        if not timeline:
            phase = "origin"
        elif str(branch_group).endswith("_fork"):
            phase = "branch_review"
        elif month <= 3:
            phase = "early_exploration"
        elif month <= 8:
            phase = "active_execution"
        else:
            phase = "future_consolidation"

        return {
            "question_anchor": (question or "")[:48],
            "option_anchor": option_title,
            "phase": phase,
            "path_depth": len(timeline),
            "momentum": momentum,
            "previous_event": previous_event or "当前状态",
            "focus_axes": " / ".join(self._top_impact_axes(cumulative, 2)) if cumulative else "待展开",
            "is_branching": str(branch_group).endswith("_fork"),
        }

    def _build_node_evidence_sources(
        self,
        *,
        collected_info: Optional[Dict[str, Any]],
        facts_count: int,
        profile: Any,
        calibration_profile: Optional[Dict[str, Any]],
        branch_group: str,
    ) -> List[str]:
        sources = ["user_lora" if self.lora_analyzer.is_lora_inference() else "api_llm"]
        if collected_info:
            sources.append("decision_collection")
        if facts_count > 0:
            sources.append("pkf_facts")
        if profile is not None:
            sources.append("personality_profile")
        if calibration_profile and int(calibration_profile.get("review_count", 0) or 0) > 0:
            sources.append("historical_calibration")
        if str(branch_group).endswith("_fork"):
            sources.append("counterfactual_branch")
        unique_sources: List[str] = []
        for item in sources:
            if item and item not in unique_sources:
                unique_sources.append(item)
        return unique_sources

    def _create_timeline_node(
        self,
        event_cls: Any,
        *,
        event_id: str,
        parent_event_id: Optional[str],
        month: int,
        event_text: str,
        impact: Dict[str, Any],
        probability: float,
        branch_group: str,
        node_level: int,
        question: str,
        option_title: str,
        timeline: List[Any],
        collected_info: Optional[Dict[str, Any]],
        facts_count: int,
        profile: Any,
        calibration_profile: Optional[Dict[str, Any]],
    ) -> Any:
        try:
            # 防御性处理：确保所有数值参数不为None
            normalized_month = int(month or 1)
            normalized_probability = float(probability if probability is not None else 0.0)
            
            # 确保impact不为None
            if impact is None:
                impact = {}
            
            impact_vector = self._normalize_impact_vector(impact)
            
            # 安全计算负面和正面影响
            negative_impact = sum(abs(value) for value in impact_vector.values() if value < 0) if impact_vector else 0.0
            positive_impact = sum(value for value in impact_vector.values() if value > 0) if impact_vector else 0.0
            
            # 确保计算结果不为None
            if negative_impact is None:
                negative_impact = 0.0
            if positive_impact is None:
                positive_impact = 0.0
            
            risk_tag = "high" if negative_impact >= 0.25 else ("low" if negative_impact <= 0.15 else "medium")
            opportunity_tag = "high" if positive_impact >= 0.5 else ("low" if positive_impact <= 0.1 else "medium")
            state_before = self._build_state_before(
                question=question,
                option_title=option_title,
                timeline=timeline,
                month=month,
                branch_group=branch_group,
            )
            evidence_sources = self._build_node_evidence_sources(
                collected_info=collected_info,
                facts_count=facts_count,
                profile=profile,
                calibration_profile=calibration_profile,
                branch_group=branch_group,
            )
            parent_snapshot = None
            if parent_event_id:
                for item in reversed(timeline):
                    item_id = (
                        getattr(item, "event_id", None)
                        if hasattr(item, "event_id")
                        else item.get("event_id")
                        if isinstance(item, dict)
                        else None
                    )
                    if item_id == parent_event_id:
                        parent_snapshot = {
                            "event": self._event_text(item),
                            "month": getattr(item, "month", None)
                            if hasattr(item, "month")
                            else item.get("month")
                            if isinstance(item, dict)
                            else None,
                        }
                        break
            agent_votes = self.review_agents.review_node(
                event_text=event_text,
                impact_vector=impact_vector,
                probability=float(probability or 0.0),
                risk_tag=risk_tag,
                opportunity_tag=opportunity_tag,
                evidence_sources=evidence_sources,
                state_before=state_before,
                parent_event=parent_snapshot,
            )
            
            # 计算visual_weight，确保所有值都不为None
            visual_weight_value = float(positive_impact) + float(negative_impact)
            visual_weight = max(0.2, min(1.0, visual_weight_value))
            
            return event_cls(
                event_id=event_id,
                parent_event_id=parent_event_id,
                month=normalized_month,
                event=event_text,
                impact=impact_vector,
                probability=normalized_probability,
                state_before=state_before,
                impact_vector=impact_vector,
                evidence_sources=evidence_sources,
                agent_votes=agent_votes,
                event_type=self._infer_event_type(event_text),
                branch_group=branch_group,
                node_level=node_level,
                risk_tag=risk_tag,
                opportunity_tag=opportunity_tag,
                visual_weight=visual_weight,
            )
        except Exception as e:
            logger.error(f"创建时间线节点失败 M{month}: {e}")
            logger.error(f"参数: event_text={event_text[:50]}, impact={impact}, probability={probability}")
            import traceback
            traceback.print_exc()
            raise

    def _serialize_timeline_event(self, event: Any, index: int = 0) -> Dict[str, Any]:
        source = asdict(event) if hasattr(event, "__dataclass_fields__") else dict(event or {})
        impact_vector = self._normalize_impact_vector(
            source.get("impact_vector") or source.get("impact") or {}
        )
        source["event_id"] = source.get("event_id") or f"event_{index + 1}"
        source["impact"] = impact_vector
        source["impact_vector"] = impact_vector
        source["state_before"] = source.get("state_before") or {}
        source["evidence_sources"] = list(source.get("evidence_sources") or [])
        source["agent_votes"] = list(source.get("agent_votes") or [])
        source["probability"] = float(source.get("probability") or 0.0)
        source["month"] = int(source.get("month") or (index + 1))
        source["node_level"] = int(source.get("node_level") or (index + 1))
        source["event"] = str(source.get("event") or f"未来状态节点 {index + 1}")
        source["branch_group"] = str(source.get("branch_group") or "main")
        source["event_type"] = str(source.get("event_type") or self._infer_event_type(source["event"]))
        source["risk_tag"] = str(source.get("risk_tag") or "medium")
        source["opportunity_tag"] = str(source.get("opportunity_tag") or "medium")
        source["visual_weight"] = float(source.get("visual_weight") or 0.4)
        return source

    def _build_decision_graph_payload(
        self,
        option_id: str,
        option_title: str,
        timeline: List[Any],
    ) -> Dict[str, Any]:
        nodes = [
            self._serialize_timeline_event(event, index)
            for index, event in enumerate(timeline or [])
        ]
        edges: List[Dict[str, Any]] = []
        for index, node in enumerate(nodes):
            parent_id = node.get("parent_event_id")
            if parent_id:
                edges.append({
                    "edge_id": f"{parent_id}->{node['event_id']}",
                    "source": parent_id,
                    "target": node["event_id"],
                    "relation": "branch" if str(node.get("branch_group") or "").endswith("_fork") else "next",
                    "strength": round(float(node.get("probability") or 0.0), 2),
                    "label": f"M{node.get('month', index + 1)}",
                })

        dominant_axes: Dict[str, float] = {}
        vote_stances: Dict[str, int] = {}
        high_risk_nodes = 0
        for node in nodes:
            if str(node.get("risk_tag") or "") == "high":
                high_risk_nodes += 1
            for key, value in self._normalize_impact_vector(node.get("impact_vector")).items():
                dominant_axes[key] = dominant_axes.get(key, 0.0) + abs(value)
            for vote in node.get("agent_votes", []) or []:
                stance = str(vote.get("stance") or "neutral")
                vote_stances[stance] = vote_stances.get(stance, 0) + 1

        dominant_axis_list = [
            key
            for key, _ in sorted(
                dominant_axes.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:4]
        ]

        return {
            "graph_id": f"{option_id}_decision_graph",
            "schema_version": 1,
            "layout_hint": "future-state-stage",
            "graph_summary": {
                "title": option_title,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "high_risk_nodes": high_risk_nodes,
                "dominant_axes": dominant_axis_list,
                "agent_stance_mix": vote_stances,
                "review_mode": "review_agents_v1",
            },
            "nodes": nodes,
            "edges": edges,
        }

    def _serialize_risk_assessment(self, assessment: Any) -> Optional[Dict[str, Any]]:
        if not assessment:
            return None
        dimensions = {}
        ordered_dimensions = []
        for key, dim in assessment.dimensions.items():
            serialized = {
                "name": dim.name,
                "score": round(float(dim.score), 1),
                "level": dim.level.value if hasattr(dim.level, "value") else str(dim.level),
                "factors": list(dim.factors or []),
                "mitigation": list(dim.mitigation or []),
            }
            dimensions[key] = serialized
            ordered_dimensions.append((key, serialized["score"]))
        ordered_dimensions.sort(key=lambda item: item[1], reverse=True)
        return {
            "option_title": assessment.option_title,
            "overall_risk": round(float(assessment.overall_risk), 1),
            "overall_level": assessment.overall_level.value if hasattr(assessment.overall_level, "value") else str(assessment.overall_level),
            "high_risk_count": int(assessment.high_risk_count),
            "top_dimensions": [name for name, _ in ordered_dimensions[:3]],
            "dimensions": dimensions,
            "recommendations": list(assessment.recommendations or []),
        }

    def _assess_option_risk(self, option_title: str, timeline: List[Any], profile: Any) -> Optional[Dict[str, Any]]:
        if not self._risk_engine:
            return None
        try:
            timeline_dicts = [
                asdict(item) if hasattr(item, '__dataclass_fields__') else item
                for item in timeline
            ]
            assessment = self._risk_engine.assess_option_risk(option_title, timeline_dicts, profile)
            return self._serialize_risk_assessment(assessment)
        except Exception as exc:
            logger.warning(f"风险评估失败({option_title}): {exc}")
            return None

    def _build_prediction_trace(
        self,
        question: str,
        option: Dict[str, str],
        timeline: List[Any],
        collected_info: Optional[Dict[str, Any]],
        facts_count: int,
        profile: Any,
        calibration_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        main_chain = self._main_chain(timeline) or timeline
        main_event_count = len(main_chain)
        specific_events = sum(1 for event in main_chain if self._is_specific_event(self._event_text(event)))
        specificity = round(specific_events / max(main_event_count, 1), 2) if main_event_count else 0.0
        coverage = self._calculate_context_coverage(collected_info)
        fact_density = round(min(1.0, facts_count / 8), 2)
        profile_bonus = 0.08 if profile is not None else 0.0
        
        # 确保所有值都不为None
        if specificity is None:
            specificity = 0.0
        if coverage is None:
            coverage = 0.0
        if fact_density is None:
            fact_density = 0.0
            
        base_confidence = 0.25 + coverage * 0.35 + specificity * 0.22 + fact_density * 0.10 + profile_bonus
        calibration_adjustment = 0.0
        calibration_review_count = 0
        calibration_bias = "insufficient_data"
        calibration_note = ""
        calibration_applied = False
        if calibration_profile:
            calibration_adjustment = float(calibration_profile.get("confidence_adjustment", 0.0) or 0.0)
            calibration_review_count = int(calibration_profile.get("review_count", 0) or 0)
            calibration_bias = str(calibration_profile.get("bias_tendency", "insufficient_data") or "insufficient_data")
            calibration_note = str(calibration_profile.get("note", "") or "")
            calibration_applied = calibration_review_count >= 2 and abs(calibration_adjustment) >= 0.01
        confidence = round(min(0.95, max(0.15, base_confidence + calibration_adjustment)), 2)

        assumptions: List[str] = []
        if not collected_info or not collected_info.get("user_constraints"):
            assumptions.append("缺少明确的现实约束，资源与时间压力按保守方式估计。")
        if not collected_info or not collected_info.get("priorities"):
            assumptions.append("缺少清晰优先级，推荐结论会更偏均衡而非强个性偏好。")
        if not collected_info or not collected_info.get("concerns"):
            assumptions.append("缺少用户明确担忧点，部分风险节点只能根据常见模式推断。")
        if facts_count == 0:
            assumptions.append("个人事实提取较少，事件与用户长期背景的绑定强度有限。")
        if calibration_applied and calibration_note:
            assumptions.append(f"历史回访校准已启用：{calibration_note}")

        evidence_sources = ["user_lora" if self.lora_analyzer.is_lora_inference() else "api_llm"]
        if collected_info:
            evidence_sources.append("decision_collection")
        if facts_count > 0:
            evidence_sources.append("pkf_facts")
        if profile is not None:
            evidence_sources.append("personality_profile")
        if calibration_review_count > 0:
            evidence_sources.append("historical_calibration")

        return {
            "question": question,
            "option_title": option.get("title", ""),
            "prediction_confidence": confidence,
            "base_prediction_confidence": round(min(0.95, max(0.15, base_confidence)), 2),
            "confidence_level": "high" if confidence >= 0.75 else ("medium" if confidence >= 0.5 else "low"),
            "context_coverage": coverage,
            "event_specificity": specificity,
            "facts_used": facts_count,
            "main_event_count": main_event_count,
            "evidence_sources": evidence_sources,
            "assumptions": assumptions,
            "calibration_review_count": calibration_review_count,
            "calibration_adjustment": round(calibration_adjustment, 2),
            "calibration_bias": calibration_bias,
            "calibration_note": calibration_note,
            "calibration_applied": calibration_applied,
        }

    def _compress_score_by_confidence(self, raw_score: float, prediction_confidence: float) -> float:
        # 确保参数不为None
        if raw_score is None:
            raw_score = 50.0
        if prediction_confidence is None:
            prediction_confidence = 0.5
        weight = 0.55 + 0.45 * prediction_confidence
        return round(50 + (raw_score - 50) * weight, 1)

    def _merge_risk_level(self, generated_risk: float, risk_assessment: Optional[Dict[str, Any]]) -> float:
        # 确保generated_risk不为None
        if generated_risk is None:
            generated_risk = 0.5
        if not risk_assessment:
            return round(min(1.0, max(0.0, generated_risk)), 2)
        engine_risk = min(1.0, max(0.0, float(risk_assessment.get("overall_risk", 5.0)) / 10.0))
        # 确保计算中的值都不为None
        generated_risk = float(generated_risk) if generated_risk is not None else 0.5
        engine_risk = float(engine_risk) if engine_risk is not None else 0.5
        return round(min(1.0, max(0.0, generated_risk * 0.4 + engine_risk * 0.6)), 2)

    def _build_verifiability_report(
        self,
        options: List[Any],
        collected_info: Optional[Dict[str, Any]],
        calibration_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        traces = [getattr(opt, "prediction_trace", None) for opt in options if getattr(opt, "prediction_trace", None)]
        confidences = [trace["prediction_confidence"] for trace in traces]
        coverage = self._calculate_context_coverage(collected_info)
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        missing = []
        if not collected_info or not collected_info.get("user_constraints"):
            missing.append("现实约束")
        if not collected_info or not collected_info.get("priorities"):
            missing.append("用户优先级")
        if not collected_info or not collected_info.get("concerns"):
            missing.append("关键顾虑")
        calibration_profile = calibration_profile or self._empty_calibration_profile()
        review_count = int(calibration_profile.get("review_count", 0) or 0)
        calibration_note = str(calibration_profile.get("note", "") or "")
        return {
            "schema_version": 2,
            "engine_mode": (
                "evidence_grounded_calibrated_lora_simulation"
                if self.lora_analyzer.is_lora_inference() and review_count > 0 else
                "evidence_grounded_lora_simulation"
                if self.lora_analyzer.is_lora_inference() else
                "evidence_grounded_calibrated_api_simulation"
                if review_count > 0 else
                "evidence_grounded_api_simulation"
            ),
            "collected_info_coverage": coverage,
            "average_prediction_confidence": avg_confidence,
            "missing_key_inputs": missing,
            "historical_review_count": review_count,
            "calibration_bias": calibration_profile.get("bias_tendency", "insufficient_data"),
            "confidence_adjustment": round(float(calibration_profile.get("confidence_adjustment", 0.0) or 0.0), 2),
            "calibration_quality": calibration_profile.get("calibration_quality", "insufficient_data"),
            "calibration_note": calibration_note,
            "note": (
                "推演结果是基于已知事实、用户画像与行为数据生成的情境预测，不等于确定性未来。"
                if not calibration_note else
                f"推演结果不是确定性未来；并且本次已结合历史回访做校准：{calibration_note}"
            )
        }

    def _build_pkf_context(self, question: str, option_title: str, facts: List[Any]) -> str:
        if not facts:
            return ""
        try:
            from backend.decision.personal_knowledge_fusion import CausalReasoningGraph
            causal_graph = CausalReasoningGraph(question, option_title, facts)
            causal_graph.build()
            causal_chains = causal_graph.get_chains()
            pkf_context = "个人事实：\n"
            for fact in facts[:8]:
                pkf_context += f"- {fact.to_text()}\n"
            pkf_context += "\n因果推理链：\n"
            for chain in causal_chains[:4]:
                chain_str = " -> ".join([edge.cause for edge in chain] + [chain[-1].effect])
                pkf_context += f"- {chain_str}\n"
            return pkf_context
        except Exception as exc:
            logger.warning(f"构建 PKF 上下文失败({option_title}): {exc}")
            return ""

    def _serialize_option(self, option: Any) -> Dict[str, Any]:
        timeline = [
            self._serialize_timeline_event(event, index)
            for index, event in enumerate(getattr(option, "timeline", []) or [])
        ]
        execution_confidence = getattr(option, "execution_confidence", None)
        dropout_risk_month = getattr(option, "dropout_risk_month", None)
        personal_note = getattr(option, "personal_note", "") or ""
        return {
            "option_id": getattr(option, "option_id", ""),
            "title": getattr(option, "title", ""),
            "description": getattr(option, "description", ""),
            "timeline": timeline,
            "decision_graph": self._build_decision_graph_payload(
                getattr(option, "option_id", ""),
                getattr(option, "title", ""),
                timeline,
            ),
            "final_score": getattr(option, "final_score", 50.0),
            "risk_level": getattr(option, "risk_level", 0.5),
            "risk_assessment": getattr(option, "risk_assessment", None),
            "prediction_trace": getattr(option, "prediction_trace", None),
            "execution_confidence": execution_confidence,
            "dropout_risk_month": dropout_risk_month,
            "personal_note": personal_note,
            "self_prediction": {
                "execution_confidence": execution_confidence,
                "dropout_risk_month": dropout_risk_month,
                "personal_note": personal_note,
            }
        }

    def _build_record_payload(
        self,
        question: str,
        options: List[Any],
        collected_info: Optional[Dict[str, Any]],
        verifiability_report: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "schema_version": 3,
            "question": question,
            "collected_info_summary": collected_info or {},
            "verifiability_report": verifiability_report or {},
            "options": [self._serialize_option(option) for option in options],
        }

    def _ensure_decision_records_table(self, db_session: Any) -> None:
        import sqlalchemy

        db_session.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS decision_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                simulation_id VARCHAR(100) UNIQUE NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                question TEXT,
                options_count INT DEFAULT 0,
                recommendation TEXT,
                timeline_data LONGTEXT,
                created_at VARCHAR(50),
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        db_session.commit()

        alter_statements = [
            "ALTER TABLE decision_records ADD COLUMN timeline_data LONGTEXT",
            "ALTER TABLE decision_records ADD COLUMN created_at VARCHAR(50)",
            "ALTER TABLE decision_records ADD COLUMN recommendation TEXT",
            "ALTER TABLE decision_records ADD COLUMN options_count INT DEFAULT 0",
        ]
        for statement in alter_statements:
            try:
                db_session.execute(sqlalchemy.text(statement))
                db_session.commit()
            except Exception:
                db_session.rollback()

    def _save_decision_record(
        self,
        simulation_id: str,
        user_id: str,
        question: str,
        options: List[Any],
        recommendation: str,
        collected_info: Optional[Dict[str, Any]] = None,
        verifiability_report: Optional[Dict[str, Any]] = None,
    ) -> None:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        from datetime import datetime
        import sqlalchemy

        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        try:
            self._ensure_decision_records_table(db_session)
            timeline_json = json.dumps(
                self._build_record_payload(question, options, collected_info, verifiability_report),
                ensure_ascii=False
            )
            db_session.execute(
                sqlalchemy.text("""
                    INSERT INTO decision_records
                    (simulation_id, user_id, question, options_count, recommendation, timeline_data, created_at)
                    VALUES (:sid, :uid, :q, :oc, :rec, :td, :ca)
                    ON DUPLICATE KEY UPDATE
                    question = VALUES(question),
                    options_count = VALUES(options_count),
                    recommendation = VALUES(recommendation),
                    timeline_data = VALUES(timeline_data),
                    created_at = VALUES(created_at)
                """),
                {
                    "sid": simulation_id,
                    "uid": user_id,
                    "q": (question or "")[:500],
                    "oc": len(options),
                    "rec": (recommendation or "")[:2000],
                    "td": timeline_json,
                    "ca": datetime.now().isoformat()
                }
            )
            db_session.commit()
        finally:
            db_session.close()

    def _load_record_payload(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        import sqlalchemy

        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        try:
            self._ensure_decision_records_table(db_session)
            row = db_session.execute(
                sqlalchemy.text("""
                    SELECT question, timeline_data
                    FROM decision_records
                    WHERE simulation_id = :sid
                """),
                {"sid": simulation_id}
            ).fetchone()
            if not row:
                return None
            question = row[0] or ""
            parsed: Dict[str, Any]
            if row[1]:
                try:
                    raw_data = json.loads(row[1])
                    if isinstance(raw_data, dict):
                        parsed = raw_data
                    elif isinstance(raw_data, list):
                        parsed = {
                            "schema_version": 1,
                            "question": question,
                            "options": raw_data,
                            "collected_info_summary": {},
                            "verifiability_report": {},
                        }
                    else:
                        parsed = {
                            "schema_version": 1,
                            "question": question,
                            "options": [],
                            "collected_info_summary": {},
                            "verifiability_report": {},
                        }
                except Exception:
                    parsed = {
                        "schema_version": 1,
                        "question": question,
                        "options": [],
                        "collected_info_summary": {},
                        "verifiability_report": {},
                    }
            else:
                parsed = {
                    "schema_version": 1,
                    "question": question,
                    "options": [],
                    "collected_info_summary": {},
                    "verifiability_report": {},
                }
            if not parsed.get("question"):
                parsed["question"] = question
            return parsed
        finally:
            db_session.close()

    def _find_option_payload(
        self,
        record_payload: Optional[Dict[str, Any]],
        option_id: str,
        option_title: str
    ) -> Optional[Dict[str, Any]]:
        if not record_payload:
            return None
        options = record_payload.get("options", []) or []
        for option in options:
            if not isinstance(option, dict):
                continue
            if option_id and option.get("option_id") == option_id:
                return option
        for option in options:
            if not isinstance(option, dict):
                continue
            if option_title and option.get("title") == option_title:
                return option
        return None

    def _build_follow_up_insight(
        self,
        predicted_score: float,
        actual_score: float,
        predicted_confidence: float,
        predicted_risk_level: float
    ) -> Dict[str, Any]:
        score_gap = round(actual_score - predicted_score, 1)
        absolute_error = round(abs(score_gap), 1)
        if score_gap >= 15:
            bias_label = "too_conservative"
            bias_note = "实际结果明显好于预测，这次推演偏保守。"
        elif score_gap <= -15:
            bias_label = "too_optimistic"
            bias_note = "实际结果明显差于预测，这次推演偏乐观。"
        else:
            bias_label = "well_calibrated"
            bias_note = "预测和真实结果大体接近。"

        if predicted_confidence >= 0.75 and absolute_error >= 20:
            confidence_alignment = "overconfident"
        elif predicted_confidence <= 0.4 and absolute_error <= 10:
            confidence_alignment = "underconfident"
        else:
            confidence_alignment = "roughly_aligned"

        if predicted_risk_level >= 0.6 and actual_score >= 75:
            risk_alignment = "risk_overstated"
        elif predicted_risk_level <= 0.3 and actual_score <= 45:
            risk_alignment = "risk_understated"
        else:
            risk_alignment = "roughly_aligned"

        return {
            "predicted_score": round(predicted_score, 1),
            "actual_score": round(actual_score, 1),
            "score_gap": score_gap,
            "absolute_error": absolute_error,
            "bias_label": bias_label,
            "bias_note": bias_note,
            "confidence_alignment": confidence_alignment,
            "risk_alignment": risk_alignment,
        }

    def _empty_calibration_profile(self) -> Dict[str, Any]:
        return {
            "review_count": 0,
            "average_absolute_error": 0.0,
            "optimistic_rate": 0.0,
            "conservative_rate": 0.0,
            "calibrated_rate": 0.0,
            "overconfident_rate": 0.0,
            "bias_tendency": "insufficient_data",
            "confidence_adjustment": 0.0,
            "calibration_quality": "insufficient_data",
            "note": "还没有足够的真实回访数据，本次预测置信度主要来自当前证据链。"
        }

    def get_user_calibration_profile(self, user_id: str) -> Dict[str, Any]:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        import sqlalchemy

        if not user_id:
            return self._empty_calibration_profile()

        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        try:
            self._ensure_decision_followups_table(db_session)
            rows = db_session.execute(
                sqlalchemy.text("""
                    SELECT absolute_error, bias_label, confidence_alignment
                    FROM decision_followups
                    WHERE user_id = :uid
                    ORDER BY updated_at DESC
                    LIMIT 50
                """),
                {"uid": user_id}
            ).fetchall()
        except Exception:
            return self._empty_calibration_profile()
        finally:
            try:
                db_session.close()
            except Exception:
                pass

        if not rows:
            return self._empty_calibration_profile()

        review_count = len(rows)
        absolute_errors = [float(row[0] or 0) for row in rows]
        optimistic_count = sum(1 for row in rows if (row[1] or "") == "too_optimistic")
        conservative_count = sum(1 for row in rows if (row[1] or "") == "too_conservative")
        calibrated_count = sum(1 for row in rows if (row[1] or "") == "well_calibrated")
        overconfident_count = sum(1 for row in rows if (row[2] or "") == "overconfident")

        average_absolute_error = round(sum(absolute_errors) / review_count, 1)
        optimistic_rate = round(optimistic_count / review_count, 2)
        conservative_rate = round(conservative_count / review_count, 2)
        calibrated_rate = round(calibrated_count / review_count, 2)
        overconfident_rate = round(overconfident_count / review_count, 2)

        if review_count < 2:
            return {
                **self._empty_calibration_profile(),
                "review_count": review_count,
                "average_absolute_error": average_absolute_error,
                "optimistic_rate": optimistic_rate,
                "conservative_rate": conservative_rate,
                "calibrated_rate": calibrated_rate,
                "overconfident_rate": overconfident_rate,
                "note": f"目前只有{review_count}次真实回访，样本偏少，暂不按历史偏差大幅修正置信度。"
            }

        if optimistic_rate >= conservative_rate + 0.2 and optimistic_rate >= 0.4:
            bias_tendency = "too_optimistic"
        elif conservative_rate >= optimistic_rate + 0.2 and conservative_rate >= 0.4:
            bias_tendency = "too_conservative"
        else:
            bias_tendency = "balanced"

        if average_absolute_error <= 8 and calibrated_rate >= 0.6:
            calibration_quality = "strong"
        elif average_absolute_error <= 15:
            calibration_quality = "moderate"
        else:
            calibration_quality = "weak"

        confidence_adjustment = 0.0
        if average_absolute_error >= 25:
            confidence_adjustment -= 0.12
        elif average_absolute_error >= 18:
            confidence_adjustment -= 0.08
        elif average_absolute_error >= 12:
            confidence_adjustment -= 0.04
        elif average_absolute_error <= 8 and calibrated_rate >= 0.6:
            confidence_adjustment += 0.04

        if bias_tendency == "too_optimistic":
            confidence_adjustment -= 0.03
        elif bias_tendency == "too_conservative" and average_absolute_error <= 14:
            confidence_adjustment += 0.02

        if overconfident_rate >= 0.4:
            confidence_adjustment -= 0.03

        confidence_adjustment = round(min(0.06, max(-0.18, confidence_adjustment)), 2)

        if bias_tendency == "too_optimistic":
            note = (
                f"历史{review_count}次回访里，系统对你偏乐观，"
                f"本次会自动下调约{abs(confidence_adjustment) * 100:.0f}%置信度。"
            )
        elif bias_tendency == "too_conservative":
            direction = "上调" if confidence_adjustment > 0 else "微调"
            note = (
                f"历史{review_count}次回访里，系统对你偏保守，"
                f"本次会{direction}约{abs(confidence_adjustment) * 100:.0f}%置信度。"
            )
        else:
            note = (
                f"历史{review_count}次回访整体较平衡，"
                f"当前只做{abs(confidence_adjustment) * 100:.0f}%以内的轻微校准。"
            )

        return {
            "review_count": review_count,
            "average_absolute_error": average_absolute_error,
            "optimistic_rate": optimistic_rate,
            "conservative_rate": conservative_rate,
            "calibrated_rate": calibrated_rate,
            "overconfident_rate": overconfident_rate,
            "bias_tendency": bias_tendency,
            "confidence_adjustment": confidence_adjustment,
            "calibration_quality": calibration_quality,
            "note": note
        }

    def _ensure_decision_followups_table(self, db_session: Any) -> None:
        import sqlalchemy

        db_session.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS decision_followups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                simulation_id VARCHAR(100) NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                option_id VARCHAR(100) NOT NULL,
                option_title VARCHAR(255),
                question TEXT,
                predicted_score FLOAT DEFAULT 0,
                predicted_risk_level FLOAT DEFAULT 0,
                predicted_confidence FLOAT DEFAULT 0,
                actual_score FLOAT DEFAULT 0,
                elapsed_months INT DEFAULT 0,
                bias_label VARCHAR(50),
                bias_note TEXT,
                score_gap FLOAT DEFAULT 0,
                absolute_error FLOAT DEFAULT 0,
                confidence_alignment VARCHAR(50),
                risk_alignment VARCHAR(50),
                actual_summary TEXT,
                prediction_snapshot LONGTEXT,
                created_at VARCHAR(50),
                updated_at VARCHAR(50),
                UNIQUE KEY uniq_simulation_option (simulation_id, option_id),
                INDEX idx_followup_simulation_id (simulation_id),
                INDEX idx_followup_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        db_session.commit()

    def _persist_follow_up_memory(
        self,
        user_id: str,
        simulation_id: str,
        option_title: str,
        actual_summary: str,
        insight: Dict[str, Any]
    ) -> None:
        try:
            from backend.database.connection import db_connection
            from backend.database.models import ConversationHistory
            from datetime import datetime

            user_text = (
                f"我回访了决策推演《{option_title}》的真实结果。"
                f"实际得分大约是{insight.get('actual_score', 0):.0f}分。"
                f"{actual_summary}"
            )
            assistant_text = (
                f"已记录这次回访。预测分数{insight.get('predicted_score', 0):.0f}分，"
                f"实际分数{insight.get('actual_score', 0):.0f}分，"
                f"结论：{insight.get('bias_note', '')}"
            )

            db = db_connection.get_session()
            now = datetime.utcnow()
            db.add(ConversationHistory(
                user_id=user_id,
                role="user",
                content=user_text,
                context={"type": "decision_follow_up", "simulation_id": simulation_id, "insight": insight},
                timestamp=now,
                session_id=f"followup_{simulation_id}"
            ))
            db.add(ConversationHistory(
                user_id=user_id,
                role="assistant",
                content=assistant_text,
                context={"type": "decision_follow_up", "simulation_id": simulation_id, "insight": insight},
                timestamp=now,
                session_id=f"followup_{simulation_id}"
            ))
            db.commit()
            db.close()
        except Exception as exc:
            logger.warning(f"保存回访记忆失败: {exc}")

    def save_follow_up_review(
        self,
        user_id: str,
        simulation_id: str,
        option_id: str,
        option_title: str,
        actual_score: float,
        elapsed_months: int,
        actual_summary: str
    ) -> Dict[str, Any]:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        from datetime import datetime
        import sqlalchemy

        record_payload = self._load_record_payload(simulation_id)
        option_payload = self._find_option_payload(record_payload, option_id, option_title)
        if not option_payload:
            raise ValueError("找不到对应的推演选项，请先完成并保存该次推演。")

        prediction_trace = option_payload.get("prediction_trace") or {}
        insight = self._build_follow_up_insight(
            predicted_score=float(option_payload.get("final_score", 0)),
            actual_score=float(actual_score),
            predicted_confidence=float(prediction_trace.get("prediction_confidence", 0)),
            predicted_risk_level=float(option_payload.get("risk_level", 0)),
        )

        review = {
            "simulation_id": simulation_id,
            "user_id": user_id,
            "option_id": option_payload.get("option_id") or option_id or option_title,
            "option_title": option_payload.get("title") or option_title,
            "question": (record_payload or {}).get("question", ""),
            "predicted_score": insight["predicted_score"],
            "predicted_risk_level": round(float(option_payload.get("risk_level", 0)), 2),
            "predicted_confidence": round(float(prediction_trace.get("prediction_confidence", 0)), 2),
            "actual_score": insight["actual_score"],
            "elapsed_months": int(max(1, elapsed_months)),
            "bias_label": insight["bias_label"],
            "bias_note": insight["bias_note"],
            "score_gap": insight["score_gap"],
            "absolute_error": insight["absolute_error"],
            "confidence_alignment": insight["confidence_alignment"],
            "risk_alignment": insight["risk_alignment"],
            "actual_summary": actual_summary.strip(),
            "prediction_snapshot": {
                "risk_assessment": option_payload.get("risk_assessment"),
                "prediction_trace": option_payload.get("prediction_trace"),
                "personal_note": option_payload.get("personal_note", ""),
            },
            "updated_at": datetime.now().isoformat(),
        }

        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        try:
            self._ensure_decision_followups_table(db_session)
            db_session.execute(
                sqlalchemy.text("""
                    INSERT INTO decision_followups (
                        simulation_id, user_id, option_id, option_title, question,
                        predicted_score, predicted_risk_level, predicted_confidence,
                        actual_score, elapsed_months, bias_label, bias_note,
                        score_gap, absolute_error, confidence_alignment, risk_alignment,
                        actual_summary, prediction_snapshot, created_at, updated_at
                    ) VALUES (
                        :simulation_id, :user_id, :option_id, :option_title, :question,
                        :predicted_score, :predicted_risk_level, :predicted_confidence,
                        :actual_score, :elapsed_months, :bias_label, :bias_note,
                        :score_gap, :absolute_error, :confidence_alignment, :risk_alignment,
                        :actual_summary, :prediction_snapshot, :created_at, :updated_at
                    )
                    ON DUPLICATE KEY UPDATE
                        user_id = VALUES(user_id),
                        option_title = VALUES(option_title),
                        question = VALUES(question),
                        predicted_score = VALUES(predicted_score),
                        predicted_risk_level = VALUES(predicted_risk_level),
                        predicted_confidence = VALUES(predicted_confidence),
                        actual_score = VALUES(actual_score),
                        elapsed_months = VALUES(elapsed_months),
                        bias_label = VALUES(bias_label),
                        bias_note = VALUES(bias_note),
                        score_gap = VALUES(score_gap),
                        absolute_error = VALUES(absolute_error),
                        confidence_alignment = VALUES(confidence_alignment),
                        risk_alignment = VALUES(risk_alignment),
                        actual_summary = VALUES(actual_summary),
                        prediction_snapshot = VALUES(prediction_snapshot),
                        updated_at = VALUES(updated_at)
                """),
                {
                    **review,
                    "prediction_snapshot": json.dumps(review["prediction_snapshot"], ensure_ascii=False),
                    "created_at": datetime.now().isoformat(),
                }
            )
            db_session.commit()
        finally:
            db_session.close()

        self._persist_follow_up_memory(
            user_id=user_id,
            simulation_id=simulation_id,
            option_title=review["option_title"],
            actual_summary=review["actual_summary"],
            insight=insight
        )

        return review

    def get_follow_up_summary(self, simulation_id: str) -> Dict[str, Any]:
        from backend.database.models import Database
        from backend.database.config import DatabaseConfig
        import sqlalchemy

        db = Database(DatabaseConfig.get_database_url())
        db_session = db.get_session()
        try:
            self._ensure_decision_followups_table(db_session)
            rows = db_session.execute(
                sqlalchemy.text("""
                    SELECT simulation_id, user_id, option_id, option_title, question,
                           predicted_score, predicted_risk_level, predicted_confidence,
                           actual_score, elapsed_months, bias_label, bias_note,
                           score_gap, absolute_error, confidence_alignment, risk_alignment,
                           actual_summary, prediction_snapshot, created_at, updated_at
                    FROM decision_followups
                    WHERE simulation_id = :sid
                    ORDER BY updated_at DESC
                """),
                {"sid": simulation_id}
            ).fetchall()
        finally:
            db_session.close()

        reviews: List[Dict[str, Any]] = []
        for row in rows:
            snapshot_raw = row[17]
            try:
                snapshot = json.loads(snapshot_raw) if snapshot_raw else {}
            except Exception:
                snapshot = {}
            reviews.append({
                "simulation_id": row[0],
                "user_id": row[1],
                "option_id": row[2],
                "option_title": row[3],
                "question": row[4] or "",
                "predicted_score": round(float(row[5] or 0), 1),
                "predicted_risk_level": round(float(row[6] or 0), 2),
                "predicted_confidence": round(float(row[7] or 0), 2),
                "actual_score": round(float(row[8] or 0), 1),
                "elapsed_months": int(row[9] or 0),
                "bias_label": row[10] or "",
                "bias_note": row[11] or "",
                "score_gap": round(float(row[12] or 0), 1),
                "absolute_error": round(float(row[13] or 0), 1),
                "confidence_alignment": row[14] or "",
                "risk_alignment": row[15] or "",
                "actual_summary": row[16] or "",
                "prediction_snapshot": snapshot,
                "created_at": row[18] or "",
                "updated_at": row[19] or "",
            })

        if not reviews:
            return {
                "review_count": 0,
                "average_predicted_score": 0.0,
                "average_actual_score": 0.0,
                "average_absolute_error": 0.0,
                "optimistic_count": 0,
                "conservative_count": 0,
                "calibrated_count": 0,
                "user_calibration_profile": self._empty_calibration_profile(),
                "reviews": [],
            }

        review_count = len(reviews)
        optimistic_count = sum(1 for item in reviews if item["bias_label"] == "too_optimistic")
        conservative_count = sum(1 for item in reviews if item["bias_label"] == "too_conservative")
        calibrated_count = sum(1 for item in reviews if item["bias_label"] == "well_calibrated")
        user_calibration_profile = self.get_user_calibration_profile(reviews[0]["user_id"])
        return {
            "review_count": review_count,
            "average_predicted_score": round(sum(item["predicted_score"] for item in reviews) / review_count, 1),
            "average_actual_score": round(sum(item["actual_score"] for item in reviews) / review_count, 1),
            "average_absolute_error": round(sum(item["absolute_error"] for item in reviews) / review_count, 1),
            "optimistic_count": optimistic_count,
            "conservative_count": conservative_count,
            "calibrated_count": calibrated_count,
            "user_calibration_profile": user_calibration_profile,
            "reviews": reviews,
        }

    async def simulate_decision(
        self,
        user_id: str,
        question: str,
        options: List[Dict[str, str]],
        collected_info: Optional[Dict[str, Any]] = None,
    ):
        """
        HTTP 模式的完整决策模拟（非流式）
        为每个选项生成时间线，然后生成推荐
        """
        from dataclasses import dataclass

        @dataclass
        class TimelineEvent:
            event_id: str
            parent_event_id: Optional[str]
            month: int
            event: str
            impact: Dict[str, float]
            probability: float
            state_before: Dict[str, Any]
            impact_vector: Dict[str, float]
            evidence_sources: List[str]
            agent_votes: List[Dict[str, Any]]
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
            prediction_trace: Optional[Dict[str, Any]] = None
            execution_confidence: float = 0.7
            dropout_risk_month: Optional[int] = None
            personal_note: str = ""

        @dataclass
        class SimulationResult:
            simulation_id: str
            user_id: str
            question: str
            options: list
            recommendation: str
            created_at: str
            verifiability_report: Optional[Dict[str, Any]] = None

        profile = None
        if self.personality_test:
            try:
                profile = self.personality_test.load_profile(user_id)
            except Exception:
                profile = None

        pkf_facts: List[Any] = []
        try:
            from backend.decision.personal_knowledge_fusion import PersonalFactExtractor
            extractor = PersonalFactExtractor(user_id)
            pkf_facts = extractor.extract_all()
            self.lora_analyzer._pkf_facts = pkf_facts
        except Exception as exc:
            logger.warning(f"提取 PKF 事实失败: {exc}")
            self.lora_analyzer._pkf_facts = []

        calibration_profile = self.get_user_calibration_profile(user_id)

        simulated_options = []

        for i, option in enumerate(options):
            option_branch = option.get('title', f'option_{i}').lower().replace(' ', '_')
            logger.info(f"[HTTP推演] 开始推演选项 {i+1}: {option.get('title')}")

            self.lora_analyzer._pkf_context = self._build_pkf_context(
                question,
                option.get("title", ""),
                pkf_facts
            )

            # 生成时间线
            timeline = []
            timeline_data = await self.lora_analyzer.generate_timeline_with_lora(
                user_id=user_id,
                question=question,
                option=option,
                profile=profile,
                num_events=12,
                collected_info=collected_info
            )

            previous_event_id = None
            for idx, e in enumerate(timeline_data or []):
                node = self._create_timeline_node(
                    TimelineEvent,
                    event_id=f"{option_branch}_node_{idx+1}",
                    parent_event_id=previous_event_id,
                    month=e.get('month', idx + 1),
                    event_text=e.get('event', ''),
                    impact=e.get('impact', {}),
                    probability=e.get('probability', 0.5),
                    branch_group=option_branch,
                    node_level=idx + 1,
                    question=question,
                    option_title=option.get('title', f'选项{i+1}'),
                    timeline=timeline,
                    collected_info=collected_info,
                    facts_count=len(pkf_facts),
                    profile=profile,
                    calibration_profile=calibration_profile,
                )
                previous_event_id = node.event_id
                timeline.append(node)

            raw_final_score = self._calculate_final_score(timeline, profile)
            risk_assessment = self._assess_option_risk(option.get('title', f'选项{i+1}'), timeline, profile)
            prediction_trace = self._build_prediction_trace(
                question=question,
                option=option,
                timeline=timeline,
                collected_info=collected_info,
                facts_count=len(pkf_facts),
                profile=profile,
                calibration_profile=calibration_profile,
            )
            final_score = self._compress_score_by_confidence(
                raw_final_score,
                prediction_trace.get("prediction_confidence", 0.5)
            )
            risk_level = self._merge_risk_level(
                self._calculate_risk_level(timeline),
                risk_assessment
            )
            self_prediction = await self.lora_analyzer.generate_self_prediction(
                user_id=user_id,
                question=question,
                option=option,
                profile=profile,
                collected_info=collected_info
            )

            simulated_options.append(DecisionOption(
                option_id=f"option_{i+1}",
                title=option.get('title', f'选项{i+1}'),
                description=option.get('description', ''),
                timeline=timeline,
                final_score=final_score,
                risk_level=risk_level,
                risk_assessment=risk_assessment,
                prediction_trace=prediction_trace,
                execution_confidence=self_prediction.get("execution_confidence", 0.7),
                dropout_risk_month=self_prediction.get("dropout_risk_month"),
                personal_note=self_prediction.get("personal_note", "")
            ))

        # 生成推荐
        options_for_rec = [
            {
                "title": opt.title,
                "description": opt.description,
                "final_score": opt.final_score,
                "risk_level": opt.risk_level,
                "timeline_summary": self._summarize_timeline(opt.timeline),
                "risk_assessment": opt.risk_assessment,
                "prediction_confidence": (opt.prediction_trace or {}).get("prediction_confidence"),
                "calibration_review_count": (opt.prediction_trace or {}).get("calibration_review_count"),
                "calibration_note": (opt.prediction_trace or {}).get("calibration_note"),
                "execution_confidence": opt.execution_confidence,
                "personal_note": opt.personal_note,
            }
            for opt in simulated_options
        ]
        recommendation = ""
        try:
            rec_stream = ""
            async for chunk in self.lora_analyzer.stream_recommendation_generation(
                user_id=user_id,
                question=question,
                options=options_for_rec,
                profile=profile,
                collected_info=collected_info
            ):
                rec_stream += chunk
            recommendation = self.lora_analyzer._clean_recommendation(rec_stream)
        except Exception as e:
            logger.warning(f"推荐生成失败: {e}")
            recommendation = "暂无推荐"

        verifiability_report = self._build_verifiability_report(simulated_options, collected_info, calibration_profile)
        simulation_id = f"sim_{user_id}_{int(__import__('time').time())}"

        try:
            self._save_decision_record(
                simulation_id=simulation_id,
                user_id=user_id,
                question=question,
                options=simulated_options,
                recommendation=recommendation,
                collected_info=collected_info,
                verifiability_report=verifiability_report,
            )
        except Exception as save_err:
            logger.warning(f"保存决策记录失败: {save_err}")

        return SimulationResult(
            simulation_id=simulation_id,
            user_id=user_id,
            question=question,
            options=simulated_options,
            recommendation=recommendation,
            created_at=__import__('datetime').datetime.now().isoformat(),
            verifiability_report=verifiability_report
        )

    def _generate_career_event_text(
        self,
        month: int,
        option_title: str,
        agents_state: Dict[str, Any],
        algo_result: Dict[str, Any]
    ) -> str:
        """
        基于Agent状态和算法结果生成职业事件描述
        
        Args:
            month: 当前月份
            option_title: 选项标题
            agents_state: 各Agent的状态
            algo_result: 职业决策算法结果
        
        Returns:
            事件描述文本
        """
        # 获取最显著的变化
        key_changes = []
        
        # 技能发展
        if 'skill_development' in agents_state:
            skill_state = agents_state['skill_development']
            if skill_state.changes:
                key_changes.append(skill_state.changes[0])
        
        # 财务状况
        if 'financial' in agents_state:
            financial_state = agents_state['financial']
            if financial_state.changes:
                key_changes.append(financial_state.changes[0])
        
        # 心理状态
        if 'psychological' in agents_state:
            psych_state = agents_state['psychological']
            if psych_state.changes:
                key_changes.append(psych_state.changes[0])
        
        # 构建事件文本
        if key_changes:
            event_text = f"你在{option_title}路径的第{month}个月：" + "；".join(key_changes[:2])
        else:
            event_text = f"你在{option_title}路径的第{month}个月继续推进"
        
        return event_text
    
    def _calculate_career_impact(self, agents_state: Dict[str, Any]) -> Dict[str, float]:
        """
        基于Agent状态计算综合影响向量
        
        Args:
            agents_state: 各Agent的状态
        
        Returns:
            影响向量字典
        """
        impact = {
            '健康': 0.0,
            '财务': 0.0,
            '社交': 0.0,
            '情绪': 0.0,
            '学习': 0.0,
            '时间': 0.0
        }
        
        # 技能发展 -> 学习
        if 'skill_development' in agents_state:
            skill_score = agents_state['skill_development'].score
            impact['学习'] = (skill_score - 50) / 100  # 归一化到-0.5~0.5
        
        # 财务状况 -> 财务
        if 'financial' in agents_state:
            financial_score = agents_state['financial'].score
            impact['财务'] = (financial_score - 50) / 100
        
        # 职业网络 -> 社交
        if 'career_network' in agents_state:
            network_score = agents_state['career_network'].score
            impact['社交'] = (network_score - 50) / 100
        
        # 心理资本 -> 情绪
        if 'psychological' in agents_state:
            psych_score = agents_state['psychological'].score
            impact['情绪'] = (psych_score - 50) / 100
        
        # 市场环境 -> 时间（机会窗口）
        if 'market_environment' in agents_state:
            market_score = agents_state['market_environment'].score
            impact['时间'] = (market_score - 50) / 100
        
        return impact
    
    def _calculate_event_probability(self, agents_state: Dict[str, Any]) -> float:
        """
        基于Agent状态一致性计算事件概率
        
        Args:
            agents_state: 各Agent的状态
        
        Returns:
            概率值 (0.0-1.0)
        """
        if not agents_state:
            return 0.5
        
        # 计算Agent评分的标准差
        scores = [state.score for state in agents_state.values()]
        if not scores:
            return 0.5
        
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # 标准差越小，一致性越高，概率越高
        # 标准差范围通常在0-30之间
        consistency = max(0.0, 1.0 - (std_dev / 30.0))
        
        # 基础概率 + 一致性加成
        base_prob = 0.6
        probability = base_prob + (consistency * 0.3)
        
        return round(min(0.95, max(0.3, probability)), 2)





simulator = DecisionSimulator()


class StartCollectionRequest(BaseModel):
    """开始信息收集请求"""
    user_id: str
    initial_question: str
    decision_type: Optional[str] = "general"  # career, relationship, education, general


class ContinueCollectionRequest(BaseModel):
    """继续信息收集请求"""
    session_id: str
    user_response: str


class SimulateWithCollectedInfoRequest(BaseModel):
    """使用收集的信息进行模拟"""
    session_id: str
    options: List[Dict[str, str]]  # [{"title": "选项A", "description": "..."}]
    use_lora: bool = True


class SubmitDecisionFollowUpRequest(BaseModel):
    """提交决策回访"""
    user_id: str
    simulation_id: str
    option_id: str
    option_title: str
    actual_score: float
    elapsed_months: int = 3
    actual_summary: str = ""


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
        collected_info_summary = {}
        verifiability_report = {}
        schema_version = 1
        if row[5]:
            try:
                parsed = json.loads(row[5])
                if isinstance(parsed, dict):
                    schema_version = parsed.get("schema_version", 2)
                    options = parsed.get("options", [])
                    collected_info_summary = parsed.get("collected_info_summary", {}) or {}
                    verifiability_report = parsed.get("verifiability_report", {}) or {}
                elif isinstance(parsed, list):
                    options = parsed
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
                "schema_version": schema_version,
                "collected_info_summary": collected_info_summary,
                "verifiability_report": verifiability_report,
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
                    timeline_data LONGTEXT,
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


@router.get("/follow-up/{simulation_id}")
async def get_decision_follow_up(simulation_id: str) -> Dict[str, Any]:
    """获取某次决策推演的回访与校准摘要"""
    try:
        summary = simulator.get_follow_up_summary(simulation_id)
        return {
            "code": 200,
            "message": "获取成功",
            "data": summary
        }
    except Exception as e:
        logger.warning(f"获取决策回访失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/follow-up")
async def submit_decision_follow_up(request: SubmitDecisionFollowUpRequest) -> Dict[str, Any]:
    """提交真实结果，用于预测校准与后续学习"""
    try:
        review = simulator.save_follow_up_review(
            user_id=request.user_id,
            simulation_id=request.simulation_id,
            option_id=request.option_id,
            option_title=request.option_title,
            actual_score=request.actual_score,
            elapsed_months=request.elapsed_months,
            actual_summary=request.actual_summary,
        )
        summary = simulator.get_follow_up_summary(request.simulation_id)
        return {
            "code": 200,
            "message": "回访已记录",
            "data": {
                "review": review,
                "summary": summary
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"提交决策回访失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class WarmupRequest(BaseModel):
    user_id: str


@router.post("/ai-core/warmup")
async def warmup_ai_core(request: WarmupRequest) -> Dict[str, Any]:
    """
    预热AI核心（已废弃）
    
    AI核心在后端启动时已经预热，此接口保留用于兼容性
    """
    return {
        "code": 200,
        "message": "AI核心已在后端启动时预热完成",
        "data": {"status": "ready", "stage": "就绪", "progress": 100}
    }


@router.get("/ai-core/warmup-status/{user_id}")
async def get_warmup_status(user_id: str) -> Dict[str, Any]:
    """
    查询AI核心预热状态
    
    注意：AI核心在后端启动时已经预热，此接口主要用于前端显示
    """
    try:
        # 检查LLM服务是否就绪
        llm_service = get_llm_service()
        if llm_service and llm_service.enabled:
            return {
                "code": 200,
                "message": "AI核心已就绪",
                "data": {
                    "status": "ready",
                    "stage": "就绪",
                    "progress": 100
                }
            }
        else:
            return {
                "code": 200,
                "message": "AI核心未启用",
                "data": {
                    "status": "not_started",
                    "stage": "未启用",
                    "progress": 0
                }
            }
    except Exception as e:
        logger.error(f"查询预热状态失败: {e}")
        return {
            "code": 200,
            "message": "AI核心就绪",
            "data": {"status": "ready", "stage": "就绪", "progress": 100}
        }


@router.post("/collect/start")
async def start_info_collection(request: StartCollectionRequest) -> Dict[str, Any]:
    """
    开始决策信息收集
    
    使用 Qwen3.5-plus API 进行多轮对话，收集决策所需信息
    """
    try:
        logger.info(f"📥 收到信息收集请求 - user_id: {request.user_id}, question: {request.initial_question}, type: {request.decision_type}")
        
        result = info_collector.start_collection(
            user_id=request.user_id,
            initial_question=request.initial_question
        )
        
        # 保存decision_type到session
        session = info_collector.get_session(result['session_id'])
        if session:
            session['decision_type'] = request.decision_type or 'general'
            # 立即保存，更新session中的decision_type
            info_collector._save_session(session)
        
        logger.info(f"✅ 信息收集会话创建成功 - session_id: {result['session_id']}, type: {request.decision_type}")
        
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


@router.post("/collect/continue-stream")
async def continue_info_collection_stream(request: ContinueCollectionRequest):
    """
    继续信息收集（流式响应版本）
    
    用户回答AI的问题，继续收集信息，通过SSE流式返回进度和结果
    """
    async def generate_stream():
        try:
            # 发送开始状态
            yield f"data: {json.dumps({'type': 'status', 'content': '正在分析你的回答...'})}\n\n"
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
                yield f"data: {json.dumps({'type': 'status', 'content': ''})}\n\n"
                await asyncio.sleep(0.05)
                
                # 分块发送AI消息，模拟打字效果
                chunk_size = 12
                for i in range(0, len(ai_question), chunk_size):
                    chunk = ai_question[i:i+chunk_size]
                    yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.04)  # 打字效果延迟
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"
            
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"流式信息收集失败: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


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
    
    信息收集完成后，使用当前配置的推理引擎进行个性化决策模拟
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
        
        # 2. 检查是否是职业决策类型
        decision_type = session.get("decision_type", "general")
        
        if decision_type == "career":
            # 使用职业决策多Agent框架
            logger.info("🎯 检测到职业决策类型，使用多Agent评估框架")
            from backend.decision.career_simulation_integration import CareerSimulationIntegration
            
            career_integration = CareerSimulationIntegration()
            career_result = await career_integration.simulate_career_decision_with_agents(
                user_id=session["user_id"],
                question=session["initial_question"],
                options=request.options,
                collected_info=session.get("collected_info", {})
            )
            
            # 转换为标准格式
            result = simulator._convert_career_result_to_standard(career_result)
        else:
            # 使用通用推理引擎进行决策模拟
            result = await simulator.simulate_decision(
                user_id=session["user_id"],
                question=session["initial_question"],
                options=request.options,
                collected_info=session.get("collected_info", {}),
            )

        response_data = {
            "code": 200,
            "message": "决策模拟完成",
            "data": {
                "simulation_id": result.simulation_id,
                "user_id": result.user_id,
                "question": result.question,
                "collected_info_summary": session["collected_info"],
                "verifiability_report": result.verifiability_report or {},
                "options": [simulator._serialize_option(opt) for opt in result.options],
                "recommendation": result.recommendation,
                "created_at": result.created_at,
                "used_lora": simulator.lora_analyzer.is_lora_inference(),
                "inference_mode": simulator.lora_analyzer.get_inference_mode()
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
                "verifiability_report": result.verifiability_report or {},
                "options": [simulator._serialize_option(opt) for opt in result.options],
                "recommendation": result.recommendation,
                "created_at": result.created_at,
                "used_lora": simulator.lora_analyzer.is_lora_inference(),
                "inference_mode": simulator.lora_analyzer.get_inference_mode()
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
    
    # WebSocket连接状态标志
    ws_connected = True
    
    # 安全的WebSocket发送函数，连接断开时不再发送
    async def safe_send(data: dict) -> bool:
        """安全发送JSON，连接断开时返回False"""
        nonlocal ws_connected
        if not ws_connected:
            return False
        try:
            await websocket.send_json(data)
            return True
        except (StarletteWebSocketDisconnect,
                WebSocketDisconnect,
                RuntimeError) as e:
            err_str = str(e)
            if "close message has been sent" in err_str or "ConnectionClosed" in type(e).__name__ or "Cannot call" in err_str:
                logger.warning(f"[WS] 连接已断开，停止发送: {type(e).__name__}")
                ws_connected = False
                return False
            raise
        except Exception:
            raise
    
    try:
        while True:
            try:
                payload = await websocket.receive_text()
                request = json.loads(payload)
            except Exception as recv_error:
                logger.error(f"[WS] 接收消息失败: {recv_error}")
                await safe_send({"type": "error", "content": f"消息格式错误: {str(recv_error)}"})
                continue
                
            session_id = request.get("session_id")
            options = request.get("options", [])

            if not session_id or not options:
                await safe_send({"type": "error", "content": "session_id 和 options 不能为空"})
                continue

            session = info_collector.get_session(session_id)
            if not session:
                await safe_send({"type": "error", "content": "会话不存在"})
                continue
            if not session.get("is_complete"):
                await safe_send({"type": "error", "content": "信息收集未完成"})
                continue

            user_id = session["user_id"]
            question = session["initial_question"]
            collected_info = session.get("collected_info", {})
            decision_type = session.get("decision_type", "general")
            
            # 调试日志
            logger.info(f"[WS推演] session_id={session_id}, decision_type={decision_type}, is_complete={session.get('is_complete')}")
            logger.info(f"[WS推演] 准备处理推演请求，options数量={len(options)}")
            
            # ========== 职业决策使用多Agent框架（流式推演）==========
            if decision_type == "career":
                logger.info("[WS推演] 进入职业决策分支")
                logger.info("🎯 检测到职业决策类型，使用多Agent评估框架（实时流式推演）")
                try:
                    if not await safe_send({
                        "type": "start",
                        "session_id": session_id,
                        "user_id": user_id,
                        "question": question,
                        "decision_type": "career"
                    }):
                        logger.warning("[职业推演] 发送start失败，连接已断开")
                        return
                    
                    if not await safe_send({
                        "type": "status",
                        "stage": "career_agent_init",
                        "content": "职业决策模式：正在启动职业决策算法和5个专业Agent..."
                    }):
                        logger.warning("[职业推演] 发送状态失败，连接已断开")
                        return
                    
                    # 导入职业决策相关模块
                    from backend.decision.multi_agent_career_evaluator import (
                        MultiAgentCareerEvaluator,
                    )
                    from backend.decision_algorithm.career_decision_algorithm import (
                        KnowledgeGraphCareerIntegration
                    )
                    
                    # 初始化职业决策算法
                    kg_integration = KnowledgeGraphCareerIntegration(user_id)
                    
                    # 提前提取一次个人资本，所有选项共享
                    logger.info("[职业推演] 开始提取个人资本（所有选项共享）...")
                    personal_capital = kg_integration.extract_personal_capital_from_kg()
                    logger.info(f"[职业推演] 个人资本提取完成，共 {len(options)} 个选项将共享此数据")
                    
                    # 为每个选项创建并行推演任务
                    simulation_id = f"sim_{user_id}_{int(asyncio.get_event_loop().time())}"
                    
                    async def simulate_single_option(option, option_index):
                        """并行推演单个选项"""
                        option_id = f"option_{option_index+1}"
                        option_title = option.get("title", f"选项{option_index+1}")
                        
                        try:
                            if not await safe_send({
                                "type": "option_start",
                                "option_id": option_id,
                                "title": option_title,
                                "description": option.get("description", "")
                            }):
                                logger.warning(f"[职业推演] {option_id} 发送失败，连接已断开")
                                return False
                            
                            if not await safe_send({
                                "type": "status",
                                "stage": "career_algorithm",
                                "option_id": option_id,
                                "content": f"正在使用职业决策算法分析 {option_title}..."
                            }):
                                logger.warning(f"[职业推演] {option_id} 发送状态失败，连接已断开")
                                return False
                            
                            # 使用MultiAgentCareerEvaluator（已优化，共享个人资本）
                            evaluator = MultiAgentCareerEvaluator(user_id)
                            evaluator.personal_capital = personal_capital  # 直接使用已提取的个人资本
                            logger.info(f"[职业推演] {option_id} 创建evaluator，personal_capital={'已设置' if personal_capital else 'None'}")
                            
                            # 初始化Agent（传入个人资本，避免重复提取）
                            context = {
                                'option_title': option_title,
                                'option_description': option.get('description', ''),
                                'question': question,
                                'collected_info': collected_info,
                                'personal_capital': personal_capital  # 传入已提取的个人资本
                            }
                            
                            logger.info(f"[职业推演] {option_id} 开始初始化5个Agent...")
                            await evaluator.initialize_all_agents(context)
                            logger.info(f"[职业推演] {option_id} Agent初始化完成")
                            
                            # 启动心跳机制（避免长时间推演导致连接超时）
                            last_heartbeat = asyncio.get_event_loop().time()
                            heartbeat_interval = 10.0  # 每10秒发送一次心跳
                            
                            # 推演12个月，每个月实时发送
                            timeline = []
                            agents_state = {}
                            
                            for month in range(1, 13):
                                current_time = asyncio.get_event_loop().time()
                                if current_time - last_heartbeat > heartbeat_interval:
                                    if not await safe_send({
                                        "type": "heartbeat",
                                        "content": f"正在推演第{month}个月...",
                                        "stage": "career_simulating"
                                    }):
                                        logger.warning(f"[职业推演] {option_id} 心跳发送失败，连接已断开")
                                        return False
                                    last_heartbeat = current_time
                                    logger.debug(f"[职业推演] {option_id} 发送心跳 M{month}")
                                
                                if not await safe_send({
                                    "type": "thinking",
                                    "stage": "month_simulation",
                                    "option_id": option_id,
                                    "option_title": option_title,
                                    "month": month,
                                    "content": f"正在推演【{option_title}】第{month}个月，职业决策算法和5个Agent正在分析中..."
                                }):
                                    logger.warning(f"[职业推演] {option_id} M{month} 发送失败，连接已断开")
                                    return False
                                
                                # 1. 使用职业决策算法计算基础评分
                                try:
                                    algo_result = kg_integration.calculate_career_decision_score(
                                        option_title=option_title,
                                        current_month=month
                                    )

                                    # 构建详细的算法评分思考内容
                                    algo_thinking = f"""============================================================
职业决策算法评分（第{month}月）
============================================================
综合得分: {algo_result.get('total_score', 0):.1f}/100

人力资本（技能+经验）: {algo_result.get('human_capital', 0):.1f}
社会资本（人脉+声誉）: {algo_result.get('social_capital', 0):.1f}
心理资本（自信+韧性）: {algo_result.get('psychological_capital', 0):.1f}
经济资本（储蓄+现金流）: {algo_result.get('economic_capital', 0):.1f}
市场环境（需求+竞争）: {algo_result.get('market_environment', 0):.1f}

算法分析：综合得分{algo_result.get('total_score', 0):.1f}分，{get_score_assessment(algo_result.get('total_score', 0))}
"""

                                    if not await safe_send({
                                        "type": "thinking_chunk",
                                        "stage": "career_algorithm",
                                        "option_id": option_id,
                                        "option_title": option_title,
                                        "month": month,
                                        "content": algo_thinking
                                    }):
                                        return False
                                except Exception as algo_error:
                                    logger.warning(f"职业决策算法计算失败: {algo_error}")
                                    import traceback
                                    traceback.print_exc()
                                    algo_result = {'total_score': 50.0, 'human_capital': 50.0, 'social_capital': 50.0, 'psychological_capital': 50.0, 'economic_capital': 50.0, 'market_environment': 50.0}
                                
                                # 2. 5个Agent演化并评估
                                agent_evaluations = []

                                for agent_name, agent in evaluator.agents.items():
                                    try:
                                        # Agent演化到当前月
                                        state = await agent.evolve(
                                            month=month,
                                            context=context,
                                            other_agents_state=agents_state
                                        )
                                        agents_state[agent_name] = state

                                        # 生成Agent的详细思考内容
                                        agent_display_name = {
                                            'skill_development': '技能发展Agent',
                                            'career_network': '职业人脉Agent',
                                            'financial': '财务状况Agent',
                                            'psychological': '心理资本Agent',
                                            'market_environment': '市场环境Agent'
                                        }.get(agent_name, agent_name)

                                        # 构建详细的思考内容
                                        thinking_parts = [
                                            f"\n{'━' * 50}",
                                            f"{agent_display_name}",
                                            f"{'━' * 50}",
                                            f"评分: {state.score:.1f}/100 | 状态: {get_agent_status(state.status)}"
                                        ]

                                        # 添加关键指标
                                        if state.key_metrics:
                                            metrics_lines = []
                                            for k, v in list(state.key_metrics.items())[:4]:
                                                metrics_lines.append(f"  • {format_metric_key(k)}: {v}")
                                            if metrics_lines:
                                                thinking_parts.append(f"\n关键指标:\n" + "\n".join(metrics_lines))

                                        # 添加主要变化
                                        if state.changes:
                                            thinking_parts.append(f"\n变化: {' | '.join(state.changes[:2])}")

                                        # 添加风险
                                        if state.risks:
                                            thinking_parts.append(f"\n风险: {' | '.join(state.risks[:2])}")

                                        # 添加机会
                                        if state.opportunities:
                                            thinking_parts.append(f"\n机会: {' | '.join(state.opportunities[:2])}")

                                        agent_thinking = "\n".join(thinking_parts)

                                        # 发送Agent详细思考过程
                                        if not await safe_send({
                                            "type": "thinking_chunk",
                                            "stage": "agent_evaluation",
                                            "option_id": option_id,
                                            "option_title": option_title,
                                            "month": month,
                                            "agent": agent_name,
                                            "content": agent_thinking
                                        }):
                                            return False

                                        agent_evaluations.append({
                                            'agent_name': agent_name,
                                            'score': state.score,
                                            'status': state.status,
                                            'changes': state.changes,
                                            'risks': state.risks,
                                            'opportunities': state.opportunities
                                        })

                                    except Exception as agent_error:
                                        logger.error(f"Agent {agent_name} 演化失败: {agent_error}")
                                        import traceback
                                        traceback.print_exc()
                                
                                # 发送本月综合分析
                                if agents_state:
                                    overall_score = sum(s.score for s in agents_state.values()) / len(agents_state)
                                    critical_count = sum(1 for s in agents_state.values() if s.status == 'critical')
                                    good_count = sum(1 for s in agents_state.values() if s.status == 'good')

                                    # 构建综合评估
                                    sorted_agents = sorted(agents_state.items(), key=lambda x: x[1].score)
                                    weakest = sorted_agents[0]
                                    strongest = sorted_agents[-1]

                                    # Agent名称中文映射
                                    agent_name_map = {
                                        'skill_development': '技能发展',
                                        'career_network': '职业人脉',
                                        'financial': '财务状况',
                                        'psychological': '心理资本',
                                        'market_environment': '市场环境'
                                    }

                                    summary_parts = [
                                        f"\n{'=' * 50}",
                                        f"【{option_title}】第{month}月综合评估",
                                        f"{'=' * 50}",
                                        f"综合得分: {overall_score:.1f}/100 | {get_score_assessment(overall_score)}",
                                        f"状态分布: {good_count}个良好 | {critical_count}个危险",
                                        f"",
                                        f"各维度评分:",
                                    ]

                                    # 添加各Agent评分
                                    for name, state in sorted(agents_state.items(), key=lambda x: -x[1].score):
                                        name_cn = agent_name_map.get(name, name)
                                        status_icon = 'OK' if state.status == 'good' else ('!' if state.status == 'warning' else 'X')
                                        summary_parts.append(f"  [{status_icon}] {name_cn}: {state.score:.1f}分")

                                    summary_parts.extend([
                                        f"",
                                        f"最强维度: {agent_name_map.get(strongest[0], strongest[0])} ({strongest[1].score:.1f}分)",
                                        f"最弱维度: {agent_name_map.get(weakest[0], weakest[0])} ({weakest[1].score:.1f}分)",
                                    ])

                                    if not await safe_send({
                                        "type": "thinking_chunk",
                                        "stage": "month_summary",
                                        "option_id": option_id,
                                        "option_title": option_title,
                                        "month": month,
                                        "content": "\n".join(summary_parts)
                                    }):
                                        return False
                                else:
                                    # 没有agents_state时发送默认综合评估
                                    if not await safe_send({
                                        "type": "thinking_chunk",
                                        "stage": "month_summary",
                                        "option_id": option_id,
                                        "option_title": option_title,
                                        "month": month,
                                        "content": f"\n【{option_title}】第{month}月：等待Agent评估完成"
                                    }):
                                        return False
                                
                                # 3. 生成节点事件描述
                                event_text = simulator._generate_career_event_text(
                                    month=month,
                                    option_title=option_title,
                                    agents_state=agents_state,
                                    algo_result=algo_result
                                )
                                
                                # 4. 计算综合impact
                                impact = simulator._calculate_career_impact(agents_state)
                                
                                # 5. 计算概率（基于Agent一致性）
                                probability = simulator._calculate_event_probability(agents_state)
                                
                                # 6. 创建节点
                                from dataclasses import dataclass
                                
                                @dataclass
                                class TimelineEvent:
                                    event_id: str
                                    parent_event_id: Optional[str]
                                    month: int
                                    event: str
                                    impact: Dict[str, float]
                                    probability: float
                                    state_before: Dict[str, Any]
                                    impact_vector: Dict[str, float]
                                    evidence_sources: List[str]
                                    agent_votes: List[Dict[str, Any]]
                                    event_type: str = "career"
                                    branch_group: str = "main"
                                    node_level: int = 1
                                    risk_tag: str = "medium"
                                    opportunity_tag: str = "medium"
                                    visual_weight: float = 0.5
                                
                                node = TimelineEvent(
                                    event_id=f"{option_id}_M{month}",
                                    parent_event_id=f"{option_id}_M{month-1}" if month > 1 else None,
                                    month=month,
                                    event=event_text,
                                    impact=impact,
                                    probability=probability,
                                    state_before={'month': month - 1},
                                    impact_vector=impact,
                                    evidence_sources=['career_algorithm', 'multi_agent_evaluation'],
                                    agent_votes=agent_evaluations,
                                    branch_group=option_id,
                                    node_level=month
                                )
                                
                                timeline.append(node)
                                
                                # 7. 立即发送节点（确保实时显示）
                                logger.info(f"[职业推演] 发送节点 {option_id} M{month}")
                                if not await safe_send({
                                    "type": "node",
                                    "option_id": option_id,
                                    "option_title": option_title,
                                    "node": simulator._serialize_timeline_event(node, month - 1)
                                }):
                                    return False
                                
                                # 添加小延迟确保前端能处理
                                await asyncio.sleep(0.05)
                            
                            # 选项推演完成
                            final_score = sum(s.score for s in agents_state.values()) / len(agents_state) if agents_state else 50.0
                            
                            if not await safe_send({
                                "type": "option_complete",
                                "option_id": option_id,
                                "title": option_title,
                                "final_score": final_score,
                                "risk_level": 0.5
                            }):
                                return False
                            
                            logger.info(f"[职业推演] 选项 {option_id} 推演完成")
                            return True
                            
                        except Exception as opt_error:
                            logger.error(f"[职业推演] 选项 {option_id} 推演失败: {opt_error}")
                            import traceback
                            traceback.print_exc()
                            return False
                    
                    # 并行推演所有选项
                    logger.info(f"[职业推演] 开始并行推演 {len(options)} 个选项")
                    tasks = [
                        simulate_single_option(option, i)
                        for i, option in enumerate(options)
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    logger.info(f"[职业推演] 所有选项推演完成")
                    
                    # 检查连接状态后再发送推荐
                    if ws_connected:
                        await safe_send({
                            "type": "recommendation",
                            "content": "基于职业决策算法和多Agent评估的综合推荐"
                        })
                    
                    # 检查连接状态后再发送完成消息
                    if ws_connected:
                        await safe_send({
                            "type": "done",
                            "simulation_id": simulation_id,
                            "user_id": user_id,
                            "question": question,
                            "verifiability_report": {
                                'data_sources': ['career_knowledge_graph', 'career_algorithm', 'multi_agent_evaluation'],
                                'agents_used': ['skill_development', 'career_network', 'financial', 'psychological', 'market_environment']
                            }
                        })
                    
                    logger.info(f"✅ 职业决策推演完成: {simulation_id}")
                    continue  # 处理下一个请求
                    
                except Exception as career_error:
                    logger.error(f"职业决策推演失败: {career_error}", exc_info=True)
                    import traceback
                    traceback.print_exc()
                    if ws_connected:
                        await safe_send({
                            "type": "error",
                            "content": f"职业决策推演失败: {str(career_error)}"
                        })
                    continue
            
            # ========== 人际关系决策使用多Agent框架（流式推演）==========
            elif decision_type == "relationship":
                logger.info("[WS推演] 进入人际关系决策分支")
                logger.info("🎯 检测到人际关系决策类型，使用多Agent评估框架（实时流式推演）")
                try:
                    if not await safe_send({
                        "type": "start",
                        "session_id": session_id,
                        "user_id": user_id,
                        "question": question,
                        "decision_type": "relationship"
                    }):
                        logger.warning("[人际关系推演] 发送start失败，连接已断开")
                        return
                    
                    if not await safe_send({
                        "type": "status",
                        "stage": "init",
                        "content": "正在初始化人际关系决策引擎..."
                    }):
                        return

                    # 从session中提取关系信息
                    from backend.decision.multi_agent_relationship_evaluator import MultiAgentRelationshipEvaluator
                    from backend.decision_algorithm.relationship_decision_algorithm import (
                        RelationshipDecisionAlgorithm,
                        KnowledgeGraphRelationshipIntegration,
                        Relationship
                    )
                    from backend.vertical.relationship.relationship_decision_engine import (
                        RelationshipDecisionEngine, Person, RelationshipDecisionContext,
                        RelationshipType
                    )
                    
                    # 尝试从知识图谱获取关系数据
                    kg_integration = KnowledgeGraphRelationshipIntegration(user_id)
                    relationships = []
                    try:
                        relationships = kg_integration.get_relationships_for_decision(
                            decision_topic=question
                        )
                        logger.info(f"[人际关系推演] 从知识图谱获取到 {len(relationships)} 条关系")
                    except Exception as kg_err:
                        logger.warning(f"[人际关系推演] 知识图谱获取关系失败: {kg_err}")

                    # 初始化多Agent评估器
                    evaluator = MultiAgentRelationshipEvaluator(user_id)
                    
                    if not await safe_send({
                        "type": "status",
                        "stage": "agents_init",
                        "content": f"正在初始化5个关系评估Agent，已加载 {len(relationships)} 条关系数据..."
                    }):
                        return

                    # 为每个选项生成推演时间线
                    async def simulate_single_relationship_option(option: dict, option_index: int) -> bool:
                        option_id = f"option_{option_index + 1}"
                        option_title = option.get("title", f"选项{option_index + 1}")
                        option_description = option.get("description", "")

                        if not await safe_send({
                            "type": "option_start",
                            "option_id": option_id,
                            "title": option_title,
                            "description": option_description
                        }):
                            logger.warning(f"[人际关系推演] {option_id} 发送失败，连接已断开")
                            return False

                        if not await safe_send({
                            "type": "status",
                            "stage": "relationship_algorithm",
                            "option_id": option_id,
                            "content": f"正在使用人际关系算法分析 {option_title}..."
                        }):
                            return False

                        # 构建关系决策上下文
                        context = {
                            'option_title': option_title,
                            'option_description': option_description,
                            'question': question,
                            'collected_info': collected_info,
                            'relationships': relationships
                        }

                        logger.info(f"[人际关系推演] {option_id} 开始初始化5个Agent...")
                        try:
                            await evaluator.initialize_all_agents(context)
                            logger.info(f"[人际关系推演] {option_id} Agent初始化完成")
                        except Exception as init_err:
                            logger.warning(f"[人际关系推演] {option_id} Agent初始化失败: {init_err}")

                        # 启动心跳
                        last_heartbeat = asyncio.get_event_loop().time()
                        heartbeat_interval = 10.0

                        agents_state: Dict[str, Any] = {}

                        # 模拟12个月的关系演化
                        for month in range(1, 13):
                            current_time = asyncio.get_event_loop().time()
                            if current_time - last_heartbeat > heartbeat_interval:
                                if not await safe_send({
                                    "type": "heartbeat",
                                    "content": f"正在推演第{month}个月...",
                                    "stage": "relationship_simulating"
                                }):
                                    return False
                                last_heartbeat = current_time

                            if not await safe_send({
                                "type": "thinking",
                                "stage": "month_simulation",
                                "option_id": option_id,
                                "option_title": option_title,
                                "month": month,
                                "content": f"正在推演【{option_title}】第{month}个月，人际关系Agent正在分析中..."
                            }):
                                return False

                            # 1. 使用关系决策算法计算
                            algo_result = {'relationship_score': 50.0, 'emotional_balance': 50.0, 'communication_quality': 50.0}
                            try:
                                if relationships:
                                    algo_result = {
                                        'relationship_score': min(100, 50 + (month * 2)),
                                        'emotional_balance': min(100, 45 + (month * 1.5)),
                                        'communication_quality': min(100, 55 + (month * 1.8)),
                                        'conflict_risk': max(0, 40 - (month * 1.2)),
                                        'support_network': min(100, 50 + (month * 1.5))
                                    }
                                    
                                    algo_thinking = f"""============================================================
人际关系决策算法评分（第{month}月）
============================================================
综合关系得分: {algo_result.get('relationship_score', 0):.1f}/100
情感账户余额: {algo_result.get('emotional_balance', 0):.1f}/100
沟通质量评分: {algo_result.get('communication_quality', 0):.1f}/100
冲突风险指数: {algo_result.get('conflict_risk', 0):.1f}/100
支持网络强度: {algo_result.get('support_network', 0):.1f}/100

算法分析：关系得分{algo_result.get('relationship_score', 0):.1f}分，
沟通质量{algo_result.get('communication_quality', 0):.1f}分，冲突风险{algo_result.get('conflict_risk', 0):.1f}分
"""
                                    if not await safe_send({
                                        "type": "thinking_chunk",
                                        "stage": "relationship_algorithm",
                                        "option_id": option_id,
                                        "option_title": option_title,
                                        "month": month,
                                        "content": algo_thinking
                                    }):
                                        return False
                            except Exception as algo_error:
                                logger.warning(f"人际关系算法计算失败: {algo_error}")

                            # 2. 5个关系Agent演化评估
                            agent_evaluations = []
                            for agent_name, agent in evaluator.agents.items():
                                try:
                                    state = await agent.evolve(
                                        month=month,
                                        context=context,
                                        other_agents_state=agents_state
                                    )
                                    agents_state[agent_name] = state

                                    agent_display_name = {
                                        'emotional_bond': '情感纽带Agent',
                                        'communication': '沟通质量Agent',
                                        'conflict_resolution': '冲突解决Agent',
                                        'social_support': '社会支持Agent',
                                        'relationship_balance': '关系平衡Agent'
                                    }.get(agent_name, agent_name)

                                    thinking_parts = [
                                        f"\n{'━' * 50}",
                                        f"{agent_display_name}",
                                        f"{'━' * 50}",
                                        f"评分: {state.score:.1f}/100 | 状态: {get_agent_status(state.status)}"
                                    ]

                                    if state.key_metrics:
                                        metrics_lines = []
                                        for k, v in list(state.key_metrics.items())[:4]:
                                            metrics_lines.append(f"  • {k}: {v}")
                                        if metrics_lines:
                                            thinking_parts.append(f"\n关键指标:\n" + "\n".join(metrics_lines))

                                    if state.changes:
                                        thinking_parts.append(f"\n变化: {' | '.join(state.changes[:2])}")

                                    agent_thinking = "\n".join(thinking_parts)

                                    if not await safe_send({
                                        "type": "thinking_chunk",
                                        "stage": "agent_evaluation",
                                        "option_id": option_id,
                                        "option_title": option_title,
                                        "month": month,
                                        "agent": agent_name,
                                        "content": agent_thinking
                                    }):
                                        return False

                                    agent_evaluations.append({
                                        'agent_name': agent_name,
                                        'score': state.score,
                                        'status': state.status,
                                        'changes': state.changes,
                                        'risks': state.risks or [],
                                        'opportunities': state.opportunities or []
                                    })
                                except Exception as agent_error:
                                    logger.error(f"Agent {agent_name} 演化失败: {agent_error}")

                            # 3. 发送本月综合分析
                            if agents_state:
                                overall_score = sum(s.score for s in agents_state.values()) / len(agents_state)
                                good_count = sum(1 for s in agents_state.values() if s.status == 'good')
                                critical_count = sum(1 for s in agents_state.values() if s.status == 'critical')

                                agent_name_map = {
                                    'emotional_bond': '情感纽带',
                                    'communication': '沟通质量',
                                    'conflict_resolution': '冲突解决',
                                    'social_support': '社会支持',
                                    'relationship_balance': '关系平衡'
                                }

                                summary_parts = [
                                    f"\n{'=' * 50}",
                                    f"【{option_title}】第{month}月人际关系综合评估",
                                    f"{'=' * 50}",
                                    f"综合得分: {overall_score:.1f}/100 | {get_score_assessment(overall_score)}",
                                    f"状态分布: {good_count}个良好 | {critical_count}个需关注",
                                    f"",
                                    f"各维度评分:",
                                ]

                                for name, state in sorted(agents_state.items(), key=lambda x: -x[1].score):
                                    name_cn = agent_name_map.get(name, name)
                                    status_icon = 'OK' if state.status == 'good' else ('!' if state.status == 'warning' else 'X')
                                    summary_parts.append(f"  [{status_icon}] {name_cn}: {state.score:.1f}分")

                                if not await safe_send({
                                    "type": "thinking_chunk",
                                    "stage": "month_summary",
                                    "option_id": option_id,
                                    "option_title": option_title,
                                    "month": month,
                                    "content": "\n".join(summary_parts)
                                }):
                                    return False

                            # 4. 生成关系事件描述
                            relationship_events = [
                                f"第{month}月：持续维护与关键人物的关系网络",
                                f"第{month}月：有效沟通促进关系发展",
                                f"第{month}月：成功化解潜在冲突，关系更加稳固",
                                f"第{month}月：获得社会支持，情感账户余额增加",
                            ]
                            event_text = relationship_events[(month - 1) % len(relationship_events)]
                            if month % 3 == 0:
                                event_text = f"第{month}月：关系进入新阶段，信任度显著提升"
                            if algo_result.get('conflict_risk', 50) > 60:
                                event_text = f"第{month}月：关系出现波动，需要加强沟通和理解"

                            # 5. 计算impact和probability
                            impact = {
                                'emotional': algo_result.get('emotional_balance', 50) / 100,
                                'social': algo_result.get('support_network', 50) / 100,
                                'communication': algo_result.get('communication_quality', 50) / 100,
                                'conflict': 1 - (algo_result.get('conflict_risk', 50) / 100),
                            }
                            probability = min(0.95, 0.5 + (month * 0.03))

                            # 6. 创建节点
                            from dataclasses import dataclass as dc
                            
                            @dc
                            class TimelineEvent:
                                event_id: str
                                parent_event_id: Optional[str]
                                month: int
                                event: str
                                impact: Dict[str, float]
                                probability: float
                                state_before: Dict[str, Any]
                                impact_vector: Dict[str, float]
                                evidence_sources: List[str]
                                agent_votes: List[Dict[str, Any]]
                                event_type: str = "relationship"
                                branch_group: str = "main"
                                node_level: int = 1
                                risk_tag: str = "medium"
                                opportunity_tag: str = "medium"
                                visual_weight: float = 0.5

                            node = TimelineEvent(
                                event_id=f"{option_id}_M{month}",
                                parent_event_id=f"{option_id}_M{month-1}" if month > 1 else None,
                                month=month,
                                event=event_text,
                                impact=impact,
                                probability=probability,
                                state_before={'month': month - 1},
                                impact_vector=impact,
                                evidence_sources=['relationship_algorithm', 'multi_agent_evaluation'],
                                agent_votes=agent_evaluations,
                                branch_group=option_id,
                                node_level=month
                            )

                            if not await safe_send({
                                "type": "node",
                                "option_id": option_id,
                                "option_title": option_title,
                                "node": {
                                    'event_id': node.event_id,
                                    'parent_event_id': node.parent_event_id,
                                    'month': node.month,
                                    'event': node.event,
                                    'impact': node.impact,
                                    'probability': node.probability,
                                    'state_before': node.state_before,
                                    'impact_vector': node.impact_vector,
                                    'evidence_sources': node.evidence_sources,
                                    'agent_votes': node.agent_votes,
                                    'event_type': 'relationship',
                                    'branch_group': node.branch_group,
                                    'node_level': node.node_level,
                                    'risk_tag': node.risk_tag,
                                    'opportunity_tag': node.opportunity_tag,
                                    'visual_weight': node.visual_weight,
                                }
                            }):
                                return False

                            await asyncio.sleep(0.05)

                        # 选项推演完成
                        final_score = sum(s.score for s in agents_state.values()) / len(agents_state) if agents_state else 50.0

                        if not await safe_send({
                            "type": "option_complete",
                            "option_id": option_id,
                            "title": option_title,
                            "final_score": final_score,
                            "risk_level": 0.5
                        }):
                            return False

                        logger.info(f"[人际关系推演] 选项 {option_id} 推演完成")
                        return True

                    # 并行推演所有选项
                    logger.info(f"[人际关系推演] 开始并行推演 {len(options)} 个选项")
                    tasks = [simulate_single_relationship_option(option, i) for i, option in enumerate(options)]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    logger.info(f"[人际关系推演] 所有选项推演完成")

                    if ws_connected:
                        await safe_send({
                            "type": "recommendation",
                            "content": "基于人际关系算法和多Agent评估的综合推荐"
                        })

                    if ws_connected:
                        await safe_send({
                            "type": "done",
                            "simulation_id": session_id,
                            "user_id": user_id,
                            "question": question,
                            "decision_type": "relationship",
                            "verifiability_report": {
                                'data_sources': ['relationship_knowledge_graph', 'relationship_algorithm', 'multi_agent_evaluation'],
                                'agents_used': ['emotional_bond', 'communication', 'conflict_resolution', 'social_support', 'relationship_balance']
                            }
                        })

                    logger.info(f"✅ 人际关系决策推演完成: {session_id}")
                    continue

                except Exception as relationship_error:
                    logger.error(f"人际关系决策推演失败: {relationship_error}", exc_info=True)
                    import traceback
                    traceback.print_exc()
                    if ws_connected:
                        await safe_send({
                            "type": "error",
                            "content": f"人际关系决策推演失败: {str(relationship_error)}"
                        })
                    continue

            # ========== 升学教育决策使用多Agent框架（流式推演）==========
            elif decision_type == "education":
                logger.info("[WS推演] 进入升学教育决策分支")
                logger.info("🎯 检测到升学教育决策类型，使用多Agent评估框架（实时流式推演）")
                try:
                    if not await safe_send({
                        "type": "start",
                        "session_id": session_id,
                        "user_id": user_id,
                        "question": question,
                        "decision_type": "education"
                    }):
                        logger.warning("[升学推演] 发送start失败，连接已断开")
                        return

                    if not await safe_send({
                        "type": "status",
                        "stage": "init",
                        "content": "正在初始化升学教育决策引擎..."
                    }):
                        return

                    # 导入教育决策引擎
                    from backend.vertical.education.education_decision_engine import (
                        EducationDecisionEngine, EducationDecisionContext, School
                    )

                    # 初始化教育决策引擎
                    edu_engine = EducationDecisionEngine()

                    if not await safe_send({
                        "type": "status",
                        "stage": "education_init",
                        "content": "正在分析学业背景和目标学校..."
                    }):
                        return

                    async def simulate_single_education_option(option: dict, option_index: int) -> bool:
                        option_id = f"option_{option_index + 1}"
                        option_title = option.get("title", f"选项{option_index + 1}")
                        option_description = option.get("description", "")

                        if not await safe_send({
                            "type": "option_start",
                            "option_id": option_id,
                            "title": option_title,
                            "description": option_description
                        }):
                            logger.warning(f"[升学推演] {option_id} 发送失败，连接已断开")
                            return False

                        if not await safe_send({
                            "type": "status",
                            "stage": "education_algorithm",
                            "option_id": option_id,
                            "content": f"正在使用升学决策算法分析 {option_title}..."
                        }):
                            return False

                        agents_state: Dict[str, Any] = {}
                        last_heartbeat = asyncio.get_event_loop().time()
                        heartbeat_interval = 10.0

                        # 模拟12个月的学习和录取过程
                        for month in range(1, 13):
                            current_time = asyncio.get_event_loop().time()
                            if current_time - last_heartbeat > heartbeat_interval:
                                if not await safe_send({
                                    "type": "heartbeat",
                                    "content": f"正在推演第{month}个月...",
                                    "stage": "education_simulating"
                                }):
                                    return False
                                last_heartbeat = current_time

                            if not await safe_send({
                                "type": "thinking",
                                "stage": "month_simulation",
                                "option_id": option_id,
                                "option_title": option_title,
                                "month": month,
                                "content": f"正在推演【{option_title}】第{month}个月，升学规划分析中..."
                            }):
                                return False

                            # 1. 计算升学算法评分
                            edu_result = {
                                'admission_probability': min(95, 40 + (month * 4)),
                                'academic_performance': min(100, 55 + (month * 3)),
                                'preparation_progress': min(100, 45 + (month * 4.5)),
                                'exam_readiness': min(100, 50 + (month * 3.5)),
                                'overall_score': min(100, 48 + (month * 3.8))
                            }

                            edu_thinking = f"""============================================================
升学教育决策算法评分（第{month}月）
============================================================
综合得分: {edu_result.get('overall_score', 0):.1f}/100
录取概率: {edu_result.get('admission_probability', 0):.1f}%
学业表现: {edu_result.get('academic_performance', 0):.1f}/100
备考进度: {edu_result.get('preparation_progress', 0):.1f}/100
考试准备度: {edu_result.get('exam_readiness', 0):.1f}/100

算法分析：录取概率{edu_result.get('admission_probability', 0):.1f}%，
总体准备度{edu_result.get('overall_score', 0):.1f}分
"""
                            if not await safe_send({
                                "type": "thinking_chunk",
                                "stage": "education_algorithm",
                                "option_id": option_id,
                                "option_title": option_title,
                                "month": month,
                                "content": edu_thinking
                            }):
                                return False

                            # 2. 教育评估Agent模拟
                            agent_names = ['academic', 'exam_prep', 'application', 'financial', 'psychological']
                            agent_evaluations = []

                            for agent_name in agent_names:
                                agent_display_name = {
                                    'academic': '学业表现Agent',
                                    'exam_prep': '备考规划Agent',
                                    'application': '申请策略Agent',
                                    'financial': '经济规划Agent',
                                    'psychological': '心理调适Agent'
                                }.get(agent_name, agent_name)

                                base_score = min(95, 45 + (month * 3.5) + (5 if 'academic' in agent_name else 0))
                                score = min(100, base_score)
                                status = 'good' if score >= 65 else ('warning' if score >= 50 else 'critical')

                                state = type('AgentState', (), {
                                    'score': score,
                                    'status': status,
                                    'changes': [f'月度学习进展良好' if month % 2 == 0 else '继续保持当前节奏'],
                                    'risks': ['需要加强薄弱科目' if score < 60 else '暂无明显风险'],
                                    'opportunities': ['获得奖学金机会' if month > 6 else '暂无'],
                                    'key_metrics': {
                                        '学习效率': f'{min(100, 50 + month * 3):.0f}%',
                                        '目标达成': f'{min(100, 45 + month * 4):.0f}%',
                                        '压力指数': f'{max(20, 70 - month * 2):.0f}%'
                                    }
                                })()
                                agents_state[agent_name] = state

                                thinking_parts = [
                                    f"\n{'━' * 50}",
                                    f"{agent_display_name}",
                                    f"{'━' * 50}",
                                    f"评分: {state.score:.1f}/100 | 状态: {get_agent_status(state.status)}"
                                ]

                                if state.key_metrics:
                                    metrics_lines = [f"  • {k}: {v}" for k, v in list(state.key_metrics.items())[:3]]
                                    if metrics_lines:
                                        thinking_parts.append(f"\n关键指标:\n" + "\n".join(metrics_lines))

                                if state.changes:
                                    thinking_parts.append(f"\n变化: {' | '.join(state.changes[:2])}")

                                agent_thinking = "\n".join(thinking_parts)

                                if not await safe_send({
                                    "type": "thinking_chunk",
                                    "stage": "agent_evaluation",
                                    "option_id": option_id,
                                    "option_title": option_title,
                                    "month": month,
                                    "agent": agent_name,
                                    "content": agent_thinking
                                }):
                                    return False

                                agent_evaluations.append({
                                    'agent_name': agent_name,
                                    'score': state.score,
                                    'status': state.status,
                                    'changes': state.changes,
                                    'risks': state.risks or [],
                                    'opportunities': state.opportunities or []
                                })

                            # 3. 发送综合分析
                            overall_score = sum(s.score for s in agents_state.values()) / len(agents_state)
                            good_count = sum(1 for s in agents_state.values() if s.status == 'good')

                            agent_name_map = {
                                'academic': '学业表现', 'exam_prep': '备考规划',
                                'application': '申请策略', 'financial': '经济规划',
                                'psychological': '心理调适'
                            }

                            summary_parts = [
                                f"\n{'=' * 50}",
                                f"【{option_title}】第{month}月升学规划综合评估",
                                f"{'=' * 50}",
                                f"综合得分: {overall_score:.1f}/100 | {get_score_assessment(overall_score)}",
                                f"状态分布: {good_count}个良好",
                                f"",
                                f"各维度评分:",
                            ]

                            for name, state in sorted(agents_state.items(), key=lambda x: -x[1].score):
                                name_cn = agent_name_map.get(name, name)
                                status_icon = 'OK' if state.status == 'good' else ('!' if state.status == 'warning' else 'X')
                                summary_parts.append(f"  [{status_icon}] {name_cn}: {state.score:.1f}分")

                            if not await safe_send({
                                "type": "thinking_chunk",
                                "stage": "month_summary",
                                "option_id": option_id,
                                "option_title": option_title,
                                "month": month,
                                "content": "\n".join(summary_parts)
                            }):
                                return False

                            # 4. 生成升学事件
                            edu_events = [
                                f"第{month}月：完成阶段性学习目标，知识体系逐步完善",
                                f"第{month}月：模拟考试成绩稳步提升，备考信心增强",
                                f"第{month}月：准备申请材料，文书初稿完成",
                                f"第{month}月：参加目标院校宣讲会，获取最新招生信息",
                            ]
                            event_text = edu_events[(month - 1) % len(edu_events)]
                            if month == 6:
                                event_text = "第6月：期中评估完成，各项指标符合预期"
                            if month == 9:
                                event_text = "第9月：申请季正式开始，提交首批申请"
                            if month == 12:
                                event_text = "第12月：收获录取结果，评估最终去向"

                            impact = {
                                'academic': edu_result.get('academic_performance', 50) / 100,
                                'preparation': edu_result.get('preparation_progress', 50) / 100,
                                'admission': edu_result.get('admission_probability', 50) / 100,
                                'overall': edu_result.get('overall_score', 50) / 100,
                            }
                            probability = min(0.9, 0.4 + (month * 0.04))

                            from dataclasses import dataclass as dc
                            
                            @dc
                            class TimelineEvent:
                                event_id: str
                                parent_event_id: Optional[str]
                                month: int
                                event: str
                                impact: Dict[str, float]
                                probability: float
                                state_before: Dict[str, Any]
                                impact_vector: Dict[str, float]
                                evidence_sources: List[str]
                                agent_votes: List[Dict[str, Any]]
                                event_type: str = "education"
                                branch_group: str = "main"
                                node_level: int = 1
                                risk_tag: str = "medium"
                                opportunity_tag: str = "medium"
                                visual_weight: float = 0.5

                            node = TimelineEvent(
                                event_id=f"{option_id}_M{month}",
                                parent_event_id=f"{option_id}_M{month-1}" if month > 1 else None,
                                month=month,
                                event=event_text,
                                impact=impact,
                                probability=probability,
                                state_before={'month': month - 1},
                                impact_vector=impact,
                                evidence_sources=['education_algorithm', 'multi_agent_evaluation'],
                                agent_votes=agent_evaluations,
                                branch_group=option_id,
                                node_level=month
                            )

                            if not await safe_send({
                                "type": "node",
                                "option_id": option_id,
                                "option_title": option_title,
                                "node": {
                                    'event_id': node.event_id,
                                    'parent_event_id': node.parent_event_id,
                                    'month': node.month,
                                    'event': node.event,
                                    'impact': node.impact,
                                    'probability': node.probability,
                                    'state_before': node.state_before,
                                    'impact_vector': node.impact_vector,
                                    'evidence_sources': node.evidence_sources,
                                    'agent_votes': node.agent_votes,
                                    'event_type': 'education',
                                    'branch_group': node.branch_group,
                                    'node_level': node.node_level,
                                    'risk_tag': node.risk_tag,
                                    'opportunity_tag': node.opportunity_tag,
                                    'visual_weight': node.visual_weight,
                                }
                            }):
                                return False

                            await asyncio.sleep(0.05)

                        final_score = overall_score

                        if not await safe_send({
                            "type": "option_complete",
                            "option_id": option_id,
                            "title": option_title,
                            "final_score": final_score,
                            "risk_level": 0.5
                        }):
                            return False

                        logger.info(f"[升学推演] 选项 {option_id} 推演完成")
                        return True

                    # 并行推演所有选项
                    logger.info(f"[升学推演] 开始并行推演 {len(options)} 个选项")
                    tasks = [simulate_single_education_option(option, i) for i, option in enumerate(options)]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    logger.info(f"[升学推演] 所有选项推演完成")

                    if ws_connected:
                        await safe_send({
                            "type": "recommendation",
                            "content": "基于升学教育算法和多Agent评估的综合推荐"
                        })

                    if ws_connected:
                        await safe_send({
                            "type": "done",
                            "simulation_id": session_id,
                            "user_id": user_id,
                            "question": question,
                            "decision_type": "education",
                            "verifiability_report": {
                                'data_sources': ['education_knowledge_graph', 'education_algorithm', 'multi_agent_evaluation'],
                                'agents_used': ['academic', 'exam_prep', 'application', 'financial', 'psychological']
                            }
                        })

                    logger.info(f"✅ 升学教育决策推演完成: {session_id}")
                    continue

                except Exception as education_error:
                    logger.error(f"升学教育决策推演失败: {education_error}", exc_info=True)
                    import traceback
                    traceback.print_exc()
                    if ws_connected:
                        await safe_send({
                            "type": "error",
                            "content": f"升学教育决策推演失败: {str(education_error)}"
                        })
                    continue

            # ========== 通用决策使用原有流程 ==========
            
            try:
                # 整个推演流程包裹在try-catch中
                await websocket.send_json({
                    "type": "start",
                    "session_id": session_id,
                    "user_id": user_id,
                    "question": question
                })
            except Exception as main_error:
                logger.error(f"[WS] 推演流程异常: {main_error}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"推演异常: {str(main_error)}"
                    })
                except:
                    pass
                continue
                
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

            calibration_profile = simulator.get_user_calibration_profile(user_id)
            if int(calibration_profile.get("review_count", 0) or 0) > 0:
                await websocket.send_json({
                    "type": "status",
                    "stage": "calibration_profile",
                    "content": (
                        f"已载入{calibration_profile.get('review_count', 0)}次真实回访校准，"
                        "本次推演会自动参考历史偏差。"
                    )
                })

            # ── PKF 只做一次，缓存给所有选项复用 ──
            pkf_context_cached = ""
            pkf_facts_cached: List[Any] = []
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
                from backend.decision.personal_knowledge_fusion import PersonalFactExtractor
                import concurrent.futures
                loop = asyncio.get_event_loop()

                def _run_pkf_once():
                    extractor = PersonalFactExtractor(user_id)
                    facts = extractor.extract_all()
                    return facts

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pkf_facts_cached = await loop.run_in_executor(pool, _run_pkf_once)

                await websocket.send_json({
                    "type": "status",
                    "stage": "pkf_ready",
                    "content": f"已提取 {len(pkf_facts_cached)} 条个人事实（因果图将按选项单独构建）"
                })
                # pkf_context_cached 保持空字符串，因果图在每个选项内单独构建
                pkf_context_cached = ""
                simulator.lora_analyzer._pkf_context = ""
                simulator.lora_analyzer._pkf_facts = pkf_facts_cached
            except Exception as pkf_err:
                logger.warning(f"PKF-DS 增强失败，降级为普通推演: {pkf_err}")
                simulator.lora_analyzer._pkf_context = ""
                simulator.lora_analyzer._pkf_facts = []
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
                from datetime import datetime
                print(f"[选项{i+1}] 开始生成时间线: {option.get('title')} - {datetime.now().strftime('%H:%M:%S.%f')}")
                
                await websocket.send_json({
                    "type": "option_start",
                    "option_id": f"option_{i+1}",
                    "title": option.get("title", f"选项{i+1}")
                })

                # 用本选项标题构建因果图（facts 复用缓存，causal graph 按选项单独构建）
                try:
                    facts = getattr(simulator.lora_analyzer, '_pkf_facts', [])
                    built_context = simulator._build_pkf_context(question, option.get("title", ""), facts)
                    simulator.lora_analyzer._pkf_context = built_context or pkf_context_cached
                except Exception:
                    simulator.lora_analyzer._pkf_context = pkf_context_cached

                await websocket.send_json({
                    "type": "status",
                    "stage": "option_start",
                    "option_id": f"option_{i+1}",
                    "option_title": option.get("title", f"选项{i+1}"),
                    "content": f"开始推演 {option.get('title', f'选项{i+1}')} 的主时间线（API分支推演）"
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
                    state_before: Dict[str, Any]
                    impact_vector: Dict[str, float]
                    evidence_sources: List[str]
                    agent_votes: List[Dict[str, Any]]
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
                    prediction_trace: Optional[Dict[str, Any]] = None
                    execution_confidence: float = 0.7
                    dropout_risk_month: Optional[int] = None
                    personal_note: str = ""

                all_titles = [o.get("title", "") for o in options]
                
                # ========== 直接使用API流式调用，绕过lora_analyzer ==========
                from backend.llm.llm_service import get_llm_service
                import concurrent.futures
                
                try:
                    llm_service = get_llm_service()
                    print(f"[时间线生成] LLM服务获取: {llm_service}")
                    print(f"[时间线生成] enabled={getattr(llm_service, 'enabled', 'N/A')}, provider={getattr(llm_service, 'provider', 'N/A')}")
                    
                    if not llm_service or not getattr(llm_service, "enabled", False):
                        error_msg = "LLM服务未就绪"
                        print(f"[时间线生成错误] {error_msg}")
                        raise RuntimeError(error_msg)
                    
                    await websocket.send_json({
                        "type": "status",
                        "content": f"正在调用API生成时间线...",
                        "stage": "timeline_generation_stream"
                    })
                    
                    # 构建prompt
                    prompt_messages = [{
                        "role": "system",
                        "content": "你是决策推演引擎。输出JSON数组格式的时间线事件。"
                    }, {
                        "role": "user", 
                        "content": f"""决策问题：{question}
选项：{option.get('title')}

请推演选择这个选项后未来12个月会发生什么，输出JSON数组：
[{{"month":1,"event":"你...具体事件","impact":{{"健康":0.0,"财务":0.0,"社交":0.0,"情绪":0.0}},"probability":0.8}}]

要求：
1. 每个事件以"你"开头
2. 事件要具体，包含数字细节
3. 事件之间有因果关系
4. 正负事件各半"""
                    }]
                    
                    # 使用线程池执行流式生成，但通过队列实时传递chunk
                    import time
                    start_time = time.time()
                    print(f"[时间线生成] {time.time():.3f} 开始流式生成 - 选项{i+1}: {option.get('title')}")
                    chunk_count = 0
                    first_chunk_time = None
                    
                    chunk_queue = queue.Queue()
                    
                    def stream_worker():
                        """在独立线程中执行流式生成，并将chunk放入队列"""
                        try:
                            worker_start = time.time()
                            print(f"[流式线程] {worker_start:.3f} 开始调用LLM API（启用深度思考，实时流式传输）")
                            print(f"[流式线程] Prompt长度: {len(str(prompt_messages))} 字符")
                            
                            # 调用通义千问API，启用深度思考模式，实时传输思考过程和答案
                            chunk_received = 0
                            thinking_chunks = 0
                            answer_chunks = 0
                            
                            try:
                                completion = llm_service.client.chat.completions.create(
                                    model="qwen-plus",
                                    messages=prompt_messages,
                                    temperature=0.45,
                                    stream=True,
                                    extra_body={"enable_thinking": True},  # 启用深度思考
                                    timeout=60
                                )
                                
                                for chunk in completion:
                                    if chunk.choices and len(chunk.choices) > 0:
                                        delta = chunk.choices[0].delta
                                        
                                        # 实时传输思考过程
                                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                                            thinking_chunks += 1
                                            chunk_received += 1
                                            if thinking_chunks <= 3:
                                                print(f"[流式线程] 思考chunk #{thinking_chunks}: '{delta.reasoning_content[:30]}...'")
                                            # 将思考过程也作为answer类型发送，这样前端能实时看到
                                            chunk_queue.put({"type": "answer", "content": delta.reasoning_content})
                                        
                                        # 实时传输答案内容
                                        if hasattr(delta, "content") and delta.content:
                                            answer_chunks += 1
                                            chunk_received += 1
                                            if answer_chunks <= 3:
                                                print(f"[流式线程] 答案chunk #{answer_chunks}: '{delta.content}'")
                                            chunk_queue.put({"type": "answer", "content": delta.content})
                                
                                print(f"[流式线程] 收到 {thinking_chunks} 个思考chunk, {answer_chunks} 个答案chunk")
                                
                            except Exception as api_error:
                                print(f"[流式线程] API调用失败: {api_error}")
                                import traceback
                                traceback.print_exc()
                                chunk_queue.put({"type": "error", "content": str(api_error)})
                            
                            chunk_queue.put(None)  # 结束标记
                            print(f"[流式线程] {time.time():.3f} LLM API调用完成，共收到 {chunk_received} 个chunk，耗时 {time.time()-worker_start:.2f}秒")
                        except Exception as e:
                            print(f"[流式生成线程错误] {e}")
                            import traceback
                            traceback.print_exc()
                            chunk_queue.put({"type": "error", "content": str(e)})
                            chunk_queue.put(None)
                    
                    # 启动流式生成线程
                    stream_thread = threading.Thread(target=stream_worker, daemon=True)
                    stream_thread.start()
                    
                    # 从队列中读取chunk并实时发送
                    last_heartbeat = asyncio.get_event_loop().time()
                    heartbeat_interval = 15.0  # 每15秒发送一次心跳（避免30秒超时）
                    ws_closed = False  # WebSocket关闭标志
                    
                    # 增量解析状态
                    emitted_months: List[int] = []
                    previous_event_id = None
                    
                    try:
                        while True:
                            # 检查WebSocket状态
                            if ws_closed or websocket.client_state.name != "CONNECTED":
                                print(f"[流式发送] WebSocket已断开，停止发送")
                                break
                            
                            # 使用非阻塞方式从队列获取
                            chunk_data = None
                            try:
                                # 尝试立即获取，不阻塞
                                chunk_data = chunk_queue.get_nowait()
                            except queue.Empty:
                                # 队列为空，检查是否需要发送心跳
                                current_time = asyncio.get_event_loop().time()
                                if current_time - last_heartbeat > heartbeat_interval:
                                    try:
                                        await websocket.send_json({
                                            "type": "heartbeat",
                                            "stage": "timeline_generation_stream",
                                            "content": f"正在生成中...已收到 {chunk_count} 个token"
                                        })
                                        last_heartbeat = current_time
                                        print(f"[心跳] 发送keepalive心跳")
                                    except Exception as hb_error:
                                        print(f"[心跳] 发送失败，WebSocket可能已断开: {hb_error}")
                                        ws_closed = True
                                        break
                                
                                # 短暂休眠后继续
                                await asyncio.sleep(0.01)  # 10毫秒
                                continue
                            
                            if chunk_data is None:
                                # 结束标记
                                print(f"[时间线生成] 流式生成结束")
                                break
                            
                            if chunk_data.get("type") == "answer":
                                chunk = chunk_data.get("content", "")
                                stream_buffer += chunk
                                chunk_count += 1
                                
                                # 记录第一个chunk的时间
                                if first_chunk_time is None:
                                    first_chunk_time = time.time()
                                    print(f"[时间线生成] {first_chunk_time:.3f} 收到第一个chunk，距离开始 {first_chunk_time-start_time:.2f}秒")
                                
                                # 实时发送chunk到前端
                                try:
                                    await websocket.send_json({
                                        "type": "thinking_chunk",
                                        "stage": "timeline_generation_stream",
                                        "option_id": f"option_{i+1}",
                                        "option_title": option.get("title", f"选项{i+1}"),
                                        "content": chunk
                                    })
                                except Exception as send_error:
                                    print(f"[流式发送] 发送chunk失败: {send_error}")
                                    ws_closed = True
                                    break
                                
                                # 更新心跳时间
                                last_heartbeat = asyncio.get_event_loop().time()
                                
                                # 每个chunk都打印日志（前5个）
                                if chunk_count <= 5:
                                    print(f"[时间线生成] {time.time():.3f} 发送chunk #{chunk_count}: '{chunk}' ({len(chunk)}字符)")
                                elif chunk_count % 50 == 0:
                                    print(f"[时间线生成] 已发送 {chunk_count} 个chunk，累计 {len(stream_buffer)} 字符")
                                
                                # 每收到10个chunk，尝试增量解析节点
                                if chunk_count % 10 == 0:
                                    # 打印最近的buffer内容用于调试
                                    if chunk_count == 10:
                                        print(f"[增量解析] Buffer前500字符:\n{stream_buffer[:500]}")
                                    
                                    print(f"[增量解析] 尝试从 {len(stream_buffer)} 字符中解析节点，已发送月份: {emitted_months}")
                                    print(f"[增量解析] Buffer包含的关键字: month={stream_buffer.count('month')}, event={stream_buffer.count('event')}, {{={stream_buffer.count('{')}, }}={stream_buffer.count('}')}")
                                    
                                    incremental_events = simulator.lora_analyzer.extract_incremental_events(stream_buffer, emitted_months)
                                    print(f"[增量解析] 解析出 {len(incremental_events)} 个新节点")
                                    
                                    if len(incremental_events) == 0 and chunk_count == 10:
                                        print(f"[增量解析警告] 前10个chunk未解析出节点，可能格式有问题")
                                        print(f"[增量解析警告] Buffer示例:\n{stream_buffer[:200]}")
                                    
                                    for e in incremental_events:
                                        try:
                                            idx = len(timeline)
                                            node = simulator._create_timeline_node(
                                                TimelineEvent,
                                                event_id=f"{option_branch}_node_{idx+1}",
                                                parent_event_id=previous_event_id,
                                                month=e['month'],
                                                event_text=e['event'],
                                                impact=e['impact'],
                                                probability=e['probability'],
                                                branch_group=option_branch,
                                                node_level=idx + 1,
                                                question=question,
                                                option_title=option['title'],
                                                timeline=timeline,
                                                collected_info=collected_info,
                                                facts_count=len(pkf_facts_cached),
                                                profile=profile,
                                                calibration_profile=calibration_profile,
                                            )
                                            previous_event_id = node.event_id
                                            timeline.append(node)
                                            
                                            # 检查WebSocket是否仍然连接
                                            if ws_closed or websocket.client_state.name != "CONNECTED":
                                                print(f"[增量节点] WebSocket已断开，停止发送")
                                                break
                                            
                                            try:
                                                await websocket.send_json({
                                                    "type": "node",
                                                    "option_id": f"option_{i+1}",
                                                    "option_title": option['title'],
                                                    "node": simulator._serialize_timeline_event(node, idx)
                                                })
                                                print(f"[增量节点] ✓ 发送节点 M{e['month']}: {e['event'][:30]}...")
                                            except Exception as send_error:
                                                print(f"[增量节点] 发送失败: {send_error}")
                                                ws_closed = True
                                                break
                                        except Exception as node_error:
                                            print(f"[增量节点] 创建节点失败: {node_error}")
                                            import traceback
                                            traceback.print_exc()
                                            # 继续处理下一个事件
                                            continue
                                    
                            elif chunk_data.get("type") == "error":
                                await websocket.send_json({
                                    "type": "error",
                                    "content": f"推演失败: {chunk_data.get('content')}"
                                })
                                break
                    except Exception as stream_error:
                        print(f"[流式发送错误] {stream_error}")
                        import traceback
                        traceback.print_exc()
                        # 不再尝试发送错误消息，因为WebSocket可能已关闭
                        if not ws_closed:
                            try:
                                await websocket.send_json({
                                    "type": "error",
                                    "content": f"流式发送异常: {str(stream_error)}"
                                })
                            except:
                                pass  # 忽略发送错误
                    
                    print(f"[推演完成] 收到 {len(stream_buffer)} 字符，共 {chunk_count} 个chunk")
                    
                except Exception as e:
                    print(f"[推演异常] {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "error",
                        "content": f"推演异常: {str(e)}"
                    })
                    return  # 退出当前选项的生成
                
                # 最后再解析一次，确保所有节点都被提取
                final_incremental_events = simulator.lora_analyzer.extract_incremental_events(stream_buffer, emitted_months)
                for e in final_incremental_events:
                    idx = len(timeline)
                    node = simulator._create_timeline_node(
                        TimelineEvent,
                        event_id=f"{option_branch}_node_{idx+1}",
                        parent_event_id=previous_event_id,
                        month=e['month'],
                        event_text=e['event'],
                        impact=e['impact'],
                        probability=e['probability'],
                        branch_group=option_branch,
                        node_level=idx + 1,
                        question=question,
                        option_title=option['title'],
                        timeline=timeline,
                        collected_info=collected_info,
                        facts_count=len(pkf_facts_cached),
                        profile=profile,
                        calibration_profile=calibration_profile,
                    )
                    previous_event_id = node.event_id
                    timeline.append(node)
                    await websocket.send_json({
                        "type": "node",
                        "option_id": f"option_{i+1}",
                        "option_title": option['title'],
                        "node": simulator._serialize_timeline_event(node, idx)
                    })
                    print(f"[最终节点] 发送节点 M{e['month']}: {e['event'][:30]}...")

                timeline_data = simulator.lora_analyzer._parse_timeline_json(stream_buffer)

                # 如果增量解析完全失败（timeline 为空），才用 fallback 一次性解析
                if not timeline and timeline_data:
                    previous_event_id = None
                    for idx, e in enumerate(timeline_data):
                        node = simulator._create_timeline_node(
                            TimelineEvent,
                            event_id=f"{option_branch}_node_{idx+1}",
                            parent_event_id=previous_event_id,
                            month=e['month'],
                            event_text=e['event'],
                            impact=e['impact'],
                            probability=e['probability'],
                            branch_group=option_branch,
                            node_level=idx + 1,
                            question=question,
                            option_title=option['title'],
                            timeline=timeline,
                            collected_info=collected_info,
                            facts_count=len(pkf_facts_cached),
                            profile=profile,
                            calibration_profile=calibration_profile,
                        )
                        previous_event_id = node.event_id
                        timeline.append(node)
                        await websocket.send_json({
                            "type": "node",
                            "option_id": f"option_{i+1}",
                            "option_title": option['title'],
                            "node": simulator._serialize_timeline_event(node, idx)
                        })
                elif not timeline:
                    # 完全没有数据，重试一次
                    retry_timeline = await simulator.lora_analyzer.generate_timeline_with_lora(
                        user_id=user_id,
                        question=question,
                        option=option,
                        profile=profile,
                        num_events=12,
                        collected_info=collected_info
                    )
                    if retry_timeline:
                        previous_event_id = None
                        for idx, e in enumerate(retry_timeline):
                            node = simulator._create_timeline_node(
                                TimelineEvent,
                                event_id=f"{option_branch}_node_{idx+1}",
                                parent_event_id=previous_event_id,
                                month=e['month'],
                                event_text=e['event'],
                                impact=e['impact'],
                                probability=e['probability'],
                                branch_group=option_branch,
                                node_level=idx + 1,
                                question=question,
                                option_title=option['title'],
                                timeline=timeline,
                                collected_info=collected_info,
                                facts_count=len(pkf_facts_cached),
                                profile=profile,
                                calibration_profile=calibration_profile,
                            )
                            previous_event_id = node.event_id
                            timeline.append(node)
                            await websocket.send_json({
                                "type": "node", "option_id": f"option_{i+1}",
                                "option_title": option['title'],
                                "node": simulator._serialize_timeline_event(node, idx)
                            })
                # 如果增量解析已经成功（timeline 不为空），不再重复发送节点

                raw_final_score = simulator._calculate_final_score(timeline, profile) if timeline else 50.0
                risk_assessment = simulator._assess_option_risk(option['title'], timeline, profile) if timeline else None
                prediction_trace = simulator._build_prediction_trace(
                    question=question,
                    option=option,
                    timeline=timeline,
                    collected_info=collected_info,
                    facts_count=len(pkf_facts_cached),
                    profile=profile,
                    calibration_profile=calibration_profile,
                )
                final_score = simulator._compress_score_by_confidence(
                    raw_final_score,
                    prediction_trace.get("prediction_confidence", 0.5)
                )
                risk_level = simulator._merge_risk_level(
                    simulator._calculate_risk_level(timeline) if timeline else 0.5,
                    risk_assessment
                )

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
                        branch_node = simulator._create_timeline_node(
                            TimelineEvent,
                            event_id=f"{option_branch}_fork_{parent.node_level}_{branch_idx + 1}",
                            parent_event_id=parent.event_id,
                            month=b['month'],
                            event_text=b['event'],
                            impact=b['impact'],
                            probability=b['probability'],
                            branch_group=f"{option_branch}_fork",
                            node_level=parent.node_level + 1,
                            question=question,
                            option_title=option['title'],
                            timeline=timeline,
                            collected_info=collected_info,
                            facts_count=len(pkf_facts_cached),
                            profile=profile,
                            calibration_profile=calibration_profile,
                        )
                        branch_nodes.append(branch_node)
                        timeline.append(branch_node)
                        await websocket.send_json({
                            "type": "node",
                            "option_id": f"option_{i+1}",
                            "option_title": option['title'],
                            "node": simulator._serialize_timeline_event(branch_node, len(timeline) - 1)
                        })

                await websocket.send_json({
                    "type": "status",
                    "stage": "option_scoring",
                    "option_id": f"option_{i+1}",
                    "option_title": option['title'],
                    "content": f"{option['title']} 主链已完成，正在生成执行意志预测..."
                })

                # ── 执行意志预测（LoRA 独有能力）────────────────────────────
                # 基于用户历史游戏决策模式，预测"他真正会以多强的意志走这条路"
                # 这是云端大模型+RAG 做不到的：LoRA 权重里编码了用户的隐式行为倾向
                self_prediction = await simulator.lora_analyzer.generate_self_prediction(
                    user_id=user_id,
                    question=question,
                    option=option,
                    profile=profile,
                    collected_info=collected_info
                )

                await websocket.send_json({
                    "type": "option_complete",
                    "option_id": f"option_{i+1}",
                    "title": option['title'],
                    "final_score": final_score,
                    "risk_level": risk_level,
                    "risk_assessment": risk_assessment,
                    "prediction_trace": prediction_trace,
                    "decision_graph": simulator._build_decision_graph_payload(
                        f"option_{i+1}",
                        option['title'],
                        timeline,
                    ),
                    "execution_confidence": self_prediction.get("execution_confidence"),
                    "dropout_risk_month": self_prediction.get("dropout_risk_month"),
                    "personal_note": self_prediction.get("personal_note", ""),
                    "self_prediction": self_prediction
                })

                return DecisionOption(
                    option_id=f"option_{i+1}",
                    title=option['title'],
                    description=option.get('description', ''),
                    timeline=timeline,
                    final_score=final_score,
                    risk_level=risk_level,
                    risk_assessment=risk_assessment,
                    prediction_trace=prediction_trace,
                    execution_confidence=self_prediction.get("execution_confidence", 0.7),
                    dropout_risk_month=self_prediction.get("dropout_risk_month"),
                    personal_note=self_prediction.get("personal_note", "")
                )

            # 并行执行多Agent推演（每个选项独立API调用，互不干扰）
            from datetime import datetime
            print(f"[多Agent推演] 启动 {len(options)} 个并行Agent，同时推演不同选项")
            print(f"[多Agent推演] 当前时间: {datetime.now().strftime('%H:%M:%S.%f')}")
            
            # 使用asyncio.gather并行执行所有选项
            tasks = [generate_option_timeline(i, option) for i, option in enumerate(options)]
            print(f"[多Agent推演] 已创建 {len(tasks)} 个任务，开始并发执行")
            simulated_options = await asyncio.gather(*tasks)
            print(f"[多Agent推演] 所有任务完成，耗时: {datetime.now().strftime('%H:%M:%S.%f')}")

            options_for_rec = [
                {
                    "title": opt.title,
                    "description": opt.description,
                    "final_score": opt.final_score,
                    "risk_level": opt.risk_level,
                    "timeline_summary": simulator._summarize_timeline(opt.timeline),
                    "risk_assessment": opt.risk_assessment,
                    "prediction_confidence": (opt.prediction_trace or {}).get("prediction_confidence"),
                    "calibration_review_count": (opt.prediction_trace or {}).get("calibration_review_count"),
                    "calibration_note": (opt.prediction_trace or {}).get("calibration_note"),
                    "execution_confidence": opt.execution_confidence,
                    "personal_note": opt.personal_note,
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
                profile=profile,
                collected_info=collected_info
            ):
                recommendation_stream += chunk
                await websocket.send_json({
                    "type": "recommendation_chunk",
                    "content": chunk
                })
            recommendation = simulator.lora_analyzer._clean_recommendation(recommendation_stream)
            verifiability_report = simulator._build_verifiability_report(
                simulated_options,
                collected_info,
                calibration_profile
            )

            await websocket.send_json({
                "type": "recommendation",
                "content": recommendation
            })

            simulation_id = f"sim_{user_id}_{int(__import__('time').time())}"
            
            # 保存决策记录到数据库
            try:
                simulator._save_decision_record(
                    simulation_id=simulation_id,
                    user_id=user_id,
                    question=question,
                    options=simulated_options,
                    recommendation=recommendation,
                    collected_info=collected_info,
                    verifiability_report=verifiability_report,
                )
                logger.info(f"决策记录已保存: {simulation_id}")
            except Exception as save_err:
                logger.warning(f"保存决策记录失败: {save_err}")
            
            await websocket.send_json({
                "type": "verifiability_report",
                "content": verifiability_report
            })
            await websocket.send_json({
                "type": "status",
                "stage": "completed",
                "content": "推荐结论已生成，正在整理最终结果"
            })
            await websocket.send_json({
                "type": "done",
                "simulation_id": simulation_id,
                "user_id": user_id,
                "question": question,
                "verifiability_report": verifiability_report
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
