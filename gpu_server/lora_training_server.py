"""
GPU服务器 LoRA 训练 API 服务
提供远程训练接口，支持从主服务器同步数据并训练
"""
import os
import sys
import json
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpu_server.lora_trainer_gpu import GPULoRATrainer


# ==================== 配置 ====================
class Config:
    # 数据目录（AutoDL数据盘）
    DATA_DIR = os.environ.get("DATA_DIR", "/root/autodl-tmp")
    MODELS_DIR = os.path.join(DATA_DIR, "models")
    LORA_DIR = os.path.join(MODELS_DIR, "lora")
    LOGS_DIR = os.path.join(DATA_DIR, "logs")
    
    # API密钥（用于验证请求）
    API_KEY = os.environ.get("GPU_API_KEY", "your-secret-api-key-change-me")
    
    # 默认模型
    DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "qwen2.5-7b")
    
    # 服务配置
    HOST = "0.0.0.0"
    PORT = int(os.environ.get("GPU_SERVER_PORT", "8000"))


# 创建必要目录
os.makedirs(Config.LORA_DIR, exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True)


# ==================== 数据模型 ====================
class TrainingRequest(BaseModel):
    """训练请求"""
    user_id: str
    conversations: List[Dict]  # [{"user": "...", "assistant": "..."}]
    model_type: Optional[str] = None
    num_epochs: Optional[int] = 3
    learning_rate: Optional[float] = 2e-4


class GenerateRequest(BaseModel):
    """生成请求"""
    user_id: str
    prompt: str
    max_new_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7


class TrainingStatus(BaseModel):
    """训练状态"""
    user_id: str
    is_training: bool
    last_training_time: Optional[str]
    total_trainings: int
    training_samples: int
    model_version: int
    model_type: str
    has_lora: bool


# ==================== 全局状态 ====================
class ServerState:
    def __init__(self):
        self.training_tasks: Dict[str, asyncio.Task] = {}
        self.training_results: Dict[str, Dict] = {}
        self.trainers: Dict[str, GPULoRATrainer] = {}
        self.start_time = datetime.now()
    
    def get_trainer(self, user_id: str, model_type: str = None) -> GPULoRATrainer:
        """获取或创建训练器"""
        key = f"{user_id}_{model_type or Config.DEFAULT_MODEL}"
        if key not in self.trainers:
            self.trainers[key] = GPULoRATrainer(
                user_id=user_id,
                model_type=model_type or Config.DEFAULT_MODEL,
                output_base_dir=Config.LORA_DIR
            )
        return self.trainers[key]


state = ServerState()


# ==================== 生命周期 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"🚀 GPU训练服务启动")
    print(f"📁 数据目录: {Config.DATA_DIR}")
    print(f"🤖 默认模型: {Config.DEFAULT_MODEL}")
    
    # 检查GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"✅ GPU: {gpu_name} ({gpu_mem:.1f} GB)")
        else:
            print("⚠️ 警告: CUDA不可用，将使用CPU训练")
    except Exception as e:
        print(f"⚠️ GPU检测失败: {e}")
    
    yield
    
    # 清理
    print("🛑 服务关闭中...")
    for task in state.training_tasks.values():
        task.cancel()


# ==================== FastAPI应用 ====================
app = FastAPI(
    title="LoRA Training Server",
    description="GPU服务器LoRA训练API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 认证 ====================
def verify_api_key(x_api_key: str = Header(None)):
    """验证API密钥"""
    if x_api_key != Config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ==================== API端点 ====================
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "LoRA Training Server",
        "status": "running",
        "gpu_available": _check_gpu()
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    import torch
    
    gpu_info = None
    if torch.cuda.is_available():
        gpu_info = {
            "name": torch.cuda.get_device_name(0),
            "memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            "memory_allocated_gb": torch.cuda.memory_allocated() / 1024**3,
            "memory_cached_gb": torch.cuda.memory_reserved() / 1024**3
        }
    
    return {
        "status": "healthy",
        "uptime_seconds": (datetime.now() - state.start_time).total_seconds(),
        "gpu": gpu_info,
        "active_trainings": len([t for t in state.training_tasks.values() if not t.done()]),
        "total_trainers": len(state.trainers)
    }


@app.get("/gpu/status")
async def gpu_status():
    """GPU状态详情"""
    import torch
    
    if not torch.cuda.is_available():
        return {"available": False, "message": "CUDA not available"}
    
    return {
        "available": True,
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "device_name": torch.cuda.get_device_name(0),
        "memory": {
            "total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
            "cached_gb": torch.cuda.memory_reserved() / 1024**3,
            "free_gb": (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3
        },
        "cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__
    }


@app.post("/train")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None)
):
    """启动训练任务"""
    verify_api_key(x_api_key)
    
    user_id = request.user_id
    
    # 检查是否已有训练任务
    if user_id in state.training_tasks and not state.training_tasks[user_id].done():
        raise HTTPException(
            status_code=409,
            detail=f"用户 {user_id} 已有训练任务在进行中"
        )
    
    # 验证数据
    if len(request.conversations) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"数据量不足，需要至少5条对话，当前: {len(request.conversations)}"
        )
    
    # 创建训练任务
    task_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    async def run_training():
        trainer = state.get_trainer(user_id, request.model_type)
        result = trainer.train(
            conversations=request.conversations,
            num_epochs=request.num_epochs,
            learning_rate=request.learning_rate
        )
        state.training_results[user_id] = {
            "task_id": task_id,
            "completed_at": datetime.now().isoformat(),
            "result": result
        }
        return result
    
    # 启动后台任务
    task = asyncio.create_task(run_training())
    state.training_tasks[user_id] = task
    
    return {
        "task_id": task_id,
        "user_id": user_id,
        "status": "started",
        "message": f"训练任务已启动，数据量: {len(request.conversations)} 条对话"
    }


