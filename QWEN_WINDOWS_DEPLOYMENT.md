# Qwen 模型 Windows 部署指南

## 问题诊断

你遇到的错误 `ModuleNotFoundError: No module named 'vllm._C'` 是因为 vLLM 在 Windows 上的 C++ 扩展编译失败。

vLLM 主要针对 Linux 优化，Windows 支持不完善。

---

## 解决方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Ollama** | 安装简单，开箱即用，Windows支持好 | 功能相对简单 | ⭐⭐⭐⭐⭐ |
| **Transformers + FastAPI** | 完全控制，灵活性高，支持LoRA训练 | 需要手动编写服务器代码 | ⭐⭐⭐⭐ |
| **llama.cpp** | 轻量级，速度快 | 需要转换模型格式(GGUF) | ⭐⭐⭐ |
| **vLLM (WSL)** | 性能最好 | 需要WSL，配置复杂 | ⭐⭐ |

---

## 方案1: Ollama（最推荐）

### 安装步骤

1. **下载 Ollama for Windows**
   ```
   访问: https://ollama.com/download/windows
   下载并安装 OllamaSetup.exe
   ```

2. **运行 Qwen 模型**
   ```powershell
   # 拉取并运行 Qwen2.5-0.5B
   ollama run qwen2.5:0.5b
   
   # 或者后台运行服务
   ollama serve
   ```

3. **测试 API**
   ```powershell
   # 测试对话
   curl http://localhost:11434/api/generate -d '{
     "model": "qwen2.5:0.5b",
     "prompt": "你好，请介绍一下你自己",
     "stream": false
   }'
   ```

### 集成到后端

修改 `backend/llm/llm_service.py`:

```python
import requests

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
    
    def chat(self, messages, model="qwen2.5:0.5b"):
        """OpenAI 兼容的聊天接口"""
        # 构建 prompt
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"{role}: {content}\n"
        
        # 调用 Ollama API
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        return response.json()["response"]
```

---

## 方案2: Transformers + FastAPI（最灵活）

### 优势
- 完全控制模型加载和推理
- 支持 LoRA 训练和加载
- 可以自定义 API 接口
- 与你的 LoRA 训练系统完美集成

### 使用方法

1. **启动服务器**
   ```powershell
   # 双击运行
   start_qwen_server.bat
   
   # 或者命令行
   conda activate pytorch
   python backend/llm/local_qwen_server.py
   ```

2. **测试服务器**
   ```powershell
   python test_local_qwen.py
   ```

3. **集成到主系统**
   
   修改 `backend/llm/llm_service.py`:
   ```python
   import requests
   
   class LocalQwenClient:
       def __init__(self, base_url="http://localhost:8000"):
           self.base_url = base_url
       
       def chat(self, messages, temperature=0.7, max_tokens=2048):
           """OpenAI 兼容的聊天接口"""
           response = requests.post(
               f"{self.base_url}/v1/chat/completions",
               json={
                   "model": "qwen3.5-0.8b",
                   "messages": messages,
                   "temperature": temperature,
                   "max_tokens": max_tokens
               }
           )
           
           result = response.json()
           return result["choices"][0]["message"]["content"]
   ```

### 支持 LoRA 加载

修改 `backend/llm/local_qwen_server.py`，添加 LoRA 支持:

```python
from peft import PeftModel

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, user_id: str = None):
    """支持 LoRA 的聊天接口"""
    
    # 如果指定了 user_id，尝试加载用户的 LoRA
    current_model = model
    
    if user_id:
        lora_path = f"./models/lora/{user_id}/latest"
        if os.path.exists(lora_path):
            print(f"📥 加载用户 {user_id} 的 LoRA 模型")
            current_model = PeftModel.from_pretrained(model, lora_path)
    
    # 生成回复（使用 current_model）
    # ... 其余代码不变
```

---

## 方案3: llama.cpp

### 安装步骤

