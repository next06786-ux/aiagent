"""
数据流协调器
将感知层数据流经5层架构，应用于6个生活领域
自动将数据存入RAG记忆系统
自动构建知识图谱（支持人物关系、升学规划、职业发展三种视图）
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

# 尝试导入生产级RAG
try:
    from learning.production_rag_system import ProductionRAGSystem, MemoryType
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# 导入信息提取和知识图谱
try:
    from knowledge.information_extractor import InformationExtractor
    from knowledge.information_knowledge_graph import InformationKnowledgeGraph
    INFO_KG_AVAILABLE = True
except ImportError:
    INFO_KG_AVAILABLE = False
    print("⚠️ 知识图谱模块不可用")


@dataclass
class PerceptionData:
    """感知层数据"""
    user_id: str
    text: Optional[str] = None
    image: Optional[str] = None
    sensors: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LifeDomainInsight:
    """生活领域洞察"""
    domain: str  # time, social, learning, emotion, finance, health
    insights: List[str]
    predictions: List[str]
    recommendations: List[str]
    confidence: float


class DataFlowOrchestrator:
    """数据流协调器 - 连接5层架构 + RAG记忆系统 + 知识图谱"""
    
    def __init__(self, perception_layer, meta_agent, knowledge_graph, 
                 reinforcement_learner, multimodal_fusion, rag_system=None,
                 info_kg_system=None):
        # 5层架构组件
        self.perception_layer = perception_layer
        self.meta_agent = meta_agent
        self.knowledge_graph = knowledge_graph
        self.reinforcement_learner = reinforcement_learner
        self.multimodal_fusion = multimodal_fusion
        
        # RAG记忆系统（核心记忆中枢）
        self.rag_system = rag_system
        
        # 知识图谱系统（支持人物关系、升学规划、职业发展三种视图）
        self.info_kg_system = info_kg_system
        
        # 信息提取器
        if INFO_KG_AVAILABLE:
            self.info_extractor = InformationExtractor()
            print("✓ 信息提取器已初始化")
        else:
            self.info_extractor = None
            print("⚠️ 信息提取器不可用")
        
        # 接入大模型
        try:
            from llm.llm_service import get_llm_service
            self.llm = get_llm_service()
            self.llm_enabled = self.llm is not None
            if self.llm_enabled:
                print("✓ 数据流协调器已接入大模型")
        except Exception as e:
            self.llm = None
            self.llm_enabled = False
            print(f"⚠️ 数据流协调器未接入大模型: {e}")
    
    def process_perception_data_sync(
        self, 
        perception_data: PerceptionData
    ) -> Dict[str, Any]:
        """
        同步处理感知层数据（用于对话场景）
        简化版本，快速返回结果
        """
        try:
            # 简化的处理流程
            result = {
                "domain_insights": {},
                "knowledge_graph_stats": {},
                "learning_stats": {}
            }
            
            # 获取知识图谱统计
            if self.knowledge_graph:
                result["knowledge_graph_stats"] = self.knowledge_graph.get_statistics()
            
            # 获取学习统计
            if self.reinforcement_learner:
                result["learning_stats"] = self.reinforcement_learner.get_statistics()
            
            # 生成6个领域的简单洞察
            domains = ["time", "social", "learning", "emotion", "finance", "health"]
            for domain in domains:
                result["domain_insights"][domain] = {
                    "suggestions": [f"基于你的{domain}数据分析..."],
                    "confidence": 0.7
                }
            
            return result
            
        except Exception as e:
            print(f"同步处理错误: {e}")
            return {"error": str(e)}
    
    async def process_perception_data(
        self, 
        perception_data: PerceptionData
    ) -> Dict[str, Any]:
        """
        处理感知层数据，流经5层架构
        
        第1层：多模态感知层 - 数据采集和质量评估
        第2层：混合推理层 - 元智能体协调
        第3层：知识图谱层 - 实体关系模式
        第4层：强化学习层 - 持续优化
        第5层：决策融合层 - 生成洞察
        
        核心：RAG记忆系统 - 存储所有数据和洞察
        """
        
        # 第1层：感知层处理
        perception_result = await self._layer1_perception(perception_data)
        
        # 存入RAG记忆 - 传感器数据
        if self.rag_system and RAG_AVAILABLE and perception_data.sensors:
            self._store_sensor_memory(perception_data)
        
        # 【新增】自动提取信息并构建知识图谱
        if self.info_extractor and self.info_kg_system and INFO_KG_AVAILABLE:
            await self._extract_and_build_knowledge_graph(
                perception_data, 
                perception_result
            )
        
        # 第2层：混合推理
        reasoning_result = await self._layer2_reasoning(perception_result)
        
        # 第3层：知识图谱更新
        knowledge_result = await self._layer3_knowledge(
            perception_data, reasoning_result
        )
        
        # 第4层：强化学习（如果有反馈）
        learning_result = self._layer4_learning()
        
        # 第5层：决策融合 - 生成6个领域的洞察
        domain_insights = await self._layer5_fusion(
            perception_result,
            reasoning_result,
            knowledge_result,
            learning_result
        )
        
        # 存入RAG记忆 - 对话和洞察
        if self.rag_system and RAG_AVAILABLE:
            self._store_conversation_memory(perception_data)
            self._store_insights_memory(domain_insights)
        
        return {
            "perception": perception_result,
            "reasoning": reasoning_result,
            "knowledge": knowledge_result,
            "learning": learning_result,
            "domain_insights": domain_insights,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _layer1_perception(
        self, 
        data: PerceptionData
    ) -> Dict[str, Any]:
        """第1层：多模态感知"""
        
        # 构造感知层需要的数据格式
        perception_data = {
            "text": data.text or "",
            "image": data.image,
            "sensor": data.sensors or {},
            "context": {
                "timestamp": data.timestamp.timestamp() if data.timestamp else None
            }
        }
        
        result = self.perception_layer.perceive(
            user_id=data.user_id,
            data=perception_data
        )
        
        return {
            "quality": result.get("overall_quality", 0),
            "modalities": result.get("modality_results", {}),
            "fusion": result.get("fusion_result", {})
        }
    
    async def _layer2_reasoning(
        self, 
        perception_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """第2层：混合推理（元智能体）"""
        # 构造用户数据
        user_data = {
            "perception_quality": perception_result.get("overall_quality", 0.5),
            "text_data": perception_result.get("text_result", {}),
            "sensor_data": perception_result.get("sensor_result", {})
        }
        
        # 元智能体协调
        result = await self.meta_agent.orchestrate(user_data)
        
        return {
            "selected_agents": result.get("selected_agents", []),
            "weights": result.get("weights", {}),
            "confidence": result.get("decision", {}).get("confidence", 0.5),
            "advice": result.get("advice", [])
        }
    
    async def _layer3_knowledge(
        self,
        perception_data: PerceptionData,
        reasoning_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """第3层：知识图谱更新"""
        # 构造历史记录
        history_record = {
            "timestamp": perception_data.timestamp,
            "activity": perception_data.text or "unknown",
            "sensors": perception_data.sensors or {}
        }
        
        # 更新知识图谱
        self.knowledge_graph.build([history_record])
        
        # 查询相关模式
        stats = self.knowledge_graph.get_statistics()
        
        return {
            "entities": stats["entities"]["total"],
            "relations": stats["relations"]["total"],
            "patterns": stats.get("patterns", {}).get("total", 0)  # 安全获取
        }
    
    def _layer4_learning(self) -> Dict[str, Any]:
        """第4层：强化学习状态"""
        stats = self.reinforcement_learner.get_statistics()
        
        return {
            "episodes": stats["total_episodes"],
            "average_reward": stats["average_reward"],
            "optimized_weights": stats["agent_weights"]
        }
    
    async def _layer5_fusion(
        self,
        perception: Dict[str, Any],
        reasoning: Dict[str, Any],
        knowledge: Dict[str, Any],
        learning: Dict[str, Any]
    ) -> List[LifeDomainInsight]:
        """第5层：决策融合 - 生成6个领域洞察"""
        
        insights = []
        
        # 1. 时间管理领域
        insights.append(await self._generate_time_insight(
            perception, reasoning, knowledge
        ))
        
        # 2. 社交管理领域
        insights.append(await self._generate_social_insight(
            perception, reasoning, knowledge
        ))
        
        # 3. 学习管理领域
        insights.append(await self._generate_learning_insight(
            perception, reasoning, knowledge
        ))
        
        # 4. 情绪管理领域
        insights.append(await self._generate_emotion_insight(
            perception, reasoning, knowledge
        ))
        
        # 5. 财务管理领域
        insights.append(await self._generate_finance_insight(
            perception, reasoning, knowledge
        ))
        
        # 6. 健康管理领域
        insights.append(await self._generate_health_insight(
            perception, reasoning, knowledge
        ))
        
        return [
            {
                "domain": ins.domain,
                "insights": ins.insights,
                "predictions": ins.predictions,
                "recommendations": ins.recommendations,
                "confidence": ins.confidence
            }
            for ins in insights
        ]
    
    async def _generate_time_insight(
        self, perception, reasoning, knowledge
    ) -> LifeDomainInsight:
        """时间管理洞察 - 基于真实数据 + 大模型增强"""
        
        # 如果有大模型，用它生成更智能的洞察
        if self.llm_enabled:
            try:
                # 从RAG检索相关历史
                context = ""
                if self.rag_system and RAG_AVAILABLE:
                    context = self.rag_system.get_context_for_conversation(
                        "时间管理 工作效率",
                        max_memories=3
                    )
                
                prompt = f"""