@app.get("/train/status/{user_id}")
async def get_training_status(user_id: str, x_api_key: str = Header(None)):
    """获取训练状态"""
    verify_api_key(x_api_key)
    
    # 检查是否有进行中的任务
    is_running = user_id in state.training_tasks and not state.training_tasks[user_id].done()
    
    # 获取训练器状态
    trainer = state.get_trainer(user_id)
    trainer_status = trainer.get_status()
    
    # 获取最近的训练结果
    last_result = state.training_results.get(user_id)
    
    return {
        "user_id": user_id,
        "is_training": is_running,
        "trainer_status": trainer_status,
        "last_result": last_result
    }


@app.post("/generate")
async def generate_text(request: GenerateRequest, x_api_key: str = Header(None)):
    """使用LoRA模型生成文本"""
    verify_api_key(x_api_key)
    
    trainer = state.get_trainer(request.user_id)
    
    # 检查是否有LoRA模型
    if not trainer.get_status().get("has_lora"):
        raise HTTPException(
            status_code=404,
            detail=f"用户 {request.user_id} 没有训练好的LoRA模型"
        )
    
    try:
        response = trainer.generate(
            prompt=request.prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature
        )
        return {
            "user_id": request.user_id,
            "prompt": request.prompt,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models(x_api_key: str = Header(None)):
    """列出所有可用模型"""
    verify_api_key(x_api_key)
    
    return {
        "available_models": list(GPULoRATrainer.MODEL_CONFIGS.keys()),
        "default_model": Config.DEFAULT_MODEL,
        "model_configs": GPULoRATrainer.MODEL_CONFIGS
    }


@app.get("/users")
async def list_users(x_api_key: str = Header(None)):
    """列出所有有LoRA模型的用户"""
    verify_api_key(x_api_key)
    
    users = []
    if os.path.exists(Config.LORA_DIR):
        for user_dir in os.listdir(Config.LORA_DIR):
            user_path = os.path.join(Config.LORA_DIR, user_dir)
            if os.path.isdir(user_path):
                status_file = os.path.join(user_path, "status.json")
                if os.path.exists(status_file):
                    with open(status_file, 'r') as f:
                        status = json.load(f)
                    users.append({
                        "user_id": user_dir,
                        "model_version": status.get("model_version", 0),
                        "last_training": status.get("last_training_time"),
                        "training_samples": status.get("training_samples", 0)
                    })
    
    return {"users": users, "total": len(users)}


@app.delete("/models/{user_id}")
async def delete_user_model(user_id: str, x_api_key: str = Header(None)):
    """删除用户的LoRA模型"""
    verify_api_key(x_api_key)
    
    import shutil
    user_path = os.path.join(Config.LORA_DIR, user_id)
    
    if not os.path.exists(user_path):
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有LoRA模型")
    
    shutil.rmtree(user_path)
    
    # 清理缓存的trainer
    keys_to_remove = [k for k in state.trainers if k.startswith(user_id)]
    for k in keys_to_remove:
        del state.trainers[k]
    
    return {"message": f"已删除用户 {user_id} 的LoRA模型"}


# ==================== 辅助函数 ====================
def _check_gpu() -> bool:
    """检查GPU是否可用"""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False


# ==================== 主入口 ====================
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           LoRA Training Server - GPU Edition             ║
╠══════════════════════════════════════════════════════════╣
║  启动命令: python gpu_server/lora_training_server.py     ║
║  API文档:  http://localhost:{Config.PORT}/docs                  ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "lora_training_server:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        workers=1  # GPU训练只能单worker
    )
