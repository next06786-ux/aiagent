"""
个人知识图谱
构建用户的"数字记忆" - 实体、关系、模式挖掘
"""
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class Entity:
    """实体"""
    entity_id: str
    entity_type: str  # person, event, object, location
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Relation:
    """关系"""
    relation_id: str
    relation_type: str  # causal, temporal, correlation
    source_entity: str
    target_entity: str
    strength: float  # [0, 1]
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Pattern:
    """模式"""
    pattern_id: str
    pattern_type: str  # cyclic, trigger, trend
    description: str
    entities: List[str]
    relations: List[str]
    confidence: float
    occurrences: int = 0
    last_seen: datetime = field(default_factory=datetime.now)


class EntityExtractor:
    """实体识别器 - 使用大模型提取实体"""
    
    def __init__(self):
        self.entity_counter = 0
        
        # 接入大模型
        try:
            from llm.llm_service import get_llm_service
            self.llm = get_llm_service()
            self.llm_enabled = self.llm is not None
        except Exception:
            self.llm = None
            self.llm_enabled = False
    
    def extract(self, user_history: List[Dict[str, Any]]) -> List[Entity]:
        """从用户历史中提取实体"""
        
        # 如果有大模型，用它来提取实体
        if self.llm_enabled and user_history:
            try:
                # 合并历史记录为文本
                history_text = "\n".join([
                    f"- {record.get('activity', '')} {record.get('text', '')}"
                    for record in user_history[:10]  # 只取最近10条
                ])
                
                prompt = f"""
从以下用户活动中提取实体（人物、事件、地点、物品）：

{history_text}

以JSON格式返回：
[
    {{
        "type": "person/event/location/object",
        "name": "实体名称",
        "attributes": {{"key": "value"}}
    }}
]
"""
                response = self.llm.chat([
                    {"role": "system", "content": "你是实体识别专家。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.3)
                
                # 解析大模型响应
                import json
                import re
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    llm_entities = json.loads(json_match.group())
                    entities = []
                    for e in llm_entities:
                        entities.append(self._create_entity(
                            e['type'],
                            e['name'],
                            e.get('attributes', {})
                        ))
                    return entities
            except Exception as e:
                print(f"大模型实体提取失败，使用规则方法: {e}")
        
        # 降级：使用规则方法
        entities = []
        
        for record in user_history:
            # 提取人物
            if 'people' in record:
                for person in record['people']:
                    entities.append(self._create_entity(
                        'person',
                        person,
                        {'role': record.get('context', 'unknown')}
                    ))
            
            # 提取事件
            if 'activity' in record:
                entities.append(self._create_entity(
                    'event',
                    record['activity'],
                    {
                        'duration': record.get('duration', 0),
                        'timestamp': record.get('timestamp', datetime.now())
                    }
                ))
            
            # 提取地点
            if 'location' in record:
                entities.append(self._create_entity(
                    'location',
                    record['location'],
                    {'visit_count': 1}
                ))
            
            # 提取物品
            if 'objects' in record:
                for obj in record['objects']:
                    entities.append(self._create_entity(
                        'object',
                        obj,
                        {'category': record.get('category', 'general')}
                    ))
        
        return entities
    
    def _create_entity(self, entity_type: str, name: str, attributes: Dict) -> Entity:
        """创建实体"""
        self.entity_counter += 1
        return Entity(
            entity_id=f"{entity_type}_{self.entity_counter}",
            entity_type=entity_type,
            name=name,
            attributes=attributes
        )


class RelationExtractor:
    """关系抽取器"""
    
    def __init__(self):
        self.relation_counter = 0
    
    def extract(
        self,
        entities: List[Entity],
        user_history: List[Dict[str, Any]]
    ) -> List[Relation]:
        """抽取实体之间的关系"""
        relations = []
        
        # 因果关系
        causal_relations = self._extract_causal(entities, user_history)
        relations.extend(causal_relations)
        
        # 时序关系
        temporal_relations = self._extract_temporal(entities, user_history)
        relations.extend(temporal_relations)
        
        # 相关关系
        correlation_relations = self._extract_correlation(entities, user_history)
        relations.extend(correlation_relations)
        
        return relations
    
    def _extract_causal(
        self,
        entities: List[Entity],
        user_history: List[Dict[str, Any]]
    ) -> List[Relation]:
        """提取因果关系"""
        relations = []
        
        # 示例：工作压力 → 睡眠不足
        work_entities = [e for e in entities if 'work' in e.name.lower()]
        sleep_entities = [e for e in entities if 'sleep' in e.name.lower()]
        
        for work_e in work_entities:
            for sleep_e in sleep_entities:
                # 检查历史数据中的因果证据
                evidence = self._find_causal_evidence(
                    work_e, sleep_e, user_history
                )
                if evidence:
                    relations.append(self._create_relation(
                        'causal',
                        work_e.entity_id,
                        sleep_e.entity_id,
                        0.7,
                        evidence
                    ))
        
        return relations
    
    def _extract_temporal(
        self,
        entities: List[Entity],
        user_history: List[Dict[str, Any]]
    ) -> List[Relation]:
        """提取时序关系"""
        relations = []
        
        # 按时间排序的实体
        time_sorted = sorted(
            [e for e in entities if e.entity_type == 'event'],
            key=lambda x: x.attributes.get('timestamp', datetime.now())
        )
        
        # 连续事件建立时序关系
        for i in range(len(time_sorted) - 1):
            relations.append(self._create_relation(
                'temporal',
                time_sorted[i].entity_id,
                time_sorted[i+1].entity_id,
                0.9,
                [{'type': 'sequence'}]
            ))
        
        return relations
    
    def _extract_correlation(
        self,
        entities: List[Entity],
        user_history: List[Dict[str, Any]]
    ) -> List[Relation]:
        """提取相关关系"""
        relations = []
        
        # 示例：社交活动 ↔ 情绪改善
        social_entities = [e for e in entities if 'social' in e.name.lower()]
        emotion_entities = [e for e in entities if e.entity_type == 'event' and 'mood' in str(e.attributes)]
        
        for social_e in social_entities:
            for emotion_e in emotion_entities:
                relations.append(self._create_relation(
                    'correlation',
                    social_e.entity_id,
                    emotion_e.entity_id,
                    0.6,
                    [{'type': 'co-occurrence'}]
                ))
        
        return relations
    
    def _find_causal_evidence(
        self,
        cause: Entity,
        effect: Entity,
        history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """查找因果证据"""
        evidence = []
        
        for record in history:
            if cause.name.lower() in str(record).lower() and \
               effect.name.lower() in str(record).lower():
                evidence.append({
                    'timestamp': record.get('timestamp', datetime.now()),
                    'data': record
                })
        
        return evidence
    
    def _create_relation(
        self,
        relation_type: str,
        source: str,
        target: str,
        strength: float,
        evidence: List[Dict]
    ) -> Relation:
        """创建关系"""
        self.relation_counter += 1
        return Relation(
            relation_id=f"rel_{self.relation_counter}",
            relation_type=relation_type,
            source_entity=source,
            target_entity=target,
            strength=strength,
            evidence=evidence
        )


class PatternMiner:
    """模式挖掘器"""
    
    def __init__(self):
        self.pattern_counter = 0
    
    def mine(
        self,
        entities: List[Entity],
        relations: List[Relation],
        user_history: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """挖掘模式"""
        patterns = []
        
        # 周期模式
        cyclic = self._mine_cyclic_patterns(entities, user_history)
        patterns.extend(cyclic)
        
        # 触发模式
        trigger = self._mine_trigger_patterns(relations)
        patterns.extend(trigger)
        
        # 趋势模式
        trend = self._mine_trend_patterns(entities, user_history)
        patterns.extend(trend)
        
        return patterns
    
    def _mine_cyclic_patterns(
        self,
        entities: List[Entity],
        history: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """挖掘周期模式"""
        patterns = []
        
        # 按星期几分组
        weekday_events = defaultdict(list)
        for record in history:
            if 'timestamp' in record:
                weekday = record['timestamp'].weekday()
                weekday_events[weekday].append(record)
        
        # 检测每周一的模式
        if len(weekday_events[0]) > 2:  # 至少出现3次
            patterns.append(Pattern(
                pattern_id=f"pattern_{self.pattern_counter}",
                pattern_type="cyclic",
                description="每周一压力水平较高",
                entities=[e.entity_id for e in entities if 'stress' in e.name.lower()],
                relations=[],
                confidence=0.8,
                occurrences=len(weekday_events[0])
            ))
            self.pattern_counter += 1
        
        return patterns
    
    def _mine_trigger_patterns(self, relations: List[Relation]) -> List[Pattern]:
        """挖掘触发模式"""
        patterns = []
        
        # 查找强因果关系
        strong_causal = [r for r in relations if r.relation_type == 'causal' and r.strength > 0.7]
        
        for rel in strong_causal:
            patterns.append(Pattern(
                pattern_id=f"pattern_{self.pattern_counter}",
                pattern_type="trigger",
                description=f"{rel.source_entity} 触发 {rel.target_entity}",
                entities=[rel.source_entity, rel.target_entity],
                relations=[rel.relation_id],
                confidence=rel.strength,
                occurrences=len(rel.evidence)
            ))
            self.pattern_counter += 1
        
        return patterns
    
    def _mine_trend_patterns(
        self,
        entities: List[Entity],
        history: List[Dict[str, Any]]
    ) -> List[Pattern]:
        """挖掘趋势模式"""
        patterns = []
        
        # 检测健康分数趋势
        health_scores = []
        for record in history:
            if 'health_score' in record:
                health_scores.append(record['health_score'])
        
        if len(health_scores) > 5:
            # 简单趋势检测
            recent_avg = sum(health_scores[-3:]) / 3
            overall_avg = sum(health_scores) / len(health_scores)
            
            if recent_avg < overall_avg - 10:
                patterns.append(Pattern(
                    pattern_id=f"pattern_{self.pattern_counter}",
                    pattern_type="trend",
                    description="健康分数呈下降趋势",
                    entities=[e.entity_id for e in entities if 'health' in e.name.lower()],
                    relations=[],
                    confidence=0.7,
                    occurrences=len(health_scores)
                ))
                self.pattern_counter += 1
        
        return patterns


class PersonalKnowledgeGraph:
    """个人知识图谱"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.patterns: Dict[str, Pattern] = {}
        
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self.pattern_miner = PatternMiner()
    
    def build(self, user_history: List[Dict[str, Any]]):
        """构建知识图谱"""
        print(f"\n[知识图谱] 开始构建用户 {self.user_id} 的知识图谱")
        
        # 1. 实体识别
        entities = self.entity_extractor.extract(user_history)
        for entity in entities:
            self.entities[entity.entity_id] = entity
        print(f"  提取实体: {len(entities)} 个")
        
        # 2. 关系抽取
        relations = self.relation_extractor.extract(entities, user_history)
        for relation in relations:
            self.relations[relation.relation_id] = relation
        print(f"  抽取关系: {len(relations)} 个")
        
        # 3. 模式挖掘
        patterns = self.pattern_miner.mine(entities, relations, user_history)
        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern
        print(f"  挖掘模式: {len(patterns)} 个")
    
    def query(self, question: str) -> Dict[str, Any]:
        """基于图谱回答问题"""
        question_lower = question.lower()
        
        # 为什么类问题 - 查找因果链
        if '为什么' in question or 'why' in question_lower:
            return self._query_why(question)
        
        # 什么时候类问题 - 查找时序关系
        elif '什么时候' in question or 'when' in question_lower:
            return self._query_when(question)
        
        # 如何类问题 - 查找模式和建议
        elif '如何' in question or 'how' in question_lower:
            return self._query_how(question)
        
        # 默认：返回相关实体和关系
        else:
            return self._query_general(question)
    
    def _query_why(self, question: str) -> Dict[str, Any]:
        """回答"为什么"类问题"""
        # 查找因果关系
        causal_relations = [
            r for r in self.relations.values()
            if r.relation_type == 'causal'
        ]
        
        # 构建因果链
        causal_chain = []
        for rel in causal_relations:
            source = self.entities.get(rel.source_entity)
            target = self.entities.get(rel.target_entity)
            if source and target:
                causal_chain.append({
                    'cause': source.name,
                    'effect': target.name,
                    'strength': rel.strength,
                    'evidence_count': len(rel.evidence)
                })
        
        return {
            'question_type': 'why',
            'causal_chain': causal_chain,
            'answer': self._generate_why_answer(causal_chain)
        }
    
    def _query_when(self, question: str) -> Dict[str, Any]:
        """回答"什么时候"类问题"""
        # 查找时序关系和周期模式
        cyclic_patterns = [
            p for p in self.patterns.values()
            if p.pattern_type == 'cyclic'
        ]
        
        return {
            'question_type': 'when',
            'patterns': [
                {
                    'description': p.description,
                    'confidence': p.confidence,
                    'occurrences': p.occurrences
                }
                for p in cyclic_patterns
            ],
            'answer': self._generate_when_answer(cyclic_patterns)
        }
    
    def _query_how(self, question: str) -> Dict[str, Any]:
        """回答"如何"类问题"""
        # 查找相关模式和建议
        all_patterns = list(self.patterns.values())
        
        recommendations = []
        for pattern in all_patterns:
            if pattern.pattern_type == 'trigger':
                recommendations.append(f"避免触发 {pattern.description}")
            elif pattern.pattern_type == 'trend' and '下降' in pattern.description:
                recommendations.append(f"注意：{pattern.description}")
        
        return {
            'question_type': 'how',
            'recommendations': recommendations,
            'patterns': [p.description for p in all_patterns],
            'answer': self._generate_how_answer(recommendations)
        }
    
    def _query_general(self, question: str) -> Dict[str, Any]:
        """通用查询"""
        # 查找相关实体
        relevant_entities = []
        for entity in self.entities.values():
            if any(word in entity.name.lower() for word in question.lower().split()):
                relevant_entities.append({
                    'name': entity.name,
                    'type': entity.entity_type,
                    'attributes': entity.attributes
                })
        
        return {
            'question_type': 'general',
            'entities': relevant_entities,
            'entity_count': len(self.entities),
            'relation_count': len(self.relations),
            'pattern_count': len(self.patterns)
        }
    
    def _generate_why_answer(self, causal_chain: List[Dict]) -> str:
        """生成"为什么"的答案"""
        if not causal_chain:
            return "暂时没有发现明确的因果关系"
        
        answer = "根据知识图谱分析，可能的原因包括：\n"
        for i, link in enumerate(causal_chain, 1):
            answer += f"{i}. {link['cause']} 导致 {link['effect']} "
            answer += f"(置信度: {link['strength']:.2f}, 证据: {link['evidence_count']}次)\n"
        
        return answer
    
    def _generate_when_answer(self, patterns: List[Pattern]) -> str:
        """生成"什么时候"的答案"""
        if not patterns:
            return "暂时没有发现明显的时间模式"
        
        answer = "根据历史数据分析：\n"
        for pattern in patterns:
            answer += f"- {pattern.description} (出现{pattern.occurrences}次)\n"
        
        return answer
    
    def _generate_how_answer(self, recommendations: List[str]) -> str:
        """生成"如何"的答案"""
        if not recommendations:
            return "继续保持当前的健康习惯"
        
        answer = "建议采取以下措施：\n"
        for i, rec in enumerate(recommendations, 1):
            answer += f"{i}. {rec}\n"
        
        return answer
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return {
            'user_id': self.user_id,
            'entities': {
                'total': len(self.entities),
                'by_type': self._count_by_type(self.entities.values(), 'entity_type')
            },
            'relations': {
                'total': len(self.relations),
                'by_type': self._count_by_type(self.relations.values(), 'relation_type')
            },
            'patterns': {
                'total': len(self.patterns),
                'by_type': self._count_by_type(self.patterns.values(), 'pattern_type')
            }
        }
    
    def _count_by_type(self, items, type_attr: str) -> Dict[str, int]:
        """按类型统计"""
        counts = defaultdict(int)
        for item in items:
            item_type = getattr(item, type_attr)
            counts[item_type] += 1
        return dict(counts)
    
    def export(self) -> Dict[str, Any]:
        """导出图谱"""
        return {
            'user_id': self.user_id,
            'entities': [
                {
                    'id': e.entity_id,
                    'type': e.entity_type,
                    'name': e.name,
                    'attributes': e.attributes
                }
                for e in self.entities.values()
            ],
            'relations': [
                {
                    'id': r.relation_id,
                    'type': r.relation_type,
                    'source': r.source_entity,
                    'target': r.target_entity,
                    'strength': r.strength
                }
                for r in self.relations.values()
            ],
            'patterns': [
                {
                    'id': p.pattern_id,
                    'type': p.pattern_type,
                    'description': p.description,
                    'confidence': p.confidence
                }
                for p in self.patterns.values()
            ]
        }