1. **下载预编译版本**
   ```
   访问: https://github.com/ggerganov/llama.cpp/releases
   下载 llama-<version>-bin-win-cuda-cu12.2.0-x64.zip
   ```

2. **下载 GGUF 格式模型**
   ```
   访问: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
   下载 qwen2.5-0.5b-instruct-q4_0.gguf
   ```

3. **启动服务器**
   ```powershell
   llama-server.exe -m qwen2.5-0.5b-instruct-q4_0.gguf --port 8000 --ctx-size 32768
   ```

---

## 推荐配置

### 开发阶段（现在）
使用 **Transformers + FastAPI** 方案:
- ✅ 完全控制
- ✅ 支持 LoRA 训练
- ✅ 易于调试
- ✅ 与现有代码集成好

### 比赛演示阶段
使用 **Ollama** 方案:
- ✅ 稳定可靠
- ✅ 安装简单
- ✅ 性能足够
- ✅ 不容易出问题

### 生产部署阶段
迁移到 **Linux + vLLM**:
- ✅ 性能最优
- ✅ 支持批处理
- ✅ 支持张量并行
- ✅ 成熟稳定

---

## 性能对比（RTX 3050）

| 方案 | 推理速度 | 显存占用 | 启动时间 |
|------|----------|----------|----------|
| Ollama | 40-60 tokens/s | ~2.5GB | 5秒 |
| Transformers (Qwen3.5-0.8B) | 35-50 tokens/s | ~2GB | 10秒 |
| llama.cpp | 50-70 tokens/s | ~1.5GB | 3秒 |
| vLLM (Linux) | 80-100 tokens/s | ~2GB | 15秒 |

---

## 下一步操作

### 立即可做的:

1. **安装 Ollama**（5分钟）
   - 下载安装包
   - 运行 `ollama run qwen2.5:0.5b`
   - 测试 API

2. **或者使用 Transformers 方案**（10分钟）
   - 运行 `start_qwen_server.bat`
   - 运行 `python test_local_qwen.py`
   - 验证功能

### 后续集成:

3. **集成到主系统**
   - 修改 `backend/llm/llm_service.py`
   - 修改 `backend/conversation/simple_streaming.py`
   - 测试对话功能

4. **实现 LoRA 训练**
   - 创建 `backend/lora/auto_lora_trainer.py`
   - 实现自动训练逻辑
   - 测试训练流程

5. **前端展示**
   - 创建训练状态页面
   - 显示模型版本
   - 手动触发训练按钮

---

## 常见问题

### Q: Qwen2.5-0.5B 和 Qwen3.5-0.8B 哪个好？
A: Qwen3.5-0.8B 更新更强，参数更多（0.8B vs 0.5B），推理速度相近，显存占用略高（2GB vs 1.5GB）。如果你在 2026-03-16 有 Qwen3.5-0.8B，优先使用它。

### Q: 必须用 vLLM 吗？
A: 不必须。Transformers 方案完全够用，而且更灵活，支持 LoRA 训练。

### Q: LoRA 训练必须在 GPU 上吗？
A: 是的，CPU 训练太慢（几小时）。RTX 3050 训练 10 分钟完全可行。

### Q: 能在移动端训练吗？
A: 不能。移动端算力不足，而且会严重发热和耗电。必须在 PC 或服务器上训练。

---

## 总结

**当前最佳方案**: 使用 Transformers + FastAPI

**理由**:
1. Windows 兼容性好
2. 支持 LoRA 训练和加载
3. 完全控制，易于调试
4. 与你的系统架构完美契合
5. RTX 3050 性能足够

**操作步骤**:
```powershell
# 1. 启动 Qwen 服务器
start_qwen_server.bat

# 2. 测试服务器
python test_local_qwen.py

# 3. 集成到主系统
# 修改 backend/llm/llm_service.py

# 4. 实现 LoRA 训练
# 创建 backend/lora/auto_lora_trainer.py
```

现在就可以开始了！
