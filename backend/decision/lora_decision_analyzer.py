"""
决策分析器
保留本地 Qwen3.5-9B + 用户 LoRA 能力，同时支持 API 推理模式。
默认通过 DECISION_INFERENCE_MODE 控制实际执行链路。
"""
import os
import sys
import json
import re
import asyncio
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.llm.llm_service import get_llm_service

LORA_BASE_DIR = os.path.abspath(
    os.environ.get("LORA_MODELS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'models', 'lora'))
)


class LoRADecisionAnalyzer:
    """决策推理适配器：可切换 LoRA 本地推理或 API 推理"""

    def __init__(self):
        self.inference_mode = os.getenv("DECISION_INFERENCE_MODE", "api").strip().lower()
        self.lora_manager = None
        self.lora_base_dir = LORA_BASE_DIR
        self.llm_service = get_llm_service()

    def get_inference_mode(self) -> str:
        return "lora" if self.inference_mode == "lora" else "api"

    def is_lora_inference(self) -> bool:
        return self.get_inference_mode() == "lora"

    def is_api_inference(self) -> bool:
        return self.get_inference_mode() == "api"

    def _ensure_lora_manager(self):
        if self.lora_manager is None:
            from backend.lora.lora_model_manager import lora_manager
            self.lora_manager = lora_manager
        return self.lora_manager

    def _ensure_llm_service(self):
        if self.llm_service is None:
            self.llm_service = get_llm_service()
        if not self.llm_service or not getattr(self.llm_service, "enabled", False):
            raise RuntimeError("API 推理服务未就绪")
        return self.llm_service

    def _chatml_prompt_to_messages(self, prompt: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        pattern = r"<\|im_start\|>(system|user|assistant)\n(.*?)(?=<\|im_start\|>|\Z)"
        for role, content in re.findall(pattern, prompt, re.DOTALL):
            cleaned = content.replace("<|im_end|>", "").replace("<think>", "").strip()
            if not cleaned or role == "assistant":
                continue
            messages.append({"role": role, "content": cleaned})
        if messages:
            return messages

        cleaned_prompt = (
            prompt.replace("<|im_start|>", "")
            .replace("<|im_end|>", "")
            .replace("<think>", "")
            .strip()
        )
        return [{"role": "user", "content": cleaned_prompt}] if cleaned_prompt else []

    def _call_api_with_prompt(
        self,
        prompt: str,
        temperature: float = 0.4,
        response_format: Optional[str] = None
    ) -> str:
        llm_service = self._ensure_llm_service()
        messages = self._chatml_prompt_to_messages(prompt)
        return llm_service.chat(messages, temperature=temperature, response_format=response_format)

    def _call_api_stream(
        self,
        prompt: str,
        temperature: float = 0.4
    ):
        """API流式调用（生成器）"""
        llm_service = self._ensure_llm_service()
        messages = self._chatml_prompt_to_messages(prompt)
        # 使用LLM服务的流式接口
        for chunk in llm_service.chat_stream(messages, temperature=temperature):
            if chunk.get("type") == "answer":
                yield chunk.get("content", "")
            elif chunk.get("type") == "thinking":
                # 思考过程也可以yield出去
                yield chunk.get("content", "")

    async def _stream_text_chunks(self, text: str, chunk_size: int = 96):
        if not text:
            return
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
            await asyncio.sleep(0)

    def get_user_lora_path(self, user_id: str) -> Optional[str]:
        if self.is_api_inference():
            status_file = os.path.join(self.lora_base_dir, user_id, "status.json")
            if not os.path.exists(status_file):
                return None
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    status = json.load(f)
                return status.get("lora_path") or status.get("model_path")
            except Exception:
                return None
        return self._ensure_lora_manager().get_user_lora_path(user_id)

    def has_lora_model(self, user_id: str) -> bool:
        if self.is_api_inference():
            return self.get_user_lora_path(user_id) is not None
        return self._ensure_lora_manager().has_lora_model(user_id)

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
        num_events: int = 3,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if self.is_api_inference():
            return await self.generate_timeline_with_api(
                user_id=user_id,
                question=question,
                option=option,
                profile=profile,
                num_events=num_events,
                collected_info=collected_info
            )
        if not self.has_lora_model(user_id):
            raise ValueError(f"用户 {user_id} 还没有训练 LoRA 模型")
        if self.is_user_training(user_id):
            raise RuntimeError(f"用户 {user_id} 的 LoRA 正在训练中，请稍后再试个性化决策模拟")

        # 查询知识图谱中的相关人物，注入 prompt
        kg_context = self._query_relevant_persons(user_id, question)

        # 从 RAG 记忆中检索与决策问题相关的生活细节
        life_context = self._retrieve_life_context(user_id, question)
        collected_context = self._format_collected_info(collected_info)
        behavioral_dna = self._get_behavioral_dna(user_id)

        prompt = self._build_timeline_prompt(question, option, profile, num_events,
                                             strict=False, kg_context=kg_context,
                                             life_context=life_context,
                                             collected_context=collected_context,
                                             behavioral_dna=behavioral_dna)
        response = await asyncio.to_thread(
            self._ensure_lora_manager().generate,
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
                                                       life_context=life_context,
                                                       collected_context=collected_context,
                                                       behavioral_dna=behavioral_dna)
            retry_response = await asyncio.to_thread(
                self._ensure_lora_manager().generate,
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

    async def generate_timeline_with_api(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 3,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        kg_context = self._query_relevant_persons(user_id, question)
        life_context = self._retrieve_life_context(user_id, question)
        collected_context = self._format_collected_info(collected_info)
        behavioral_dna = self._get_behavioral_dna(user_id)

        prompt = self._build_timeline_prompt(
            question,
            option,
            profile,
            num_events,
            strict=False,
            kg_context=kg_context,
            life_context=life_context,
            collected_context=collected_context,
            behavioral_dna=behavioral_dna
        )
        response = await asyncio.to_thread(self._call_api_with_prompt, prompt, 0.35, None)
        timeline = self._parse_timeline_json(response)

        if not timeline:
            retry_prompt = self._build_timeline_prompt(
                question,
                option,
                profile,
                num_events,
                strict=True,
                kg_context=kg_context,
                life_context=life_context,
                collected_context=collected_context,
                behavioral_dna=behavioral_dna
            )
            retry_response = await asyncio.to_thread(self._call_api_with_prompt, retry_prompt, 0.2, None)
            timeline = self._parse_timeline_json(retry_response)

        if not timeline:
            fallback_response = self._build_fallback_timeline(question, option, profile, num_events)
            timeline = self._parse_timeline_json(fallback_response)

        if not timeline:
            raise RuntimeError("API 时间线生成结果为空或无法解析")
        return timeline

    async def generate_personalized_recommendation(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> str:
        if self.is_api_inference():
            return await self.generate_personalized_recommendation_with_api(
                user_id=user_id,
                question=question,
                options=options,
                profile=profile,
                collected_info=collected_info
            )
        if not self.has_lora_model(user_id):
            raise ValueError(f"用户 {user_id} 还没有训练 LoRA 模型")
        if self.is_user_training(user_id):
            raise RuntimeError(f"用户 {user_id} 的 LoRA 正在训练中，请稍后再试个性化推荐生成")

        prompt = self._build_recommendation_prompt(question, options, profile, collected_info)
        response = await asyncio.to_thread(
            self._ensure_lora_manager().generate,
            user_id,
            prompt,
            140,
            0.35,
        )
        return self._clean_recommendation(response)

    async def generate_personalized_recommendation_with_api(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> str:
        prompt = self._build_recommendation_prompt(question, options, profile, collected_info)
        response = await asyncio.to_thread(
            self._call_api_with_prompt,
            prompt,
            0.45,
            "json_object"
        )
        return self._clean_recommendation(response)

    async def stream_timeline_generation(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 12,
        all_option_titles: List[str] = None,
        collected_info: Optional[Dict[str, Any]] = None
    ):
        if self.is_api_inference():
            # 使用真正的API流式调用
            async for chunk in self._stream_timeline_generation_with_api(
                user_id=user_id,
                question=question,
                option=option,
                profile=profile,
                num_events=num_events,
                all_option_titles=all_option_titles,
                collected_info=collected_info
            ):
                yield chunk
            return
        """分批流式生成时间线：每批 4 个节点，后续批次传入累积状态作为上下文"""
        kg_context = await asyncio.to_thread(self._query_relevant_persons, user_id, question)
        life_context = await asyncio.to_thread(self._retrieve_life_context, user_id, question)
        collected_context = self._format_collected_info(collected_info)
        behavioral_dna = self._get_behavioral_dna(user_id)

        batch_size = 2
        generated_so_far: List[Dict] = []

        for batch_idx in range(0, num_events, batch_size):
            batch_count = min(batch_size, num_events - batch_idx)
            start_month = batch_idx + 1

            # 计算当前各维度累积状态，传给 prompt
            cumulative_state: Optional[Dict[str, float]] = None
            if generated_so_far:
                acc: Dict[str, float] = {}
                for e in generated_so_far:
                    for k, v in e.get('impact', {}).items():
                        acc[k] = round(acc.get(k, 0.0) + v, 2)
                cumulative_state = acc

            prompt = self._build_timeline_prompt(
                question, option, profile, batch_count,
                strict=False, kg_context=kg_context,
                life_context=life_context,
                collected_context=collected_context,
                other_options=all_option_titles,
                generated_so_far=generated_so_far,
                start_month=start_month,
                cumulative_state=cumulative_state,
                behavioral_dna=behavioral_dna
            )

            batch_buffer = ""
            for chunk in self._ensure_lora_manager().generate_stream(user_id, prompt, 1200, 0.45):
                batch_buffer += chunk
                yield chunk
                await asyncio.sleep(0)

            # 解析本批次结果，加入上下文
            batch_events = self._parse_timeline_json(batch_buffer)

            # ── 空话过滤 + 局部重生成 ──────────────────────────────────────
            for i, ev in enumerate(batch_events):
                if not self._is_hollow_event(ev.get('event', '')):
                    continue
                # 针对这一个月单独重生成
                regen_prompt = self._build_timeline_prompt(
                    question, option, profile, 1,
                    strict=True, kg_context=kg_context,
                    life_context=life_context,
                    collected_context=collected_context,
                    other_options=all_option_titles,
                    generated_so_far=generated_so_far,
                    start_month=ev['month'],
                    cumulative_state=cumulative_state,
                    behavioral_dna=behavioral_dna
                )
                try:
                    regen_response = await asyncio.to_thread(
                        self._ensure_lora_manager().generate, user_id, regen_prompt, 300, 0.5
                    )
                    regen_events = self._parse_timeline_json(regen_response)
                    if regen_events and not self._is_hollow_event(regen_events[0].get('event', '')):
                        replacement = regen_events[0]
                        replacement['month'] = ev['month']
                        batch_events[i] = replacement
                        print(f"[空话重生成] 第{ev['month']}月已替换")
                except Exception as e:
                    print(f"[空话重生成] 第{ev['month']}月重生成失败: {e}")

            generated_so_far.extend(batch_events)

    async def stream_recommendation_generation(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any,
        collected_info: Optional[Dict[str, Any]] = None
    ):
        if self.is_api_inference():
            recommendation = await self.generate_personalized_recommendation_with_api(
                user_id=user_id,
                question=question,
                options=options,
                profile=profile,
                collected_info=collected_info
            )
            async for chunk in self._stream_text_chunks(recommendation):
                yield chunk
            return
        prompt = self._build_recommendation_prompt(question, options, profile, collected_info)
        for chunk in self._ensure_lora_manager().generate_stream(user_id, prompt, 300, 0.4):
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
        if self.is_api_inference():
            return await self.generate_branch_events_with_api(
                user_id=user_id,
                question=question,
                option=option,
                parent_event=parent_event,
                profile=profile
            )
        prompt = self._build_branch_prompt(question, option, parent_event, profile)
        response = await asyncio.to_thread(
            self._ensure_lora_manager().generate,
            user_id,
            prompt,
            350,
            0.42,
        )
        branches = self._parse_timeline_json(response)
        if not branches:
            return self._build_fallback_branch_events(parent_event)
        return branches[:2]

    async def generate_branch_events_with_api(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        parent_event: Dict[str, Any],
        profile: Any
    ) -> List[Dict[str, Any]]:
        prompt = self._build_branch_prompt(question, option, parent_event, profile)
        response = await asyncio.to_thread(self._call_api_with_prompt, prompt, 0.45, None)
        branches = self._parse_timeline_json(response)
        if not branches:
            return self._build_fallback_branch_events(parent_event)
        return branches[:2]

    async def generate_self_prediction(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self.is_api_inference():
            return await self.generate_self_prediction_with_api(
                user_id=user_id,
                question=question,
                option=option,
                profile=profile,
                collected_info=collected_info
            )
        """
        让 LoRA 预测"这个用户选了这条路之后，真正会以多强的意志去执行"。

        这是本地 LoRA 相对于云端大模型真正有差异的能力：
        LoRA 权重编码了用户从未说出的行为倾向（历史游戏决策模式），
        云端大模型只能根据检索到的显式文本猜测。

        返回：
          execution_confidence  0-1，执行意志强度
          dropout_risk_month    预测最可能动摇的月份（可为 None）
          personal_note         用户视角的自我评估（第一人称文字）
        """
        empty = {"execution_confidence": 0.7, "dropout_risk_month": None, "personal_note": ""}
        if not self.has_lora_model(user_id):
            return empty

        prompt = self._build_self_prediction_prompt(
            question,
            option,
            profile,
            collected_context=self._format_collected_info(collected_info),
            behavioral_dna=self._get_behavioral_dna(user_id)
        )
        try:
            response = await asyncio.to_thread(
                self._ensure_lora_manager().generate,
                user_id, prompt, 220, 0.38
            )
            return self._parse_self_prediction(response)
        except Exception as e:
            print(f"[自我预测推理] 失败: {e}")
            return empty

    async def generate_self_prediction_with_api(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        empty = {"execution_confidence": 0.7, "dropout_risk_month": None, "personal_note": ""}
        prompt = self._build_self_prediction_prompt(
            question,
            option,
            profile,
            collected_context=self._format_collected_info(collected_info),
            behavioral_dna=self._get_behavioral_dna(user_id)
        )
        try:
            response = await asyncio.to_thread(
                self._call_api_with_prompt,
                prompt,
                0.4,
                "json_object"
            )
            return self._parse_self_prediction(response)
        except Exception as e:
            print(f"[API自我预测推理] 失败: {e}")
            return empty

    def _build_self_prediction_prompt(
        self,
        question: str,
        option: Dict[str, str],
        profile: Any,
        collected_context: str = "",
        behavioral_dna: str = ""
    ) -> str:
        option_title = option.get('title', '')
        option_desc  = option.get('description', '')

        system_msg = (
            "你现在是做决策的用户本人，不是 AI 助手。\n"
            "用第一人称'我'，诚实地预测：如果我选了这条路，我真正会怎么走下去？\n"
            "不是'我应该'，而是'我实际上会'。要体现真实的犹豫和可能的动摇。\n"
            "只输出 JSON，不要有任何其他文字。"
        )
        prompt = f"<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n"
        prompt += f"我面临的决策：{question}\n"
        prompt += f"我选择的方向：{option_title}"
        if option_desc:
            prompt += f"（{option_desc[:60]}）"
        prompt += "\n"
        if profile:
            style = getattr(profile, 'decision_style', '')
            risk  = getattr(profile, 'risk_preference', '')
            if style or risk:
                prompt += f"我的决策特征：{style} {risk}\n"
        if collected_context:
            prompt += f"本次决策已确认的现实情况：\n{collected_context}\n"
        if behavioral_dna:
            prompt += f"{behavioral_dna}\n"
        prompt += (
            "\n请预测我选择这条路后的执行情况，输出 JSON：\n"
            '{"execution_score":75,"dropout_month":4,"note":"我第三四个月遇到压力可能会拖着不推进"}\n'
            "说明：execution_score 是我真实的执行意志（0-100），"
            "dropout_month 是我最可能动摇的月份（没有风险则填 null），"
            "note 是我自己的内心评估（第一人称，30字以内）\n"
            f"<|im_end|>\n<|im_start|>assistant\n"
        )
        return prompt

    def _parse_self_prediction(self, response: str) -> Dict[str, Any]:
        empty = {"execution_confidence": 0.7, "dropout_risk_month": None, "personal_note": ""}
        try:
            cleaned = re.sub(r'```json\s*', '', response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            m = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
            if not m:
                return empty
            data = json.loads(m.group(0))
            score = float(data.get('execution_score', 70))
            month = data.get('dropout_month')
            note  = str(data.get('note', ''))[:80]
            return {
                "execution_confidence": round(min(1.0, max(0.0, score / 100)), 2),
                "dropout_risk_month":   int(month) if month is not None else None,
                "personal_note":        note
            }
        except Exception:
            return empty

    def extract_incremental_events(self, response: str, emitted_months: List[int]) -> List[Dict[str, Any]]:
        """从流式输出中增量提取已完成的事件 JSON 对象"""
        events: List[Dict[str, Any]] = []
        try:
            cleaned = re.sub(r'```json\s*', '', response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            
            # 用括号匹配法找完整的 JSON 对象，而不是简单的 .*?
            depth = 0
            start = -1
            json_objects_found = 0
            for pos in range(len(cleaned)):
                ch = cleaned[pos]
                if ch == '{':
                    if depth == 0:
                        start = pos
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0 and start >= 0:
                        raw = cleaned[start:pos + 1]
                        start = -1
                        json_objects_found += 1
                        # 检查是否包含 month 字段
                        if '"month"' not in raw:
                            continue
                        
                        # 检查JSON是否完整（必须包含所有必需字段）
                        if '"event"' not in raw or '"impact"' not in raw or '"probability"' not in raw:
                            continue
                        
                        try:
                            item = json.loads(raw)
                        except Exception as parse_err:
                            # JSON不完整或格式错误，跳过
                            continue
                        
                        parsed = self._extract_events([item])
                        if not parsed:
                            continue
                        event = parsed[0]
                        if event['month'] in emitted_months:
                            continue
                        # 空话过滤：标记 hollow=True，调用方可选择重生成
                        if self._is_hollow_event(event.get('event', '')):
                            event['hollow'] = True
                        emitted_months.append(event['month'])
                        events.append(event)
            
            if json_objects_found > 0 and len(events) > 0:
                print(f"[增量解析] 找到 {json_objects_found} 个JSON对象，提取出 {len(events)} 个新事件")
        except Exception as e:
            print(f"[增量解析] 异常: {e}")
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
            info = self._ensure_lora_manager().get_model_info(user_id)
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
        """从知识图谱中查询人物，只注入最核心的家人/好友"""
        try:
            from backend.knowledge.neo4j_knowledge_graph import Neo4jKnowledgeGraph
            with Neo4jKnowledgeGraph(user_id) as kg:
                central_nodes = kg.get_central_nodes(limit=3)
                if not central_nodes:
                    return ""
                lines = []
                for node in central_nodes:
                    name = node.get('name', '')
                    if not name:
                        continue
                    rels = kg.get_entity_relationships(name)
                    rel_parts = []
                    for r in rels[:2]:
                        rel_type = r.get('type', '')
                        rel_target = r.get('target', '') or r.get('name', '')
                        if rel_type and rel_target:
                            rel_parts.append(f"{rel_type} {rel_target}")
                    rel_desc = "、".join(rel_parts) if rel_parts else "相关人物"
                    lines.append(f"- {name}（{rel_desc}）")
                if not lines:
                    return ""
                result = "\n".join(lines)
                result += "\n注意：只在这些人物与当前决策场景直接相关时才提及，不要强行塞进每个事件。"
                print(f"[知识图谱] 注入 {len(lines)} 个核心人物到决策 prompt")
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

    def _format_collected_info(self, collected_info: Optional[Dict[str, Any]]) -> str:
        """将信息收集阶段得到的结构化现实约束转成稳定的 prompt 上下文。"""
        if not collected_info:
            return ""

        lines: List[str] = []
        decision_context = collected_info.get("decision_context", {})
        user_constraints = collected_info.get("user_constraints", {})
        priorities = collected_info.get("priorities", {})
        concerns = collected_info.get("concerns", [])
        options_mentioned = collected_info.get("options_mentioned", [])

        if isinstance(decision_context, dict) and decision_context:
            lines.append("已确认的背景：")
            for key, value in decision_context.items():
                if value:
                    lines.append(f"- {key}: {value}")

        if isinstance(user_constraints, dict) and user_constraints:
            lines.append("必须遵守的现实约束：")
            for _, value in user_constraints.items():
                if value:
                    lines.append(f"- {value}")

        if isinstance(priorities, dict) and priorities:
            lines.append("用户最看重的因素：")
            for _, value in priorities.items():
                if value:
                    lines.append(f"- {value}")

        if isinstance(concerns, list) and concerns:
            lines.append("用户明确担心的问题：")
            for item in concerns[:6]:
                if item:
                    lines.append(f"- {item}")

        if isinstance(options_mentioned, list) and options_mentioned:
            lines.append("用户主动提到过的方向：")
            for item in options_mentioned[:6]:
                if item:
                    lines.append(f"- {item}")

        return "\n".join(lines)

    def _get_behavioral_dna(self, user_id: str) -> str:
        """
        从游戏对话记录中实时提取用户行为DNA，直接注入推理prompt。
        第1局起就能用，不需要等LoRA训练完成。
        """
        try:
            from backend.database.connection import db_connection
            from backend.database.models import ConversationHistory
            from sqlalchemy import and_
            from collections import Counter

            db = db_connection.get_session()
            rows = db.query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.session_id.like('game_%')
                )
            ).order_by(ConversationHistory.timestamp.asc()).all()
            db.close()

            if not rows:
                return ""

            # 构建对话对
            game_pairs = []
            for i in range(len(rows) - 1):
                if rows[i].role == 'user' and rows[i + 1].role == 'assistant':
                    game_pairs.append({
                        'user': rows[i].content or '',
                        'assistant': rows[i + 1].content or ''
                    })

            if not game_pairs:
                return ""

            RISK_SIGNALS    = ['冒险', '赌一把', '拼一下', '放手一搏', '大胆', '尝试', '挑战', '去闯']
            SAFE_SIGNALS    = ['稳妥', '保守', '安全', '稳定', '踏实', '谨慎', '保险', '不冒险', '求稳']
            PRIORITY_WORDS  = ['家人', '家庭', '父母', '孩子', '收入', '薪资', '健康', '身体',
                               '朋友', '感情', '事业', '自由', '时间', '稳定', '发展']
            PERSIST_SIGNALS = ['坚持', '继续', '再试试', '撑下去', '不放弃', '还有希望']
            RETREAT_SIGNALS = ['算了', '放弃', '不想了', '太累了', '不值得', '还是算了', '退出']

            risk_count = safe_count = persist_count = retreat_count = 0
            priority_kws = []
            sample_choices = []

            for pair in game_pairs:
                text = pair['user'] + pair['assistant']
                for kw in RISK_SIGNALS:
                    if kw in text: risk_count += 1
                for kw in SAFE_SIGNALS:
                    if kw in text: safe_count += 1
                for kw in PRIORITY_WORDS:
                    if kw in text: priority_kws.append(kw)
                for kw in PERSIST_SIGNALS:
                    if kw in text: persist_count += 1
                for kw in RETREAT_SIGNALS:
                    if kw in text: retreat_count += 1
                if len(pair['user']) > 15:
                    sample_choices.append(pair['user'][:100])

            total_risk = risk_count + safe_count
            risk_rate = risk_count / total_risk if total_risk > 0 else None
            total_persist = persist_count + retreat_count
            persist_rate = persist_count / total_persist if total_persist > 0 else None

            kw_counter = Counter(priority_kws)
            top_prios = [kw for kw, _ in kw_counter.most_common(3)]

            lines = [f"## 用户历史决策行为（从 {len(game_pairs)} 局游戏实测，非猜测）"]

            if risk_rate is not None:
                risk_label = (
                    "明显偏向冒险" if risk_rate > 0.65 else
                    "明显偏向保守" if risk_rate < 0.35 else
                    "风险中性、倾向稳健"
                )
                lines.append(f"- 风险偏好：{risk_label}（冒险信号占{risk_rate*100:.0f}%）")

            if persist_rate is not None:
                persist_label = (
                    "执行力强，遇阻不轻易放弃" if persist_rate > 0.65 else
                    "容易在遇到压力后动摇退出" if persist_rate < 0.35 else
                    "执行意志中等，压力大时有退出倾向"
                )
                lines.append(f"- 执行特征：{persist_label}（坚持信号占{persist_rate*100:.0f}%）")

            if top_prios:
                lines.append(f"- 最在意的事：{'、'.join(top_prios)}")

            if sample_choices:
                lines.append("- 过去面对类似情境时的真实选择：")
                for sc in sample_choices[-3:]:  # 最近3条
                    lines.append(f"  · {sc}")

            lines.append("（推演事件必须与以上行为特征保持一致，不要与用户一贯风格相矛盾）")

            result = "\n".join(lines)
            print(f"[行为DNA] 基于{len(game_pairs)}局游戏注入行为特征到决策prompt")
            return result

        except Exception as e:
            print(f"[行为DNA] 提取失败: {e}")
            return ""

    def _build_timeline_prompt(self, question: str, option: Dict[str, str], profile: Any,
                                num_events: int, strict: bool = False,
                                kg_context: str = "",
                                user_feedback: List[Dict[str, str]] = None,
                                life_context: str = "",
                                collected_context: str = "",
                                other_options: List[str] = None,
                                generated_so_far: List[Dict] = None,
                                start_month: int = 1,
                                cumulative_state: Dict[str, float] = None,
                                behavioral_dna: str = "") -> str:
        option_title = option['title']
        option_desc = option.get('description', '')
        end_month = start_month + num_events - 1
        is_continuation = bool(generated_so_far)

        # ── 系统消息：写作规则（明确好/坏示例）──────────────────────────────
        system_msg = (
            f"你是决策推演引擎。任务：推演用户选择「{option_title}」后"
            f"第{start_month}到第{end_month}个月真实会发生什么。\n\n"
            "## 基准约定（所有选项共用同一起点）\n"
            "- impact 值代表相对于用户当前状态的变化量，起点为 0\n"
            "- 不同选项的推演从同一个现实起点出发，不要假设用户之前走了其他路\n\n"
            "## 写作铁律（违反任何一条都是错误输出）\n"
            "① 每条事件必须以「你」开头，第二人称\n"
            "② 至少一半事件含具体数字（金额/天数/次数/排名/分数等）\n"
            "③ 事件之间必须有因果关系，后面的事件从前面事件的结果中生长\n"
            "④ 必须有正面也有负面事件，正负比例约 1:1，绝不全正或全负\n"
            "⑤ 如果缺少明确信息，宁可保守，不要编造 offer、薪资、录取、投资回报等关键事实\n"
            "⑥ 只输出 JSON 数组，不要有任何其他文字\n\n"
            "## 禁止写法（这类文字直接无效）\n"
            "✗ '逐渐适应新环境'  '能力稳步提升'  '社交关系有所改善'  '整体状态良好'\n\n"
            "## 合格写法示例\n"
            "✓ '你连续投了11天简历，终于有一家公司约你做技术面试，准备了三天'\n"
            "✓ '这个月水电房租3200块，加上还信用卡2000，账户只剩下620块'\n"
            "✓ '你妈打电话问你什么时候回家，你说等稳定了，她沉默了一会儿'\n"
            "✓ '周会上你的方案被否了，领导说思路太保守，你回家翻来覆去睡不着'"
        )

        prompt = f"<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n"

        # ── 决策背景 ──────────────────────────────────────────────────────────
        prompt += f"## 决策问题\n{question}\n\n"
        prompt += f"## 用户正在走的路\n**{option_title}**"
        if option_desc:
            prompt += f"\n{option_desc}"
        prompt += "\n\n"

        if collected_context:
            prompt += "## 本次决策已确认的现实信息（优先级高于常识猜测，必须遵守）\n"
            prompt += f"{collected_context}\n\n"

        if other_options:
            others = [o for o in other_options if o != option_title]
            if others:
                prompt += "## 用户没有选择的路（不要写这些方向的事件）\n"
                for o in others:
                    prompt += f"- {o}\n"
                prompt += "\n"

        # ── 用户个人背景（PKF/RAG/KG）────────────────────────────────────────
        if life_context:
            prompt += f"## 用户个人背景（务必让事件与这些细节挂钩）\n{life_context}\n\n"
        if kg_context:
            prompt += f"## 用户身边的人（只在与决策直接相关时才提及）\n{kg_context}\n\n"
        if behavioral_dna:
            prompt += f"{behavioral_dna}\n\n"
        if profile:
            style = getattr(profile, 'decision_style', '')
            risk = getattr(profile, 'risk_preference', '')
            priority = getattr(profile, 'life_priority', '')
            if style or risk or priority:
                prompt += f"## 用户性格特征\n决策风格:{style}  风险偏好:{risk}  生活优先级:{priority}\n\n"

        # ── 已推演事件（续写时提供上下文）────────────────────────────────────
        if is_continuation and generated_so_far:
            prompt += "## 前几个月已发生的事（在此基础上续写，不要重复）\n"
            # 最近3条完整保留，更早的压缩为20字摘要以节省token
            recent = generated_so_far[-3:]
            older = generated_so_far[:-3] if len(generated_so_far) > 3 else []
            for e in older:
                summary = e.get('event', '')[:20]
                prompt += f"- 第{e.get('month',0)}月：{summary}…\n"
            for e in recent:
                prompt += f"- 第{e.get('month',0)}月：{e.get('event','')}\n"
            prompt += "\n"

        # ── 累积状态（让后续事件体现状态压力）──────────────────────────────
        if cumulative_state:
            status_lines = []
            for dim, val in cumulative_state.items():
                if abs(val) >= 0.1:
                    direction = "↑提升" if val > 0 else "↓下降"
                    status_lines.append(f"{dim}{direction}{abs(val)*100:.0f}%")
            if status_lines:
                prompt += f"## 目前的生活状态（后续事件必须体现这些压力或红利）\n"
                prompt += "  ".join(status_lines) + "\n\n"

        # ── 用户反馈（纠错注入）──────────────────────────────────────────────
        if user_feedback:
            prompt += "## 用户的修正意见（必须遵从）\n"
            for fb in user_feedback:
                t = fb.get("type", "")
                ev = fb.get("event", "")
                cm = fb.get("comment", "")
                if t == "unlikely":
                    prompt += f"- 「{ev}」这件事不太可能发生，不要写类似的\n"
                elif t == "accurate":
                    prompt += f"- 「{ev}」这个方向是对的，继续深化\n"
                elif cm:
                    prompt += f"- 关于「{ev}」：{cm}\n"
            prompt += "\n"

        # ── 输出指令 ──────────────────────────────────────────────────────────
        prompt += (
            f"## 输出指令\n"
            f"请输出第{start_month}到第{end_month}月共{num_events}个事件。\n"
            f"所有事件必须围绕「{option_title}」这条路，不能写无关的日常流水账。\n\n"
            "## few-shot 示例（请严格模仿这个格式和具体程度）\n"
            '[{"month":1,"event":"你连续投了11天简历，终于拿到一家初创公司的技术面试，前一天晚上反复准备到凌晨两点","impact":{"健康":-0.1,"财务":-0.05,"社交":-0.05,"情绪":-0.1,"学习":0.2,"时间":-0.2},"probability":0.82},'
            '{"month":2,"event":"这个月房租水电3200加上还信用卡2000，账户只剩下480块，你开始认真想要不要接外包","impact":{"健康":-0.05,"财务":-0.25,"社交":0.0,"情绪":-0.2,"学习":0.0,"时间":-0.05},"probability":0.75}]\n\n'
            '输出格式（只返回这个JSON数组，不要有任何其他文字）：\n'
            '[{"month":N,"event":"你...具体发生了什么","impact":{"健康":0.0,"财务":0.0,"社交":0.0,"情绪":0.0,"学习":0.0,"时间":0.0},"probability":0.8}]\n'
            f"<|im_end|>\n<|im_start|>assistant\n<think>\n"
        )
        return prompt

    def _build_recommendation_prompt(
        self,
        question: str,
        options: List[Dict],
        profile: Any,
        collected_info: Optional[Dict[str, Any]] = None
    ) -> str:
        prompt = (
            "<|im_start|>system\n"
            "你是用户的决策顾问。根据推演结果给出真诚、实用的建议。\n"
            "不要说空话套话，要像一个有经验的朋友在给建议。\n"
            "如果某个选项的预测置信度较低，必须提醒用户先补充信息或先做低成本验证，再下结论。\n"
            "只输出 JSON。\n"
            "<|im_end|>\n"
        )
        prompt += f"<|im_start|>user\n我的决策问题：{question}\n\n"
        collected_context = self._format_collected_info(collected_info)
        if collected_context:
            prompt += f"已确认的现实约束与优先级：\n{collected_context}\n\n"
        prompt += "各选项的推演结果：\n"
        for opt in options:
            prompt += f"\n【{opt['title']}】得分 {opt.get('final_score', 0):.0f}/100，风险 {opt.get('risk_level', 0):.0%}\n"
            prompt += f"  关键事件：{opt.get('timeline_summary', '暂无')}\n"
            if opt.get('prediction_confidence') is not None:
                prompt += f"  预测置信度：{float(opt.get('prediction_confidence', 0)):.0%}\n"
            calibration_review_count = int(opt.get('calibration_review_count', 0) or 0)
            if calibration_review_count > 0:
                prompt += f"  历史回访样本：{calibration_review_count}次\n"
            calibration_note = (opt.get('calibration_note') or '').strip()
            if calibration_note:
                prompt += f"  历史校准提醒：{calibration_note[:80]}\n"
            if opt.get('execution_confidence') is not None:
                prompt += f"  执行意志预测：{float(opt.get('execution_confidence', 0)):.0%}\n"
            personal_note = (opt.get('personal_note') or '').strip()
            if personal_note:
                prompt += f"  用户自我预判：{personal_note[:60]}\n"
            risk_assessment = opt.get('risk_assessment') or {}
            if isinstance(risk_assessment, dict):
                overall_level = risk_assessment.get('overall_level')
                overall_risk = risk_assessment.get('overall_risk')
                if overall_level is not None and overall_risk is not None:
                    prompt += f"  风险引擎评估：{overall_level} ({float(overall_risk):.1f}/10)\n"
                top_dimensions = risk_assessment.get('top_dimensions') or []
                if top_dimensions:
                    prompt += f"  主要风险维度：{', '.join(top_dimensions[:3])}\n"
        prompt += (
            '\n请给出你的建议，JSON 格式：\n'
            '{"summary":"用大白话说你的核心建议（不超过30字）",'
            '"recommended_option":"你推荐的选项名",'
            '"reasons":["推荐理由1（要具体）","推荐理由2"],'
            '"risks":["最大的风险是什么","如何规避"],'
            '"actions":["第一步该做什么","第二步该做什么"],'
            '"confidence_note":"如果预测不够稳，请明确指出还缺什么信息"}'
            "\n<|im_end|>\n<|im_start|>assistant\n"
        )
        return prompt

    def _build_branch_prompt(self, question: str, option: Dict[str, str], parent_event: Dict[str, Any], profile: Any) -> str:
        parent_month = parent_event.get('month', 1)
        parent_text = parent_event.get('event', '')
        impact = parent_event.get('impact', {})

        # 找出父事件影响最大的维度，让分支围绕它展开
        most_negative = min(impact.items(), key=lambda x: x[1], default=('情绪', -0.3))
        most_positive = max(impact.items(), key=lambda x: x[1], default=('学习', 0.3))
        neg_dim, neg_val = most_negative
        pos_dim, pos_val = most_positive

        branch_month_a = parent_month + 1
        branch_month_b = parent_month + 1

        system_msg = (
            "你是决策分支推演引擎。根据一个关键事件，推演它最可能引发的两条分叉路。\n"
            "规则：\n"
            "① 每条事件必须以「你」开头\n"
            "② 必须包含具体细节（数字/人名/场景）\n"
            "③ 分支A是从该事件中找到转机，分支B是该事件的压力持续发酵\n"
            "④ 两条分支必须和父事件直接因果相关，不能写无关的事情\n"
            "⑤ 只输出JSON数组"
        )

        prompt = f"<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n"
        prompt += f"## 决策背景\n问题：{question}\n方向：{option.get('title', '')}\n\n"
        prompt += f"## 触发分叉的父事件（第{parent_month}月）\n{parent_text}\n\n"
        prompt += f"## 父事件造成的主要影响\n"
        if abs(neg_val) > 0.05:
            prompt += f"- {neg_dim}受到了较大冲击（{neg_val*100:+.0f}%）\n"
        if abs(pos_val) > 0.05:
            prompt += f"- {pos_dim}有一定收益（{pos_val*100:+.0f}%）\n"
        if profile:
            risk_pref = getattr(profile, 'risk_preference', '')
            if risk_pref:
                prompt += f"\n用户风险偏好：{risk_pref}\n"
        prompt += (
            f"\n## 输出要求\n"
            f"基于上面的父事件，输出2条第{branch_month_a}个月的分支事件：\n"
            f"- 分支A（probability>0.5）：因为父事件，{pos_dim}方面出现了转机，具体怎么发展\n"
            f"- 分支B（probability<0.5）：因为父事件，{neg_dim}方面的压力继续积累，具体发酵成什么\n\n"
            '输出格式（只返回JSON数组）：\n'
            f'[{{"month":{branch_month_a},"event":"你...（分支A）","impact":{{"健康":0.0,"财务":0.0,"社交":0.0,"情绪":0.0,"学习":0.0,"时间":0.0}},"probability":0.65}},'
            f'{{"month":{branch_month_b},"event":"你...（分支B）","impact":{{"健康":0.0,"财务":0.0,"社交":0.0,"情绪":0.0,"学习":0.0,"时间":0.0}},"probability":0.35}}]\n'
            f"<|im_end|>\n<|im_start|>assistant\n"
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
                            # 单维度 clamp：每个维度最多影响 ±0.4
                            # 确保value不为None
                            if value is None:
                                value = 0.0
                            impact[dim] = round(max(-0.4, min(0.4, float(value))), 2)
                        except Exception:
                            impact[dim] = 0.0
                else:
                    impact = {dim: 0.0 for dim in allowed_dims}
                # 多样性校正：若所有非零维度全正或全负，削减过度偏向的幅度
                nonzero_vals = [v for v in impact.values() if abs(v) > 0.01]
                if nonzero_vals:
                    all_positive = all(v > 0 for v in nonzero_vals)
                    all_negative = all(v < 0 for v in nonzero_vals)
                    if all_positive:
                        impact = {k: round(v * 0.65, 2) for k, v in impact.items()}
                    elif all_negative:
                        impact = {k: round(v * 0.65, 2) for k, v in impact.items()}
                try:
                    month = int(item['month'])
                except Exception:
                    continue
                try:
                    probability = float(item.get('probability', 0.8))
                    # 确保probability不为None
                    if probability is None:
                        probability = 0.8
                except Exception:
                    probability = 0.8
                probability = max(0.05, min(0.98, probability))
                
                # 最终验证：确保所有必需字段都不为None
                if month is None or probability is None or not impact:
                    print(f"[事件验证] 跳过无效事件: month={month}, probability={probability}, impact={impact}")
                    continue
                
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

    # 空话词库：模型输出这些短语等于什么都没说
    _HOLLOW_PHRASES = [
        '逐渐适应', '稳步提升', '整体状态良好', '有所改善', '有所提升', '逐步改善',
        '能力稳步', '关系有所', '状态良好', '生活逐渐', '工作逐渐', '持续进步',
        '努力适应', '慢慢适应', '开始适应', '继续努力', '继续坚持', '不断努力',
        '不断进步', '取得进展', '稳定发展', '保持稳定', '积极向上', '积极努力',
        '认真对待', '用心做事', '踏实工作', '全力以赴', '用心生活',
    ]

    def _is_hollow_event(self, text: str) -> bool:
        """检测事件是否为无实质内容的空话"""
        if not text:
            return True
        # 空话词库命中
        for phrase in self._HOLLOW_PHRASES:
            if phrase in text:
                return True
        # 没有任何数字且没有「你」开头 → 大概率是泛化表述
        import re as _re
        has_number = bool(_re.search(r'\d', text))
        starts_with_you = text.startswith('你')
        if not has_number and not starts_with_you and len(text) < 25:
            return True
        return False

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
        raw_impact = parent_event.get('impact', {})
        positive_impact = {k: round(float(v) * 0.6, 2) for k, v in raw_impact.items()} if isinstance(raw_impact, dict) else {'健康': 0.0, '财务': 0.1, '社交': 0.0, '情绪': 0.1, '学习': 0.1, '时间': -0.05}
        negative_impact = {k: round(-abs(float(v)) * 0.5, 2) for k, v in raw_impact.items()} if isinstance(raw_impact, dict) else {'健康': -0.1, '财务': -0.1, '社交': -0.05, '情绪': -0.1, '学习': 0.0, '时间': -0.1}

        # 从父事件中提取可用的具体线索，构建有内容的 fallback
        # 找出影响最大的正/负维度
        pos_dim = max(positive_impact, key=lambda k: positive_impact[k]) if positive_impact else '情绪'
        neg_dim = min(negative_impact, key=lambda k: negative_impact[k]) if negative_impact else '财务'
        dim_label_a = {'财务': '收入', '健康': '身体状态', '情绪': '心态', '学习': '技能', '社交': '人际', '时间': '精力'}.get(pos_dim, pos_dim)
        dim_label_b = {'财务': '经济压力', '健康': '健康状况', '情绪': '情绪状态', '学习': '进展', '社交': '人际关系', '时间': '时间分配'}.get(neg_dim, neg_dim)

        return [
            {
                'month': month + 1,
                'event': f"你从这件事中找到了突破口，{dim_label_a}开始朝好的方向转变，你感到这条路还有走下去的可能",
                'impact': positive_impact,
                'probability': 0.60
            },
            {
                'month': month + 1,
                'event': f"这件事带来的{dim_label_b}没有消退，反而在接下来的日子里持续影响你的状态和决策",
                'impact': negative_impact,
                'probability': 0.40
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

    async def _stream_timeline_generation_with_api(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 12,
        all_option_titles: List[str] = None,
        collected_info: Optional[Dict[str, Any]] = None
    ):
        """使用API进行真正的流式时间线生成"""
        # 构建上下文
        kg_context = await asyncio.to_thread(self._query_relevant_persons, user_id, question)
        life_context = await asyncio.to_thread(self._retrieve_life_context, user_id, question)
        collected_context = self._format_collected_info(collected_info)
        behavioral_dna = self._get_behavioral_dna(user_id)
        
        # 分批生成，每批4个月
        batch_size = 4
        generated_so_far: List[Dict] = []
        
        for batch_idx in range(0, num_events, batch_size):
            batch_count = min(batch_size, num_events - batch_idx)
            start_month = batch_idx + 1
            
            # 计算累积状态
            cumulative_state: Optional[Dict[str, float]] = None
            if generated_so_far:
                acc: Dict[str, float] = {}
                for e in generated_so_far:
                    for k, v in e.get('impact', {}).items():
                        acc[k] = round(acc.get(k, 0.0) + v, 2)
                cumulative_state = acc
            
            # 构建prompt
            prompt = self._build_timeline_prompt(
                question, option, profile, batch_count,
                strict=False, kg_context=kg_context,
                life_context=life_context,
                collected_context=collected_context,
                other_options=all_option_titles,
                generated_so_far=generated_so_far,
                start_month=start_month,
                cumulative_state=cumulative_state,
                behavioral_dna=behavioral_dna
            )
            
            # 使用真正的流式API调用
            batch_buffer = ""
            
            def stream_generator():
                return self._call_api_stream(prompt, temperature=0.45)
            
            # 在线程池中执行流式生成
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as pool:
                stream_iter = await loop.run_in_executor(pool, stream_generator)
                for chunk in stream_iter:
                    batch_buffer += chunk
                    yield chunk
                    await asyncio.sleep(0)
            
            # 解析本批次结果
            batch_events = self._parse_timeline_json(batch_buffer)
            
            # 空话过滤（如果需要）
            for i, ev in enumerate(batch_events):
                if not self._is_hollow_event(ev.get('event', '')):
                    continue
                # 重生成逻辑...
                
            generated_so_far.extend(batch_events)
