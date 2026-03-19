"""
本地 Qwen 模型服务器
使用 Transformers 库直接加载模型，提供 OpenAI 兼容的 API
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
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
    """启动时加载模型"""
    global model, tokenizer
    
    model_name = get_model_hf_name()
    model_config = get_current_model_config()
    
    print(f"正在加载模型: {model_name}")
    print(f"显示名称: {model_config['display_name']}")
    print(f"预计显存占用: {model_config['vram_required']} GB")
    print(f"预计推理速度: {model_config['inference_speed']} tokens/s")
    
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    
    # 加载模型到 GPU
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    
    print(f"模型加载完成，使用设备: {model.device}")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI 兼容的聊天接口"""
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
        
        # 生成回复（优化版）
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,  # 限制候选词数量，加速采样
                repetition_penalty=1.1,  # 减少重复
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True  # 使用 KV cache 加速
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
        "model_loaded": model is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
