#!/usr/bin/env python3
"""
vLLM 统一服务 API
整合推理服务 + LoRA 训练 + 管理接口
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from contextlib import asynccontextmanager

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# vLLM 导入
try:
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    print("⚠️ vLLM 未安装")


# ============== 配置 ==============

class Config:
    DATA_DIR = os.environ.get("DATA_DIR", "/root/autodl-tmp")
    BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    LORA_DIR = f"{DATA_DIR}/models/lora"
    
    # vLLM 配置
    VLLM_CONFIG = {
        "tensor_parallel_size": 1,
        "gpu_memory_utilization": 0.85,
        "max_model_len": 4096,
        "dtype": "bfloat16",
        "trust_remote_code": True,
        "enable_lora": True,
        "max_loras": 50,
        "max_lora_rank": 64,
        "max_cpu_loras": 100,
    }
    
    HOST = "0.0.0.0"
    PORT = 8000


# ============== 数据模型 ==============

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False

class TrainRequest(BaseModel):
    user_id: str
    conversations: List[Dict[str, str]]  # [{"user": "...", "assistant": "..."}]
    num_epochs: int = 3
    learning_rate: float = 2e-4

class GenerateRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024


# ============== 引擎 ==============

class VLLMEngine:
    """vLLM 推理引擎"""
    
    def __init__(self):
        self.llm: Optional[LLM] = None
        self.lora_registry: Dict[str, Dict] = {}
        self.training_tasks: Dict[str, Dict] = {}
    
    def initialize(self):
        if not VLLM_AVAILABLE:
            raise RuntimeError("vLLM 未安装")
        
        print(f"🚀 初始化 vLLM...")
        print(f"   模型: {Config.BASE_MODEL}")
        
        self.llm = LLM(model=Config.BASE_MODEL, **Config.VLLM_CONFIG)
        
        print("✅ vLLM 初始化完成")
        self._scan_loras()
    
    def _scan_loras(self):
        """扫描 LoRA 适配器"""
        lora_base = Path(Config.LORA_DIR)
        if not lora_base.exists():
            lora_base.mkdir(parents=True, exist_ok=True)
            return
        
        self.lora_registry.clear()
        
        for user_dir in lora_base.iterdir():
            if not user_dir.is_dir():
                continue
            
            user_id = user_dir.name
            versions = [d for d in user_dir.iterdir() if d.is_dir() and d.name.startswith('v')]
            
            if not versions:
                continue
            
            latest = sorted(versions, key=lambda x: int(x.name[1:]))[-1]
            final_path = latest / "final"
            
            if final_path.exists():
                self.lora_registry[user_id] = {
                    "user_id": user_id,
                    "path": str(final_path),
                    "version": int(latest.name[1:]),
                    "name": f"user_{user_id}"
                }
        
        print(f"📦 发现 {len(self.lora_registry)} 个 LoRA")
    
    def get_lora_request(self, user_id: str) -> Optional[LoRARequest]:
        if user_id not in self.lora_registry:
            return None
        
        info = self.lora_registry[user_id]
        return LoRARequest(
            lora_name=info["name"],
            lora_int_id=hash(user_id) % 10000,
            lora_path=info["path"]
        )
    
    def generate(
        self,
        prompts: List[str],
        user_id: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> List[str]:
        
        params = SamplingParams(
            temperature=temperature,
            top_p=0.9,
            max_tokens=max_tokens
        )
        
        lora_req = self.get_lora_request(user_id) if user_id else None
        
        if lora_req:
            outputs = self.llm.generate(prompts, params, lora_request=lora_req)
        else:
            outputs = self.llm.generate(prompts, params)
        
        return [o.outputs[0].text for o in outputs]
    
    def reload_loras(self):
        self._scan_loras()
        return len(self.lora_registry)


# 全局引擎
engine: Optional[VLLMEngine] = None


# ============== FastAPI ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = VLLMEngine()
    engine.initialize()
    yield
    print("🛑 服务关闭")

app = FastAPI(
    title="vLLM Multi-LoRA Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== API 端点 ==============

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "lora_count": len(engine.lora_registry) if engine else 0,
        "model": Config.BASE_MODEL
    }


@app.get("/v1/models")
async def list_models():
    models = [{"id": "base", "object": "model"}]
    if engine:
        for uid, info in engine.lora_registry.items():
            models.append({
                "id": info["name"],
                "user_id": uid,
                "version": info["version"]
            })
    return {"data": models}


@app.get("/v1/loras")
async def list_loras():
    return {
        "loras": list(engine.lora_registry.values()) if engine else [],
        "total": len(engine.lora_registry) if engine else 0
    }


@app.post("/v1/loras/reload")
async def reload_loras():
    count = engine.reload_loras()
    return {"message": "已重新加载", "count": count}


@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    if not engine:
        raise HTTPException(503, "引擎未初始化")
    
    # 构建 prompt
    parts = []
    for msg in request.messages:
        if msg.role == "system":
            parts.append(f"<|im_start|>system\n{msg.content}<|im_end|>")
        elif msg.role == "user":
            parts.append(f"<|im_start|>user\n{msg.content}<|im_end|>")
        elif msg.role == "assistant":
            parts.append(f"<|im_start|>assistant\n{msg.content}<|im_end|>")
    parts.append("<|im_start|>assistant\n")
    prompt = "\n".join(parts)
    
    results = engine.generate(
        [prompt],
        user_id=request.user_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    text = results[0]
    if "<|im_end|>" in text:
        text = text.split("<|im_end|>")[0]
    
    return {
        "id": f"chatcmpl-{datetime.now().timestamp()}",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text.strip()},
            "finish_reason": "stop"
        }],
        "model": f"user_{request.user_id}" if request.user_id else "base"
    }


@app.post("/v1/completions")
async def complete(request: GenerateRequest):
    if not engine:
        raise HTTPException(503, "引擎未初始化")
    
    results = engine.generate(
        [request.prompt],
        user_id=request.user_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    return {
        "choices": [{"text": results[0], "index": 0}],
        "model": f"user_{request.user_id}" if request.user_id else "base"
    }


@app.post("/v1/train")
async def train_lora(request: TrainRequest, background_tasks: BackgroundTasks):
    """异步训练 LoRA"""
    
    # 检查是否正在训练
    if request.user_id in engine.training_tasks:
        task = engine.training_tasks[request.user_id]
        if task.get("status") == "training":
            raise HTTPException(400, f"用户 {request.user_id} 正在训练中")
    
    # 记录任务
    engine.training_tasks[request.user_id] = {
        "status": "queued",
        "started_at": datetime.now().isoformat(),
        "samples": len(request.conversations)
    }
    
    # 后台训练
    background_tasks.add_task(
        _train_lora_task,
        request.user_id,
        request.conversations,
        request.num_epochs,
        request.learning_rate
    )
    
    return {
        "message": "训练任务已提交",
        "user_id": request.user_id,
        "samples": len(request.conversations)
    }


async def _train_lora_task(
    user_id: str,
    conversations: List[Dict],
    num_epochs: int,
    learning_rate: float
):
    """后台训练任务"""
    from gpu_server.vllm_lora_trainer import VLLMLoRATrainer, TrainingConfig
    
    engine.training_tasks[user_id]["status"] = "training"
    
    try:
        config = TrainingConfig(
            num_epochs=num_epochs,
            learning_rate=learning_rate
        )
        trainer = VLLMLoRATrainer(user_id, config)
        result = trainer.train(conversations)
        
        engine.training_tasks[user_id]["status"] = "completed"
        engine.training_tasks[user_id]["result"] = result
        
        # 重新加载 LoRA
        if result.get("success"):
            engine.reload_loras()
            
    except Exception as e:
        engine.training_tasks[user_id]["status"] = "failed"
        engine.training_tasks[user_id]["error"] = str(e)


@app.get("/v1/train/{user_id}/status")
async def get_training_status(user_id: str):
    """获取训练状态"""
    if user_id not in engine.training_tasks:
        raise HTTPException(404, "未找到训练任务")
    return engine.training_tasks[user_id]


@app.get("/v1/users/{user_id}/lora")
async def get_user_lora(user_id: str):
    """获取用户 LoRA 信息"""
    if user_id not in engine.lora_registry:
        return {"has_lora": False, "user_id": user_id}
    
    info = engine.lora_registry[user_id]
    return {
        "has_lora": True,
        **info
    }


# ============== 主函数 ==============

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    
    if args.model:
        os.environ["BASE_MODEL"] = args.model
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║         vLLM Multi-LoRA 统一服务                              ║
║         推理 + 训练 + 管理                                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "gpu_server.vllm_service_api:app",
        host=args.host,
        port=args.port,
        workers=1
    )


if __name__ == "__main__":
    main()
