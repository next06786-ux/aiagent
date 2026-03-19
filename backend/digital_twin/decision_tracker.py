"""
数字孪生决策追踪器
对比用户决策 vs AI建议，长期追踪效果
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import os


class DecisionOutcome(Enum):
    """决策结果"""
    PENDING = "pending"  # 待验证
    SUCCESS = "success"  # 成功
    FAILURE = "failure"  # 失败
    PARTIAL = "partial"  # 部分成功


@dataclass
class Decision:
    """决策记录"""
    id: str
    user_id: str
    domain: str  # time, social, learning, emotion, finance, health
    situation: str
    timestamp: datetime
    
    # 用户决策
    user_decision: str
    
    # AI建议
    ai_recommendation: str
    ai_reasoning: str
    
    # 可选参数（有默认值）
    user_reasoning: Optional[str] = None
    ai_confidence: float = 0.0
    
    # 决策是否一致
    is_aligned: bool = False
    
    # 结果追踪
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    outcome_timestamp: Optional[datetime] = None
    outcome_score: float = 0.0  # 0-1，越高越好
    outcome_notes: Optional[str] = None
    
    # 验证时间（多久后验证结果）
    verification_days: int = 7


class DecisionTracker:
    """决策追踪器"""
    
    def __init__(self, user_id: str, storage_path: str = "./data/decisions"):
        self.user_id = user_id
        self.storage_path = storage_path
        self.decisions: List[Decision] = []
        
        os.makedirs(storage_path, exist_ok=True)
        self.load_decisions()
    
    def record_decision(
        self,
        domain: str,
        situation: str,
        user_decision: str,
        ai_recommendation: str,
        ai_reasoning: str,
        ai_confidence: float,
        user_reasoning: Optional[str] = None,
        verification_days: int = 7
    ) -> str:
        """记录一次决策对比"""
        decision_id = f"dec_{datetime.now().timestamp()}_{len(self.decisions)}"
        
        # 判断决策是否一致
        is_aligned = self._check_alignment(user_decision, ai_recommendation)
        
        decision = Decision(
            id=decision_id,
            user_id=self.user_id,
            domain=domain,
            situation=situation,
            timestamp=datetime.now(),
            user_decision=user_decision,
            user_reasoning=user_reasoning,
            ai_recommendation=ai_recommendation,
            ai_reasoning=ai_reasoning,
            ai_confidence=ai_confidence,
            is_aligned=is_aligned,
            verification_days=verification_days
        )
        
        self.decisions.append(decision)
        self.save_decisions()
        
        return decision_id
    
    def update_outcome(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        outcome_score: float,
        outcome_notes: Optional[str] = None
    ):
        """更新决策结果"""
        for decision in self.decisions:
            if decision.id == decision_id:
                decision.outcome = outcome
                decision.outcome_timestamp = datetime.now()
                decision.outcome_score = outcome_score
                decision.outcome_notes = outcome_notes
                self.save_decisions()
                break
    
    def get_pending_verifications(self) -> List[Decision]:
        """获取待验证的决策"""
        now = datetime.now()
        pending = []
        
        for decision in self.decisions:
            if decision.outcome == DecisionOutcome.PENDING:
                # 检查是否到了验证时间
                verification_time = decision.timestamp + timedelta(days=decision.verification_days)
                if now >= verification_time:
                    pending.append(decision)
        
        return pending
    
    def get_decision_comparison(
        self,
        domain: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取决策对比分析"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 筛选决策
        filtered = [
            d for d in self.decisions
            if d.timestamp >= cutoff_time and
            (domain is None or d.domain == domain) and
            d.outcome != DecisionOutcome.PENDING
        ]
        
        if not filtered:
            return {
                "total_decisions": 0,
                "user_success_rate": 0,
                "ai_would_success_rate": 0,
                "alignment_rate": 0
            }
        
        # 统计用户决策成功率
        user_success = sum(
            1 for d in filtered
            if d.outcome in [DecisionOutcome.SUCCESS, DecisionOutcome.PARTIAL]
        )
        user_success_rate = user_success / len(filtered)
        
        # 统计如果采用AI建议的成功率
        aligned_decisions = [d for d in filtered if d.is_aligned]
        ai_would_success = sum(
            1 for d in aligned_decisions
            if d.outcome in [DecisionOutcome.SUCCESS, DecisionOutcome.PARTIAL]
        )
        ai_would_success_rate = (
            ai_would_success / len(aligned_decisions)
            if aligned_decisions else 0
        )
        
        # 统计决策一致率
        alignment_rate = len(aligned_decisions) / len(filtered)
        
        # 按领域统计
        domain_stats = {}
        for d in filtered:
            if d.domain not in domain_stats:
                domain_stats[d.domain] = {
                    "count": 0,
                    "user_success": 0,
                    "aligned": 0
                }
            
            domain_stats[d.domain]["count"] += 1
            if d.outcome in [DecisionOutcome.SUCCESS, DecisionOutcome.PARTIAL]:
                domain_stats[d.domain]["user_success"] += 1
            if d.is_aligned:
                domain_stats[d.domain]["aligned"] += 1
        
        # 计算各领域成功率
        for domain_name, stats in domain_stats.items():
            stats["success_rate"] = stats["user_success"] / stats["count"]
            stats["alignment_rate"] = stats["aligned"] / stats["count"]
        
        return {
            "total_decisions": len(filtered),
            "user_success_rate": user_success_rate,
            "ai_would_success_rate": ai_would_success_rate,
            "alignment_rate": alignment_rate,
            "domain_stats": domain_stats,
            "average_outcome_score": sum(d.outcome_score for d in filtered) / len(filtered)
        }
    
    def get_divergent_decisions(
        self,
        days: int = 30
    ) -> List[Decision]:
        """获取用户与AI决策不一致的案例"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        divergent = [
            d for d in self.decisions
            if d.timestamp >= cutoff_time and
            not d.is_aligned and
            d.outcome != DecisionOutcome.PENDING
        ]
        
        # 按结果排序，失败的在前
        divergent.sort(key=lambda x: x.outcome_score)
        
        return divergent
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.decisions:
            return {
                "total_decisions": 0,
                "pending_verifications": 0,
                "verified_decisions": 0
            }
        
        pending = sum(1 for d in self.decisions if d.outcome == DecisionOutcome.PENDING)
        verified = len(self.decisions) - pending
        
        # 最近30天的对比
        comparison_30d = self.get_decision_comparison(days=30)
        
        return {
            "total_decisions": len(self.decisions),
            "pending_verifications": pending,
            "verified_decisions": verified,
            "recent_30_days": comparison_30d,
            "domains": list(set(d.domain for d in self.decisions))
        }
    
    def _check_alignment(
        self,
        user_decision: str,
        ai_recommendation: str
    ) -> bool:
        """检查决策是否一致（简化版）"""
        # 实际应用中应使用更复杂的语义相似度判断
        user_lower = user_decision.lower()
        ai_lower = ai_recommendation.lower()
        
        # 简单的关键词匹配
        common_words = set(user_lower.split()) & set(ai_lower.split())
        
        return len(common_words) >= 2
    
    def save_decisions(self):
        """保存决策到磁盘"""
        filepath = os.path.join(self.storage_path, f"{self.user_id}_decisions.json")
        
        data = {
            "user_id": self.user_id,
            "decisions": [
                {
                    "id": d.id,
                    "user_id": d.user_id,
                    "domain": d.domain,
                    "situation": d.situation,
                    "timestamp": d.timestamp.isoformat(),
                    "user_decision": d.user_decision,
                    "user_reasoning": d.user_reasoning,
                    "ai_recommendation": d.ai_recommendation,
                    "ai_reasoning": d.ai_reasoning,
                    "ai_confidence": d.ai_confidence,
                    "is_aligned": d.is_aligned,
                    "outcome": d.outcome.value,
                    "outcome_timestamp": d.outcome_timestamp.isoformat() if d.outcome_timestamp else None,
                    "outcome_score": d.outcome_score,
                    "outcome_notes": d.outcome_notes,
                    "verification_days": d.verification_days
                }
                for d in self.decisions
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_decisions(self):
        """从磁盘加载决策"""
        filepath = os.path.join(self.storage_path, f"{self.user_id}_decisions.json")
        
        if not os.path.exists(filepath):
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.decisions = [
                Decision(
                    id=d["id"],
                    user_id=d["user_id"],
                    domain=d["domain"],
                    situation=d["situation"],
                    timestamp=datetime.fromisoformat(d["timestamp"]),
                    user_decision=d["user_decision"],
                    user_reasoning=d.get("user_reasoning"),
                    ai_recommendation=d["ai_recommendation"],
                    ai_reasoning=d["ai_reasoning"],
                    ai_confidence=d["ai_confidence"],
                    is_aligned=d["is_aligned"],
                    outcome=DecisionOutcome(d["outcome"]),
                    outcome_timestamp=datetime.fromisoformat(d["outcome_timestamp"]) if d.get("outcome_timestamp") else None,
                    outcome_score=d["outcome_score"],
                    outcome_notes=d.get("outcome_notes"),
                    verification_days=d.get("verification_days", 7)
                )
                for d in data["decisions"]
            ]
        except Exception as e:
            print(f"Failed to load decisions: {e}")
            self.decisions = []
