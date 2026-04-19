# GPU 服务器部署指南 (SGLang)

## 快速开始

### 1. 设置环境变量

```bash
export HF_HOME=/root/autodl-tmp/huggingface
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0
```

### 2. 安装 SGLang

```bash
pip install sglang[all] -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 启动服务器

```bash
# 使用启动脚本
python gpu_server/start_server.py

# 或直接使用 SGLang 命令
python -m sglang.launch_server \
  --model-path Qwen/Qwen3.5-9B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --mem-fraction-static 0.8 \
  --context-length 32768 \
  --reasoning-parser qwen3 \
  --download-dir /root/autodl-tmp/huggingface
```

### 4. 启用 LoRA 支持

```bash
python gpu_server/start_server.py --enable-lora

# 或手动指定
python -m sglang.launch_server \
  --model-path Qwen/Qwen3.5-9B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --mem-fraction-static 0.8 \
  --context-length 32768 \
  --reasoning-parser qwen3 \
  --download-dir /root/autodl-tmp/huggingface \
  --max-lora-rank 64 \
  --lora-target-modules q_proj,k_proj,v_proj,o_proj
```

## 可用模型

| 模型 | 显存需求 | 说明 |
|------|----------|------|
| qwen3.5-9b | 20 GB | 主力模型，推荐 |
| qwen3.5-0.8b | 2 GB | 轻量模型 |

## 测试连接

```bash
# 健康检查
curl http://localhost:8000/health

# 测试聊天
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-9B",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

## 后端配置

在 `backend/.env` 中设置：

```bash
LLM_PROVIDER=sglang
SGLANG_SERVER_URL=http://localhost:8000
SGLANG_MODEL_NAME=Qwen/Qwen3.5-9B
```

## 目录结构

```
/root/autodl-tmp/
├── huggingface/     # HuggingFace 模型缓存
├── models/
│   ├── base/        # 基座模型
│   └── lora/        # 用户 LoRA 适配器
├── data/
│   ├── database/    # 数据库文件
│   └── rag/         # RAG 数据
└── logs/            # 日志文件
```
