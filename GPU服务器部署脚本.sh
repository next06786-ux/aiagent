#!/bin/bash
# GPU服务器部署脚本 - 在 https://u821458-b49a-bdca5515.westc.seetacloud.com:8443 上运行

# 1. 安装依赖
pip install fastapi uvicorn torch transformers accelerate python-dotenv pydantic

# 2. 设置环境变量
export LOCAL_QUANTIZED_MODEL_PATH=/root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt

# 3. 启动远程模型服务器（监听8001端口）
cd /root/autodl-tmp/aiagent
python -m backend.llm.remote_model_server --host 0.0.0.0 --port 8001 --model-path /root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt

# 注意：需要在服务器控制台添加端口映射 8001 -> 8443
