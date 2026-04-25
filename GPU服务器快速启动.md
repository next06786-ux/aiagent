# GPU服务器快速启动指南

## 服务器信息
- **外部访问地址**: https://u821458-b49a-bdca5515.westc.seetacloud.com:8443
- **容器内端口**: 6006
- **外部映射端口**: 8443
- **模型路径**: /root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt

---

## 在GPU服务器上执行

### 1. 安装依赖
```bash
pip install fastapi uvicorn torch transformers accelerate python-dotenv pydantic httpx
```

### 2. 启动模型服务
```bash
cd /root/autodl-tmp/aiagent
export LOCAL_QUANTIZED_MODEL_PATH=/root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt

python -m backend.llm.remote_model_server \
  --host 0.0.0.0 \
  --port 6006 \
  --model-path /root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt
```

### 3. 配置AutoDL端口映射 ⚠️ 重要
在AutoDL控制台配置端口映射：
1. 登录 [AutoDL控制台](https://www.autodl.com/console/instance/list)
2. 找到你的实例，点击"自定义服务"
3. 添加端口映射：
   - **容器端口**: 6006
   - **外部端口**: 8443
4. 保存后等待几秒钟生效

### 4. 测试连接
```bash
# 在GPU服务器上测试（内网）
curl http://localhost:6006/health

# 在本地测试（外网，需要-k跳过证书验证）
curl -k https://u821458-b49a-bdca5515.westc.seetacloud.com:8443/health
```

---

## 在本地项目中使用

### 1. 环境变量已配置（.env）
```bash
REMOTE_MODEL_URL=https://u821458-b49a-bdca5515.westc.seetacloud.com:8443
```

### 2. 重启后端容器
```bash
docker compose restart backend
```

### 3. 在前端界面切换模型
访问 http://localhost:3000 -> AI核心对话 -> 点击模型选择器 -> 选择"本地量化模型"

### 4. 或通过API切换
```bash
curl -X POST http://localhost:8000/api/llm/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "local_quantized"}'
```

---

## 故障排查

### 问题1: 连接超时或404
**原因**: AutoDL端口映射未配置或配置错误

**解决**:
1. 检查AutoDL控制台的"自定义服务"配置
2. 确保容器端口是 **6006**，外部端口是 **8443**
3. 保存后等待30秒生效

### 问题2: 模型加载失败
**原因**: 模型文件路径不正确

**解决**:
```bash
# 检查模型文件是否存在
ls -lh /root/autodl-tmp/quarot_qwen3-8b_w4a16kv16_s50.pt

# 应该显示约15GB的文件
```

### 问题3: 前端无法切换模型
**原因**: 后端容器未读取到新的环境变量

**解决**:
```bash
# 重新构建并启动后端
docker compose build backend
docker compose up -d backend

# 查看日志确认连接状态
docker compose logs -f backend | grep -i "remote\|quantized"
```

---

## 快速命令

### GPU服务器端
```bash
# 一键启动
cd /root/autodl-tmp/aiagent && bash GPU服务器部署脚本.sh
```

### 本地端
```bash
# 测试连接
python test_remote_connection.py

# 或使用shell脚本
bash test_gpu_connection.sh

# 重启后端
docker compose restart backend
```
