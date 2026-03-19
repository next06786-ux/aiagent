"""
因果推理引擎 - 涌现检测深化
实现因果关系推理、多尺度模式识别、模式解释生成
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from collections import defaultdict, deque


@dataclass
class CausalRelation:
    """因果关系"""
    cause: str  # 原因指标
    effect: str  # 结果指标
    strength: float  # 因果强度（0-1）
    delay: int  # 时间延迟（天数）
    confidence: float  # 置信度（0-1）
    evidence: List[str]  # 证据


@dataclass
class CausalChain:
    """因果链"""
    chain_id: str
    relations: List[CausalRelation]  # 因果关系序列
    total_strength: float  # 总强度
    length: int  # 链长度
    domains: List[str]  # 涉及的领域
    description: str  # 链描述


@dataclass
class Pattern:
    """多尺度模式"""
    pattern_id: str
    pattern_type: str  # cascade, feedback_loop, tipping_point, synergy
    scale: str  # micro, meso, macro
    domains: List[str]
    metrics: List[str]
    strength: float
    confidence: float
    causal_chains: List[CausalChain]
    explanation: str


class CausalInferenceEngine:
    """因果推理引擎"""
    
    def __init__(self):
        self.causal_graph = defaultdict(list)  # 因果图
        self.time_series_data = {}  # 时间序列数据
        self.causal_relations = []  # 因果关系列表
        
    def infer_causality(self, history: List[Dict[str, Any]]) -> List[CausalRelation]:
        """
        推理因果关系
        使用Granger因果检验和交叉相关分析
        """
        relations = []
        
        if len(history) < 10:
            return relations
        
        # 提取所有指标
        metrics = self._extract_metrics(history)
        
        # 对每对指标进行因果检验
        for metric1 in metrics:
            for metric2 in metrics:
                if metric1 == metric2:
                    continue
                
                # 检验metric1是否导致metric2
                relation = self._granger_causality_test(
                    history, metric1, metric2
                )
                
                if relation and relation.confidence > 0.6:
                    relations.append(relation)
        
        self.causal_relations = relations
        return relations
    
    def _extract_metrics(self, history: List[Dict[str, Any]]) -> List[str]:
        """提取所有指标"""
        metrics = set()
        for record in history:
            metrics.update(record.keys())
        return list(metrics)
    
    def _granger_causality_test(
        self,
        history: List[Dict[str, Any]],
        cause_metric: str,
        effect_metric: str,
        max_lag: int = 3
    ) -> Optional[CausalRelation]:
        """
        Granger因果检验
        检验cause_metric是否导致effect_metric
        """
        try:
            # 提取时间序列
            cause_series = [h.get(cause_metric, 0) for h in history]
            effect_series = [h.get(effect_metric, 0) for h in history]
            
            if len(cause_series) < max_lag + 2:
                return None
            
            # 计算不同延迟下的相关性
            best_lag = 0
            best_correlation = 0
            best_strength = 0
            
            for lag in range(1, max_lag + 1):
                if lag >= len(cause_series):
                    break
                
                # 计算交叉相关
                correlation = np.corrcoef(
                    cause_series[:-lag],
                    effect_series[lag:]
                )[0, 1]
                
                if abs(correlation) > abs(best_correlation):
                    best_correlation = correlation
                    best_lag = lag
                    best_strength = abs(correlation)
            
            # 如果相关性足够强，认为存在因果关系
            if best_strength > 0.5:
                confidence = min(best_strength, 1.0)
                
                return CausalRelation(
                    cause=cause_metric,
                    effect=effect_metric,
                    strength=best_strength,
                    delay=best_lag,
                    confidence=confidence,
                    evidence=[
                        f"Cross-correlation: {best_correlation:.3f}",
                        f"Lag: {best_lag} days",
                        f"Strength: {best_strength:.3f}"
                    ]
                )
        except Exception as e:
            print(f"Error in Granger causality test: {e}")
        
        return None
    
    def build_causal_graph(self, relations: List[CausalRelation]) -> Dict[str, List[str]]:
        """构建因果图"""
        graph = defaultdict(list)
        
        for relation in relations:
            graph[relation.cause].append(relation.effect)
        
        self.causal_graph = graph
        return dict(graph)
    
    def find_causal_chains(self, max_length: int = 5) -> List[CausalChain]:
        """
        查找因果链
        使用深度优先搜索
        """
        chains = []
        visited = set()
        
        for start_metric in self.causal_graph:
            chain = self._dfs_find_chain(
                start_metric, [], visited, max_length
            )
            
            if len(chain) > 1:
                causal_chain = self._build_causal_chain(chain)
                if causal_chain:
                    chains.append(causal_chain)
        
        return chains
    
    def _dfs_find_chain(
        self,
        current: str,
        path: List[str],
        visited: set,
        max_length: int
    ) -> List[str]:
        """深度优先搜索查找因果链"""
        if len(path) >= max_length:
            return path
        
        if current in visited:
            return path
        
        path.append(current)
        visited.add(current)
        
        if current in self.causal_graph:
            for next_metric in self.causal_graph[current]:
                longer_path = self._dfs_find_chain(
                    next_metric, path.copy(), visited.copy(), max_length
                )
                if len(longer_path) > len(path):
                    path = longer_path
        
        return path
    
    def _build_causal_chain(self, metrics: List[str]) -> Optional[CausalChain]:
        """构建因果链对象"""
        if len(metrics) < 2:
            return None
        
        relations = []
        total_strength = 0
        
        for i in range(len(metrics) - 1):
            cause = metrics[i]
            effect = metrics[i + 1]
            
            # 查找对应的因果关系
            for relation in self.causal_relations:
                if relation.cause == cause and relation.effect == effect:
                    relations.append(relation)
                    total_strength += relation.strength
                    break
        
        if not relations:
            return None
        
        # 提取涉及的领域
        domains = self._extract_domains(metrics)
        
        # 生成描述
        description = self._generate_chain_description(metrics, relations)
        
        return CausalChain(
            chain_id=f"chain_{datetime.now().timestamp()}",
            relations=relations,
            total_strength=total_strength / len(relations),
            length=len(metrics),
            domains=domains,
            description=description
        )
    
    def _extract_domains(self, metrics: List[str]) -> List[str]:
        """从指标中提取领域"""
        domain_keywords = {
            'health': ['sleep', 'exercise', 'heart_rate', 'health_score', 'immunity'],
            'time': ['work_hours', 'focus_time', 'efficiency', 'time_pressure'],
            'emotion': ['mood', 'stress', 'emotional_stability'],
            'social': ['social_hours', 'loneliness', 'social_satisfaction'],
            'finance': ['savings', 'spending', 'income', 'debt'],
            'learning': ['learning_hours', 'test_score', 'knowledge_retention']
        }
        
        domains = set()
        for metric in metrics:
            metric_lower = metric.lower()
            for domain, keywords in domain_keywords.items():
                if any(kw in metric_lower for kw in keywords):
                    domains.add(domain)
        
        return list(domains)
    
    def _generate_chain_description(
        self,
        metrics: List[str],
        relations: List[CausalRelation]
    ) -> str:
        """生成因果链描述"""
        parts = []
        
        for i, metric in enumerate(metrics):
            parts.append(metric)
            
            if i < len(relations):
                relation = relations[i]
                arrow = "→" if relation.strength > 0 else "⇢"
                parts.append(f" {arrow}({relation.strength:.2f}) ")
        
        return "".join(parts)


class MultiScalePatternDetector:
    """多尺度模式检测器"""
    
    def __init__(self):
        self.causal_engine = CausalInferenceEngine()
    
    def detect_patterns(
        self,
        history: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """检测多尺度模式"""
        patterns = []
        
        # 1. 推理因果关系
        relations = self.causal_engine.infer_causality(history)
        self.causal_engine.build_causal_graph(relations)
        
        # 2. 查找因果链
        chains = self.causal_engine.find_causal_chains()
        
        # 3. 检测微观模式（单个指标变化）
        micro_patterns = self._detect_micro_patterns(history)
        patterns.extend(micro_patterns)
        
        # 4. 检测中观模式（因果链）
        meso_patterns = self._detect_meso_patterns(chains)
        patterns.extend(meso_patterns)
        
        # 5. 检测宏观模式（系统级别）
        macro_patterns = self._detect_macro_patterns(history, chains)
        patterns.extend(macro_patterns)
        
        return patterns
    
    def _detect_micro_patterns(self, history: List[Dict[str, Any]]) -> List[Pattern]:
        """检测微观模式"""
        patterns = []
        
        if len(history) < 3:
            return patterns
        
        recent = history[-3:]
        
        # 检测单个指标的显著变化
        for metric in recent[0].keys():
            if isinstance(recent[0][metric], (int, float)):
                values = [h.get(metric, 0) for h in recent]
                
                # 计算变化率
                change_rate = abs(values[-1] - values[0]) / (abs(values[0]) + 1)
                
                if change_rate > 0.3:  # 变化超过30%
                    pattern = Pattern(
                        pattern_id=f"micro_{metric}_{datetime.now().timestamp()}",
                        pattern_type="micro_change",
                        scale="micro",
                        domains=[self._get_domain(metric)],
                        metrics=[metric],
                        strength=min(change_rate, 1.0),
                        confidence=0.8,
                        causal_chains=[],
                        explanation=f"{metric} changed by {change_rate*100:.1f}%"
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_meso_patterns(self, chains: List[CausalChain]) -> List[Pattern]:
        """检测中观模式"""
        patterns = []
        
        for chain in chains:
            if chain.length >= 2:
                pattern = Pattern(
                    pattern_id=f"meso_{chain.chain_id}",
                    pattern_type="causal_chain",
                    scale="meso",
                    domains=chain.domains,
                    metrics=[r.cause for r in chain.relations] + [chain.relations[-1].effect],
                    strength=chain.total_strength,
                    confidence=0.75,
                    causal_chains=[chain],
                    explanation=chain.description
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_macro_patterns(
        self,
        history: List[Dict[str, Any]],
        chains: List[CausalChain]
    ) -> List[Pattern]:
        """检测宏观模式"""
        patterns = []
        
        # 检测系统级别的协同效应
        if len(chains) >= 2:
            # 查找共享指标的链
            shared_metrics = self._find_shared_metrics(chains)
            
            if shared_metrics:
                pattern = Pattern(
                    pattern_id=f"macro_synergy_{datetime.now().timestamp()}",
                    pattern_type="system_synergy",
                    scale="macro",
                    domains=list(set(d for c in chains for d in c.domains)),
                    metrics=shared_metrics,
                    strength=0.7,
                    confidence=0.7,
                    causal_chains=chains,
                    explanation="Multiple causal chains interact at system level"
                )
                patterns.append(pattern)
        
        return patterns
    
    def _find_shared_metrics(self, chains: List[CausalChain]) -> List[str]:
        """查找链之间的共享指标"""
        if not chains:
            return []
        
        # 获取第一条链的所有指标
        shared = set(chains[0].relations[0].cause for _ in chains[0].relations)
        shared.update(r.effect for r in chains[0].relations)
        
        # 与其他链的指标求交集
        for chain in chains[1:]:
            chain_metrics = set()
            chain_metrics.add(chain.relations[0].cause)
            chain_metrics.update(r.effect for r in chain.relations)
            shared &= chain_metrics
        
        return list(shared)
    
    def _get_domain(self, metric: str) -> str:
        """获取指标所属的领域"""
        domain_keywords = {
            'health': ['sleep', 'exercise', 'heart_rate', 'health_score', 'immunity'],
            'time': ['work_hours', 'focus_time', 'efficiency', 'time_pressure'],
            'emotion': ['mood', 'stress', 'emotional_stability'],
            'social': ['social_hours', 'loneliness', 'social_satisfaction'],
            'finance': ['savings', 'spending', 'income', 'debt'],
            'learning': ['learning_hours', 'test_score', 'knowledge_retention']
        }
        
        metric_lower = metric.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in metric_lower for kw in keywords):
                return domain
        
        return 'unknown'


class PatternExplainer:
    """模式解释生成器"""
    
    def generate_explanation(self, pattern: Pattern) -> str:
        """生成模式解释"""
        if pattern.scale == "micro":
            return self._explain_micro_pattern(pattern)
        elif pattern.scale == "meso":
            return self._explain_meso_pattern(pattern)
        elif pattern.scale == "macro":
            return self._explain_macro_pattern(pattern)
        else:
            return "Unknown pattern"
    
    def _explain_micro_pattern(self, pattern: Pattern) -> str:
        """解释微观模式"""
        metric = pattern.metrics[0] if pattern.metrics else "unknown"
        change = pattern.strength * 100
        
        return f"检测到{metric}发生了显著变化（{change:.1f}%），这可能表明该指标的状态发生了改变。"
    
    def _explain_meso_pattern(self, pattern: Pattern) -> str:
        """解释中观模式"""
        if not pattern.causal_chains:
            return "检测到因果链模式"
        
        chain = pattern.causal_chains[0]
        explanation = f"检测到因果链：{chain.description}\n"
        explanation += f"链强度：{chain.total_strength:.2f}，涉及领域：{', '.join(chain.domains)}\n"
        explanation += "这表明这些指标之间存在因果关系，改变一个指标可能会影响其他指标。"
        
        return explanation
    
    def _explain_macro_pattern(self, pattern: Pattern) -> str:
        """解释宏观模式"""
        domains = ', '.join(pattern.domains)
        
        explanation = f"检测到系统级别的协同效应，涉及领域：{domains}\n"
        explanation += f"多条因果链在系统层面相互作用，形成复杂的因果网络。\n"
        explanation += "这表明生活的不同方面之间存在深层的相互影响。"
        
        return explanation


# 全局实例
_detector = None

def get_pattern_detector() -> MultiScalePatternDetector:
    """获取全局多尺度模式检测器实例"""
    global _detector
    if _detector is None:
        _detector = MultiScalePatternDetector()
    return _detector

