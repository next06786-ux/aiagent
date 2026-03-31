"""
LoRA 自动化训练系统
为每个用户训练专属的个性化 LoRA 模型（基于本地 Qwen3.5-9B）
集成 llmquant 训练后自动量化（4-bit per-channel）
"""
import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Optional

import torch
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, TrainerCallback
from peft import LoraConfig, get_peft_model, TaskType

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 全局训练进度存储 {user_id: {progress, stage, is_training}}
_training_progress: Dict[str, Dict] = {}


def get_training_progress(user_id: str) -> Dict:
    """获取用户的训练进度"""
    return _training_progress.get(user_id, {
        "is_training": False, "progress": 0, "stage": "", "error": None
    })


class ProgressCallback(TrainerCallback):
    """训练进度回调"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.total_steps = 1

    def on_train_begin(self, args, state, control, **kwargs):
        self.total_steps = max(state.max_steps, 1)
        _training_progress[self.user_id] = {
            "is_training": True,
            "progress": 5,
            "stage": f"开始训练 共{self.total_steps}步",
            "error": None
        }

    def on_log(self, args, state, control, logs=None, **kwargs):
        progress = min(95, int(state.global_step / self.total_steps * 90) + 5)
        _training_progress[self.user_id] = {
            "is_training": True,
            "progress": progress,
            "stage": f"训练中 {state.global_step}/{self.total_steps}",
            "error": None
        }


class ConversationDataset(Dataset):
    """对话数据集"""

    def __init__(self, conversations: List[Dict], tokenizer, max_length: int = 512):
        self.conversations = conversations
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.conversations)

    def __getitem__(self, idx):
        item = self.conversations[idx]
        text = f"<|im_start|>user\n{item['user']}<|im_end|>\n<|im_start|>assistant\n{item['assistant']}<|im_end|>"
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze()
        }


class AutoLoRATrainer:
    """LoRA 自动化训练器（集成训练后自动量化）"""

    def __init__(self, user_id: str, base_model_name: Optional[str] = None):
        if not user_id:
            raise ValueError("user_id 不能为空")

        self.user_id = user_id
        self.base_model_name = base_model_name or os.environ.get(
            "LOCAL_BASE_MODEL_PATH", "/root/autodl-tmp/models/base/Qwen3.5-9B"
        )

        self.lora_config = LoraConfig(
            r=64,
            lora_alpha=128,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )

        self.training_config = {
            "min_data_size": 20,
            "num_epochs": 1,
            "batch_size": 1,
            "learning_rate": 2e-4,
            "max_length": 256
        }

        self.user_lora_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "models", "lora", user_id)
        )
        self.status_file = os.path.join(self.user_lora_root, "status.json")
        self.status = self.load_status()
        self._rag_system = None

    def load_status(self) -> Dict:
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
                if status.get("last_train_time"):
                    status["last_train_time"] = datetime.fromisoformat(status["last_train_time"])
                return status
        return {
            "last_train_time": None,
            "total_trainings": 0,
            "current_data_size": 0,
            "is_training": False,
            "model_version": 0
        }

    def save_status(self):
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        status_to_save = {
            **self.status,
            "last_train_time": self.status["last_train_time"].isoformat() if self.status["last_train_time"] else None
        }
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_to_save, f, indent=2, ensure_ascii=False)

    def check_training_trigger(self) -> bool:
        conversations = self.get_user_conversations()
        self.status["current_data_size"] = len(conversations)
        if len(conversations) < self.training_config["min_data_size"]:
            print(f"❌ 数据不足: {len(conversations)}/{self.training_config['min_data_size']}")
            return False
        if self.status["is_training"]:
            print("⚠️ 已有训练任务在进行中")
            return False
        return True

    def get_user_conversations(self) -> List[Dict]:
        """从数据库获取用户对话数据用于训练（只取上次训练后的新对话）
        
        分层策略：
        - 决策相关对话全部保留（高信号）
        - 游戏数据额外加权（复制一份，强化决策偏好学习）
        - 通用对话按比例采样（最多占决策数据的50%，保留语言风格）
        """
        import random

        DECISION_KEYWORDS = [
            '要不要', '该不该', '值不值', '怎么选', '如何选择',
            '换工作', '考研', '创业', '投资', '搬家', '辞职', '跳槽',
            '纠结', '犹豫', '拿不定主意', '建议', '风险', '机会', '后悔',
            '打算', '计划', '决定', '选择', '利弊', '优缺点',
            '要去', '要留', '要做', '要放弃', '要坚持'
        ]

        try:
            from backend.database.models import ConversationHistory, Database
            from backend.database.config import DatabaseConfig

            db = Database(DatabaseConfig.get_database_url())
            session = db.get_session()

            query = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == self.user_id
            )
            if self.status.get("last_train_time"):
                query = query.filter(ConversationHistory.timestamp > self.status["last_train_time"])

            rows = query.order_by(ConversationHistory.timestamp.asc()).all()
            session.close()

            # 构建对话对，同时记录 session_id
            raw_pairs = []
            i = 0
            while i < len(rows) - 1:
                if rows[i].role == 'user' and rows[i + 1].role == 'assistant':
                    user_msg = rows[i].content or ""
                    ai_msg   = rows[i + 1].content or ""
                    if user_msg.strip() and ai_msg.strip() and '无法回答' not in ai_msg:
                        raw_pairs.append({
                            "user":       user_msg,
                            "assistant":  ai_msg,
                            "timestamp":  rows[i].timestamp.isoformat() if rows[i].timestamp else "",
                            "session_id": getattr(rows[i], 'session_id', '') or ''
                        })
                    i += 2
                else:
                    i += 1

            # 分层（LoRA 只学长期稳定的偏好和风格，不学短期事实）
            game_convs     = []   # 游戏选择 → LoRA（决策偏好模式）
            preference_convs = [] # 价值观/偏好表达 → LoRA
            general_convs  = []   # 普通对话 → LoRA（语言风格）
            # 以下不进 LoRA：
            # - collect_ 开头的决策收集对话（特定于单次决策，应去 Prompt）
            # - feedback_ 开头的反馈对话（已单独处理）

            PREFERENCE_KEYWORDS = [
                '我觉得', '我认为', '我喜欢', '我讨厌', '我害怕', '我希望',
                '对我来说', '我看重', '我在意', '我不在乎', '我倾向',
                '我的原则', '我一直', '我从来', '我习惯', '我性格',
                '家人觉得', '朋友说我', '别人评价我'
            ]

            for conv in raw_pairs:
                sid  = conv.get('session_id', '')
                text = conv['user'] + conv['assistant']

                # 决策收集对话 → 不进 LoRA（去 Prompt）
                if sid.startswith('collect_') or sid.startswith('feedback_'):
                    continue

                # 游戏数据 → LoRA（决策偏好）
                if sid.startswith('game_'):
                    game_convs.append(conv)
                # 价值观/偏好表达 → LoRA（长期性格）
                elif any(kw in text for kw in PREFERENCE_KEYWORDS):
                    preference_convs.append(conv)
                # 决策关键词但不是收集对话 → LoRA（决策思维模式）
                elif any(kw in text for kw in DECISION_KEYWORDS):
                    preference_convs.append(conv)
                else:
                    general_convs.append(conv)

            # ── 用 LLM 对不确定的对话做二次分类 ──
            # 从 general_convs 中识别出隐含的偏好表达
            if general_convs:
                reclassified = self._llm_classify_conversations(general_convs)
                extra_preference = [c for c in reclassified if c.get("_class") == "preference"]
                remaining_general = [c for c in reclassified if c.get("_class") != "preference"]
                preference_convs.extend(extra_preference)
                general_convs = remaining_general
                if extra_preference:
                    print(f"[LLM分类] 从通用对话中识别出 {len(extra_preference)} 条偏好表达")

            # 游戏数据加权（复制一份，强化决策偏好信号）
            weighted_game = game_convs * 2

            # 通用数据采样（保留语言风格，但不占主导）
            preference_total = len(preference_convs) + len(game_convs)
            max_general = max(10, preference_total // 2)
            sampled_general = random.sample(general_convs, min(len(general_convs), max_general))

            result = weighted_game + preference_convs + sampled_general
            random.shuffle(result)

            print(
                f"[LoRA训练数据] 游戏:{len(game_convs)}x2  偏好:{len(preference_convs)}"
                f"  通用采样:{len(sampled_general)}/{len(general_convs)}"
                f"  排除:collect/feedback  合计:{len(result)}"
            )

            # ── 合成决策推演格式的训练样本（训练-推理格式对齐）──
            synthetic = self._synthesize_decision_training_data(preference_convs + game_convs)
            if synthetic:
                result.extend(synthetic)
                print(f"[LoRA训练数据] 合成推演格式样本: {len(synthetic)} 条")

            random.shuffle(result)
            return result

        except Exception as e:
            print(f"从数据库获取对话失败: {e}")
            return []

    def _llm_classify_conversations(self, convs: List[Dict]) -> List[Dict]:
        """
        用 LLM 批量分类对话：区分"长期偏好表达"和"短期闲聊"。
        只在 LoRA 训练触发时调用一次，不影响实时性能。
        """
        if not convs:
            return convs

        try:
            from backend.llm.llm_service import get_llm_service
            llm = get_llm_service()
            if not llm or not llm.enabled:
                # LLM 不可用，全部标记为 general
                for c in convs:
                    c["_class"] = "general"
                return convs

            # 批量分类（每批最多 10 条，避免 prompt 过长）
            batch_size = 10
            for i in range(0, len(convs), batch_size):
                batch = convs[i:i + batch_size]
                texts = []
                for idx, c in enumerate(batch):
                    texts.append(f"{idx}. {c['user'][:80]}")

                prompt = (
                    "请判断以下每条用户发言属于哪个类别：\n"
                    "A = 长期偏好/价值观/性格表达（如：我比较保守、我很看重家人意见、我不喜欢冒险）\n"
                    "B = 短期状态/具体事件/闲聊（如：今天加班了、帮我写段代码、天气不错）\n\n"
                    + "\n".join(texts) + "\n\n"
                    "请只输出每条的编号和类别，格式如：0:A 1:B 2:A"
                )

                try:
                    response = llm.chat([
                        {"role": "system", "content": "你是文本分类助手，只输出分类结果。"},
                        {"role": "user", "content": prompt}
                    ], temperature=0.0)

                    if response:
                        # 解析 "0:A 1:B 2:A" 格式
                        import re
                        matches = re.findall(r'(\d+)\s*[:：]\s*([ABab])', response)
                        for num_str, label in matches:
                            num = int(num_str)
                            if 0 <= num < len(batch):
                                batch[num]["_class"] = "preference" if label.upper() == "A" else "general"

                except Exception as e:
                    print(f"[LLM分类] 批次分类失败: {e}")

            # 未被分类的默认为 general
            for c in convs:
                if "_class" not in c:
                    c["_class"] = "general"

            return convs

        except Exception as e:
            print(f"[LLM分类] 整体失败: {e}")
            for c in convs:
                c["_class"] = "general"
            return convs

    def _synthesize_decision_training_data(self, decision_convs: List[Dict]) -> List[Dict]:
        """
        训练-推理格式对齐：把用户的决策对话转换成和推演 prompt 一致的格式。
        
        这样 LoRA 学到的不是"怎么聊天"，而是"怎么为这个用户做决策推演"。
        训练样本的 user 部分 = 推演 prompt 格式
        训练样本的 assistant 部分 = 符合该用户风格的推演事件 JSON
        """
        if not decision_convs:
            return []

        synthetic = []

        try:
            # 1. 用 PKF-DS 抽取个人事实
            from backend.decision.personal_knowledge_fusion import PersonalFactExtractor
            extractor = PersonalFactExtractor(self.user_id)
            facts = extractor.extract_all()
            facts_text = "\n".join([f"- {f.to_text()}" for f in facts[:8]])

            if not facts_text.strip():
                facts_text = "- 暂无详细个人事实"

            # 2. 从决策对话中提取决策问题
            decision_questions = []
            for conv in decision_convs[:5]:
                text = conv.get("user", "")
                if len(text) > 10:
                    decision_questions.append(text[:100])

            if not decision_questions:
                return []

            # 3. 用通义千问 API 为每个决策问题生成"标准答案"
            from backend.llm.llm_service import get_llm_service
            llm = get_llm_service()
            if not llm or not llm.enabled:
                return self._synthesize_fallback(decision_questions, facts_text)

            for q in decision_questions[:3]:  # 最多 3 个，避免 API 调用过多
                # 构造和推演时一致的 prompt 格式
                user_prompt = (
                    f"<|im_start|>system\n"
                    f"你是用户的未来决策推演引擎。请根据用户问题、选项和个性化特征，"
                    f"生成真实、具体、实用的未来事件。输出必须是 JSON 数组。<|im_end|>\n"
                    f"<|im_start|>user\n"
                    f"决策问题：{q}\n"
                    f"决策选项：{q.split('还是')[-1].strip() if '还是' in q else '当前倾向'}\n"
                    f"用户个人事实：\n{facts_text}\n"
                    f"请输出 4 个按时间递进的关键事件，每个事件都要贴近用户的真实生活。\n"
                    f"输出格式：[{{\"month\":1,\"event\":\"具体事件\",\"impact\":{{\"健康\":0.0,\"财务\":0.0,"
                    f"\"社交\":0.0,\"情绪\":0.0,\"学习\":0.0,\"时间\":0.0}},\"probability\":0.8}}]\n"
                    f"<|im_end|>\n<|im_start|>assistant\n"
                )

                # 用通义千问生成标准答案（不是 LoRA，是云端 API）
                gen_prompt = (
                    f"为以下用户生成 4 个决策推演事件（JSON 数组），"
                    f"事件必须引用用户的个人事实，贴近真实生活：\n\n"
                    f"决策问题：{q}\n"
                    f"用户个人事实：\n{facts_text}\n\n"
                    f"输出 JSON 数组，每个元素包含 month, event, impact, probability。"
                    f"event 必须具体，引用用户的真实信息。"
                )

                try:
                    response = llm.chat([
                        {"role": "system", "content": "你是决策推演专家，只输出 JSON 数组。"},
                        {"role": "user", "content": gen_prompt}
                    ], temperature=0.3)

                    if response and response.strip():
                        import re
                        response = re.sub(r"```json\s*", "", response)
                        response = re.sub(r"```\s*", "", response)
                        # 验证是合法 JSON
                        json.loads(response.strip())
                        # 合成训练样本：user = 推演 prompt，assistant = JSON 结果
                        synthetic.append({
                            "user": user_prompt,
                            "assistant": response.strip()
                        })
                except Exception as e:
                    print(f"[合成训练数据] 生成失败: {e}")
                    continue

        except Exception as e:
            print(f"[合成训练数据] 整体失败: {e}")

        return synthetic

    def _synthesize_fallback(self, questions: List[str], facts_text: str) -> List[Dict]:
        """LLM 不可用时的兜底合成"""
        synthetic = []
        for q in questions[:2]:
            user_prompt = (
                f"<|im_start|>system\n你是用户的未来决策推演引擎。输出必须是 JSON 数组。<|im_end|>\n"
                f"<|im_start|>user\n决策问题：{q}\n"
                f"用户个人事实：\n{facts_text}\n"
                f"请输出 2 个按时间递进的关键事件。<|im_end|>\n<|im_start|>assistant\n"
            )
            fallback_answer = json.dumps([
                {"month": 1, "event": f"开始认真评估{q[:20]}的各方面影响", 
                 "impact": {"健康": 0.0, "财务": 0.0, "社交": 0.0, "情绪": -0.1, "学习": 0.1, "时间": -0.1},
                 "probability": 0.85},
                {"month": 3, "event": f"经过两个月的准备和调研，对{q[:20]}有了更清晰的判断",
                 "impact": {"健康": 0.0, "财务": 0.05, "社交": 0.05, "情绪": 0.1, "学习": 0.15, "时间": -0.05},
                 "probability": 0.75}
            ], ensure_ascii=False)
            synthetic.append({"user": user_prompt, "assistant": fallback_answer})
        return synthetic

    def prepare_dataset(self, conversations: List[Dict]) -> Dataset:
        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True,
            local_files_only=True
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        return ConversationDataset(conversations, tokenizer, self.training_config["max_length"])

    async def _auto_quantize_lora_after_training(self, lora_path: str):
        """
        训练完成后自动执行 LoRA 量化
        使用 llmquant 的 4-bit per-channel 量化方案
        """
        try:
            from backend.llm.model_config import get_quantization_config
            from backend.model_compression.lora_quantizer import LoRAQuantizer
            
            quant_config = get_quantization_config()
            
            if not quant_config.get("quantize_after_training"):
                print(f"ℹ️  LoRA 自动量化未启用，跳过量化步骤")
                return
            
            print(f"\n{'='*60}")
            print(f"🔧 开始自动量化 LoRA 权重")
            print(f"{'='*60}")
            
            _training_progress[self.user_id]["stage"] = "量化LoRA权重..."
            _training_progress[self.user_id]["progress"] = 97
            
            quantizer = LoRAQuantizer(
                user_id=self.user_id,
                lora_dir=os.path.dirname(os.path.dirname(lora_path))
            )
            
            result = quantizer.quantize_lora_weights(
                bits=quant_config.get("lora_quantization_bits", 4),
                per_channel=quant_config.get("lora_quantization_per_channel", True),
                save_metadata=True
            )
            
            if result["status"] == "success":
                print(f"\n✅ LoRA 量化成功")
                print(f"   压缩率: {result['compression_ratio']:.2f}x")
                print(f"   存储空间: {result['size_before_mb']:.1f}MB → {result['size_after_mb']:.1f}MB")
                print(f"   输出路径: {result['output_path']}\n")
                
                self.status["lora_quantized"] = True
                self.status["quantization_bits"] = quant_config.get("lora_quantization_bits", 4)
                self.status["quantization_compression_ratio"] = result['compression_ratio']
                self.save_status()
            else:
                print(f"\n⚠️  LoRA 量化失败: {result.get('error', '未知错误')}")
        
        except Exception as e:
            print(f"\n⚠️  LoRA 量化异常: {e}")
            import traceback
            traceback.print_exc()

    def train_lora(self, dataset: Dataset) -> Optional[str]:
        """训练 LoRA 模型，完成后自动量化"""
        print(f"\n{'='*60}")
        print(f"🚀 开始为用户 {self.user_id} 训练 LoRA 模型")
        print(f"📊 训练数据量: {len(dataset)}")
        print(f"{'='*60}\n")

        _training_progress[self.user_id] = {
            "is_training": True, "progress": 0, "stage": "准备GPU资源...", "error": None
        }

        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                import gc
                gc.collect()
                print(f"GPU缓存已清理，可用显存: {torch.cuda.mem_get_info()[0] / 1024**3:.1f} GB")

            print(f"📥 获取已加载的基座模型...")
            _training_progress[self.user_id]["stage"] = "获取基座模型..."
            _training_progress[self.user_id]["progress"] = 2
            
            from backend.lora.lora_model_manager import lora_manager
            lora_manager.load_base_model()
            base_model = lora_manager.base_model
            tokenizer = lora_manager.tokenizer
            
            if base_model is None:
                raise RuntimeError("基座模型未加载，请检查模型路径")

            if self.user_id in lora_manager.loaded_loras:
                del lora_manager.loaded_loras[self.user_id]
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                print(f"已卸载用户 {self.user_id} 的旧LoRA")

            print("添加 LoRA 适配器...")
            _training_progress[self.user_id]["stage"] = "初始化LoRA适配器..."
            _training_progress[self.user_id]["progress"] = 5
            
            base_model.gradient_checkpointing_enable()
            model = get_peft_model(base_model, self.lora_config)

            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total_params = sum(p.numel() for p in model.parameters())
            print(f"📊 可训练参数: {trainable_params:,} / {total_params:,} ({100 * trainable_params / total_params:.2f}%)")

            output_dir = os.path.join(self.user_lora_root, f"v{self.status['model_version'] + 1}")
            os.makedirs(output_dir, exist_ok=True)

            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=self.training_config["num_epochs"],
                per_device_train_batch_size=1,
                gradient_accumulation_steps=2,
                learning_rate=self.training_config["learning_rate"],
                bf16=False,
                fp16=False,
                logging_steps=1,
                save_strategy="epoch",
                save_total_limit=2,
                report_to="none",
                remove_unused_columns=False,
                gradient_checkpointing=True,
                optim="adamw_torch",
                max_grad_norm=0.3,
            )

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset,
                callbacks=[ProgressCallback(self.user_id)],
            )

            print("🎯 开始训练...\n")
            start_time = datetime.now()
            trainer.train()
            duration = (datetime.now() - start_time).total_seconds()

            _training_progress[self.user_id]["stage"] = "保存模型权重..."
            _training_progress[self.user_id]["progress"] = 96

            final_path = os.path.join(output_dir, "final")
            os.makedirs(final_path, exist_ok=True)
            model.save_pretrained(final_path, safe_serialization=True)

            tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
                local_files_only=True
            )
            if tokenizer.pad_token_id is None:
                tokenizer.pad_token = tokenizer.eos_token
            tokenizer.save_pretrained(final_path)

            expected_files = [
                os.path.join(final_path, "adapter_config.json"),
                os.path.join(final_path, "adapter_model.safetensors")
            ]
            missing_files = [f for f in expected_files if not os.path.exists(f)]
            if missing_files:
                raise RuntimeError(f"LoRA 保存不完整，缺少文件: {missing_files}")

            print(f"\n训练完成!")
            print(f"耗时: {duration:.1f} 秒")
            print(f"模型已保存到: {final_path}\n")
            
            # 异步执行量化，不阻塞训练流程
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._auto_quantize_lora_after_training(final_path))
            except Exception:
                # 如果 asyncio 不可用，同步执行
                import inspect
                if inspect.iscoroutinefunction(self._auto_quantize_lora_after_training):
                    try:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(self._auto_quantize_lora_after_training(final_path))
                    except:
                        print("量化步骤将在后台进行")
            
            try:
                base_model.gradient_checkpointing_disable()
                model.merge_and_unload()
            except Exception:
                pass
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            _training_progress[self.user_id] = {
                "is_training": False, "progress": 100, "stage": "训练完成", "error": None
            }
            return final_path

        except Exception as e:
            print(f"\n训练失败: {e}")
            import traceback
            traceback.print_exc()
            try:
                base_model = lora_manager.base_model
                if base_model is not None:
                    base_model.gradient_checkpointing_disable()
            except Exception:
                pass
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            _training_progress[self.user_id] = {
                "is_training": False, "progress": 0, "stage": "训练失败", "error": str(e)
            }
            return None

    def auto_train_workflow(self):
        """自动训练工作流"""
        print(f"\n{'='*60}")
        print(f"LoRA 自动训练检查")
        print(f"用户: {self.user_id}")
        print(f"{'='*60}\n")

        _training_progress[self.user_id] = {
            "is_training": True, "progress": 0, "stage": "检查训练条件...", "error": None
        }

        if not self.check_training_trigger():
            _training_progress[self.user_id] = {
                "is_training": False, "progress": 0, "stage": "", "error": None
            }
            return

        _training_progress[self.user_id]["stage"] = "收集训练数据（对话分类中）..."
        _training_progress[self.user_id]["progress"] = 1
        conversations = self.get_user_conversations()
        print(f"收集到 {len(conversations)} 条对话")

        _training_progress[self.user_id]["stage"] = "准备数据集..."
        _training_progress[self.user_id]["progress"] = 2
        dataset = self.prepare_dataset(conversations)

        self.status["is_training"] = True
        self.save_status()

        try:
            model_path = self.train_lora(dataset)
            if model_path:
                self.status["last_train_time"] = datetime.now()
                self.status["total_trainings"] += 1
                self.status["model_version"] += 1
                self.status["is_training"] = False
                self.save_status()
            else:
                self.status["is_training"] = False
                self.save_status()
        except Exception as e:
            self.status["is_training"] = False
            self.save_status()
            print(f"训练异常: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    trainer = AutoLoRATrainer("test_user")
    trainer.auto_train_workflow()
