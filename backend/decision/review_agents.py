from typing import Any, Dict, List, Optional


class ReviewAgentScaffold:
    """Heuristic reviewer agents for scoring and calibrating decision nodes."""

    def _clamp(self, value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        return max(minimum, min(maximum, value))

    def _build_reason(
        self,
        label: str,
        score: float,
        probability: float,
        focus: List[str],
        state_before: Dict[str, Any],
    ) -> str:
        phase = str(state_before.get("phase") or "unknown")
        focus_text = "、".join(focus[:2]) if focus else "当前路径"
        return (
            f"{label}关注 {focus_text}，评分 {score:.2f}，"
            f"结合当前阶段 {phase} 与事件概率 {probability:.0%} 给出判断。"
        )

    def review_node(
        self,
        *,
        event_text: str,
        impact_vector: Dict[str, float],
        probability: float,
        risk_tag: str,
        opportunity_tag: str,
        evidence_sources: List[str],
        state_before: Dict[str, Any],
        parent_event: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        # 防御性处理：确保所有参数不为None
        impact_vector = impact_vector or {}
        probability = float(probability if probability is not None else 0.0)
        evidence_sources = evidence_sources or []
        state_before = state_before or {}
        
        positive = sum(value for value in impact_vector.values() if value > 0)
        negative = sum(abs(value) for value in impact_vector.values() if value < 0)
        evidence_weight = min(1.0, len(evidence_sources) / 4.0)
        branch_penalty = 0.08 if bool(state_before.get("is_branching")) else 0.0
        
        # 安全获取prior_momentum
        prior_momentum_raw = state_before.get("momentum")
        prior_momentum = float(prior_momentum_raw) if prior_momentum_raw is not None else 0.0
        focus = [
            key
            for key, _ in sorted(
                impact_vector.items(),
                key=lambda item: abs(item[1]),
                reverse=True,
            )[:3]
        ]
        parent_event_name = str((parent_event or {}).get("event") or "")
        continuity_bonus = 0.08 if parent_event_name and parent_event_name != event_text else 0.0

        confidence = round(
            self._clamp(0.45 + probability * 0.28 + evidence_weight * 0.2),
            2,
        )

        risk_score = round(
            self._clamp(negative * 1.45 + (1 - probability) * 0.24 + branch_penalty),
            2,
        )
        opportunity_score = round(
            self._clamp(positive * 1.2 + probability * 0.22 - negative * 0.18),
            2,
        )
        execution_score = round(
            self._clamp(
                probability * 0.44
                + positive * 0.36
                - negative * 0.18
                + max(0.0, prior_momentum) * 0.08
                - branch_penalty
            ),
            2,
        )
        consistency_score = round(
            self._clamp(
                0.48
                + continuity_bonus
                + evidence_weight * 0.14
                + min(0.18, probability * 0.18)
                - abs(positive - negative) * 0.08
            ),
            2,
        )

        votes = [
            {
                "agent_id": "risk_reviewer",
                "agent_name": "风险评审",
                "stance": "caution" if risk_score >= 0.56 else "stable",
                "score": risk_score,
                "confidence": confidence,
                "focus": focus[:2],
                "flags": [flag for flag in [risk_tag if risk_tag else "", "downside_scan"] if flag],
                "reason": self._build_reason("风险评审", risk_score, probability, focus, state_before),
            },
            {
                "agent_id": "opportunity_reviewer",
                "agent_name": "机会评审",
                "stance": "support" if opportunity_score >= 0.54 else "watch",
                "score": opportunity_score,
                "confidence": confidence,
                "focus": focus[:2],
                "flags": [
                    flag
                    for flag in [opportunity_tag if opportunity_tag else "", "upside_scan"]
                    if flag
                ],
                "reason": self._build_reason("机会评审", opportunity_score, probability, focus, state_before),
            },
            {
                "agent_id": "execution_reviewer",
                "agent_name": "执行评审",
                "stance": "support" if execution_score >= 0.58 else "caution",
                "score": execution_score,
                "confidence": round(self._clamp(confidence - 0.04), 2),
                "focus": focus[:2] or ["执行条件"],
                "flags": ["execution_path", "commitment_check"],
                "reason": self._build_reason("执行评审", execution_score, probability, focus, state_before),
            },
            {
                "agent_id": "consistency_reviewer",
                "agent_name": "一致性评审",
                "stance": "aligned" if consistency_score >= 0.56 else "challenge",
                "score": consistency_score,
                "confidence": round(self._clamp(confidence + 0.03), 2),
                "focus": focus[:2] or ["路径连续性"],
                "flags": ["consistency_check", "evidence_check"],
                "reason": self._build_reason("一致性评审", consistency_score, probability, focus, state_before),
            },
        ]

        return votes
