"""
对话式AI接口
让用户像聊天一样使用整个系统
支持流式输出思考过程和回复内容
默认融入知识图谱感知RAG架构
"""
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json


# ==================== 知识图谱感知RAG ====================

def get_kg_rag_context(user_id: str, query: str, max_nodes: int = 10) -> Dict[str, Any]:
    """
    获取知识图谱感知RAG上下文
    
    数据来源：
    1. 对话历史记忆（RAG向量检索）
    2. 知识图谱节点和关系（图检索）
    
    Returns:
        {
            "context_text": "可读上下文",
            "nodes": [...],
            "influence_summary": {...},
            "reasoning": "..."
        }
    """
    try:
        from backend.learning.knowledge_graph_rag import KnowledgeGraphAwareRAG, RetrievalMode
        
        kg_rag = KnowledgeGraphAwareRAG(user_id)
        context = kg_rag.retrieve(
            query=query,
            max_nodes=max_nodes,
            mode=RetrievalMode.HYBRID,
            include_reasoning=True
        )
        
        return {
            "context_text": context.to_prompt() if hasattr(context, 'to_prompt') else str(context),
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type,
                    "category": n.category,
                    "confidence": n.confidence,
                    "influence_score": n.influence_score
                }
                for n in context.nodes
            ],
            "influence_summary": context.influence_summary,
            "reasoning": context.reasoning_path,
            "relationships_count": len(context.relationships),
            "has_context": len(context.nodes) > 0
        }
    except Exception as e:
        print(f"⚠️ 获取知识图谱RAG上下文失败: {e}")
        return {
            "context_text": "",
            "nodes": [],
            "influence_summary": {},
            "reasoning": "",
            "relationships_count": 0,
            "has_context": False
        }


def build_rag_enhanced_prompt(user_id: str, message: str, system_instruction: str = "") -> str:
    """
    构建包含RAG上下文的增强Prompt
    
    RAG数据来源：
    1. 对话历史记忆（向量检索）
    2. 知识图谱（图检索）
    """
    # 获取RAG上下文
    rag_context = get_kg_rag_context(user_id, message)
    
    # 默认系统指令
    if not system_instruction:
        system_instruction = """你是一个智能生活助手，基于用户的个人知识图谱和对话历史提供帮助。
你的回答应该：
1. 结合用户知识图谱中的具体信息
2. 分析各因素对用户的影响
3. 给出有依据的建议
4. 如果信息不足，基于通用知识回答"""
    
    prompt_parts = [
        system_instruction,
        "",
        "=" * 50,
        "【用户个人数据 - RAG检索结果】",
        "=" * 50,
    ]
    
    # 添加知识图谱上下文
    if rag_context["has_context"]:
        prompt_parts.append("")
        prompt_parts.append("## 知识图谱上下文")
        
        # 影响力分析
        if rag_context["influence_summary"]:
            prompt_parts.append("### 因素影响力分析：")
            sorted_inf = sorted(rag_context["influence_summary"].items(), key=lambda x: x[1], reverse=True)
            for cat, score in sorted_inf[:5]:
                prompt_parts.append(f"- **{cat}**: {score:.1%}")
        
        # 节点列表
        if rag_context["nodes"]:
            prompt_parts.append("")
            prompt_parts.append(f"### 相关节点（共 {len(rag_context['nodes'])} 个）：")
            for node in rag_context["nodes"][:10]:
                prompt_parts.append(
                    f"- [{node['type']}] {node['name']} "
                    f"(影响: {node['influence_score']:.2f}, 置信度: {node['confidence']:.2f})"
                )
        
        # 推理路径
        if rag_context["reasoning"]:
            prompt_parts.append("")
            prompt_parts.append("### 推理路径：")
            prompt_parts.append(rag_context["reasoning"])
    else:
        prompt_parts.append("（当前没有相关的知识图谱数据，将基于通用知识回答）")
    
    prompt_parts.extend([
        "",
        "=" * 50,
        f"【用户当前问题】: {message}",
        "=" * 50,
    ])
    
    return "\n".join(prompt_parts)


