"""
优化版本地 Qwen 模型服务器
针对 RTX 3050 优化，提升推理速度
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import uvicorn
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.model_config import get_model_hf_name, get_current_model_config

app = FastAPI()

# 全局模型和分词器
model = None
tokenizer = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "qwen3.5-0.8b"
    messages: List[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False

class ChatResponse(BaseModel):
    id: str = "chatcmpl-local"
    object: str = "chat.completion"
    created: int = 0
    model: str = "qwen3.5-0.8b"
    choices: List[dict]

@app.on_event("startup")
async def load_model():
    """启动时加载模型（优化版）"""
    global model, tokenizer
    
    model_name = get_model_hf_name()
    model_config = get_current_model_config()
    
    print(f"正在加载模型: {model_name}")
    print(f"显示名称: {model_config['display_name']}")
    print(f"预计显存占用: {model_config['vram_required']} GB")
    print(f"预计推理速度: {model_config['inference_speed']} tokens/s")
    print()
    print("🚀 性能优化:")
    print("  - 使用 float16 精度")
    print("  - 启用 KV cache")
    print("  - 优化采样参数")
    print("  - 降低内存占用")
    print()
    
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    
    # 加载模型（优化配置，降低内存占用）
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        dtype=torch.float16,  # 使用 dtype 替代 torch_dtype
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,  # 降低 CPU 内存使用
        max_memory={0: "3GB", "cpu": "4GB"}  # 限制显存和内存使用
    )
    
    # 设置为评估模式
    model.eval()
    
    print()
    print(f"✅ 模型加载完成，使用设备: {model.device}")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI 兼容的聊天接口（优化版）"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        # 构建对话历史
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 应用聊天模板
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 编码输入
        inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        # 优化的生成参数
        gen_kwargs = {
            "max_new_tokens": min(request.max_tokens, 512),  # 限制最大长度
            "temperature": request.temperature,
            "do_sample": request.temperature > 0,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.05,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "use_cache": True,  # 启用 KV cache
        }
        
        # 如果温度为 0，使用贪婪解码（更快）
        if request.temperature == 0:
            gen_kwargs["do_sample"] = False
            gen_kwargs.pop("temperature", None)
            gen_kwargs.pop("top_p", None)
            gen_kwargs.pop("top_k", None)
        
        # 生成回复
        with torch.no_grad():
            with torch.cuda.amp.autocast():  # 自动混合精度
                outputs = model.generate(
                    **inputs,
                    **gen_kwargs
                )
        
        # 解码输出
        response_text = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )
        
        # 返回 OpenAI 格式的响应
        return ChatResponse(
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """列出可用模型"""
    return {
        "object": "list",
        "data": [{
            "id": "qwen3.5-0.8b",
            "object": "model",
            "created": 0,
            "owned_by": "local"
        }]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "device": str(model.device) if model else None,
        "dtype": str(model.dtype) if model else None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
