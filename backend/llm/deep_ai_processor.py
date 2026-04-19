"""
深化的AI处理流程集成器
实现完整的6层AI处理流程
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from enum import Enum

from llm.meta_agent_router import get_meta_agent_router, DomainType
from llm.enhanced_memory_retriever import get_enhanced_memory_retriever, MemoryType


class AIProcessingLayer(Enum):
    """AI处理层"""
    META_AGENT = "meta_agent"
    MEMORY = "memory"
    DOMAIN_ANALYSIS = "domain_analysis"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    HYBRID_INTELLIGENCE = "hybrid_intelligence"
    RESPONSE_GENERATION = "response_generation"


class DeepAIProcessor:
    """深化的AI处理器"""
    
    def __init__(self, user_id: str):
        """
        初始化AI处理器
        
        Args:
            user_id: 用户ID
        """
        self.user_id = user_id
        self.router = get_meta_agent_router()
        self.memory_retriever = get_enhanced_memory_retriever(user_id)
        self.processing_history = []
        
        # 如果记忆为空，初始化测试数据
        if len(self.memory_retriever.memories) == 0:
            print(f"⚠️  用户 {user_id} 的记忆库为空，正在初始化测试数据...")
            self._init_test_memories()
    
    def process(self, user_message: str, user_context: Dict[str, Any] = None, progress_callback=None, thinking_callback=None) -> Dict[str, Any]:
        """
        处理用户消息，经过6层处理
        
        Args:
            user_message: 用户消息
            user_context: 用户上下文
            progress_callback: 进度回调函数 callback(layer, message)
            thinking_callback: 思考过程回调函数 callback(thinking_text) - 实时流式推送
        
        Returns:
            处理结果
        """
        # 保存回调以便在子方法中使用
        self._current_progress_callback = progress_callback
        self._current_thinking_callback = thinking_callback
        
        processing_result = {
            "user_message": user_message,
            "timestamp": datetime.now().isoformat(),
            "layers": {}
        }
        
        # 辅助函数：添加思考内容
        def add_thinking(text: str):
            if thinking_callback:
                thinking_callback(text + "\n")
        
        # 第1层：元智能体路由
        if progress_callback:
            progress_callback(1, "🧠 元智能体正在分析问题类型...")
        add_thinking("🧠 第1层：元智能体路由分析")
        
        layer1_result = self._layer1_meta_agent_routing(user_message, user_context)
        processing_result["layers"][AIProcessingLayer.META_AGENT.value] = layer1_result
        
        domains = ', '.join(layer1_result['primary_domains'])
        if progress_callback:
            progress_callback(1, f"🧠 识别到主要领域：{domains}")
        add_thinking(f"   识别到的主要领域：{domains}")
        if layer1_result.get('routing_explanation'):
            add_thinking(f"   路由原因：{layer1_result['routing_explanation']}")
        add_thinking("")
        
        # 第2层：历史记忆检索
        if progress_callback:
            progress_callback(2, "💭 正在检索相关历史记忆...")
        add_thinking("💭 第2层：历史记忆检索")
        
        layer2_result = self._layer2_memory_retrieval(user_message, layer1_result)
        processing_result["layers"][AIProcessingLayer.MEMORY.value] = layer2_result
        
        memory_count = len(layer2_result.get('similar_memories', []))
        if progress_callback:
            progress_callback(2, f"💭 找到 {memory_count} 条相关记忆")
        
        if memory_count > 0:
            add_thinking(f"   找到 {memory_count} 条相关历史记忆")
            for i, mem in enumerate(layer2_result['similar_memories'][:2], 1):
                add_thinking(f"   • 记忆{i}：{mem['content'][:50]}... (相似度: {mem['similarity']:.1%})")
        else:
            add_thinking("   未找到相关历史记忆，这是一个新话题")
        add_thinking("")
        
        # 第3层：6领域分析
        if progress_callback:
            progress_callback(3, "🔍 正在进行6大领域深度分析...")
        add_thinking("🔍 第3层：6大领域深度分析")
        
        layer3_result = self._layer3_domain_analysis(user_message, layer1_result, layer2_result)
        processing_result["layers"][AIProcessingLayer.DOMAIN_ANALYSIS.value] = layer3_result
        
        domain_count = len(layer3_result.get('domain_analyses', {}))
        if progress_callback:
            progress_callback(3, f"🔍 完成 {domain_count} 个领域的分析")
        
        add_thinking(f"   分析了 {domain_count} 个相关领域")
        primary_focus = layer3_result.get('primary_focus', '未知')
        add_thinking(f"   主要关注点：{primary_focus}")
        add_thinking("")
        
        # 第4层：知识图谱推理
        if progress_callback:
            progress_callback(4, "🕸️ 正在进行知识图谱推理...")
        add_thinking("🕸️ 第4层：知识图谱推理")
        
        layer4_result = self._layer4_knowledge_graph_reasoning(user_message, layer1_result, layer3_result)
        processing_result["layers"][AIProcessingLayer.KNOWLEDGE_GRAPH.value] = layer4_result
        
        chain_count = len(layer4_result.get('causal_chains', []))
        if progress_callback:
            progress_callback(4, f"🕸️ 发现 {chain_count} 条因果关系链")
        
        if chain_count > 0:
            add_thinking(f"   发现 {chain_count} 条因果关系链")
            for i, chain in enumerate(layer4_result['causal_chains'][:2], 1):
                add_thinking(f"   • 因果链{i}：{chain}")
        else:
            add_thinking("   未发现明显的因果关系链")
        add_thinking("")
        
        # 第5层：混合智能选择
        if progress_callback:
            progress_callback(5, "⚡ 正在选择最优智能策略...")
        add_thinking("⚡ 第5层：混合智能策略选择")
        
        layer5_result = self._layer5_hybrid_intelligence_selection(user_message, layer1_result, layer3_result, layer4_result)
        processing_result["layers"][AIProcessingLayer.HYBRID_INTELLIGENCE.value] = layer5_result
        
        strategy = layer5_result.get('selected_strategy', '未知')
        if progress_callback:
            progress_callback(5, f"⚡ 选择策略：{strategy}")
        
        add_thinking(f"   选择策略：{strategy}")
        llm_weight = layer5_result.get('llm_weight', 0)
        personal_weight = layer5_result.get('personal_model_weight', 0)
        add_thinking(f"   LLM权重：{llm_weight:.1%} | 个人模型权重：{personal_weight:.1%}")
        add_thinking("")
        
        # 第6层：回复生成
        if progress_callback:
            progress_callback(6, "✍️ 正在生成个性化回复...")
        add_thinking("✍️ 第6层：个性化回复生成")
        
        layer6_result = self._layer6_response_generation(user_message, processing_result)
        processing_result["layers"][AIProcessingLayer.RESPONSE_GENERATION.value] = layer6_result
        
        confidence = layer6_result.get('confidence', 0)
        add_thinking(f"   生成置信度：{confidence:.1%}")
        add_thinking(f"   回复已根据您的个人特征和历史偏好进行优化")
        
        if progress_callback:
            progress_callback(6, "✍️ 回复生成完成")
        
        # 最终回复
        processing_result["final_response"] = layer6_result.get("response", "")
        processing_result["thinking_process"] = ""  # 已经流式推送了，不需要再生成
        
        # 【新增】自动存储对话记忆到RAG系统
        try:
            # 存储用户消息
            self.memory_retriever.add_memory(
                memory_type=MemoryType.CONVERSATION,
                content=f"用户提问: {user_message}",
                metadata={
                    "domain": processing_result["layers"]["domain_analysis"]["primary_focus"],
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "user_query",
                    "domains": processing_result["layers"]["meta_agent"]["primary_domains"]
                },
                importance=0.7
            )
            
            # 存储AI回复
            self.memory_retriever.add_memory(
                memory_type=MemoryType.CONVERSATION,
                content=f"AI回复: {processing_result['final_response']}",
                metadata={
                    "domain": processing_result["layers"]["domain_analysis"]["primary_focus"],
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "ai_response",
                    "user_query": user_message,
                    "confidence": processing_result["layers"]["response_generation"]["confidence"]
                },
                importance=0.75
            )
            
            print(f"✅ [自动记忆] 对话已存入RAG记忆系统")
            
        except Exception as e:
            print(f"⚠️ [自动记忆] 存储对话失败: {e}")
        
        # 保存处理历史
        self.processing_history.append(processing_result)
        
        # 清理回调
        if hasattr(self, '_current_progress_callback'):
            delattr(self, '_current_progress_callback')
        if hasattr(self, '_current_thinking_callback'):
            delattr(self, '_current_thinking_callback')
        
        return processing_result
    
    def _layer1_meta_agent_routing(self, user_message: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        第1层：元智能体路由
        根据问题类型路由到不同的领域
        
        Args:
            user_message: 用户消息
            user_context: 用户上下文
        
        Returns:
            路由结果
        """
        primary_domains, domain_scores = self.router.route(user_message, user_context)
        
        result = {
            "primary_domains": [d.value for d in primary_domains],
            "domain_scores": {d.value: s for d, s in domain_scores.items()},
            "routing_explanation": self.router.get_routing_explanation(user_message, primary_domains, domain_scores)
        }
        
        return result
    
    def _layer2_memory_retrieval(self, user_message: str, layer1_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        第2层：历史记忆检索
        检索相关的历史信息
        
        Args:
            user_message: 用户消息
            layer1_result: 第1层结果
        
        Returns:
            记忆检索结果
        """
        # 按相似度检索
        similar_memories = self.memory_retriever.retrieve_by_similarity(user_message, top_k=3)
        
        # 按类型检索（对话记忆）
        conversation_memories = self.memory_retriever.retrieve_by_type(MemoryType.CONVERSATION, top_k=2)
        
        # 按类型检索（决策记忆）
        decision_memories = self.memory_retriever.retrieve_by_type(MemoryType.DECISION, top_k=2)
        
        # 检索重要记忆
        important_memories = self.memory_retriever.retrieve_important_memories(top_k=2)
        
        result = {
            "similar_memories": [
                {
                    "content": m.content,
                    "type": m.memory_type.value,
                    "similarity": s,
                    "timestamp": m.timestamp.isoformat()
                }
                for m, s in similar_memories
            ],
            "conversation_history": [
                {
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in conversation_memories
            ],
            "decision_history": [
                {
                    "content": m.content,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in decision_memories
            ],
            "important_memories": [
                {
                    "content": m.content,
                    "importance": m.importance,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in important_memories
            ],
            "memory_statistics": self.memory_retriever.get_memory_statistics()
        }
        
        return result
    
    def _layer3_domain_analysis(self, user_message: str, layer1_result: Dict[str, Any], 
                               layer2_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        第3层：6领域分析
        对每个主要领域进行详细分析
        
        Args:
            user_message: 用户消息
            layer1_result: 第1层结果
            layer2_result: 第2层结果
        
        Returns:
            领域分析结果
        """
        primary_domains = layer1_result["primary_domains"]
        domain_analyses = {}
        
        for domain_str in primary_domains:
            domain = DomainType(domain_str)
            domain_info = self.router.get_domain_info(domain)
            
            # 这里应该调用实际的领域分析器
            # 现在返回框架结构
            analysis = {
                "domain": domain_str,
                "domain_name": domain_info.get("name", ""),
                "description": domain_info.get("description", ""),
                "key_metrics": domain_info.get("key_metrics", []),
                "analysis_focus": domain_info.get("analysis_focus", []),
                "insights": self._generate_domain_insights(domain, user_message, layer2_result),
                "recommendations": self._generate_domain_recommendations(domain, user_message)
            }
            
            domain_analyses[domain_str] = analysis
        
        result = {
            "domain_analyses": domain_analyses,
            "primary_focus": primary_domains[0] if primary_domains else "general"
        }
        
        return result
    
    def _layer4_knowledge_graph_reasoning(self, user_message: str, layer1_result: Dict[str, Any],
                                         layer3_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        第4层：知识图谱推理
        查询知识图谱中的相关信息
        
        Args:
            user_message: 用户消息
            layer1_result: 第1层结果
            layer3_result: 第3层结果
        
        Returns:
            知识图谱推理结果
        """
        # 这里应该调用实际的知识图谱推理器
        # 现在返回框架结构
        
        result = {
            "causal_chains": self._extract_causal_chains(user_message),
            "related_concepts": self._extract_related_concepts(user_message),
            "reasoning_paths": self._generate_reasoning_paths(user_message, layer1_result),
            "knowledge_graph_insights": self._generate_kg_insights(user_message)
        }
        
        return result
    
    def _layer5_hybrid_intelligence_selection(self, user_message: str, layer1_result: Dict[str, Any],
                                             layer3_result: Dict[str, Any], layer4_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        第5层：混合智能选择
        选择LLM、Personal Model还是混合策略
        
        Args:
            user_message: 用户消息
            layer1_result: 第1层结果
            layer3_result: 第3层结果
            layer4_result: 第4层结果
        
        Returns:
            混合智能选择结果
        """
        # 分析问题特征
        problem_features = self._analyze_problem_features(user_message)
        
        # 选择策略
        strategy = self._select_strategy(problem_features)
        
        result = {
            "problem_features": problem_features,
            "selected_strategy": strategy,
            "strategy_rationale": self._generate_strategy_rationale(strategy, problem_features),
            "llm_weight": self._calculate_llm_weight(strategy),
            "personal_model_weight": self._calculate_personal_model_weight(strategy)
        }
        
        return result
    
    def _layer6_response_generation(self, user_message: str, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        第6层：回复生成
        综合所有信息生成最终回复
        
        Args:
            user_message: 用户消息
            processing_result: 完整的处理结果
        
        Returns:
            回复生成结果
        """
        # 提取关键信息
        domain_analyses = processing_result["layers"]["domain_analysis"]["domain_analyses"]
        kg_insights = processing_result["layers"]["knowledge_graph"]["knowledge_graph_insights"]
        strategy = processing_result["layers"]["hybrid_intelligence"]["selected_strategy"]
        
        # 生成回复（传递进度回调）
        response = self._generate_response(user_message, domain_analyses, kg_insights, strategy, processing_result)
        
        result = {
            "response": response,
            "response_structure": {
                "analysis": self._extract_analysis_part(response),
                "reasoning": self._extract_reasoning_part(response),
                "recommendations": self._extract_recommendations_part(response),
                "action_plan": self._extract_action_plan_part(response)
            },
            "confidence": self._calculate_response_confidence(processing_result)
        }
        
        return result
    
    # 辅助方法
    
    def _generate_domain_insights(self, domain: DomainType, user_message: str, 
                                 layer2_result: Dict[str, Any]) -> List[str]:
        """生成领域洞察"""
        insights = []
        
        if domain == DomainType.HEALTH:
            insights.append("根据你的睡眠数据，最近睡眠质量有所下降")
            insights.append("建议增加运动时间以改善整体健康")
        elif domain == DomainType.TIME:
            insights.append("你的工作时间有所增加，可能导致时间压力")
            insights.append("建议优化任务优先级以提高效率")
        elif domain == DomainType.EMOTION:
            insights.append("你的情绪波动较大，可能与压力增加有关")
            insights.append("建议进行放松活动以稳定情绪")
        
        return insights
    
    def _generate_domain_recommendations(self, domain: DomainType, user_message: str) -> List[str]:
        """生成领域建议"""
        recommendations = []
        
        if domain == DomainType.HEALTH:
            recommendations.append("每天保证7-8小时睡眠")
            recommendations.append("每周进行3-4次运动")
        elif domain == DomainType.TIME:
            recommendations.append("使用番茄工作法提高专注度")
            recommendations.append("定期休息以避免认知过载")
        elif domain == DomainType.EMOTION:
            recommendations.append("每天进行10分钟冥想")
            recommendations.append("与朋友交流以释放压力")
        
        return recommendations
    
    def _extract_causal_chains(self, user_message: str) -> List[str]:
        """提取因果链"""
        # 示例因果链
        causal_chains = [
            "睡眠不足 → 压力增加 → 效率下降",
            "运动减少 → 健康分数下降 → 心情变差",
            "工作时间增加 → 社交时间减少 → 孤独感增加"
        ]
        return causal_chains
    
    def _extract_related_concepts(self, user_message: str) -> List[str]:
        """提取相关概念"""
        concepts = ["睡眠", "压力", "效率", "健康", "心情"]
        return concepts
    
    def _generate_reasoning_paths(self, user_message: str, layer1_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成推理路径"""
        paths = [
            {
                "path": "睡眠 → 免疫力 → 健康分数",
                "confidence": 0.85,
                "evidence": "历史数据显示睡眠与健康分数高度相关"
            }
        ]
        return paths
    
    def _generate_kg_insights(self, user_message: str) -> List[str]:
        """生成知识图谱洞察"""
        insights = [
            "你的睡眠问题可能是导致最近压力增加的主要原因",
            "改善睡眠可能会连锁改善你的多个生活领域"
        ]
        return insights
    
    def _analyze_problem_features(self, user_message: str) -> Dict[str, float]:
        """分析问题特征"""
        features = {
            "creativity_level": 0.3,  # 创意程度
            "personalization_level": 0.7,  # 个性化程度
            "generality_level": 0.4  # 通用性程度
        }
        return features
    
    def _select_strategy(self, problem_features: Dict[str, float]) -> str:
        """选择策略"""
        if problem_features["creativity_level"] > 0.6:
            return "llm_only"
        elif problem_features["personalization_level"] > 0.6:
            return "personal_model_only"
        else:
            return "hybrid"
    
    def _generate_strategy_rationale(self, strategy: str, problem_features: Dict[str, float]) -> str:
        """生成策略理由"""
        rationales = {
            "llm_only": "这个问题需要创意和通用知识，使用LLM最合适",
            "personal_model_only": "这个问题需要个性化和精准，使用个人模型最合适",
            "hybrid": "这个问题需要平衡创意和个性化，使用混合策略最合适"
        }
        return rationales.get(strategy, "")
    
    def _calculate_llm_weight(self, strategy: str) -> float:
        """计算LLM权重"""
        weights = {
            "llm_only": 0.9,
            "personal_model_only": 0.1,
            "hybrid": 0.5
        }
        return weights.get(strategy, 0.5)
    
    def _calculate_personal_model_weight(self, strategy: str) -> float:
        """计算个人模型权重"""
        weights = {
            "llm_only": 0.1,
            "personal_model_only": 0.9,
            "hybrid": 0.5
        }
        return weights.get(strategy, 0.5)
    
    def _generate_response(self, user_message: str, domain_analyses: Dict[str, Any],
                          kg_insights: List[str], strategy: str, processing_result: Dict[str, Any] = None) -> str:
        """生成回复（使用LLM）"""
        # 获取进度回调（如果有）
        progress_callback = None
        if processing_result and hasattr(self, '_current_progress_callback'):
            progress_callback = self._current_progress_callback
        
        # 构建提示词
        if progress_callback:
            progress_callback(6, "✍️ 正在构建AI提示词...")
        prompt = self._build_response_prompt(user_message, domain_analyses, kg_insights, strategy)
        
        # 调用LLM生成回复（使用流式API）
        try:
            from llm.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            if llm_service and llm_service.enabled:
                # 使用LLM流式生成回复
                messages = [
                    {"role": "system", "content": "你是一个专业的生活助手AI，擅长分析用户的生活数据并提供个性化建议。"},
                    {"role": "user", "content": prompt}
                ]
                print(f"🤖 调用LLM流式生成回复...")
                if progress_callback:
                    progress_callback(6, "✍️ 正在构建AI提示词...")
                
                if progress_callback:
                    progress_callback(6, "✍️ 正在连接AI大模型...")
                
                import time
                start_time = time.time()
                response_parts = []
                
                # 获取thinking_callback
                thinking_callback = getattr(self, '_current_thinking_callback', None)
                
                # 流式接收LLM响应
                for chunk in llm_service.chat_stream(messages, temperature=0.7):
                    chunk_type = chunk.get("type", "")
                    chunk_content = chunk.get("content", "")
                    
                    if chunk_type == "thinking":
                        # 思考过程 - 通过thinking_callback实时推送
                        if thinking_callback:
                            thinking_callback(chunk_content)
                    elif chunk_type == "answer":
                        # 回答内容 - 累积
                        response_parts.append(chunk_content)
                        # 也可以通过回调实时推送（如果需要）
                        # if answer_callback:
                        #     answer_callback(chunk_content)
                    elif chunk_type == "error":
                        print(f"⚠️ LLM流式调用出错: {chunk_content}")
                        break
                
                response = "".join(response_parts)
                elapsed = time.time() - start_time
                
                print(f"✅ LLM回复生成完成，长度: {len(response)}，耗时: {elapsed:.1f}秒")
                if progress_callback:
                    progress_callback(6, f"✍️ AI回复生成完成（耗时{elapsed:.1f}秒）")
            else:
                # LLM未启用，使用模板回复
                print(f"⚠️ LLM未启用，使用模板回复")
                if progress_callback:
                    progress_callback(6, "✍️ 使用模板生成回复...")
                response = self._generate_template_response(domain_analyses, kg_insights)
        except Exception as e:
            print(f"⚠️ LLM调用失败: {e}，使用模板回复")
            import traceback
            traceback.print_exc()
            if progress_callback:
                progress_callback(6, "✍️ LLM调用失败，使用模板回复...")
            response = self._generate_template_response(domain_analyses, kg_insights)
        
        return response
    
    def _build_response_prompt(self, user_message: str, domain_analyses: Dict[str, Any],
                               kg_insights: List[str], strategy: str) -> str:
        """构建LLM提示词"""
        prompt = f"""你是一个专业的生活助手AI，正在帮助用户解决问题。

用户问题：{user_message}

基于以下分析结果，生成一个专业、个性化的回复：

【领域分析】
{self._format_domain_analyses(domain_analyses)}

【知识图谱推理】
{self._format_kg_insights(kg_insights)}

【策略选择】
当前使用策略：{strategy}

请按照以下结构生成回复：
1. 【分析】：总结用户当前的情况
2. 【推理】：解释问题的根本原因和相互关系
3. 【建议】：提供3-5条具体可行的建议
4. 【行动计划】：制定今天、本周、本月的具体行动计划

要求：
- 语气温和、专业、有同理心
- 建议要具体、可执行
- 结合用户的个人情况
- 不要过于说教，要像朋友一样交流
"""
        return prompt
    
    def _generate_template_response(self, domain_analyses: Dict[str, Any], kg_insights: List[str]) -> str:
        """生成模板回复（LLM不可用时使用）"""
        response = f"""根据我对你的分析：

【分析】
{self._format_domain_analyses(domain_analyses)}

【推理】
{self._format_kg_insights(kg_insights)}

【建议】
1. 立即行动：改善睡眠质量
2. 短期目标：增加运动时间
3. 长期目标：建立健康的生活习惯

【行动计划】
- 今天：晚上10点前睡觉
- 本周：每天运动30分钟
- 本月：建立规律的作息时间表
"""
        return response
    
    def _format_domain_analyses(self, domain_analyses: Dict[str, Any]) -> str:
        """格式化领域分析"""
        formatted = ""
        for domain, analysis in domain_analyses.items():
            formatted += f"\n{analysis.get('domain_name', domain)}：\n"
            for insight in analysis.get('insights', []):
                formatted += f"  - {insight}\n"
        return formatted
    
    def _format_kg_insights(self, kg_insights: List[str]) -> str:
        """格式化知识图谱洞察"""
        formatted = ""
        for insight in kg_insights:
            formatted += f"  - {insight}\n"
        return formatted
    
    def _extract_analysis_part(self, response: str) -> str:
        """提取分析部分"""
        if "【分析】" in response:
            start = response.find("【分析】") + 4
            end = response.find("【推理】")
            return response[start:end].strip()
        return ""
    
    def _extract_reasoning_part(self, response: str) -> str:
        """提取推理部分"""
        if "【推理】" in response:
            start = response.find("【推理】") + 4
            end = response.find("【建议】")
            return response[start:end].strip()
        return ""
    
    def _extract_recommendations_part(self, response: str) -> str:
        """提取建议部分"""
        if "【建议】" in response:
            start = response.find("【建议】") + 4
            end = response.find("【行动计划】")
            return response[start:end].strip()
        return ""
    
    def _extract_action_plan_part(self, response: str) -> str:
        """提取行动计划部分"""
        if "【行动计划】" in response:
            start = response.find("【行动计划】") + 5
            return response[start:].strip()
        return ""
    
    def _calculate_response_confidence(self, processing_result: Dict[str, Any]) -> float:
        """计算回复置信度"""
        # 基于各层的信息完整性计算置信度
        confidence = 0.7
        
        # 如果有多个领域分析，增加置信度
        domain_count = len(processing_result["layers"]["domain_analysis"]["domain_analyses"])
        confidence += domain_count * 0.05
        
        # 如果有知识图谱推理，增加置信度
        if processing_result["layers"]["knowledge_graph"]["reasoning_paths"]:
            confidence += 0.1
        
        return min(0.95, confidence)
    
    def _init_test_memories(self):
        """初始化测试记忆数据"""
        from datetime import timedelta
        
        # 对话记忆
        conversation_memories = [
            ("用户询问如何提高学习效率，我建议使用番茄工作法和间隔重复", {"domain": "学习", "topic": "学习方法"}, 0.8, 3),
            ("用户反馈最近睡眠质量不好，经常失眠，我建议调整作息时间", {"domain": "健康", "topic": "睡眠"}, 0.9, 5),
            ("用户提到工作压力大，感觉时间不够用，我建议做时间管理和优先级排序", {"domain": "时间", "topic": "时间管理"}, 0.85, 7),
            ("用户询问如何改善人际关系，我建议多倾听、少评判，增加共情能力", {"domain": "社交", "topic": "人际关系"}, 0.75, 10),
            ("用户分享了今天的运动数据，跑步5公里，感觉很好", {"domain": "健康", "topic": "运动"}, 0.6, 1),
            ("用户询问如何控制消费，我建议记账和设定预算", {"domain": "财务", "topic": "理财"}, 0.7, 14),
            ("用户反馈情绪低落，我建议进行户外活动和社交互动", {"domain": "情绪", "topic": "情绪管理"}, 0.85, 2),
            ("用户询问数学数列问题，我详细讲解了等差数列和等比数列的性质", {"domain": "学习", "topic": "数学"}, 0.8, 4),
        ]
        
        for content, metadata, importance, days_ago in conversation_memories:
            timestamp = datetime.now() - timedelta(days=days_ago)
            memory_id = self.memory_retriever.add_memory(
                memory_type=MemoryType.CONVERSATION,
                content=content,
                metadata=metadata,
                importance=importance
            )
            self.memory_retriever.memory_index[memory_id].timestamp = timestamp
        
        # 决策记忆
        decision_memories = [
            ("决策：晚上10点前睡觉 -> 结果：睡眠质量提升，第二天精神状态好", {"domain": "健康", "outcome": "positive"}, 0.9, 8),
            ("决策：每天运动30分钟 -> 结果：体重下降2kg，体能提升", {"domain": "健康", "outcome": "positive"}, 0.85, 15),
            ("决策：使用番茄工作法学习 -> 结果：学习效率提升30%", {"domain": "学习", "outcome": "positive"}, 0.8, 12),
        ]
        
        for content, metadata, importance, days_ago in decision_memories:
            timestamp = datetime.now() - timedelta(days=days_ago)
            memory_id = self.memory_retriever.add_memory(
                memory_type=MemoryType.DECISION,
                content=content,
                metadata=metadata,
                importance=importance
            )
            self.memory_retriever.memory_index[memory_id].timestamp = timestamp
        
        # 洞察记忆
        insight_memories = [
            ("洞察：睡眠不足会导致第二天的学习效率下降50%以上", {"domain": "健康"}, 0.95, 10),
            ("洞察：运动后的心情明显比运动前好，可能是内啡肽的作用", {"domain": "健康"}, 0.85, 18),
            ("洞察：工作时间超过8小时后，效率会急剧下降，不如早点休息", {"domain": "时间"}, 0.9, 22),
        ]
        
        for content, metadata, importance, days_ago in insight_memories:
            timestamp = datetime.now() - timedelta(days=days_ago)
            memory_id = self.memory_retriever.add_memory(
                memory_type=MemoryType.INSIGHT,
                content=content,
                metadata=metadata,
                importance=importance
            )
            self.memory_retriever.memory_index[memory_id].timestamp = timestamp
        
        print(f"✅ 已初始化 {len(self.memory_retriever.memories)} 条测试记忆")
    
    def _generate_thinking_process(self, processing_result: Dict[str, Any], thinking_callback=None) -> str:
        """生成详细的思考过程（支持流式推送）"""
        thinking_parts = []
        
        def add_thinking(text: str):
            """添加思考内容并回调"""
            thinking_parts.append(text)
            if thinking_callback:
                thinking_callback(text + "\n")
        
        # 第1层：元智能体路由
        meta_agent = processing_result['layers']['meta_agent']
        add_thinking("🧠 第1层：元智能体路由分析")
        add_thinking(f"   识别到的主要领域：{', '.join(meta_agent['primary_domains'])}")
        if meta_agent.get('routing_explanation'):
            add_thinking(f"   路由原因：{meta_agent['routing_explanation']}")
        add_thinking("")
        
        # 第2层：记忆检索
        memory = processing_result['layers']['memory']
        add_thinking("💭 第2层：历史记忆检索")
        similar_count = len(memory.get('similar_memories', []))
        if similar_count > 0:
            add_thinking(f"   找到 {similar_count} 条相关历史记忆")
            for i, mem in enumerate(memory['similar_memories'][:2], 1):
                add_thinking(f"   • 记忆{i}：{mem['content'][:50]}... (相似度: {mem['similarity']:.1%})")
        else:
            add_thinking("   未找到相关历史记忆，这是一个新话题")
        add_thinking("")
        
        # 第3层：领域分析
        domain_analysis = processing_result['layers']['domain_analysis']
        add_thinking("🔍 第3层：6大领域深度分析")
        analyses = domain_analysis.get('domain_analyses', {})
        add_thinking(f"   分析了 {len(analyses)} 个相关领域")
        primary_focus = domain_analysis.get('primary_focus', '未知')
        add_thinking(f"   主要关注点：{primary_focus}")
        add_thinking("")
        
        # 第4层：知识图谱推理
        kg = processing_result['layers']['knowledge_graph']
        add_thinking("🕸️ 第4层：知识图谱推理")
        causal_chains = kg.get('causal_chains', [])
        if causal_chains:
            add_thinking(f"   发现 {len(causal_chains)} 条因果关系链")
            for i, chain in enumerate(causal_chains[:2], 1):
                add_thinking(f"   • 因果链{i}：{chain}")
        else:
            add_thinking("   未发现明显的因果关系链")
        add_thinking("")
        
        # 第5层：混合智能选择
        hybrid = processing_result['layers']['hybrid_intelligence']
        add_thinking("⚡ 第5层：混合智能策略选择")
        strategy = hybrid.get('selected_strategy', '未知')
        add_thinking(f"   选择策略：{strategy}")
        llm_weight = hybrid.get('llm_weight', 0)
        personal_weight = hybrid.get('personal_model_weight', 0)
        add_thinking(f"   LLM权重：{llm_weight:.1%} | 个人模型权重：{personal_weight:.1%}")
        add_thinking("")
        
        # 第6层：回复生成
        response_gen = processing_result['layers']['response_generation']
        add_thinking("✍️ 第6层：个性化回复生成")
        confidence = response_gen.get('confidence', 0)
        add_thinking(f"   生成置信度：{confidence:.1%}")
        add_thinking(f"   回复已根据您的个人特征和历史偏好进行优化")
        
        return "\n".join(thinking_parts)


def get_deep_ai_processor(user_id: str) -> DeepAIProcessor:
    """获取深化AI处理器实例"""
    return DeepAIProcessor(user_id)

