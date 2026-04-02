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
import re

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
        weight = 0.55 + 0.45 * prediction_confidence
        return round(50 + (raw_score - 50) * weight, 1)

    def _merge_risk_level(self, generated_risk: float, risk_assessment: Optional[Dict[str, Any]]) -> float:
        if not risk_assessment:
            return round(min(1.0, max(0.0, generated_risk)), 2)
        engine_risk = min(1.0, max(0.0, float(risk_assessment.get("overall_risk", 5.0)) / 10.0))
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
            asdict(event) if hasattr(event, "__dataclass_fields__") else event
            for event in getattr(option, "timeline", []) or []
        ]
        execution_confidence = getattr(option, "execution_confidence", None)
        dropout_risk_month = getattr(option, "dropout_risk_month", None)
        personal_note = getattr(option, "personal_note", "") or ""
        return {
            "option_id": getattr(option, "option_id", ""),
            "title": getattr(option, "title", ""),
            "description": getattr(option, "description", ""),
            "timeline": timeline,
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
            "schema_version": 2,
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
                    risk_tag="high" if negative_impact >= 0.25 else ("low" if negative_impact <= 0.15 else "medium"),
                    opportunity_tag="high" if positive_impact >= 0.5 else ("low" if positive_impact <= 0.1 else "medium"),
                    visual_weight=max(0.2, min(1.0, positive_impact + negative_impact))
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
        
        # 2. 使用当前推理引擎进行决策模拟
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
            collected_info = session.get("collected_info", {})
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
                    prediction_trace: Optional[Dict[str, Any]] = None
                    execution_confidence: float = 0.7
                    dropout_risk_month: Optional[int] = None
                    personal_note: str = ""

                all_titles = [o.get("title", "") for o in options]
                async for chunk in simulator.lora_analyzer.stream_timeline_generation(
                    user_id=user_id,
                    question=question,
                    option=option,
                    profile=profile,
                    num_events=12,
                    all_option_titles=all_titles,
                    collected_info=collected_info
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
                        risk_tag = "high" if negative_impact >= 0.25 else ("low" if negative_impact <= 0.15 else "medium")
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
                        risk_tag = "high" if negative_impact >= 0.25 else ("low" if negative_impact <= 0.15 else "medium")
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
                            negative_impact = sum(abs(v) for v in e['impact'].values() if v < 0)
                            positive_impact = sum(v for v in e['impact'].values() if v > 0)
                            risk_tag = "high" if negative_impact >= 0.25 else ("low" if negative_impact <= 0.15 else "medium")
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
                            risk_tag="high" if negative_impact >= 0.25 else ("low" if negative_impact <= 0.15 else "medium"),
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