class IntentType(Enum):
    """意图类型"""
    QUERY = "query"              # 查询："我为什么...？"
    ADVICE = "advice"            # 建议："我应该怎么...？"
    PREDICT = "predict"          # 预测："如果我...会怎样？"
    EXPLAIN = "explain"          # 解释："为什么你建议...？"
    STATUS = "status"            # 状态："我的健康状况如何？"
    FEEDBACK = "feedback"        # 反馈："这个建议很好"
    CASUAL = "casual"            # 闲聊："你好"


@dataclass
class ConversationContext:
    """对话上下文"""
    user_id: str
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_topic: Optional[str] = None
    last_intent: Optional[IntentType] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_start: datetime = field(default_factory=datetime.now)


class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self):
        # 意图关键词模式
        self.intent_patterns = {
            IntentType.QUERY: [
                r'为什么', r'怎么回事', r'原因', r'why', r'how come',
                r'什么导致', r'是因为'
            ],
            IntentType.ADVICE: [
                r'应该', r'怎么办', r'如何', r'怎样', r'建议',
                r'should', r'how to', r'what should', r'推荐'
            ],
            IntentType.PREDICT: [
                r'如果.*会', r'假如', r'要是', r'会不会', r'预测',
                r'if.*will', r'what if', r'未来'
            ],
            IntentType.EXPLAIN: [
                r'解释', r'说明', r'为什么.*建议', r'explain',
                r'tell me why', r'原理'
            ],
            IntentType.STATUS: [
                r'状况', r'情况', r'怎么样', r'如何', r'status',
                r'how am i', r'我的.*如何'
            ],
            IntentType.FEEDBACK: [
                r'很好', r'不错', r'有用', r'没用', r'不行',
                r'good', r'bad', r'helpful', r'采纳', r'拒绝'
            ],
            IntentType.CASUAL: [
                r'^你好', r'^hi', r'^hello', r'^嗨', r'谢谢',
                r'thank', r'再见', r'bye'
            ]
        }
    
    def recognize(self, user_message: str) -> IntentType:
        """识别用户意图"""
        message_lower = user_message.lower()
        
        # 按优先级匹配
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        # 默认为查询
        return IntentType.QUERY
    
    def extract_entities(self, user_message: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        # 提取数字
        numbers = re.findall(r'\d+\.?\d*', user_message)
        if numbers:
            entities['numbers'] = [float(n) for n in numbers]
        
        # 提取时间相关
        time_keywords = ['今天', '昨天', '明天', '最近', 'today', 'yesterday', 'recently']
        for keyword in time_keywords:
            if keyword in user_message.lower():
                entities['time_reference'] = keyword
                break
        
        # 提取健康相关
        health_keywords = {
            '睡眠': 'sleep',
            '运动': 'exercise',
            '压力': 'stress',
            '疲劳': 'fatigue',
            '健康': 'health'
        }
        for keyword, entity_type in health_keywords.items():
            if keyword in user_message:
                entities['health_aspect'] = entity_type
                break
        
        return entities


class ResponseGenerator:
    """响应生成器"""
    
    def __init__(self):
        self.response_templates = {
            IntentType.CASUAL: [
                "你好！我是你的健康助手，有什么可以帮你的吗？",
                "很高兴见到你！",
                "不客气，随时为你服务！"
            ]
        }
    
    def generate(
        self,
        intent: IntentType,
        system_result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成响应"""
        if intent == IntentType.QUERY:
            return self._generate_query_response(system_result, context)
        elif intent == IntentType.ADVICE:
            return self._generate_advice_response(system_result, context)
        elif intent == IntentType.PREDICT:
            return self._generate_predict_response(system_result, context)
        elif intent == IntentType.EXPLAIN:
            return self._generate_explain_response(system_result, context)
        elif intent == IntentType.STATUS:
            return self._generate_status_response(system_result, context)
        elif intent == IntentType.FEEDBACK:
            return self._generate_feedback_response(system_result, context)
        else:  # CASUAL
            return self.response_templates[IntentType.CASUAL][0]
    
    def _generate_query_response(
        self,
        result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成查询响应"""
        response = "根据分析，"
        
        # 从知识图谱获取答案
        if 'kg_answer' in result:
            kg_answer = result['kg_answer']
            if 'answer' in kg_answer:
                response += kg_answer['answer']
            elif 'causal_chain' in kg_answer:
                chains = kg_answer['causal_chain']
                if chains:
                    response += "可能的原因包括：\n"
                    for i, chain in enumerate(chains[:3], 1):
                        response += f"{i}. {chain.get('cause', '')} 导致 {chain.get('effect', '')}\n"
                else:
                    response += "暂时没有发现明确的因果关系。"
        else:
            response += "让我为你分析一下。"
        
        return response
    
    def _generate_advice_response(
        self,
        result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成建议响应"""
        response = "我的建议是：\n\n"
        
        if 'advice' in result and result['advice']:
            for i, advice in enumerate(result['advice'][:3], 1):
                priority = advice.get('priority', 'medium')
                message = advice.get('message', '')
                
                priority_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(priority, '⚪')
                
                response += f"{priority_emoji} {message}\n"
        else:
            response += "继续保持当前的健康习惯。"
        
        # 添加置信度
        if 'decision' in result:
            confidence = result['decision'].get('confidence', 0)
            if confidence > 0.8:
                response += f"\n（我对这个建议很有信心：{confidence:.0%}）"
        
        return response
    
    def _generate_predict_response(
        self,
        result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成预测响应"""
        response = "根据预测模型，"
        
        if 'predictions' in result:
            predictions = result['predictions']
            if isinstance(predictions, dict):
                response += "可能的结果是：\n"
                for key, value in list(predictions.items())[:3]:
                    response += f"• {key}: {value}\n"
        else:
            response += "需要更多数据才能做出准确预测。"
        
        return response
    
    def _generate_explain_response(
        self,
        result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成解释响应"""
        response = "让我解释一下：\n\n"
        
        # 解释决策过程
        if 'context' in result:
            ctx = result['context']
            response += f"1. 数据质量：{ctx.get('data_quality', 0):.0%}\n"
            response += f"2. 紧急程度：{ctx.get('urgency', 0):.0%}\n"
            response += f"3. 复杂度：{ctx.get('complexity', 0):.0%}\n\n"
        
        # 解释智能体协调
        if 'selected_agents' in result:
            agents = result['selected_agents']
            response += f"系统调用了 {len(agents)} 个智能体进行分析。\n"
        
        # 解释涌现模式
        if 'emergent_patterns' in result and result['emergent_patterns']:
            response += "\n发现的模式：\n"
            for pattern in result['emergent_patterns'][:2]:
                response += f"• {pattern.get('description', '')}\n"
        
        return response
    
    def _generate_status_response(
        self,
        result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成状态响应"""
        response = "你的当前状态：\n\n"
        
        if 'decision' in result and 'predictions' in result['decision']:
            predictions = result['decision']['predictions']
            
            for key, value in list(predictions.items())[:5]:
                if isinstance(value, (int, float)):
                    response += f"• {key}: {value:.1f}\n"
                else:
                    response += f"• {key}: {value}\n"
        
        # 添加总体评价
        if 'decision' in result:
            confidence = result['decision'].get('confidence', 0)
            if confidence > 0.8:
                response += "\n总体来说，状况良好！"
            elif confidence > 0.5:
                response += "\n总体来说，还不错。"
            else:
                response += "\n建议多关注一下健康状况。"
        
        return response
    
    def _generate_feedback_response(
        self,
        result: Dict[str, Any],
        context: ConversationContext
    ) -> str:
        """生成反馈响应"""
        return "感谢你的反馈！我会继续学习和改进。"


class ConversationalAI:
    """对话式AI系统"""
    
    def __init__(
        self,
        meta_agent,
        knowledge_graph,
        evolving_system,
        multimodal_fusion=None
    ):
        self.meta_agent = meta_agent
        self.knowledge_graph = knowledge_graph
        self.evolving_system = evolving_system
        self.multimodal_fusion = multimodal_fusion
        
        self.intent_recognizer = IntentRecognizer()
        self.response_generator = ResponseGenerator()
        
        # 对话上下文管理
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_or_create_context(self, user_id: str) -> ConversationContext:
        """获取或创建对话上下文"""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id=user_id)
        return self.contexts[user_id]
    
    async def chat(
        self,
        user_id: str,
        message: str,
        user_data: Optional[Dict[str, Any]] = None,
        use_rag: bool = True
    ) -> str:
        """
        对话接口 - 默认使用RAG增强
        
        Args:
            user_id: 用户ID
            message: 用户消息
            user_data: 可选的用户数据
            use_rag: 是否使用知识图谱感知RAG（默认True）
        
        Returns:
            系统响应
        """
        # 获取上下文
        context = self.get_or_create_context(user_id)
        
        # 记录对话历史
        context.conversation_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # 【核心】如果启用RAG，使用知识图谱感知RAG构建增强Prompt
        if use_rag:
            # 获取RAG上下文
            rag_context = get_kg_rag_context(user_id, message)
            
            # 构建增强的prompt
            enhanced_prompt = build_rag_enhanced_prompt(user_id, message)
            
            # 发送给LLM
            try:
                from backend.llm.llm_service import get_llm_service
                llm = get_llm_service()
                if llm:
                    response = llm.chat([
                        {"role": "system", "content": """你是一个智能生活助手，基于用户的个人知识图谱和对话历史提供帮助。
回答要求：
1. 结合用户知识图谱中的具体信息
2. 分析各因素对用户的影响
3. 给出有依据的建议
4. 如果信息不足，基于通用知识回答"""},
                        {"role": "user", "content": enhanced_prompt}
                    ], temperature=0.3)
                else:
                    response = self._generate_fallback_response(message, rag_context)
            except Exception as e:
                print(f"LLM调用失败，使用降级响应: {e}")
                response = self._generate_fallback_response(message, rag_context)
        else:
            # 不使用RAG的原始逻辑
            intent = self.intent_recognizer.recognize(message)
            context.last_intent = intent
            entities = self.intent_recognizer.extract_entities(message)
            
            if intent == IntentType.CASUAL:
                response = self.response_generator.generate(intent, {}, context)
            elif intent == IntentType.QUERY:
                kg_answer = self.knowledge_graph.query(message)
                result = {'kg_answer': kg_answer}
                response = self.response_generator.generate(intent, result, context)
            elif intent == IntentType.FEEDBACK:
                feedback_type = self._parse_feedback(message)
                self.evolving_system.receive_feedback(feedback_type)
                result = {}
                response = self.response_generator.generate(intent, result, context)
            else:
                if user_data is None:
                    user_data = self._extract_data_from_message(message, entities)
                result = await self.evolving_system.process_user_input(user_data)
                if intent == IntentType.QUERY:
                    kg_answer = self.knowledge_graph.query(message)
                    result['kg_answer'] = kg_answer
                response = self.response_generator.generate(intent, result, context)
        
        # 记录响应
        context.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def _generate_fallback_response(self, message: str, rag_context: Dict) -> str:
        """当LLM不可用时，生成基于RAG上下文的降级响应"""
        if rag_context.get("has_context"):
            lines = [f"基于你的个人知识图谱，我分析如下：", ""]
            
            if rag_context["influence_summary"]:
                sorted_inf = sorted(rag_context["influence_summary"].items(), key=lambda x: x[1], reverse=True)
                lines.append("**主要影响因素：**")
                for cat, score in sorted_inf[:3]:
                    lines.append(f"- {cat}: {score:.1%}")
                lines.append("")
            
            if rag_context["nodes"]:
                lines.append(f"**相关节点（{len(rag_context['nodes'])}个）：**")
                for node in rag_context["nodes"][:5]:
                    lines.append(f"- [{node['type']}] {node['name']}")
                lines.append("")
            
            lines.append(f"你的问题「{message}」需要结合上述信息进行分析。")
            lines.append("（当前AI服务不可用，请稍后再试）")
            
            return "\n".join(lines)
        else:
            return f"收到你的问题：{message}。当前没有相关知识图谱数据，请先在系统中补充相关信息。"
    
    async def chat_stream(
        self,
        user_id: str,
        message: str,
        user_data: Optional[Dict[str, Any]] = None,
        use_rag: bool = True
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        流式对话接口 - 默认使用知识图谱感知RAG + 智能导航
        
        Args:
            user_id: 用户ID
            message: 用户消息
            user_data: 可选的用户数据
            use_rag: 是否使用知识图谱感知RAG（默认True）
        
        Yields:
            包含 type 和 content 的字典
        """
        try:
            # 获取上下文
            context = self.get_or_create_context(user_id)
            
            # 记录用户消息
            context.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # 发送开始信号
            yield {
                'type': 'start',
                'content': f'开始处理: {message[:50]}...'
            }
            
            # 【智能导航】分析用户意图，检测是否需要导航
            try:
                from backend.ai_core.intent_router import intent_router
                intent_result = intent_router.analyze_intent(message)
                
                if intent_result["has_navigation_intent"]:
                    # 发送导航建议
                    navigation_prompt = intent_router.generate_navigation_prompt(intent_result)
                    if navigation_prompt:
                        yield {
                            'type': 'navigation',
                            'content': navigation_prompt,
                            'routes': intent_result["suggested_routes"],
                            'primary_route': intent_result["primary_route"]
                        }
            except Exception as e:
                print(f"意图识别失败: {e}")
            
            # 【核心】如果启用RAG，使用知识图谱感知RAG
            if use_rag:
                # 1. 获取RAG上下文
                yield {
                    'type': 'progress',
                    'content': '🔍 正在检索知识图谱和对话记忆...'
                }
                
                rag_context = get_kg_rag_context(user_id, message)
                
                if rag_context.get("has_context"):
                    # 有RAG上下文，发送分析结果
                    yield {
                        'type': 'thinking',
                        'content': f"📊 知识图谱分析完成\n" +
                                  f"   - 发现 {len(rag_context['nodes'])} 个相关节点\n" +
                                  f"   - {rag_context['relationships_count']} 条关系\n" +
                                  f"   - 主要因素: {', '.join(list(rag_context['influence_summary'].keys())[:3])}"
                    }
                else:
                    yield {
                        'type': 'thinking',
                        'content': "📊 知识图谱中没有找到直接相关的信息，将基于通用知识回答"
                    }
                
                # 2. 构建增强Prompt
                yield {
                    'type': 'progress',
                    'content': '🧠 构建增强上下文...'
                }
                
                # 3. 调用LLM
                yield {
                    'type': 'progress',
                    'content': '💬 正在生成回答...'
                }
                
                try:
                    from backend.llm.llm_service import get_llm_service
                    llm = get_llm_service()
                    
                    if llm:
                        # 构建消息
                        enhanced_prompt = build_rag_enhanced_prompt(user_id, message)
                        messages = [
                            {"role": "system", "content": """你是一个智能生活助手，基于用户的个人知识图谱和对话历史提供帮助。
回答要求：
1. 结合用户知识图谱中的具体信息
2. 分析各因素对用户的影响
3. 给出有依据的建议
4. 如果信息不足，基于通用知识回答"""},
                            {"role": "user", "content": enhanced_prompt}
                        ]
                        
                        # 流式调用（如果支持）
                        try:
                            response_generator = llm.chat_stream(messages, temperature=0.3)
                            response_content = ""
                            for chunk in response_generator:
                                response_content += chunk
                                yield {
                                    'type': 'answer_chunk',
                                    'content': chunk
                                }
                        except Exception:
                            # 不支持流式，一次性获取
                            response_content = llm.chat(messages, temperature=0.3)
                            # 模拟流式输出
                            for i, char in enumerate(response_content):
                                yield {
                                    'type': 'answer_chunk',
                                    'content': char
                                }
                                if (i + 1) % 20 == 0:
                                    yield {
                                        'type': 'progress',
                                        'content': f'已生成 {i + 1}/{len(response_content)} 字符'
                                    }
                    else:
                        # LLM不可用，使用降级响应
                        response_content = self._generate_fallback_response(message, rag_context)
                        for i, char in enumerate(response_content):
                            yield {
                                'type': 'answer_chunk',
                                'content': char
                            }
                except Exception as e:
                    print(f"LLM调用失败: {e}")
                    response_content = self._generate_fallback_response(message, rag_context)
                    for char in response_content:
                        yield {
                            'type': 'answer_chunk',
                            'content': char
                        }
            else:
                # 不使用RAG的原始逻辑
                intent = self.intent_recognizer.recognize(message)
                context.last_intent = intent
                entities = self.intent_recognizer.extract_entities(message)
                
                thinking_process = ""
                response_content = ""
                
                if intent == IntentType.CASUAL:
                    thinking_process = "这是一个闲聊消息，直接生成友好回复。"
                    yield {'type': 'thinking', 'content': thinking_process}
                    response_content = self.response_generator.generate(intent, {}, context)
                
                elif intent == IntentType.QUERY:
                    thinking_process = "用户在查询信息，查询知识图谱..."
                    yield {'type': 'thinking', 'content': thinking_process}
                    kg_answer = self.knowledge_graph.query(message)
                    result = {'kg_answer': kg_answer}
                    response_content = self.response_generator.generate(intent, result, context)
                
                elif intent == IntentType.FEEDBACK:
                    thinking_process = "用户在提供反馈，分析反馈类型..."
                    yield {'type': 'thinking', 'content': thinking_process}
                    feedback_type = self._parse_feedback(message)
                    self.evolving_system.receive_feedback(feedback_type)
                    response_content = self.response_generator.generate(intent, {}, context)
                
                else:
                    thinking_process = "分析用户数据，调用多个智能体进行处理..."
                    yield {'type': 'thinking', 'content': thinking_process}
                    if user_data is None:
                        user_data = self._extract_data_from_message(message, entities)
                    result = await self.evolving_system.process_user_input(user_data)
                    if intent == IntentType.QUERY:
                        kg_answer = self.knowledge_graph.query(message)
                        result['kg_answer'] = kg_answer
                    response_content = self.response_generator.generate(intent, result, context)
                
                # 流式输出
                for i, char in enumerate(response_content):
                    yield {
                        'type': 'answer_chunk',
                        'content': char
                    }
                    if (i + 1) % 10 == 0:
                        yield {
                            'type': 'progress',
                            'content': f'已生成 {i + 1}/{len(response_content)} 字符'
                        }
            
            # 记录完整响应
            context.conversation_history.append({
                'role': 'assistant',
                'content': response_content,
                'timestamp': datetime.now().isoformat()
            })
            
            # 发送完成信号
            yield {
                'type': 'done',
                'content': '对话完成'
            }
        
        except Exception as e:
            yield {
                'type': 'error',
                'content': str(e)
            }
    
    def _parse_feedback(self, message: str) -> str:
        """解析反馈类型"""
        positive_keywords = ['好', '不错', '有用', '采纳', 'good', 'helpful']
        negative_keywords = ['不好', '没用', '不行', '拒绝', 'bad', 'useless']
        
        message_lower = message.lower()
        
        for keyword in positive_keywords:
            if keyword in message_lower:
                return 'adopted'
        
        for keyword in negative_keywords:
            if keyword in message_lower:
                return 'rejected'
        
        return 'ignored'
    
    def _extract_data_from_message(
        self,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从消息中提取数据"""
        data = {}
        
        # 提取数字作为可能的健康指标
        if 'numbers' in entities:
            numbers = entities['numbers']
            if len(numbers) >= 1:
                # 猜测第一个数字可能是睡眠时间
                if numbers[0] < 12:
                    data['sleep_hours'] = numbers[0]
            if len(numbers) >= 2:
                # 第二个可能是运动时间
                data['exercise_minutes'] = numbers[1]
        
        # 根据健康方面设置默认值
        if 'health_aspect' in entities:
            aspect = entities['health_aspect']
            if aspect == 'sleep':
                data.setdefault('sleep_hours', 7)
            elif aspect == 'exercise':
                data.setdefault('exercise_minutes', 30)
            elif aspect == 'stress':
                data.setdefault('stress_level', 5)
        
        # 设置默认值
        data.setdefault('sleep_hours', 7)
        data.setdefault('exercise_minutes', 30)
        data.setdefault('stress_level', 5)
        
        return data
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """获取对话历史"""
        context = self.get_or_create_context(user_id)
        return context.conversation_history
    
    def clear_context(self, user_id: str):
        """清除对话上下文"""
        if user_id in self.contexts:
            del self.contexts[user_id]
