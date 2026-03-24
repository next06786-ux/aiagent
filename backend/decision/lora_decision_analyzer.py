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

LORA_BASE_DIR = os.environ.get("LORA_MODELS_DIR", "./models/lora")


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

        prompt = self._build_timeline_prompt(question, option, profile, num_events)
        response = await asyncio.to_thread(
            self.lora_manager.generate,
            user_id,
            prompt,
            600,
            0.7,
        )
        timeline = self._parse_timeline_json(response)
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
            400,
            0.7,
        )
        return self._clean_recommendation(response)

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
        try:
            info = self.lora_manager.get_model_info(user_id)
            status["is_loaded"] = info.get("is_loaded", False)
            status["model_version"] = info.get("model_version", 0)
            status["last_train_time"] = info.get("last_train_time")
            status["training_data_size"] = info.get("current_data_size", 0)
        except Exception:
            pass
        return status

    def _build_timeline_prompt(self, question: str, option: Dict[str, str], profile: Any, num_events: int) -> str:
        prompt = f"<|im_start|>system\n你是一个决策模拟引擎，必须输出纯JSON。<|im_end|>\n"
        prompt += f"<|im_start|>user\n决策问题：{question}\n"
        prompt += f"选择：{option['title']}\n"
        if option.get('description'):
            prompt += f"说明：{option['description']}\n"
        if profile:
            prompt += f"决策风格：{getattr(profile, 'decision_style', '未知')}\n"
            prompt += f"风险偏好：{getattr(profile, 'risk_preference', '未知')}\n"
            prompt += f"生活优先级：{getattr(profile, 'life_priority', '未知')}\n"
        prompt += (
            f"请模拟未来12个月内最关键的{num_events}个事件，只输出 JSON 数组。"
            f"每个元素格式为：{{\"month\":1,\"event\":\"...\",\"impact\":{{\"健康\":0.0,\"财务\":0.0,\"社交\":0.0,\"情绪\":0.0,\"学习\":0.0,\"时间\":0.0}},\"probability\":0.8}}"
            f"<|im_end|>\n<|im_start|>assistant\n"
        )
        return prompt

    def _build_recommendation_prompt(self, question: str, options: List[Dict], profile: Any) -> str:
        prompt = f"<|im_start|>system\n你是用户的个人决策顾问。<|im_end|>\n"
        prompt += f"<|im_start|>user\n我面临的决策：{question}\n\n"
        for opt in options:
            prompt += f"选项：{opt['title']}\n"
            prompt += f"综合得分：{opt.get('final_score', 0):.1f}/100\n"
            prompt += f"风险等级：{opt.get('risk_level', 0):.2f}\n"
            prompt += f"时间线摘要：{opt.get('timeline_summary', '')}\n\n"
        if profile:
            prompt += f"决策风格：{getattr(profile, 'decision_style', '未知')}\n"
            prompt += f"风险偏好：{getattr(profile, 'risk_preference', '未知')}\n"
            prompt += f"生活优先级：{getattr(profile, 'life_priority', '未知')}\n\n"
        prompt += "请给出个性化推荐，明确说明应该选哪个以及原因。<|im_end|>\n<|im_start|>assistant\n"
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
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'month' in item and 'event' in item:
                    events.append({
                        'month': int(item['month']),
                        'event': str(item['event']),
                        'impact': item.get('impact', {}),
                        'probability': float(item.get('probability', 0.8))
                    })
        events.sort(key=lambda x: x['month'])
        return events

    def _clean_recommendation(self, recommendation: str) -> str:
        recommendation = recommendation.strip()
        lines = recommendation.split('\n')
        unique_lines = []
        seen = set()
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                unique_lines.append(line)
                seen.add(line)
        return '\n'.join(unique_lines)
