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
            "train_interval_days": 7,
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
        if self.status["last_train_time"]:
            days_since_last = (datetime.now() - self.status["last_train_time"]).days
            if days_since_last < self.training_config["train_interval_days"]:
                print(f"⏰ 距离上次训练仅 {days_since_last} 天")
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

            # 分层
            game_convs     = []
            decision_convs = []
            general_convs  = []

            for conv in raw_pairs:
                sid  = conv.get('session_id', '')
                text = conv['user'] + conv['assistant']
                if sid.startswith('game_'):
                    game_convs.append(conv)
                elif any(kw in text for kw in DECISION_KEYWORDS):
                    decision_convs.append(conv)
                else:
                    general_convs.append(conv)

            # 游戏数据加权（复制一份，强化决策偏好信号）
            weighted_game = game_convs * 2

            # 通用数据采样（最多占决策+游戏数据量的50%）
            decision_total = len(decision_convs) + len(game_convs)
            max_general    = max(10, decision_total // 2)
            sampled_general = random.sample(general_convs, min(len(general_convs), max_general))

            result = weighted_game + decision_convs + sampled_general
            random.shuffle(result)

            print(
                f"[LoRA训练数据] 游戏:{len(game_convs)}×2  决策:{len(decision_convs)}"
                f"  通用采样:{len(sampled_general)}/{len(general_convs)}  合计:{len(result)}"
            )
            return result

        except Exception as e:
            print(f"从数据库获取对话失败: {e}")
            return []

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
        print(f"🤖 LoRA 自动训练检查")
        print(f"👤 用户: {self.user_id}")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        if not self.check_training_trigger():
            print("⏭️  跳过本次训练\n")
            return

        print("📚 收集训练数据...")
        conversations = self.get_user_conversations()
        print(f"✅ 收集到 {len(conversations)} 条对话\n")

        print("🔄 准备数据集...")
        dataset = self.prepare_dataset(conversations)
        print("✅ 数据集准备完成\n")

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
                print(f"📊 训练统计:")
                print(f"   - 总训练次数: {self.status['total_trainings']}")
                print(f"   - 当前版本: v{self.status['model_version']}")
                print(f"   - 数据量: {len(conversations)}")
                print(f"   - 下次训练: {self.training_config['train_interval_days']} 天后\n")
            else:
                self.status["is_training"] = False
                self.save_status()
                print("❌ 训练失败\n")
        except Exception as e:
            self.status["is_training"] = False
            self.save_status()
            print(f"❌ 训练异常: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    trainer = AutoLoRATrainer("test_user")
    trainer.auto_train_workflow()
