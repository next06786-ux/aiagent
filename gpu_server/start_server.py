#!/usr/bin/env python3
"""
GPU 服务器统一启动脚本
使用 Transformers + FastAPI 提供推理服务
"""
import os
import sys
import argparse
import signal
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_environment():
    """设置环境变量"""
    env_vars = {
        "HF_ENDPOINT": "https://hf-mirror.com",
        "HF_HUB_ENABLE_HF_TRANSFER": "0",
    }
    
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        env_vars["HF_HOME"] = hf_home
    
    for key, value in env_vars.items():
        os.environ.setdefault(key, value)
    
    print("✓ 环境变量已设置:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")


def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██╗     ██╗███████╗███████╗███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗    ║
║     ██║     ██║██╔════╝██╔════╝██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║    ║
║     ██║     ██║█████╗  █████╗  ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║    ║
║     ██║     ██║██╔══╝  ██╔══╝  ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║    ║
║     ███████╗██║██║     ███████╗███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║    ║
║     ╚══════╝╚═╝╚═╝     ╚══════╝╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝    ║
║                                                                  ║
║                 Transformers GPU Server                          ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def start_inference_server(model: str = None, port: int = 8000, quantize: bool = False):
    """
    启动 Transformers 推理服务器
    
    使用 FastAPI 包装 Transformers 模型，提供 OpenAI 兼容 API
    """
    import torch
    import uvicorn
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import List, Optional
    
    sys.path.insert(0, str(PROJECT_ROOT))
    from backend.llm.model_config import get_model_hf_name, get_inference_config, get_quantization_config
    
    model_name = model or get_model_hf_name()
    inference_cfg = get_inference_config()
    
    print(f"🚀 启动 Transformers 推理服务器...")
    print(f"  模型: {model_name}")
    print(f"  端口: {port}")
    print(f"  量化: {'启用' if quantize else '禁用'}")
    print()
    
    # 加载模型
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    load_kwargs = {
        "trust_remote_code": True,
        "device_map": "auto",
    }
    
    if quantize:
        from transformers import BitsAndBytesConfig
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        print("  使用 4-bit NF4 量化加载模型")
    else:
        load_kwargs["torch_dtype"] = torch.float16
    
    print(f"  正在加载模型 {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model_instance = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
    model_instance.eval()
    print(f"  ✓ 模型加载完成")
    
    # 创建 FastAPI 应用
    app = FastAPI(title="LifeSwarm Inference Server")
    
    class ChatMessage(BaseModel):
        role: str
        content: str
    
    class ChatRequest(BaseModel):
        model: str = model_name
        messages: List[ChatMessage]
        temperature: float = 0.7
        max_tokens: int = 2048
        top_p: float = 0.9
        stream: bool = False
    
    class ChatChoice(BaseModel):
        index: int = 0
        message: ChatMessage
        finish_reason: str = "stop"
    
    class ChatResponse(BaseModel):
        id: str = "chatcmpl-local"
        object: str = "chat.completion"
        choices: List[ChatChoice]
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "model": model_name}
    
    @app.post("/v1/chat/completions")
    async def chat_completions(request: ChatRequest):
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model_instance.device)
        
        with torch.no_grad():
            outputs = model_instance.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=max(request.temperature, 0.01),
                top_p=request.top_p,
                do_sample=True,
            )
        
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        response_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return ChatResponse(
            choices=[ChatChoice(message=ChatMessage(role="assistant", content=response_text))]
        )
    
    print(f"\n🌐 服务器启动在 http://0.0.0.0:{port}")
    print(f"   API: http://0.0.0.0:{port}/v1/chat/completions")
    print(f"   健康检查: http://0.0.0.0:{port}/health\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LifeSwarm Transformers Inference Server")
    parser.add_argument("--model", default=None, help="HuggingFace 模型名称 (默认: Qwen/Qwen3.5-9B)")
    parser.add_argument("--port", type=int, default=8000, help="服务端口 (默认: 8000)")
    parser.add_argument("--quantize", action="store_true", help="启用 4-bit 量化")
    parser.add_argument("--show-config", action="store_true", help="仅显示配置")
    
    args = parser.parse_args()
    
    # 打印横幅
    print_banner()
    
    # 设置环境
    setup_environment()
    
    # 仅显示配置
    if args.show_config:
        from backend.llm.model_config import (
            get_current_model_config, get_inference_config, get_quantization_config
        )
        model_cfg = get_current_model_config()
        print("\n📋 模型配置:")
        for key, value in model_cfg.items():
            print(f"  {key}: {value}")
        print("\n📋 推理配置:")
        for key, value in get_inference_config().items():
            print(f"  {key}: {value}")
        print("\n📋 量化配置:")
        for key, value in get_quantization_config().items():
            print(f"  {key}: {value}")
        return
    
    # 信号处理
    def signal_handler(sig, frame):
        print("\n🛑 收到停止信号，正在关闭...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动服务
    try:
        start_inference_server(
            model=args.model,
            port=args.port,
            quantize=args.quantize
        )
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
