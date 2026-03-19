# 🚀 项目部署指南：本地 → GitHub → GPU服务器

## 概览

```
本地开发机 ──push──> GitHub ──pull──> AutoDL GPU服务器
     │                                      │
     └── 代码同步 ──────────────────────────┘
```

---

## SGLang 推理服务器部署（推荐）

### 启动 SGLang 服务器（在 AutoDL GPU 上）

```bash
# 设置环境变量
export HF_HOME=/root/autodl-tmp/huggingface
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=0

# 启动 SGLang（基础模式）
python -m sglang.launch_server \
  --model-path Qwen/Qwen3.5-9B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --mem-fraction-static 0.8 \
  --context-length 32768 \
  --reasoning-parser qwen3 \
  --download-dir /root/autodl-tmp/huggingface

# 启动 SGLang（带 LoRA 支持）
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

### 后端配置（本地或服务器）

在 `backend/.env` 中配置：

```bash
# 使用 SGLang 作为 LLM 提供商
LLM_PROVIDER=sglang
SGLANG_SERVER_URL=http://YOUR_GPU_SERVER_IP:8000
SGLANG_MODEL_NAME=Qwen/Qwen3.5-9B
```

### 测试 SGLang 连接

```bash
# 测试健康检查
curl http://YOUR_GPU_SERVER_IP:8000/health

# 测试聊天
curl http://YOUR_GPU_SERVER_IP:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-9B",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

---

## 第一步：本地推送到 GitHub

### 1.1 首次设置（如果还没有仓库）

```bash
# 在项目根目录执行
cd /path/to/your/project

# 初始化 Git（如果还没有）
git init

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 或使用 SSH
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
```

### 1.2 日常推送代码

```bash
# 查看修改状态
git status

# 添加所有修改
git add .

# 提交（写清楚改了什么）
git commit -m "feat: 添加 vLLM Multi-LoRA 支持"

# 推送到 GitHub
git push origin main
```

### 1.3 快捷命令（一键推送）

```bash
# Windows PowerShell
git add . ; git commit -m "update" ; git push origin main

# Linux/Mac
git add . && git commit -m "update" && git push origin main
```

---

## 第二步：GPU服务器拉取代码

### 2.1 首次克隆（在 AutoDL 服务器上）

```bash
# SSH 连接到 AutoDL
ssh -p PORT root@YOUR_SERVER_IP

# 进入工作目录
cd /root

# 克隆仓库
git clone https://github.com/next06786-ux/aiagent.git

# 或使用 SSH（需要配置 SSH Key）
git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git

# 进入项目目录
cd YOUR_REPO
```

### 2.2 日常更新代码

```bash
# 进入项目目录
cd /root/YOUR_REPO

# 拉取最新代码
git pull origin main
```

### 2.3 配置 Git（首次需要）

```bash
# 设置用户信息
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# 保存凭证（避免每次输入密码）
git config --global credential.helper store
```

---

## 第三步：GPU服务器环境配置

### 3.1 一键部署脚本

```bash
# 进入项目目录
cd /root/YOUR_REPO

# 运行 vLLM 环境配置
bash gpu_server/setup_vllm.sh

# 或运行完整环境配置
bash gpu_server/setup_gpu_env.sh
```

### 3.2 启动服务

```bash
# 前台运行（调试用）
python gpu_server/vllm_multi_lora_server.py

# 后台运行（生产用）
nohup python gpu_server/vllm_multi_lora_server.py > /root/autodl-tmp/logs/vllm.log 2>&1 &

# 查看日志
tail -f /root/autodl-tmp/logs/vllm.log
```

---

## 完整流程示例

### 场景：修改代码后部署到GPU服务器

```bash
# ===== 本地操作 =====
# 1. 修改代码...

# 2. 提交并推送
git add .
git commit -m "fix: 修复 LoRA 加载问题"
git push origin main

# ===== GPU服务器操作 =====
# 3. SSH 连接服务器
ssh -p 12345 root@123.456.789.0

# 4. 拉取最新代码
cd /root/lifeswarm
git pull origin main

# 5. 重启服务
pkill -f vllm_multi_lora_server  # 停止旧服务
nohup python gpu_server/vllm_multi_lora_server.py > /root/autodl-tmp/logs/vllm.log 2>&1 &
```

---

## 常用命令速查

### Git 命令

| 命令 | 说明 |
|------|------|
| `git status` | 查看修改状态 |
| `git add .` | 添加所有修改 |
| `git commit -m "msg"` | 提交修改 |
| `git push origin main` | 推送到远程 |
| `git pull origin main` | 拉取最新代码 |
| `git log --oneline -5` | 查看最近5条提交 |
| `git diff` | 查看未暂存的修改 |

### 服务器命令

| 命令 | 说明 |
|------|------|
| `nvidia-smi` | 查看 GPU 状态 |
| `ps aux \| grep python` | 查看 Python 进程 |
| `pkill -f vllm` | 停止 vLLM 服务 |
| `tail -f logs/vllm.log` | 实时查看日志 |
| `df -h` | 查看磁盘空间 |
| `free -h` | 查看内存使用 |

---

## 注意事项

1. **不要提交敏感信息**：`.env` 文件已在 `.gitignore` 中，不会被提交
2. **大文件不要提交**：模型文件、数据库文件等已被忽略
3. **服务器上的数据**：用户数据存储在 `/root/autodl-tmp/`，不会被 git 覆盖
4. **AutoDL 关机**：关机前数据会保留在 `/root/autodl-tmp/`，但 `/root/` 下的代码可能丢失，建议用 `autodl-tmp` 存储重要数据