基于以下数据，生成时间管理领域的洞察：

当前状态：
- 数据质量: {perception.get('overall_quality', 0):.1%}
- 文本分析: {perception.get('text_result', {})}
- 传感器数据: {perception.get('sensor_result', {})}
- 知识图谱: {knowledge['entities']}个实体, {knowledge['patterns']}个模式

历史记忆：
{context}

请生成：
1. 2-3条当前洞察
2. 2-3条未来预测
3. 3-5条可操作建议

以JSON格式返回：
{{
    "insights": ["洞察1", "洞察2"],
    "predictions": ["预测1", "预测2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
                
                response = self.llm.chat([
                    {"role": "system", "content": "你是时间管理专家。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
                
                # 解析响应
                import json
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return LifeDomainInsight(
                        domain="time",
                        insights=result.get('insights', []),
                        predictions=result.get('predictions', []),
                        recommendations=result.get('recommendations', []),
                        confidence=reasoning['confidence']
                    )
            except Exception as e:
                print(f"大模型洞察生成失败，使用规则方法: {e}")
        
        # 降级：使用规则方法
        insights = []
        predictions = []
        recommendations = []
        
        text_result = perception.get('text_result', {})
        sensor_result = perception.get('sensor_result', {})
        quality = perception.get('overall_quality', 0)
        
        sentiment = text_result.get('sentiment', 'neutral')
        text_type = text_result.get('type', 'unknown')
        
        insights.append(f"数据质量: {quality:.1%}")
        
        if 'busy' in str(text_result).lower() or 'work' in str(text_result).lower():
            insights.append("检测到工作繁忙状态")
        
        if knowledge['entities'] > 0:
            insights.append(f"已记录 {knowledge['entities']} 个时间事件")
        
        if sentiment == 'negative' or 'stress' in str(text_result).lower():
            predictions.append("工作压力可能持续，建议合理安排休息时间")
            recommendations.append("今晚早点休息，恢复精力")
        else:
            predictions.append("当前工作节奏可持续")
        
        if knowledge['patterns'] > 0:
            predictions.append(f"发现 {knowledge['patterns']} 个时间模式，可用于优化日程")
        
        if quality < 0.5:
            recommendations.append("建议增加数据采集频率，以获得更准确的洞察")
        
        recommendations.append("使用时间块管理法，提高工作效率")
        
        if 'screen_time' in sensor_result:
            screen_time = sensor_result.get('screen_time', 0)
            if screen_time > 360:
                recommendations.append(f"屏幕使用时间较长({screen_time}分钟)，建议定时休息")
        
        return LifeDomainInsight(
            domain="time",
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=reasoning['confidence']
        )
    
    async def _generate_social_insight(
        self, perception, reasoning, knowledge
    ) -> LifeDomainInsight:
        """社交管理洞察 - 基于真实数据 + 大模型增强"""
        
        # 大模型增强
        if self.llm_enabled:
            try:
                context = ""
                if self.rag_system and RAG_AVAILABLE:
                    context = self.rag_system.get_context_for_conversation(
                        "社交 朋友 关系",
                        max_memories=3
                    )
                
                text_result = perception.get('text_result', {})
                prompt = f"""
基于以下数据，生成社交管理领域的洞察：

当前状态：
- 文本内容: {text_result}
- 知识图谱: {knowledge['relations']}个社交关系

历史记忆：
{context}

请生成JSON格式：
{{
    "insights": ["洞察1", "洞察2"],
    "predictions": ["预测1", "预测2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
                
                response = self.llm.chat([
                    {"role": "system", "content": "你是人际关系专家。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
                
                import json, re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return LifeDomainInsight(
                        domain="social",
                        insights=result.get('insights', []),
                        predictions=result.get('predictions', []),
                        recommendations=result.get('recommendations', []),
                        confidence=0.75
                    )
            except Exception as e:
                print(f"大模型社交洞察失败: {e}")
        
        # 降级：规则方法
        insights = []
        predictions = []
        recommendations = []
        
        text_result = perception.get('text_result', {})
        text_content = str(text_result.get('content', '')).lower()
        
        relations = knowledge.get('relations', 0)
        insights.append(f"知识图谱中记录了 {relations} 个社交关系")
        
        social_keywords = ['friend', 'meet', 'chat', 'call', 'party', 'dinner', 'colleague']
        has_social = any(keyword in text_content for keyword in social_keywords)
        
        if has_social:
            insights.append("检测到社交活动相关内容")
            predictions.append("社交活动有助于缓解压力")
        else:
            insights.append("近期社交活动较少")
            predictions.append("适当增加社交互动有益身心健康")
            recommendations.append("本周末可以约朋友见面")
        
        sentiment = text_result.get('sentiment', 'neutral')
        if sentiment == 'negative':
            recommendations.append("与信任的朋友倾诉可能有帮助")
        
        recommendations.append("保持每周至少2次社交互动")
        if relations < 3:
            recommendations.append("尝试拓展社交圈，参加兴趣小组")
        
        return LifeDomainInsight(
            domain="social",
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.70 + (0.10 if has_social else 0)
        )
    
    async def _generate_learning_insight(
        self, perception, reasoning, knowledge
    ) -> LifeDomainInsight:
        """学习管理洞察 - 基于真实数据 + 大模型增强"""
        
        # 大模型增强
        if self.llm_enabled:
            try:
                context = ""
                if self.rag_system and RAG_AVAILABLE:
                    context = self.rag_system.get_context_for_conversation(
                        "学习 课程 项目",
                        max_memories=3
                    )
                
                text_result = perception.get('text_result', {})
                sensor_result = perception.get('sensor_result', {})
                prompt = f"""
基于以下数据，生成学习管理领域的洞察：

当前状态：
- 文本内容: {text_result}
- 传感器: {sensor_result}
- 学习模式: {knowledge.get('patterns', 0)}个

历史记忆：
{context}

请生成JSON格式：
{{
    "insights": ["洞察1", "洞察2"],
    "predictions": ["预测1", "预测2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
                
                response = self.llm.chat([
                    {"role": "system", "content": "你是学习教练，擅长提高学习效率。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
                
                import json, re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return LifeDomainInsight(
                        domain="learning",
                        insights=result.get('insights', []),
                        predictions=result.get('predictions', []),
                        recommendations=result.get('recommendations', []),
                        confidence=0.80
                    )
            except Exception as e:
                print(f"大模型学习洞察失败: {e}")
        
        # 降级：规则方法
        insights = []
        predictions = []
        recommendations = []
        
        text_result = perception.get('text_result', {})
        sensor_result = perception.get('sensor_result', {})
        text_content = str(text_result.get('content', '')).lower()
        
        patterns = knowledge.get('patterns', 0)
        insights.append(f"已建立 {patterns} 个学习模式")
        
        learning_keywords = ['learn', 'study', 'read', 'course', 'book', 'project', 'complete']
        has_learning = any(keyword in text_content for keyword in learning_keywords)
        
        if has_learning:
            insights.append("检测到学习或项目完成相关内容")
            if 'complete' in text_content or 'finish' in text_content:
                insights.append("恭喜完成学习任务！")
                predictions.append("保持当前学习节奏")
        else:
            insights.append("今日暂无学习活动记录")
            recommendations.append("建议每天安排固定学习时间")
        
        if 'screen_time' in sensor_result:
            screen_time = sensor_result.get('screen_time', 0)
            if screen_time > 300:
                insights.append(f"屏幕使用时间: {screen_time}分钟")
                recommendations.append("长时间用眼，建议采用20-20-20法则休息")
        
        recommendations.append("采用番茄工作法，25分钟专注+5分钟休息")
        if patterns > 0:
            predictions.append(f"基于{patterns}个学习模式，可优化学习计划")
        else:
            predictions.append("持续记录学习数据，系统将发现最佳学习时段")
        
        return LifeDomainInsight(
            domain="learning",
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.75 + (0.10 if has_learning else 0)
        )
    
    async def _generate_finance_insight(
        self, perception, reasoning, knowledge
    ) -> LifeDomainInsight:
        """财务管理洞察 - 基于真实数据 + 大模型增强"""
        
        # 大模型增强
        if self.llm_enabled:
            try:
                context = ""
                if self.rag_system and RAG_AVAILABLE:
                    context = self.rag_system.get_context_for_conversation(
                        "消费 支出 理财",
                        max_memories=3
                    )
                
                text_result = perception.get('text_result', {})
                prompt = f"""
基于以下数据，生成财务管理领域的洞察：

当前状态：
- 文本内容: {text_result}
- 消费模式: {knowledge.get('patterns', 0)}个

历史记忆：
{context}

请生成JSON格式：
{{
    "insights": ["洞察1", "洞察2"],
    "predictions": ["预测1", "预测2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
                
                response = self.llm.chat([
                    {"role": "system", "content": "你是理财顾问，擅长个人财务规划。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.6)
                
                import json, re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return LifeDomainInsight(
                        domain="finance",
                        insights=result.get('insights', []),
                        predictions=result.get('predictions', []),
                        recommendations=result.get('recommendations', []),
                        confidence=0.70
                    )
            except Exception as e:
                print(f"大模型财务洞察失败: {e}")
        
        # 降级：规则方法
        insights = []
        predictions = []
        recommendations = []
        
        text_result = perception.get('text_result', {})
        text_content = str(text_result.get('content', '')).lower()
        
        finance_keywords = ['buy', 'purchase', 'pay', 'cost', 'price', 'money', 'expense']
        has_finance = any(keyword in text_content for keyword in finance_keywords)
        
        if has_finance:
            insights.append("检测到消费或财务相关内容")
            recommendations.append("记得记录本次支出")
        else:
            insights.append("今日暂无财务活动记录")
        
        insights.append("建议保持收支平衡")
        predictions.append("定期记录支出有助于财务规划")
        
        recommendations.append("设置月度预算，控制非必要支出")
        recommendations.append("建立应急基金，至少3-6个月生活费")
        
        patterns = knowledge.get('patterns', 0)
        if patterns > 0:
            predictions.append(f"发现{patterns}个消费模式，可用于优化预算")
        
        return LifeDomainInsight(
            domain="finance",
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.60 + (0.10 if has_finance else 0)
        )
    
    async def _generate_emotion_insight(
        self, perception, reasoning, knowledge
    ) -> LifeDomainInsight:
        """情绪管理洞察 - 基于真实数据 + 大模型增强"""
        
        # 大模型增强
        if self.llm_enabled:
            try:
                context = ""
                if self.rag_system and RAG_AVAILABLE:
                    context = self.rag_system.get_context_for_conversation(
                        "情绪 心情 压力",
                        max_memories=3
                    )
                
                text_result = perception.get('text_result', {})
                sensor_result = perception.get('sensor_result', {})
                sentiment = text_result.get('sentiment', 'neutral')
                
                prompt = f"""
基于以下数据，生成情绪管理领域的洞察：

当前状态：
- 情绪: {sentiment}
- 文本内容: {text_result}
- 传感器: {sensor_result}

历史记忆：
{context}

请生成JSON格式：
{{
    "insights": ["洞察1", "洞察2"],
    "predictions": ["预测1", "预测2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
                
                response = self.llm.chat([
                    {"role": "system", "content": "你是心理咨询师，擅长情绪分析和心理疏导。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.8)
                
                import json, re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return LifeDomainInsight(
                        domain="emotion",
                        insights=result.get('insights', []),
                        predictions=result.get('predictions', []),
                        recommendations=result.get('recommendations', []),
                        confidence=0.75
                    )
            except Exception as e:
                print(f"大模型情绪洞察失败: {e}")
        
        # 降级：规则方法
        insights = []
        predictions = []
        recommendations = []
        
        text_result = perception.get('text_result', {})
        sensor_result = perception.get('sensor_result', {})
        
        sentiment = text_result.get('sentiment', 'neutral')
        text_content = str(text_result.get('content', '')).lower()
        
        sentiment_map = {
            'positive': '积极',
            'negative': '消极',
            'neutral': '平和'
        }
        insights.append(f"当前情绪状态: {sentiment_map.get(sentiment, sentiment)}")
        
        if 'stress' in text_content or 'pressure' in text_content:
            insights.append("检测到压力相关表述")
        if 'happy' in text_content or 'completed' in text_content:
            insights.append("检测到成就感相关表述")
        
        if sentiment == 'negative':
            predictions.append("当前情绪偏低，建议关注心理健康")
            if 'work' in text_content:
                predictions.append("工作压力可能是主要因素")
            recommendations.append("尝试深呼吸或短暂休息")
            recommendations.append("与朋友交流可能有助于缓解压力")
        elif sentiment == 'positive':
            predictions.append("情绪状态良好，保持当前节奏")
            recommendations.append("记录当前的积极因素，未来可以复用")
        else:
            predictions.append("情绪平稳，可以尝试新的挑战")
            recommendations.append("适当的运动有助于提升情绪")
        
        if 'heart_rate' in sensor_result:
            hr = sensor_result.get('heart_rate', 70)
            if hr > 90:
                insights.append(f"心率偏高({hr}次/分)，可能处于紧张状态")
                recommendations.append("进行放松训练，降低心率")
        
        return LifeDomainInsight(
            domain="emotion",
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.70 + (0.15 if sentiment != 'neutral' else 0)
        )
    
    async def _generate_health_insight(
        self, perception, reasoning, knowledge
    ) -> LifeDomainInsight:
        """健康管理洞察 - 基于真实数据 + 大模型增强"""
        
        # 大模型增强
        if self.llm_enabled:
            try:
                context = ""
                if self.rag_system and RAG_AVAILABLE:
                    context = self.rag_system.get_context_for_conversation(
                        "健康 运动 睡眠",
                        max_memories=3
                    )
                
                sensor_result = perception.get('sensor_result', {})
                text_result = perception.get('text_result', {})
                
                prompt = f"""
基于以下数据，生成健康管理领域的洞察：

当前状态：
- 步数: {sensor_result.get('steps', 0)}步
- 心率: {sensor_result.get('heart_rate', 'N/A')}次/分
- 活动: {sensor_result.get('activity', 'unknown')}
- 文本: {text_result}

历史记忆：
{context}

请生成JSON格式：
{{
    "insights": ["洞察1", "洞察2"],
    "predictions": ["预测1", "预测2"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""
                
                response = self.llm.chat([
                    {"role": "system", "content": "你是健康顾问，擅长分析健康数据并给出实用建议。"},
                    {"role": "user", "content": prompt}
                ], temperature=0.7)
                
                import json, re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return LifeDomainInsight(
                        domain="health",
                        insights=result.get('insights', []),
                        predictions=result.get('predictions', []),
                        recommendations=result.get('recommendations', []),
                        confidence=0.85
                    )
            except Exception as e:
                print(f"大模型健康洞察失败: {e}")
        
        # 降级：规则方法
        insights = []
        predictions = []
        recommendations = []
        
        sensor_result = perception.get('sensor_result', {})
        text_result = perception.get('text_result', {})
        
        steps = sensor_result.get('steps', 0)
        insights.append(f"今日步数: {steps} 步")
        
        if steps < 5000:
            insights.append("活动量偏低")
            predictions.append("长期活动不足可能影响健康")
            recommendations.append("建议每天至少8000步")
            recommendations.append("可以尝试饭后散步或爬楼梯")
        elif steps < 8000:
            insights.append("活动量适中")
            predictions.append("保持当前活动量，健康风险较低")
            recommendations.append("可以适当增加运动强度")
        else:
            insights.append("活动量充足")
            predictions.append("运动量达标，继续保持")
            recommendations.append("注意运动后的拉伸和恢复")
        
        if 'heart_rate' in sensor_result:
            hr = sensor_result.get('heart_rate', 70)
            if hr < 60:
                insights.append(f"心率偏低({hr}次/分)")
            elif hr > 100:
                insights.append(f"心率偏高({hr}次/分)")
                recommendations.append("建议休息并监测心率变化")
            else:
                insights.append(f"心率正常({hr}次/分)")
        
        activity = sensor_result.get('activity', 'unknown')
        if activity == 'walking':
            insights.append("当前活动: 步行")
        elif activity == 'running':
            insights.append("当前活动: 跑步")
        elif activity == 'sitting':
            insights.append("当前活动: 静坐")
            if 'screen_time' in sensor_result:
                recommendations.append("久坐提醒: 建议每小时起身活动5分钟")
        
        text_content = str(text_result.get('content', '')).lower()
        if 'tired' in text_content or 'exhausted' in text_content:
            predictions.append("检测到疲劳状态，建议充足休息")
            recommendations.append("今晚早点睡觉，保证7-8小时睡眠")
        
        return LifeDomainInsight(
            domain="health",
            insights=insights,
            predictions=predictions,
            recommendations=recommendations,
            confidence=0.85 if steps > 0 else 0.60
        )
    
    def _store_sensor_memory(self, perception_data: PerceptionData):
        """存储传感器数据到RAG记忆"""
        if not self.rag_system or not RAG_AVAILABLE:
            return
        
        try:
            content = f"传感器数据: {perception_data.sensors}"
            self.rag_system.add_memory(
                memory_type=MemoryType.SENSOR_DATA,
                content=content,
                metadata={
                    "timestamp": perception_data.timestamp.isoformat(),
                    "sensors": perception_data.sensors
                },
                importance=0.4  # 传感器数据重要性较低
            )
        except Exception as e:
            print(f"Failed to store sensor memory: {e}")
    
    def _store_conversation_memory(self, perception_data: PerceptionData):
        """存储对话到RAG记忆"""
        if not self.rag_system or not RAG_AVAILABLE or not perception_data.text:
            return
        
        try:
            self.rag_system.add_memory(
                memory_type=MemoryType.CONVERSATION,
                content=perception_data.text,
                metadata={
                    "timestamp": perception_data.timestamp.isoformat(),
                    "source": "user_input"
                },
                importance=0.6  # 对话重要性中等
            )
        except Exception as e:
            print(f"Failed to store conversation memory: {e}")
    
    def _store_insights_memory(self, domain_insights: List[Dict[str, Any]]):
        """存储洞察到RAG记忆"""
        if not self.rag_system or not RAG_AVAILABLE:
            return
        
        try:
            for insight in domain_insights:
                domain = insight['domain']
                insights_text = "; ".join(insight['insights'])
                
                content = f"[{domain}领域] {insights_text}"
                
                self.rag_system.add_memory(
                    memory_type=MemoryType.INSIGHT,
                    content=content,
                    metadata={
                        "domain": domain,
                        "confidence": insight['confidence'],
                        "predictions": insight['predictions'],
                        "recommendations": insight['recommendations']
                    },
                    importance=0.8  # 洞察重要性较高
                )
        except Exception as e:
            print(f"Failed to store insights memory: {e}")
    
    # ==================== 知识图谱自动化构建 ====================
    
    async def _extract_and_build_knowledge_graph(
        self,
        perception_data: PerceptionData,
        perception_result: Dict[str, Any]
    ):
        """
        自动提取信息并构建知识图谱
        
        流程：
        1. 从感知结果中提取信息（实体、事件、概念）
        2. 推理信息之间的关系
        3. 添加信息节点到Neo4j图谱
        4. 建立关系连接
        5. 添加来源溯源
        """
        try:
            print(f"\n[知识图谱自动化] 开始构建用户 {perception_data.user_id} 的信息图谱...")
            
            # 1. 提取信息
            all_entities = []
            all_events = []
            all_concepts = []
            
            # 从图像提取
            if 'image_perception' in perception_result:
                print("  [提取] 从图像中提取信息...")
                image_info = self.info_extractor.extract_from_photo(
                    perception_result['image_perception']
                )
                all_entities.extend(image_info['entities'])
                all_events.extend(image_info['events'])
                all_concepts.extend(image_info['concepts'])
                print(f"    ✓ 图像: {len(image_info['entities'])}实体, {len(image_info['events'])}事件, {len(image_info['concepts'])}概念")
            
            # 从传感器提取
            if 'sensor_perception' in perception_result:
                print("  [提取] 从传感器中提取信息...")
                sensor_info = self.info_extractor.extract_from_sensor(
                    perception_result['sensor_perception']
                )
                all_entities.extend(sensor_info['entities'])
                all_events.extend(sensor_info['events'])
                all_concepts.extend(sensor_info['concepts'])
                print(f"    ✓ 传感器: {len(sensor_info['entities'])}实体, {len(sensor_info['events'])}事件, {len(sensor_info['concepts'])}概念")
            
            # 从对话提取
            if perception_data.text:
                print("  [提取] 从对话中提取信息...")
                text_metadata = {}
                if 'text_perception' in perception_result:
                    text_metadata = {
                        'intent': perception_result['text_perception'].get('intent'),
                        'sentiment': perception_result['text_perception'].get('sentiment')
                    }
                
                text_info = self.info_extractor.extract_from_conversation(
                    perception_data.text,
                    text_metadata
                )
                all_entities.extend(text_info['entities'])
                all_events.extend(text_info['events'])
                all_concepts.extend(text_info['concepts'])
                print(f"    ✓ 对话: {len(text_info['entities'])}实体, {len(text_info['events'])}事件, {len(text_info['concepts'])}概念")
            
            # 2. 合并去重
            print("  [合并] 去重和合并信息...")
            all_entities = self.info_extractor.merge_duplicate_information(all_entities)
            all_events = self.info_extractor.merge_duplicate_information(all_events)
            all_concepts = self.info_extractor.merge_duplicate_information(all_concepts)
            
            total_info = len(all_entities) + len(all_events) + len(all_concepts)
            print(f"    ✓ 合并后: {len(all_entities)}实体, {len(all_events)}事件, {len(all_concepts)}概念 (共{total_info}个)")
            
            if total_info == 0:
                print("  ⚠️ 未提取到任何信息，跳过图谱构建")
                return
            
            # 3. 推理关系
            print("  [推理] 推理信息之间的关系...")
            relationships = self.info_extractor.infer_relationships(
                all_entities,
                all_events,
                all_concepts,
                context={
                    'timestamp': perception_data.timestamp,
                    'user_id': perception_data.user_id
                }
            )
            print(f"    ✓ 推理出 {len(relationships)} 个关系")
            
            # 4. 添加到Neo4j图谱
            print("  [存储] 添加信息节点到Neo4j...")
            
            # 生成来源ID
            source_id = f"{perception_data.user_id}_{int(perception_data.timestamp.timestamp() * 1000)}"
            
            # 添加来源节点
            self.info_kg_system.add_source(
                source_type=self._determine_source_type(perception_data),
                source_id=source_id,
                timestamp=int(perception_data.timestamp.timestamp() * 1000),
                metadata={
                    'has_text': bool(perception_data.text),
                    'has_image': bool(perception_data.image),
                    'has_sensors': bool(perception_data.sensors)
                }
            )
            
            # 添加实体节点
            entity_count = 0
            for entity in all_entities:
                info_id = self.info_kg_system.add_information(
                    name=entity['name'],
                    info_type='entity',
                    category=entity.get('category', '其他'),
                    confidence=entity.get('confidence', 0.7),
                    attributes={
                        'entity_type': entity.get('entity_type', 'unknown'),
                        **entity.get('attributes', {})
                    }
                )
                
                # 添加溯源关系
                if info_id:
                    self.info_kg_system.add_source_relationship(
                        info_name=entity['name'],
                        source_id=source_id,
                        relation_type='EXTRACTED_FROM',
                        confidence=entity.get('confidence', 0.7)
                    )
                    entity_count += 1
            
            # 添加事件节点
            event_count = 0
            for event in all_events:
                info_id = self.info_kg_system.add_information(
                    name=event['name'],
                    info_type='event',
                    category=event.get('category', '其他'),
                    confidence=event.get('confidence', 0.7),
                    attributes={
                        'event_type': event.get('event_type', 'unknown'),
                        **event.get('attributes', {})
                    }
                )
                
                # 添加溯源关系
                if info_id:
                    self.info_kg_system.add_source_relationship(
                        info_name=event['name'],
                        source_id=source_id,
                        relation_type='RECORDED_IN',
                        confidence=event.get('confidence', 0.7)
                    )
                    event_count += 1
            
            # 添加概念节点
            concept_count = 0
            for concept in all_concepts:
                info_id = self.info_kg_system.add_information(
                    name=concept['name'],
                    info_type='concept',
                    category=concept.get('category', '其他'),
                    confidence=concept.get('confidence', 0.7),
                    attributes=concept.get('attributes', {})
                )
                
                # 添加溯源关系
                if info_id:
                    self.info_kg_system.add_source_relationship(
                        info_name=concept['name'],
                        source_id=source_id,
                        relation_type='MENTIONED_IN',
                        confidence=concept.get('confidence', 0.7)
                    )
                    concept_count += 1
            
            print(f"    ✓ 已添加: {entity_count}实体, {event_count}事件, {concept_count}概念")
            
            # 5. 添加关系
            print("  [连接] 建立信息之间的关系...")
            relation_count = 0
            for rel in relationships:
                success = self.info_kg_system.add_information_relationship(
                    source_name=rel['source'],
                    target_name=rel['target'],
                    relation_type=rel['type'],
                    properties={
                        'confidence': rel.get('confidence', 0.7),
                        'inferred_at': datetime.now().isoformat()
                    }
                )
                if success:
                    relation_count += 1
            
            print(f"    ✓ 已建立 {relation_count} 个关系")
            
            # 6. 获取图谱统计
            stats = self.info_kg_system.get_statistics()
            print(f"\n[知识图谱自动化] 构建完成!")
            print(f"  当前图谱规模:")
            print(f"    - 信息节点: {stats['information']['total']} 个")
            print(f"    - 来源记录: {stats['sources']['total']} 个")
            print(f"    - 关系连接: {stats['relationships']['total']} 个\n")
            
        except Exception as e:
            import traceback
            print(f"\n❌ 知识图谱自动化构建失败: {e}")
            traceback.print_exc()
    
    def _determine_source_type(self, perception_data: PerceptionData) -> str:
        """确定数据来源类型"""
        if perception_data.image:
            return 'photo'
        elif perception_data.sensors:
            return 'sensor_record'
        elif perception_data.text:
            return 'conversation'
        else:
            return 'manual_input'


# 创建全局实例的工厂函数
def create_data_flow_orchestrator(
    perception_layer,
    meta_agent,
    knowledge_graph,
    reinforcement_learner,
    multimodal_fusion,
    rag_system=None,
    info_kg_system=None
) -> DataFlowOrchestrator:
    """创建数据流协调器"""
    return DataFlowOrchestrator(
        perception_layer=perception_layer,
        meta_agent=meta_agent,
        knowledge_graph=knowledge_graph,
        reinforcement_learner=reinforcement_learner,
        multimodal_fusion=multimodal_fusion,
        rag_system=rag_system,
        info_kg_system=info_kg_system
    )
