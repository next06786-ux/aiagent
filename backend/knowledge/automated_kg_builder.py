"""
知识图谱自动化构建系统
从用户数据自动构建和维护知识图谱
"""

from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from enum import Enum
import json
import re


class EntityType(Enum):
    """实体类型"""
    METRIC = "metric"  # 指标（睡眠、压力等）
    DOMAIN = "domain"  # 领域（健康、时间等）
    ACTION = "action"  # 行动（运动、冥想等）
    STATE = "state"  # 状态（好、差等）
    CONCEPT = "concept"  # 概念


class RelationType(Enum):
    """关系类型"""
    CAUSES = "causes"  # 导致
    INFLUENCED_BY = "influenced_by"  # 受...影响
    CORRELATES_WITH = "correlates_with"  # 与...相关
    IMPROVES = "improves"  # 改善
    WORSENS = "worsens"  # 恶化
    PART_OF = "part_of"  # 属于
    SIMILAR_TO = "similar_to"  # 类似于


class Entity:
    """实体"""
    
    def __init__(self, entity_id: str, name: str, entity_type: EntityType,
                 domain: str = None, properties: Dict[str, Any] = None):
        """
        初始化实体
        
        Args:
            entity_id: 实体ID
            name: 实体名称
            entity_type: 实体类型
            domain: 所属领域
            properties: 属性
        """
        self.entity_id = entity_id
        self.name = name
        self.entity_type = entity_type
        self.domain = domain
        self.properties = properties or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.frequency = 0  # 出现频率
        self.importance = 0.5  # 重要性
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "domain": self.domain,
            "properties": self.properties,
            "frequency": self.frequency,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class Relation:
    """关系"""
    
    def __init__(self, relation_id: str, source_id: str, target_id: str,
                 relation_type: RelationType, weight: float = 1.0,
                 confidence: float = 0.5, evidence: List[str] = None):
        """
        初始化关系
        
        Args:
            relation_id: 关系ID
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            weight: 权重
            confidence: 置信度
            evidence: 证据
        """
        self.relation_id = relation_id
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.weight = weight
        self.confidence = confidence
        self.evidence = evidence or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class AutomatedKnowledgeGraphBuilder:
    """自动化知识图谱构建器"""
    
    def __init__(self, user_id: str):
        """
        初始化构建器
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.entity_index: Dict[str, Set[str]] = {}  # 名称到ID的索引
        
        # 预定义的实体和关系
        self._initialize_predefined_entities()
    
    def _initialize_predefined_entities(self):
        """初始化预定义的实体"""
        
        # 6大领域
        domains = [
            ("health", "健康", EntityType.DOMAIN),
            ("time", "时间", EntityType.DOMAIN),
            ("emotion", "情绪", EntityType.DOMAIN),
            ("social", "社交", EntityType.DOMAIN),
            ("finance", "财务", EntityType.DOMAIN),
            ("learning", "学习", EntityType.DOMAIN)
        ]
        
        for domain_id, domain_name, entity_type in domains:
            entity = Entity(domain_id, domain_name, entity_type)
            self.entities[domain_id] = entity
            self._add_to_index(domain_name, domain_id)
        
        # 健康领域的指标
        health_metrics = [
            ("sleep_hours", "睡眠时长", "health"),
            ("sleep_quality", "睡眠质量", "health"),
            ("exercise_minutes", "运动时长", "health"),
            ("stress_level", "压力水平", "health"),
            ("heart_rate", "心率", "health"),
            ("health_score", "健康分数", "health")
        ]
        
        for metric_id, metric_name, domain in health_metrics:
            entity = Entity(metric_id, metric_name, EntityType.METRIC, domain)
            self.entities[metric_id] = entity
            self._add_to_index(metric_name, metric_id)
        
        # 时间领域的指标
        time_metrics = [
            ("work_hours", "工作时长", "time"),
            ("focus_time", "专注时间", "time"),
            ("task_completion_rate", "任务完成率", "time"),
            ("efficiency_score", "效率分数", "time"),
            ("time_pressure", "时间压力", "time")
        ]
        
        for metric_id, metric_name, domain in time_metrics:
            entity = Entity(metric_id, metric_name, EntityType.METRIC, domain)
            self.entities[metric_id] = entity
            self._add_to_index(metric_name, metric_id)
        
        # 情绪领域的指标
        emotion_metrics = [
            ("mood", "心情", "emotion"),
            ("anxiety_level", "焦虑水平", "emotion"),
            ("happiness", "幸福感", "emotion"),
            ("emotional_stability", "情绪稳定性", "emotion")
        ]
        
        for metric_id, metric_name, domain in emotion_metrics:
            entity = Entity(metric_id, metric_name, EntityType.METRIC, domain)
            self.entities[metric_id] = entity
            self._add_to_index(metric_name, metric_id)
        
        # 社交领域的指标
        social_metrics = [
            ("social_hours", "社交时间", "social"),
            ("social_interactions", "社交互动", "social"),
            ("loneliness", "孤独感", "social"),
            ("social_satisfaction", "社交满意度", "social")
        ]
        
        for metric_id, metric_name, domain in social_metrics:
            entity = Entity(metric_id, metric_name, EntityType.METRIC, domain)
            self.entities[metric_id] = entity
            self._add_to_index(metric_name, metric_id)
        
        # 财务领域的指标
        finance_metrics = [
            ("income", "收入", "finance"),
            ("spending", "支出", "finance"),
            ("savings", "储蓄", "finance"),
            ("debt", "债务", "finance"),
            ("financial_health", "财务健康", "finance")
        ]
        
        for metric_id, metric_name, domain in finance_metrics:
            entity = Entity(metric_id, metric_name, EntityType.METRIC, domain)
            self.entities[metric_id] = entity
            self._add_to_index(metric_name, metric_id)
        
        # 学习领域的指标
        learning_metrics = [
            ("learning_hours", "学习时长", "learning"),
            ("learning_quality", "学习质量", "learning"),
            ("test_score", "测试成绩", "learning"),
            ("goal_progress", "目标进度", "learning")
        ]
        
        for metric_id, metric_name, domain in learning_metrics:
            entity = Entity(metric_id, metric_name, EntityType.METRIC, domain)
            self.entities[metric_id] = entity
            self._add_to_index(metric_name, metric_id)
        
        # 常见行动
        actions = [
            ("exercise", "运动", "health"),
            ("sleep", "睡眠", "health"),
            ("meditation", "冥想", "emotion"),
            ("social_activity", "社交活动", "social"),
            ("learning_activity", "学习活动", "learning"),
            ("work", "工作", "time")
        ]
        
        for action_id, action_name, domain in actions:
            entity = Entity(action_id, action_name, EntityType.ACTION, domain)
            self.entities[action_id] = entity
            self._add_to_index(action_name, action_id)
    
    def extract_entities_from_text(self, text: str, domain: str = None) -> List[str]:
        """
        从文本中提取实体
        
        Args:
            text: 文本
            domain: 领域（可选）
        
        Returns:
            实体ID列表
        """
        extracted_entities = []
        text_lower = text.lower()
        
        # 查找匹配的实体
        for entity_id, entity in self.entities.items():
            if entity.name.lower() in text_lower:
                extracted_entities.append(entity_id)
                entity.frequency += 1
                entity.updated_at = datetime.now()
        
        return extracted_entities
    
    def extract_entities_from_data(self, data: Dict[str, Any]) -> List[str]:
        """
        从数据中提取实体
        
        Args:
            data: 数据字典
        
        Returns:
            实体ID列表
        """
        extracted_entities = []
        
        # 遍历数据中的所有键
        for key, value in data.items():
            # 检查是否有对应的实体
            if key in self.entities:
                extracted_entities.append(key)
                self.entities[key].frequency += 1
                self.entities[key].updated_at = datetime.now()
        
        return extracted_entities
    
    def infer_relations_from_data(self, data: Dict[str, Any], 
                                  extracted_entities: List[str]) -> List[Tuple[str, str, RelationType, float]]:
        """
        从数据推理关系
        
        Args:
            data: 数据字典
            extracted_entities: 提取的实体列表
        
        Returns:
            (源实体ID, 目标实体ID, 关系类型, 权重)列表
        """
        inferred_relations = []
        
        # 预定义的关系规则
        relation_rules = [
            # 睡眠相关
            ("sleep_hours", "stress_level", RelationType.INFLUENCED_BY, 0.8),
            ("sleep_hours", "health_score", RelationType.IMPROVES, 0.7),
            ("sleep_quality", "mood", RelationType.IMPROVES, 0.75),
            
            # 运动相关
            ("exercise_minutes", "health_score", RelationType.IMPROVES, 0.8),
            ("exercise_minutes", "stress_level", RelationType.WORSENS, 0.6),
            ("exercise_minutes", "mood", RelationType.IMPROVES, 0.7),
            
            # 压力相关
            ("stress_level", "health_score", RelationType.WORSENS, 0.8),
            ("stress_level", "mood", RelationType.WORSENS, 0.85),
            ("stress_level", "efficiency_score", RelationType.WORSENS, 0.7),
            
            # 时间相关
            ("work_hours", "stress_level", RelationType.CAUSES, 0.7),
            ("focus_time", "efficiency_score", RelationType.IMPROVES, 0.8),
            ("task_completion_rate", "efficiency_score", RelationType.IMPROVES, 0.75),
            
            # 社交相关
            ("social_hours", "loneliness", RelationType.WORSENS, 0.8),
            ("social_hours", "mood", RelationType.IMPROVES, 0.7),
            ("social_satisfaction", "health_score", RelationType.IMPROVES, 0.6),
            
            # 学习相关
            ("learning_hours", "goal_progress", RelationType.IMPROVES, 0.75),
            ("learning_quality", "test_score", RelationType.IMPROVES, 0.8),
        ]
        
        # 应用规则
        for source_id, target_id, relation_type, weight in relation_rules:
            if source_id in extracted_entities and target_id in extracted_entities:
                inferred_relations.append((source_id, target_id, relation_type, weight))
        
        return inferred_relations
    
    def add_relation(self, source_id: str, target_id: str, relation_type: RelationType,
                    weight: float = 1.0, confidence: float = 0.5, evidence: List[str] = None) -> str:
        """
        添加关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            weight: 权重
            confidence: 置信度
            evidence: 证据
        
        Returns:
            关系ID
        """
        relation_id = f"rel_{source_id}_{target_id}_{datetime.now().timestamp()}"
        
        # 检查是否已存在相同的关系
        for rel in self.relations.values():
            if rel.source_id == source_id and rel.target_id == target_id and rel.relation_type == relation_type:
                # 更新现有关系
                rel.weight = (rel.weight + weight) / 2
                rel.confidence = (rel.confidence + confidence) / 2
                if evidence:
                    rel.evidence.extend(evidence)
                rel.updated_at = datetime.now()
                return rel.relation_id
        
        # 创建新关系
        relation = Relation(relation_id, source_id, target_id, relation_type, weight, confidence, evidence)
        self.relations[relation_id] = relation
        
        return relation_id
    
    def build_from_user_data(self, user_data: Dict[str, Any], user_message: str = None) -> Dict[str, Any]:
        """
        从用户数据构建知识图谱
        
        Args:
            user_data: 用户数据
            user_message: 用户消息（可选）
        
        Returns:
            构建结果
        """
        result = {
            "extracted_entities": [],
            "inferred_relations": [],
            "new_entities": 0,
            "new_relations": 0
        }
        
        # 从用户消息提取实体
        if user_message:
            extracted_from_text = self.extract_entities_from_text(user_message)
            result["extracted_entities"].extend(extracted_from_text)
        
        # 从用户数据提取实体
        extracted_from_data = self.extract_entities_from_data(user_data)
        result["extracted_entities"].extend(extracted_from_data)
        
        # 去重
        result["extracted_entities"] = list(set(result["extracted_entities"]))
        
        # 推理关系
        inferred_relations = self.infer_relations_from_data(user_data, result["extracted_entities"])
        
        # 添加关系
        for source_id, target_id, relation_type, weight in inferred_relations:
            relation_id = self.add_relation(source_id, target_id, relation_type, weight, 0.7)
            result["inferred_relations"].append({
                "relation_id": relation_id,
                "source": source_id,
                "target": target_id,
                "type": relation_type.value,
                "weight": weight
            })
            result["new_relations"] += 1
        
        return result
    
    def get_entity_neighbors(self, entity_id: str, relation_type: RelationType = None) -> List[Tuple[str, RelationType, float]]:
        """
        获取实体的邻居
        
        Args:
            entity_id: 实体ID
            relation_type: 关系类型过滤（可选）
        
        Returns:
            (邻居实体ID, 关系类型, 权重)列表
        """
        neighbors = []
        
        for relation in self.relations.values():
            if relation.source_id == entity_id:
                if relation_type is None or relation.relation_type == relation_type:
                    neighbors.append((relation.target_id, relation.relation_type, relation.weight))
        
        return neighbors
    
    def get_causal_chains(self, start_entity_id: str, max_depth: int = 3) -> List[List[str]]:
        """
        获取因果链
        
        Args:
            start_entity_id: 起始实体ID
            max_depth: 最大深度
        
        Returns:
            因果链列表
        """
        chains = []
        
        def dfs(current_id: str, path: List[str], depth: int):
            if depth > max_depth:
                return
            
            neighbors = self.get_entity_neighbors(current_id, RelationType.CAUSES)
            
            if not neighbors:
                if len(path) > 1:
                    chains.append(path)
            else:
                for neighbor_id, _, _ in neighbors:
                    dfs(neighbor_id, path + [neighbor_id], depth + 1)
        
        dfs(start_entity_id, [start_entity_id], 0)
        
        return chains
    
    def export_graph(self) -> Dict[str, Any]:
        """
        导出知识图谱
        
        Returns:
            图谱数据
        """
        return {
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations.values()],
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "exported_at": datetime.now().isoformat()
        }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图谱统计信息
        
        Returns:
            统计信息
        """
        # 计算实体统计
        entity_types = {}
        for entity in self.entities.values():
            entity_type = entity.entity_type.value
            if entity_type not in entity_types:
                entity_types[entity_type] = 0
            entity_types[entity_type] += 1
        
        # 计算关系统计
        relation_types = {}
        for relation in self.relations.values():
            relation_type = relation.relation_type.value
            if relation_type not in relation_types:
                relation_types[relation_type] = 0
            relation_types[relation_type] += 1
        
        # 计算最常出现的实体
        top_entities = sorted(self.entities.values(), key=lambda e: e.frequency, reverse=True)[:5]
        
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": entity_types,
            "relation_types": relation_types,
            "top_entities": [
                {"name": e.name, "frequency": e.frequency, "importance": e.importance}
                for e in top_entities
            ],
            "average_entity_frequency": sum(e.frequency for e in self.entities.values()) / len(self.entities) if self.entities else 0,
            "average_relation_weight": sum(r.weight for r in self.relations.values()) / len(self.relations) if self.relations else 0
        }
    
    def _add_to_index(self, name: str, entity_id: str):
        """添加到索引"""
        if name not in self.entity_index:
            self.entity_index[name] = set()
        self.entity_index[name].add(entity_id)


def get_automated_kg_builder(user_id: str) -> AutomatedKnowledgeGraphBuilder:
    """获取自动化知识图谱构建器实例"""
    return AutomatedKnowledgeGraphBuilder(user_id)

