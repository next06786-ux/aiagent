"""
LoRA 自动化训练系统
为每个用户训练专属的个性化 LoRA 模型（基于本地 Qwen3.5-9B）
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
    def __init__(self, user_id: str, total_steps: int):
        self.user_id = user_id
        self.total_steps = max(total_steps, 1)

    def on_log(self, args, state, control, logs=None, **kwargs):
        progress = min(95, int(state.global_step / self.total_steps * 90) + 5)
        _training_progress[self.user_id] = {
            "is_training": True,
            "progress": progress,
            "stage": f"训练中 step {state.global_step}/{self.total_steps}",
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
    """LoRA 自动化训练器"""

    def __init__(self, user_id: str, base_model_name: Optional[str] = None):
        if not user_id:
            raise ValueError("user_id 不能为空")

        self.user_id = user_id
        self.base_model_name = base_model_name or os.environ.get("LOCAL_BASE_MODEL_PATH", "/root/autodl-tmp/models/base/Qwen3.5-9B")

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

        self.user_lora_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "lora", user_id))
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
        """从数据库获取用户对话数据用于训练"""
        try:
            from backend.database.models import ConversationHistory, Database
            from backend.database.config import DatabaseConfig
            
            db = Database(DatabaseConfig.get_database_url())
            session = db.get_session()
            
            # 查询所有对话，按时间排序
            rows = session.query(ConversationHistory).filter(
                ConversationHistory.user_id == self.user_id
            ).order_by(ConversationHistory.timestamp.asc()).all()
            
            session.close()
            
            # 配对 user/assistant 消息
            conversations = []
            i = 0
            while i < len(rows) - 1:
                if rows[i].role == 'user' and rows[i + 1].role == 'assistant':
                    user_msg = rows[i].content or ""
                    ai_msg = rows[i + 1].content or ""
                    if user_msg.strip() and ai_msg.strip() and '无法回答' not in ai_msg:
                        conversations.append({
                            "user": user_msg,
                            "assistant": ai_msg,
                            "timestamp": rows[i].timestamp.isoformat() if rows[i].timestamp else ""
                        })
                    i += 2
                else:
                    i += 1
            
            print(f"📊 从数据库获取 {len(conversations)} 条有效对话对")
            return conversations
        except Exception as e:
            print(f"⚠️ 从数据库获取对话失败: {e}")
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

    def train_lora(self, dataset: Dataset) -> Optional[str]:
        print(f"\n{'='*60}")
        print(f"🚀 开始为用户 {self.user_id} 训练 LoRA 模型")
        print(f"📊 训练数据量: {len(dataset)}")
        print(f"{'='*60}\n")

        _training_progress[self.user_id] = {
            "is_training": True, "progress": 0, "stage": "准备GPU资源...", "error": None
        }

        try:
            # 训练前清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                import gc
                gc.collect()
                print(f"GPU缓存已清理，可用显存: {torch.cuda.mem_get_info()[0] / 1024**3:.1f} GB")

            # 复用 lora_manager 已加载的基座模型，避免重复加载OOM
            print(f"📥 获取已加载的基座模型...")
            _training_progress[self.user_id]["stage"] = "获取基座模型..."
            _training_progress[self.user_id]["progress"] = 2
            
            from backend.lora.lora_model_manager import lora_manager
            lora_manager.load_base_model()  # 确保已加载
            base_model = lora_manager.base_model
            tokenizer = lora_manager.tokenizer
            
            if base_model is None:
                raise RuntimeError("基座模型未加载，请检查模型路径")

            # 卸载该用户已有的LoRA（如果有），避免冲突
            if self.user_id in lora_manager.loaded_loras:
                del lora_manager.loaded_loras[self.user_id]
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                print(f"已卸载用户 {self.user_id} 的旧LoRA")

            print("添加 LoRA 适配器...")
            _training_progress[self.user_id]["stage"] = "初始化LoRA适配器..."
            _training_progress[self.user_id]["progress"] = 5
            
            # 启用gradient checkpointing
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
                bf16=False,  # 8-bit量化时不用bf16
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

            num_epochs = self.training_config["num_epochs"]
            batch_size = self.training_config["batch_size"]
            total_steps = max(1, (len(dataset) // (batch_size * 4)) * num_epochs)

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=dataset,
                callbacks=[ProgressCallback(self.user_id, total_steps)],
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
            
            # 训练完成后恢复模型到推理状态
            try:
                base_model.gradient_checkpointing_disable()
                # 移除PEFT包装，恢复原始base_model
                model.merge_and_unload()  # 不改变lora_manager.base_model
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
            # 恢复模型状态
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
