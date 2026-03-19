#!/usr/bin/env python3
"""
vLLM Multi-LoRA 服务器
支持多用户专属 LoRA 模型的高效推理

特性：
- 单基座模型 + 多 LoRA 适配器
- 零切换延迟
- 高并发支持
- OpenAI 兼容 API
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# vLLM 导入
try:
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    print("⚠️ vLLM 未安装，请运行: pip install vllm")


# ============== 配置 ==============

class VLLMConfig:
    """vLLM 服务配置"""
    
    # 数据目录
    DATA_DIR = os.environ.get("DATA_DIR", "/root/autodl-tmp")
    
    # 基座模型配置
    BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    
    # vLLM 引擎配置
    ENGINE_CONFIG = {
        "tensor_parallel_size": 1,          # 单卡
        "gpu_memory_utilization": 0.85,     # GPU 显存利用率
        "max_model_len": 4096,              # 最大序列长度
        "dtype": "bfloat16",                # 数据类型
        "trust_remote_code": True,
        
        # Multi-LoRA 配置
        "enable_lora": True,
        "max_loras": 50,                    # 最多同时加载 50 个 LoRA
        "max_lora_rank": 64,                # 最大 LoRA rank
        "max_cpu_loras": 100,               # CPU 缓存的 LoRA 数量
    }
    
    # LoRA 存储路径
    LORA_BASE_PATH = f"{DATA_DIR}/models/lora"
    
    # 服务配置
    HOST = "0.0.0.0"
    PORT = 8000


# ============== 数据模型 ==============

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    """OpenAI 兼容的聊天请求"""
    model: str = "default"
    messages: List[ChatMessage]
    user_id: Optional[str] = None           # 用户 ID，用于选择 LoRA
    lora_name: Optional[str] = None         # 直接指定 LoRA 名称
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    stream: bool = False

class CompletionRequest(BaseModel):
    """文本补全请求"""
    prompt: str
    user_id: Optional[str] = None
    lora_name: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    stream: bool = False

class LoRAInfo(BaseModel):
    """LoRA 信息"""
    name: str
    user_id: str
    path: str
    version: int
    created_at: Optional[str] = None
    is_loaded: bool = False


# ============== vLLM 引擎管理 ==============

class VLLMMultiLoRAEngine:
    """vLLM Multi-LoRA 引擎"""
    
    def __init__(self):
        self.llm: Optional[LLM] = None
        self.lora_registry: Dict[str, LoRAInfo] = {}
        self.lora_id_counter = 1
        self.config = VLLMConfig()
        
    def initialize(self):
        """初始化 vLLM 引擎"""
        if not VLLM_AVAILABLE:
            raise RuntimeError("vLLM 未安装")
        
        print(f"🚀 初始化 vLLM 引擎...")
        print(f"   基座模型: {self.config.BASE_MODEL}")
        print(f"   LoRA 目录: {self.config.LORA_BASE_PATH}")
        
        # 创建 vLLM 引擎
        self.llm = LLM(
            model=self.config.BASE_MODEL,
            **self.config.ENGINE_CONFIG
        )
        
        print(f"✅ vLLM 引擎初始化完成")
        
        # 扫描并注册已有的 LoRA
        self._scan_lora_adapters()
        
    def _scan_lora_adapters(self):
        """扫描并注册所有 LoRA 适配器"""
        lora_base = Path(self.config.LORA_BASE_PATH)
        
        if not lora_base.exists():
            lora_base.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建 LoRA 目录: {lora_base}")
            return
        
        print(f"🔍 扫描 LoRA 适配器...")
        
        for user_dir in lora_base.iterdir():
            if not user_dir.is_dir():
                continue
            
            user_id = user_dir.name
            
            # 查找最新版本
            versions = [d for d in user_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('v')]
            
            if not versions:
                continue
            
            # 按版本号排序，取最新
            latest = sorted(versions, key=lambda x: int(x.name[1:]))[-1]
            final_path = latest / "final"
            
            if final_path.exists():
                lora_name = f"user_{user_id}"
                self.register_lora(
                    name=lora_name,
                    user_id=user_id,
                    path=str(final_path),
                    version=int(latest.name[1:])
                )
        
        print(f"✅ 发现 {len(self.lora_registry)} 个 LoRA 适配器")
    
    def register_lora(self, name: str, user_id: str, path: str, version: int = 1):
        """注册 LoRA 适配器"""
        self.lora_registry[name] = LoRAInfo(
            name=name,
            user_id=user_id,
            path=path,
            version=version,
            created_at=datetime.now().isoformat(),
            is_loaded=False
        )
        print(f"   📦 注册 LoRA: {name} (v{version})")
    
    def get_lora_request(self, user_id: str = None, lora_name: str = None) -> Optional[LoRARequest]:
        """获取 LoRA 请求对象"""
        # 优先使用直接指定的 lora_name
        if lora_name and lora_name in self.lora_registry:
            lora_info = self.lora_registry[lora_name]
        elif user_id:
            # 根据 user_id 查找
            lora_name = f"user_{user_id}"
            if lora_name not in self.lora_registry:
                return None
            lora_info = self.lora_registry[lora_name]
        else:
            return None
        
        # 创建 LoRA 请求
        return LoRARequest(
            lora_name=lora_info.name,
            lora_int_id=hash(lora_info.name) % 10000,  # 生成唯一 ID
            lora_path=lora_info.path
        )
    
    def generate(
        self,
        prompts: List[str],
        user_id: str = None,
        lora_name: str = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 1024,
    ) -> List[str]:
        """生成文本"""
        if self.llm is None:
            raise RuntimeError("引擎未初始化")
        
        # 采样参数
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        
        # 获取 LoRA 请求
        lora_request = self.get_lora_request(user_id, lora_name)
        
        # 生成
        if lora_request:
            outputs = self.llm.generate(
                prompts,
                sampling_params,
                lora_request=lora_request
            )
        else:
            outputs = self.llm.generate(prompts, sampling_params)
        
        # 提取结果
        results = []
        for output in outputs:
            generated_text = output.outputs[0].text
            results.append(generated_text)
        
        return results
    
    def list_loras(self) -> List[LoRAInfo]:
        """列出所有注册的 LoRA"""
        return list(self.lora_registry.values())
    
    def reload_loras(self):
        """重新扫描 LoRA 适配器"""
        self.lora_registry.clear()
        self._scan_lora_adapters()


# ============== FastAPI 应用 ==============

app = FastAPI(
    title="vLLM Multi-LoRA Server",
    description="支持多用户专属 LoRA 的高性能推理服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局引擎实例
engine: Optional[VLLMMultiLoRAEngine] = None


@app.on_event("startup")
async def startup():
    """启动时初始化引擎"""
    global engine
    engine = VLLMMultiLoRAEngine()
    engine.initialize()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "engine": "vllm",
        "lora_count": len(engine.lora_registry) if engine else 0
    }


@app.get("/v1/models")
async def list_models():
    """列出可用模型（OpenAI 兼容）"""
    models = [{"id": "base", "object": "model"}]
    
    if engine:
        for lora in engine.list_loras():
            models.append({
                "id": lora.name,
                "object": "model",
                "user_id": lora.user_id,
                "version": lora.version
            })
    
    return {"object": "list", "data": models}


@app.get("/v1/loras")
async def list_loras():
    """列出所有 LoRA 适配器"""
    if not engine:
        raise HTTPException(status_code=503, detail="引擎未初始化")
    
    return {
        "loras": [lora.dict() for lora in engine.list_loras()],
        "total": len(engine.lora_registry)
    }


@app.post("/v1/loras/reload")
async def reload_loras():
    """重新加载 LoRA 适配器"""
    if not engine:
        raise HTTPException(status_code=503, detail="引擎未初始化")
    
    engine.reload_loras()
    return {"message": "LoRA 适配器已重新加载", "count": len(engine.lora_registry)}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """聊天补全（OpenAI 兼容）"""
    if not engine:
        raise HTTPException(status_code=503, detail="引擎未初始化")
    
    # 构建 prompt（Qwen 格式）
    prompt_parts = []
    for msg in request.messages:
        if msg.role == "system":
            prompt_parts.append(f"<|im_start|>system\n{msg.content}<|im_end|>")
        elif msg.role == "user":
            prompt_parts.append(f"<|im_start|>user\n{msg.content}<|im_end|>")
        elif msg.role == "assistant":
            prompt_parts.append(f"<|im_start|>assistant\n{msg.content}<|im_end|>")
    
    prompt_parts.append("<|im_start|>assistant\n")
    prompt = "\n".join(prompt_parts)
    
    # 生成
    try:
        results = engine.generate(
            prompts=[prompt],
            user_id=request.user_id,
            lora_name=request.lora_name,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
        
        response_text = results[0]
        
        # 清理结束标记
        if "<|im_end|>" in response_text:
            response_text = response_text.split("<|im_end|>")[0]
        
        return {
            "id": f"chatcmpl-{datetime.now().timestamp()}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.lora_name or request.user_id or "base",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text.strip()
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(response_text) // 4,
                "total_tokens": (len(prompt) + len(response_text)) // 4
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """文本补全"""
    if not engine:
        raise HTTPException(status_code=503, detail="引擎未初始化")
    
    try:
        results = engine.generate(
            prompts=[request.prompt],
            user_id=request.user_id,
            lora_name=request.lora_name,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
        
        return {
            "id": f"cmpl-{datetime.now().timestamp()}",
            "object": "text_completion",
            "created": int(datetime.now().timestamp()),
            "model": request.lora_name or request.user_id or "base",
            "choices": [{
                "text": results[0],
                "index": 0,
                "finish_reason": "stop"
            }]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate_simple(
    prompt: str,
    user_id: str = None,
    lora_name: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1024
):
    """简单生成接口"""
    if not engine:
        raise HTTPException(status_code=503, detail="引擎未初始化")
    
    results = engine.generate(
        prompts=[prompt],
        user_id=user_id,
        lora_name=lora_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return {
        "text": results[0],
        "user_id": user_id,
        "lora_used": lora_name or (f"user_{user_id}" if user_id else None)
    }


# ============== 主函数 ==============

def main():
    """启动服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="vLLM Multi-LoRA Server")
    parser.add_argument("--host", default="0.0.0.0", help="服务地址")
    parser.add_argument("--port", type=int, default=8000, help="服务端口")
    parser.add_argument("--model", default=None, help="基座模型")
    
    args = parser.parse_args()
    
    if args.model:
        os.environ["BASE_MODEL"] = args.model
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║           vLLM Multi-LoRA Server                             ║
║           多用户专属 LoRA 高性能推理服务                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "gpu_server.vllm_multi_lora_server:app",
        host=args.host,
        port=args.port,
        reload=False,
        workers=1
    )


if __name__ == "__main__":
    main()
