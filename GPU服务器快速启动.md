# GPU服务器快速启动指南

## 在GPU服务器上执行（https://u821458-b49a-bdca5515.westc.seetacloud.com:8443）

### 1. 安装依赖
```bash
pip install fastapi uvicorn torch transformers accelerate
```

### 2. 启动模型服务
```bash
cd /root/your-project-path
export LOCAL_QUANTIZED_MODEL_PATH=/root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt
python -m backend.llm.remote_model_server --host 0.0.0.0 --port 8001 --model-path /root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt
```

### 3. 配置端口映射
在服务器控制台添加端口映射：
- 内部端口：8001
- 外部端口：8443（或其他可用端口）

### 4. 测试连接
```bash
curl https://u821458-b49a-bdca5515.westc.seetacloud.com:8443/health
```

## 在本地项目中使用

### 1. 已配置环境变量（.env）
```
REMOTE_MODEL_URL=https://u821458-b49a-bdca5515.westc.seetacloud.com:8443
```

### 2. 在AI核心对话界面选择"远程基座模型"

### 3. 或通过API切换
```bash
curl -X POST http://localhost:8000/api/llm/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "remote_model"}'
```

## 验证
访问 http://localhost:3000 -> AI核心 -> 模型选择器 -> 选择"远程基座模型"
