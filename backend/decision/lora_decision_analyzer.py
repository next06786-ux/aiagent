"""
LoRA增强的决策分析器
通过 SGLang 服务器使用 Qwen3.5-9B 基座 + 用户专属 LoRA 进行个性化决策分析

架构：
  前端 → 后端 API → LoRADecisionAnalyzer → SGLang Server (基座 + LoRA)
  
SGLang 启动时带 --enable-lora，推理时通过 model 字段指定 LoRA adapter 路径，
SGLang 会自动在基座模型上叠加该用户的 LoRA adapter。
"""
import os
import sys
import json
import re
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.llm.sglang_client import get_sglang_client, SGLangClient


# LoRA 模型存储路径（与 gpu_server/gpu_config.py 中 PATHS['models_lora'] 一致）
LORA_BASE_DIR = os.environ.get("LORA_MODELS_DIR", "./models/lora")


class LoRADecisionAnalyzer:
    """通过 SGLang + LoRA 进行个性化决策分析"""

    def __init__(self):
        self.sglang: SGLangClient = get_sglang_client()
        self.lora_base_dir = LORA_BASE_DIR

    # ==================== LoRA 路径管理 ====================

    def get_user_lora_path(self, user_id: str) -> Optional[str]:
        """获取用户最新的 LoRA adapter 路径"""
        lora_dir = os.path.join(self.lora_base_dir, user_id)
        if not os.path.exists(lora_dir):
            return None

        versions = [
            d for d in os.listdir(lora_dir)
            if d.startswith('v') and os.path.isdir(os.path.join(lora_dir, d))
        ]
        if not versions:
            return None

        latest = sorted(versions, key=lambda x: int(x[1:]))[-1]
        lora_path = os.path.join(lora_dir, latest, "final")
        return lora_path if os.path.exists(lora_path) else None

    def has_lora_model(self, user_id: str) -> bool:
        """检查用户是否有训练好的 LoRA 模型"""
        return self.get_user_lora_path(user_id) is not None

    def is_user_training(self, user_id: str) -> bool:
        """检查用户是否正在训练 LoRA，训练期间拒绝高成本个性化推理以避免 GPU 争抢"""
        status_file = os.path.join(self.lora_base_dir, user_id, "status.json")
        if not os.path.exists(status_file):
            return False
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
            return bool(status.get("is_training", False))
        except Exception:
            return False

    # ==================== 时间线生成 ====================

    async def generate_timeline_with_lora(
        self,
        user_id: str,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int = 3
    ) -> List[Dict[str, Any]]:
        """
        通过 SGLang (基座 + 用户 LoRA) 生成决策时间线
        """
        lora_path = self.get_user_lora_path(user_id)
        if not lora_path:
            raise ValueError(f"用户 {user_id} 还没有训练 LoRA 模型")
        if self.is_user_training(user_id):
            raise RuntimeError(f"用户 {user_id} 的 LoRA 正在训练中，请稍后再试个性化决策模拟")

        health = await self.sglang.health_check()
        if health.get("status") != "healthy":
            raise RuntimeError(f"SGLang 服务不可用: {health}")

        messages = self._build_timeline_messages(question, option, profile, num_events)

        try:
            response = await self.sglang.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=600,
                top_p=0.9,
                lora_path=lora_path
            )
            timeline = self._parse_timeline_json(response)
            print(f"✅ SGLang+LoRA 生成 {len(timeline)} 个时间线事件 (用户: {user_id})")
            return timeline

        except Exception as e:
            print(f"⚠️ SGLang+LoRA 时间线生成失败: {e}")
            return []

    # ==================== 个性化推荐 ====================

    async def generate_personalized_recommendation(
        self,
        user_id: str,
        question: str,
        options: List[Dict],
        profile: Any
    ) -> str:
        """
        通过 SGLang (基座 + 用户 LoRA) 生成个性化决策推荐
        """
        lora_path = self.get_user_lora_path(user_id)
        if not lora_path:
            raise ValueError(f"用户 {user_id} 还没有训练 LoRA 模型")
        if self.is_user_training(user_id):
            raise RuntimeError(f"用户 {user_id} 的 LoRA 正在训练中，请稍后再试个性化推荐生成")

        health = await self.sglang.health_check()
        if health.get("status") != "healthy":
            raise RuntimeError(f"SGLang 服务不可用: {health}")

        messages = self._build_recommendation_messages(question, options, profile)

        try:
            response = await self.sglang.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=400,
                top_p=0.9,
                lora_path=lora_path
            )
            return self._clean_recommendation(response)

        except Exception as e:
            print(f"⚠️ SGLang+LoRA 推荐生成失败: {e}")
            return f"推荐生成失败: {str(e)}"

    # ==================== LoRA 状态 ====================

    def get_lora_status(self, user_id: str) -> Dict[str, Any]:
        """获取用户的 LoRA 模型状态"""
        lora_path = self.get_user_lora_path(user_id)
        status = {
            "has_lora": lora_path is not None,
            "lora_path": lora_path,
            "model_version": 0,
            "last_train_time": None,
            "training_data_size": 0,
        }

        # 尝试读取训练状态文件
        status_file = os.path.join(self.lora_base_dir, user_id, "status.json")
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    status["model_version"] = saved.get("model_version", 0)
                    status["last_train_time"] = saved.get("last_train_time")
                    status["training_data_size"] = saved.get("current_data_size", 0)
            except Exception:
                pass

        return status

    # ==================== Prompt 构造 ====================

    def _build_timeline_messages(
        self,
        question: str,
        option: Dict[str, str],
        profile: Any,
        num_events: int
    ) -> List[Dict[str, str]]:
        """构造时间线生成的 chat messages"""
        system = (
            "你是一个决策模拟引擎。根据用户的性格特征和决策选项，"
            "模拟未来可能发生的事件时间线。"
            "你必须以纯 JSON 格式输出，不要包含任何其他文字。"
        )

        personality_info = ""
        if profile:
            personality_info = f"\n我的性格：{getattr(profile, 'decision_style', '未知')}，{getattr(profile, 'risk_preference', '未知')}"

        user_msg = (
            f"决策问题：{question}\n"
            f"我选择：{option['title']}"
            f"{personality_info}\n\n"
            f"请模拟我做出这个选择后未来12个月内的{num_events}个关键事件。\n"
            f"输出格式（纯JSON数组）：\n"
            f'[{{"month": 1, "event": "事件描述", "impact": {{"health": 0.0, "finance": 0.0, "social": 0.0, "emotion": 0.0, "learning": 0.0}}, "probability": 0.8}}]'
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]

    def _build_recommendation_messages(
        self,
        question: str,
        options: List[Dict],
        profile: Any
    ) -> List[Dict[str, str]]:
        """构造推荐生成的 chat messages"""
        system = "你是用户的个人决策顾问，根据用户性格特点给出个性化建议。"

        options_text = ""
        for opt in options:
            options_text += (
                f"\n{opt['title']}：\n"
                f"  综合得分：{opt.get('final_score', 0):.1f}/100\n"
                f"  风险等级：{opt.get('risk_level', 0):.2f}\n"
            )

        personality_info = ""
        if profile:
            personality_info = (
                f"\n我的性格特点：\n"
                f"- 决策风格：{getattr(profile, 'decision_style', '未知')}\n"
                f"- 风险偏好：{getattr(profile, 'risk_preference', '未知')}\n"
                f"- 生活优先级：{getattr(profile, 'life_priority', '未知')}\n"
            )

        user_msg = (
            f"我面临一个重要决策：{question}\n\n"
            f"各选项分析结果：{options_text}"
            f"{personality_info}\n"
            f"请给我一个个性化的建议，告诉我应该选择哪个选项，以及为什么。"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]

    # ==================== 响应解析 ====================

    def _parse_timeline_json(self, response: str) -> List[Dict[str, Any]]:
        """解析时间线 JSON 响应（兼容多种格式）"""
        timeline = []
        try:
            # 移除 markdown 代码块
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)

            # 方式1: {"timeline": [...]}
            m1 = re.search(r'\{"timeline":\s*\[(.*?)\]\s*\}', response, re.DOTALL)
            if m1:
                try:
                    data = json.loads(m1.group(0))
                    timeline = self._extract_events(data['timeline'])
                    if timeline:
                        return timeline
                except Exception:
                    pass

            # 方式2: 直接数组 [...]
            m2 = re.search(r'\[\s*\{.*?\}\s*\]', response, re.DOTALL)
            if m2:
                try:
                    data = json.loads(m2.group(0))
                    timeline = self._extract_events(data)
                    if timeline:
                        return timeline
                except Exception:
                    pass

            # 方式3: 尝试整个响应作为 JSON
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
        """从数据中提取事件"""
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
        """清理推荐文本"""
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
