"""
LoRA增强的决策分析器
使用本地 transformers + peft 在 Qwen3.5-9B 基座上挂载用户专属 LoRA，
用于决策模拟与个性化推荐。
"""
import os
import sys
import json
import re
import asyncio
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.lora.lora_model_manager import lora_manager

LORA_BASE_DIR = os.path.abspath(
    os.environ.get("LORA_MODELS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'models', 'lora'))
)


class LoRADecisionAnalyzer:
    """通过本地 Qwen3.5-9B + 用户 LoRA 进行个性化决策分析"""

    def __init__(self):
        self.lora_manager = lora_manager
        self.lora_base_dir = LORA_BASE_DIR

    def get_user_lora_path(self, user_id: str) -> Optional[str]:
        return self.lora_manager.get_user_lora_path(user_id)

    def has_lora_model(self, user_id: str) -> bool:
        return self.lora_manager.has_lora_model(user_id)

    def is_user_training(self, user_id: str) -> bool:
        status_file = os.path.join(self.lora_base_dir, user_id, "status.json")
        if not os.path.exists(status_file):
            return False
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
            return bool(status.get("is_training", False))
        except Exception:
            return False

    async def generate_timeline_with_lora(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 3
    ) -> List[Dict[str, Any]]:
        if not self.has_lora_model(user_id):
            raise ValueError(f"用户 {user_id} 还没有训练 LoRA 模型")
        if self.is_user_training(user_id):
            raise RuntimeError(f"用户 {user_id} 的 LoRA 正在训练中，请稍后再试个性化决策模拟")

        # 查询知识图谱中的相关人物，注入 prompt
        kg_context = self._query_relevant_persons(user_id, question)

        # 从 RAG 记忆中检索与决策问题相关的生活细节
        life_context = self._retrieve_life_context(user_id, question)

        prompt = self._build_timeline_prompt(question, option, profile, num_events,
                                             strict=False, kg_context=kg_context,
                                             life_context=life_context)
        response = await asyncio.to_thread(
            self.lora_manager.generate,
            user_id,
            prompt,
            320,
            0.25,
        )
        print(f"📝 LoRA原始响应长度: {len(response)}")
        print(f"📝 LoRA原始响应前500字符: {response[:500]}")
        timeline = self._parse_timeline_json(response)

        if not timeline:
            retry_prompt = self._build_timeline_prompt(question, option, profile, num_events,
                                                       strict=True, kg_context=kg_context,
                                                       life_context=life_context)
            retry_response = await asyncio.to_thread(
                self.lora_manager.generate,
                user_id,
                retry_prompt,
                320,
                0.1,
            )
            print(f"📝 LoRA重试响应长度: {len(retry_response)}")
            print(f"📝 LoRA重试响应前500字符: {retry_response[:500]}")
            timeline = self._parse_timeline_json(retry_response)

        if not timeline:
            fallback_response = self._build_fallback_timeline(question, option, profile, num_events)
            timeline = self._parse_timeline_json(fallback_response)

        if not timeline:
            raise RuntimeError("LoRA 时间线生成结果为空或无法解析")
        return timeline

    async def generate_personalized_recommendation(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any
    ) -> str:
        if not self.has_lora_model(user_id):
            raise ValueError(f"用户 {user_id} 还没有训练 LoRA 模型")
        if self.is_user_training(user_id):
            raise RuntimeError(f"用户 {user_id} 的 LoRA 正在训练中，请稍后再试个性化推荐生成")

        prompt = self._build_recommendation_prompt(question, options, profile)
        response = await asyncio.to_thread(
            self.lora_manager.generate,
            user_id,
            prompt,
            140,
            0.35,
        )
        return self._clean_recommendation(response)

    async def stream_timeline_generation(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 12
    ):
        """分批流式生成时间线：每批 4 个节点，共 3 批，后续批次带上前面的结果作为上下文"""
        # 在线程中执行可能阻塞的知识图谱查询
        kg_context = await asyncio.to_thread(self._query_relevant_persons, user_id, question)
        life_context = await asyncio.to_thread(self._retrieve_life_context, user_id, question)

        batch_size = 4
        generated_so_far: List[Dict] = []

        for batch_idx in range(0, num_events, batch_size):
            batch_count = min(batch_size, num_events - batch_idx)
            start_month = batch_idx + 1
            end_month = batch_idx + batch_count

            # 构建带上下文的 prompt
            context_prefix = ""
            if generated_so_far:
                context_prefix = "## 已推演的事件（在此基础上继续，不要重复类似内容）\n"
                for e in generated_so_far:
                    context_prefix += f"- 第{e.get('month',0)}月：{e.get('event','')}\n"
                context_prefix += (
                    f"\n请继续生成第{start_month}到第{end_month}月的事件。\n"
                    "要求：后续事件必须是前面事件的因果结果，不能重复前面的主题。\n"
                    "如果前面都是正面事件，这批要出现困难或转折。\n\n"
                )

            prompt = self._build_timeline_prompt(
                question, option, profile, batch_count,
                strict=False, kg_context=kg_context,
                life_context=life_context
            )
            # 在 prompt 的 user 部分插入上下文
            if context_prefix:
                prompt = prompt.replace(
                    f"请输出 {batch_count} 个按时间递进的关键事件",
                    context_prefix + f"请输出 {batch_count} 个按时间递进的关键事件"
                )

            batch_buffer = ""
            for chunk in self.lora_manager.generate_stream(user_id, prompt, 600, 0.45):
                batch_buffer += chunk
                yield chunk
                # 让出事件循环，防止长时间阻塞导致 WebSocket 超时断开
                await asyncio.sleep(0)

            # 解析本批次结果，加入上下文
            batch_events = self._parse_timeline_json(batch_buffer)
            generated_so_far.extend(batch_events)

    async def stream_recommendation_generation(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any
    ):
        prompt = self._build_recommendation_prompt(question, options, profile)
        for chunk in self.lora_manager.generate_stream(user_id, prompt, 300, 0.4):
            yield chunk
            await asyncio.sleep(0)

    async def generate_branch_events_with_lora(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        parent_event: Dict[str, Any],
        profile: Any
    ) -> List[Dict[str, Any]]:
        prompt = self._build_branch_prompt(question, option, parent_event, profile)
        response = await asyncio.to_thread(
            self.lora_manager.generate,
            user_id,
            prompt,
            120,
            0.25,
        )
        branches = self._parse_timeline_json(response)
        if not branches:
            return self._build_fallback_branch_events(parent_event)
        return branches[:2]

    def extract_incremental_events(self, response: str, emitted_months: List[int]) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        try:
            cleaned = re.sub(r'```json\s*', '', response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            for match in re.finditer(r'\{\s*"month"\s*:\s*\d+.*?\}', cleaned, re.DOTALL):
                raw = match.group(0)
                try:
                    item = json.loads(raw)
                except Exception:
                    continue
                parsed = self._extract_events([item])
                if not parsed:
                    continue
                event = parsed[0]
                if event['month'] in emitted_months:
                    continue
                emitted_months.append(event['month'])
                events.append(event)
        except Exception:
            pass
        return events

    def get_lora_status(self, user_id: str) -> Dict[str, Any]:
        lora_path = self.get_user_lora_path(user_id)
        status = {
            "has_lora": lora_path is not None,
            "lora_path": lora_path,
            "model_version": 0,
            "last_train_time": None,
            "training_data_size": 0,
            "is_loaded": False,
        }
        
        # 从训练状态文件读取版本和上次训练时间
        last_train_time = None
        try:
            status_file = os.path.join(self.lora_base_dir, user_id, "status.json")
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    train_status = json.load(f)
                status["model_version"] = train_status.get("model_version", 0)
                ltt = train_status.get("last_train_time")
                if ltt:
                    from datetime import datetime as dt
                    last_train_time = dt.fromisoformat(ltt)
                    status["last_train_time"] = ltt
        except Exception:
            pass
        
        try:
            info = self.lora_manager.get_model_info(user_id)
            status["is_loaded"] = info.get("is_loaded", False)
        except Exception:
            pass
        
        # 只统计上次训练之后的新对话对数（训练后重置计数）
        try:
            from backend.database.models import ConversationHistory, Database
            from backend.database.config import DatabaseConfig
            db = Database(DatabaseConfig.get_database_url())
            session = db.get_session()
            
            query = session.query(ConversationHistory.role, ConversationHistory.content).filter(
                ConversationHistory.user_id == user_id
            )
            if last_train_time:
                query = query.filter(ConversationHistory.timestamp > last_train_time)
            
            rows = query.order_by(ConversationHistory.timestamp.asc()).all()
            session.close()
            
            pair_count = 0
            i = 0
            while i < len(rows) - 1:
                if rows[i].role == 'user' and rows[i + 1].role == 'assistant':
                    content = rows[i + 1].content or ""
                    if rows[i].content and content.strip() and '无法回答' not in content:
                        pair_count += 1
                    i += 2
                else:
                    i += 1
            status["training_data_size"] = pair_count
        except Exception:
            status["training_data_size"] = 0
        
        return status

    def _query_relevant_persons(self, user_id: str, question: str) -> str:
        """从知识图谱中查询与决策问题相关的人物，返回可注入 prompt 的文本"""
        try:
            from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
            with Neo4jKnowledgeGraph(user_id) as kg:
                # 取中心度最高的前5个人物节点
                central_nodes = kg.get_central_nodes(limit=5)
                if not central_nodes:
                    return ""

                lines = []
                for node in central_nodes:
                    name = node.get('name', '')
                    if not name:
                        continue
                    rels = kg.get_entity_relationships(name)
                    # 取前3条关系描述
                    rel_parts = []
                    for r in rels[:3]:
                        rel_type   = r.get('type', '')
                        rel_target = r.get('target', '') or r.get('name', '')
                        if rel_type and rel_target:
                            rel_parts.append(f"{rel_type} {rel_target}")
                        elif rel_type:
                            rel_parts.append(rel_type)
                    rel_desc = "、".join(rel_parts) if rel_parts else "相关人物"
                    lines.append(f"- {name}（{rel_desc}）")

                if not lines:
                    return ""

                result = "\n".join(lines)
                print(f"[知识图谱] 注入 {len(lines)} 个相关人物到决策 prompt")
                return result
        except Exception as e:
            print(f"[知识图谱] 查询相关人物失败: {e}")
            return ""

    def _retrieve_life_context(self, user_id: str, question: str) -> str:
        """从 RAG 记忆系统中检索与决策问题相关的用户生活细节
        
        优先使用 PKF-DS 框架抽取的结构化个人事实（如果可用）
        同时覆盖两个数据来源：
        1. AI 核心对话（日常聊天中透露的生活信息）
        2. 决策信息收集对话（针对本次决策的详细背景）
        """
        # 优先使用 PKF-DS 注入的上下文
        pkf_ctx = getattr(self, '_pkf_context', '')
        if pkf_ctx:
            return pkf_ctx
        try:
            from backend.learning.unified_rag_system import MemorySystemManager
            rag = MemorySystemManager.get_system(user_id)
            results = rag.search(question, top_k=8)
            if not results:
                return ""

            lines = []
            for mem in results:
                content = ""
                if hasattr(mem, 'content'):
                    content = mem.content
                elif isinstance(mem, dict):
                    content = mem.get('content', '')
                if content and len(content) > 10:
                    lines.append(f"- {content[:150]}")

            # 额外从数据库检索最近的决策收集对话（session_id 以 collect_ 开头）
            try:
                from backend.database.connection import db_connection
                from backend.database.models import ConversationHistory
                from sqlalchemy import and_

                db = db_connection.get_session()
                recent_collect = db.query(ConversationHistory).filter(
                    and_(
                        ConversationHistory.user_id == user_id,
                        ConversationHistory.session_id.like('collect_%'),
                        ConversationHistory.role == 'user'
                    )
                ).order_by(ConversationHistory.timestamp.desc()).limit(10).all()
                db.close()

                for row in recent_collect:
                    if row.content and len(row.content) > 10:
                        lines.append(f"- [收集] {row.content[:150]}")
            except Exception:
                pass

            # 额外检索游戏数据对话（session_id 以 game_ 开头）
            try:
                db = db_connection.get_session()
                game_data = db.query(ConversationHistory).filter(
                    and_(
                        ConversationHistory.user_id == user_id,
                        ConversationHistory.session_id.like('game_%')
                    )
                ).order_by(ConversationHistory.timestamp.desc()).limit(5).all()
                db.close()

                for row in game_data:
                    if row.content and len(row.content) > 10:
                        lines.append(f"- [游戏] {row.content[:150]}")
            except Exception:
                pass

            if not lines:
                return ""

            result = "\n".join(lines[:10])
            print(f"[生活细节] 注入 {len(lines)} 条（RAG+收集+游戏）到决策 prompt")
            return result
        except Exception as e:
            print(f"[生活细节] 检索失败: {e}")
            return ""

    def _build_timeline_prompt(self, question: str, option: Dict[str, str], profile: Any,
                                num_events: int, strict: bool = False,
                                kg_context: str = "",
                                user_feedback: List[Dict[str, str]] = None,
                                life_context: str = "") -> str:
        system_msg = (
            "你是一个决策推演引擎。你的任务是为用户模拟选择某个方向后，未来几个月会发生的具体事件。\n"
            "核心原则：\n"
            "1. 每个事件必须是具体的、可感知的场景，不能是空洞的总结或书面语废话\n"
            "2. 好的事件示例：'面试了3家公司，拿到1个offer但薪资比预期低20%'\n"
            "3. 坏的事件示例：'开始积极探索职业发展方向'（太空洞）\n"
            "4. 事件要有因果递进关系，后面的事件是前面事件的自然结果\n"
            "5. 必须包含正面和负面事件，不能全是好事或全是坏事\n"
            "6. 只输出 JSON 数组，不要任何解释"
        )
        prompt = f"<|im_start|>system\n{system_msg}<|im_end|>\n"
        prompt += f"<|im_start|>user\n"
        prompt += f"## 用户的决策问题\n{question}\n\n"
        prompt += f"## 用户选择的方向\n{option['title']}"
        if option.get('description'):
            prompt += f" — {option['description']}"
        prompt += "\n\n"

        # 注入用户真实背景
        if life_context:
            prompt += f"## 用户的真实情况（必须在事件中引用这些具体信息）\n{life_context}\n\n"
        if kg_context:
            prompt += f"## 用户身边的人（事件中可以提到这些人的反应和影响）\n{kg_context}\n\n"
        if profile:
            style = getattr(profile, 'decision_style', '')
            risk = getattr(profile, 'risk_preference', '')
            priority = getattr(profile, 'life_priority', '')
            if style or risk or priority:
                prompt += f"## 用户特征\n决策风格: {style}，风险偏好: {risk}，生活优先级: {priority}\n\n"

        if user_feedback:
            prompt += "## 用户对之前推演的反馈\n"
            for fb in user_feedback:
                event_text = fb.get("event", "")
                feedback_type = fb.get("type", "")
                comment = fb.get("comment", "")
                if feedback_type == "unlikely":
                    prompt += f"- 用户认为'{event_text}'不太可能发生，请调整\n"
                elif feedback_type == "accurate":
                    prompt += f"- 用户认为'{event_text}'很准确\n"
                elif comment:
                    prompt += f"- 关于'{event_text}'，用户说：{comment}\n"
            prompt += "\n"

        prompt += (
            f"## 输出要求\n"
            f"生成 {num_events} 个事件，模拟选择「{option['title']}」后未来 {num_events} 个月的真实经历。\n"
            "每个事件要求：\n"
            "- event: 用第二人称'你'描述，像在讲故事，要有具体的数字、人名、地点、行动\n"
            "- 不同月份的事件要有明显的递进和变化，不能重复类似的内容\n"
            "- 前3个月侧重行动和初期反馈，中间侧重遇到的困难和调整，后期侧重结果和转折\n"
            "- impact 的值要有区分度，不能全是 0.1/-0.1 这种小幅波动\n"
            "- probability 要根据事件的现实可能性合理设置，不能全是 0.7-0.8\n\n"
            "输出格式（只输出 JSON 数组）：\n"
            '[{"month":1,"event":"你开始...","impact":{"健康":-0.1,"财务":0.2,"社交":0.0,"情绪":0.1,"学习":0.3,"时间":-0.3},"probability":0.85}]\n'
            f"<|im_end|>\n<|im_start|>assistant\n"
        )
        return prompt

    def _build_recommendation_prompt(self, question: str, options: List[Dict], profile: Any) -> str:
        prompt = (
            "<|im_start|>system\n"
            "你是用户的决策顾问。根据推演结果给出真诚、实用的建议。\n"
            "不要说空话套话，要像一个有经验的朋友在给建议。只输出 JSON。\n"
            "<|im_end|>\n"
        )
        prompt += f"<|im_start|>user\n我的决策问题：{question}\n\n"
        prompt += "各选项的推演结果：\n"
        for opt in options:
            prompt += f"\n【{opt['title']}】得分 {opt.get('final_score', 0):.0f}/100，风险 {opt.get('risk_level', 0):.0%}\n"
            prompt += f"  关键事件：{opt.get('timeline_summary', '暂无')}\n"
        prompt += (
            '\n请给出你的建议，JSON 格式：\n'
            '{"summary":"用大白话说你的核心建议（不超过30字）",'
            '"recommended_option":"你推荐的选项名",'
            '"reasons":["推荐理由1（要具体）","推荐理由2"],'
            '"risks":["最大的风险是什么","如何规避"],'
            '"actions":["第一步该做什么","第二步该做什么"]}'
            "\n<|im_end|>\n<|im_start|>assistant\n"
        )
        return prompt

    def _build_branch_prompt(self, question: str, option: Dict[str, str], parent_event: Dict[str, Any], profile: Any) -> str:
        prompt = "<|im_start|>system\n你是未来决策推演引擎。请围绕给定父事件，生成2个分支事件。只输出 JSON 数组。<|im_end|>\n"
        prompt += f"<|im_start|>user\n决策问题：{question}\n"
        prompt += f"决策选项：{option.get('title', '当前选项')}\n"
        prompt += f"父事件：第{parent_event.get('month', 1)}月，{parent_event.get('event', '')}\n"
        if profile:
            prompt += f"用户决策风格：{getattr(profile, 'decision_style', '未知')}\n"
            prompt += f"用户风险偏好：{getattr(profile, 'risk_preference', '未知')}\n"
        prompt += (
            "请输出2个分支事件：1个偏乐观，1个偏风险。\n"
            "输出格式：[{\"month\":2,\"event\":\"事件\",\"impact\":{\"健康\":0.0,\"财务\":0.0,\"社交\":0.0,\"情绪\":0.0,\"学习\":0.0,\"时间\":0.0},\"probability\":0.6}]"
            "<|im_end|>\n<|im_start|>assistant\n"
        )
        return prompt

    def _parse_timeline_json(self, response: str) -> List[Dict[str, Any]]:
        timeline = []
        try:
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            m1 = re.search(r'\{\s*"timeline"\s*:\s*\[(.*?)\]\s*\}', response, re.DOTALL)
            if m1:
                try:
                    data = json.loads(m1.group(0))
                    timeline = self._extract_events(data['timeline'])
                    if timeline:
                        return timeline
                except Exception:
                    pass
            m2 = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
            if m2:
                try:
                    data = json.loads(m2.group(0))
                    timeline = self._extract_events(data)
                    if timeline:
                        return timeline
                except Exception:
                    pass
            try:
                data = json.loads(response.strip())
                if isinstance(data, list):
                    timeline = self._extract_events(data)
                elif isinstance(data, dict) and 'timeline' in data:
                    timeline = self._extract_events(data['timeline'])
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️ 解析时间线 JSON 失败: {e}")
        return timeline

    def _extract_events(self, data) -> List[Dict[str, Any]]:
        events = []
        allowed_dims = ['健康', '财务', '社交', '情绪', '学习', '时间']
        if isinstance(data, list):
            for item in data:
                if not (isinstance(item, dict) and 'month' in item and 'event' in item):
                    continue
                raw_event = str(item['event']).strip()
                if not self._is_valid_event_text(raw_event):
                    continue
                raw_impact = item.get('impact', {})
                impact: Dict[str, float] = {}
                if isinstance(raw_impact, dict):
                    for dim in allowed_dims:
                        value = raw_impact.get(dim, 0.0)
                        try:
                            impact[dim] = round(float(value), 2)
                        except Exception:
                            impact[dim] = 0.0
                else:
                    impact = {dim: 0.0 for dim in allowed_dims}
                try:
                    month = int(item['month'])
                except Exception:
                    continue
                try:
                    probability = float(item.get('probability', 0.8))
                except Exception:
                    probability = 0.8
                probability = max(0.05, min(0.98, probability))
                events.append({
                    'month': month,
                    'event': raw_event,
                    'impact': impact,
                    'probability': probability
                })
        events.sort(key=lambda x: x['month'])
        return events

    def _parse_timeline_text(self, response: str) -> List[Dict[str, Any]]:
        return []

    def _is_valid_event_text(self, text: str) -> bool:
        if not text or len(text) < 6:
            return False
        lowered = text.lower()
        invalid_markers = [
            'assistant', 'user', 'json', 'timeline', '```', '<|im_start|>', '<|im_end|>',
            'month', 'probability', 'impact', 'event_id', 'parent_event_id'
        ]
        if any(marker in lowered for marker in invalid_markers):
            return False
        if text.startswith('{') or text.startswith('['):
            return False
        if '_' in text and len(text.split()) <= 2:
            return False
        return True

    def _build_fallback_timeline(self, question: str, option: Dict[str, str], profile: Any, num_events: int) -> str:
        option_title = option.get('title', '当前选项')
        texts = [
            f"开始围绕{option_title}投入时间与精力，初步验证这条路是否适合自己",
            f"在推进{option_title}的过程中接触到更真实的反馈，优劣势逐渐变清楚",
            f"执行成本和现实压力开始显现，需要重新分配时间与注意力",
            f"出现一次关键调整机会，决定这条路径是继续加码还是及时修正",
            f"这一选择对后续节奏和资源安排产生更稳定的长期影响",
            f"经过一段时间积累后，{option_title}带来的阶段性结果开始落地",
            f"用户会基于阶段结果重新评估是否继续深耕这条路径"
        ]
        impacts = [
            {'健康': -0.05, '财务': 0.05, '社交': 0.0, '情绪': 0.1, '学习': 0.25, '时间': -0.15},
            {'健康': -0.05, '财务': 0.1, '社交': 0.05, '情绪': 0.05, '学习': 0.2, '时间': -0.1},
            {'健康': -0.1, '财务': -0.05, '社交': -0.05, '情绪': -0.1, '学习': 0.1, '时间': -0.2},
            {'健康': 0.0, '财务': 0.1, '社交': 0.0, '情绪': 0.1, '学习': 0.15, '时间': -0.05},
            {'健康': 0.05, '财务': 0.15, '社交': 0.05, '情绪': 0.1, '学习': 0.1, '时间': -0.05},
            {'健康': 0.0, '财务': 0.2, '社交': 0.05, '情绪': 0.15, '学习': 0.1, '时间': -0.05},
            {'健康': 0.05, '财务': 0.1, '社交': 0.0, '情绪': 0.05, '学习': 0.05, '时间': 0.0}
        ]
        events = []
        for idx in range(min(num_events, len(texts))):
            events.append({
                'month': idx + 1,
                'event': texts[idx],
                'impact': impacts[idx],
                'probability': round(max(0.55, 0.9 - idx * 0.05), 2)
            })
        return json.dumps(events, ensure_ascii=False)

    def _build_fallback_branch_events(self, parent_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        month = int(parent_event.get('month', 1))
        event_text = parent_event.get('event', '该事件')
        positive_impact = {k: round(float(v) * 0.6, 2) for k, v in parent_event.get('impact', {}).items()} if isinstance(parent_event.get('impact', {}), dict) else {'健康': 0.0, '财务': 0.1, '社交': 0.0, '情绪': 0.1, '学习': 0.1, '时间': -0.05}
        negative_impact = {k: round(-abs(float(v)) * 0.5, 2) for k, v in parent_event.get('impact', {}).items()} if isinstance(parent_event.get('impact', {}), dict) else {'健康': -0.1, '财务': -0.1, '社交': -0.05, '情绪': -0.1, '学习': 0.0, '时间': -0.1}
        return [
            {
                'month': month + 1,
                'event': f"{event_text}推进顺利，出现额外机会",
                'impact': positive_impact,
                'probability': 0.62
            },
            {
                'month': month + 2,
                'event': f"{event_text}推进过程中遇到阻力，需要重新调整",
                'impact': negative_impact,
                'probability': 0.38
            }
        ]

    def _clean_recommendation(self, recommendation: str) -> str:
        recommendation = recommendation.strip()
        recommendation = re.sub(r'```json\s*', '', recommendation)
        recommendation = re.sub(r'```\s*', '', recommendation)
        try:
            parsed = json.loads(recommendation)
            if isinstance(parsed, dict):
                return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass
        lines = recommendation.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                unique_lines.append(line)
                seen.add(line)
        return '\n'.join(unique_lines)
