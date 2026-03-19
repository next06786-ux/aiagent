# GPU服务器完整部署指南

## 概述

本指南介绍如何将整个LifeSwarm后端系统部署到GPU服务器（如AutoDL），实现：
- 完整的后端API服务
- GPU加速的LoRA训练
- 本地大模型推理
- RAG知识库系统

## 服务器要求

### 推荐配置
- **GPU**: NVIDIA GPU，显存 ≥16GB（推荐32GB）
- **内存**: ≥32GB
- **存储**: ≥100GB（数据盘）
- **系统**: Ubuntu 20.04/22.04

### AutoDL推荐镜像
- PyTorch 2.1 + CUDA 12.1
- 或 PyTorch 2.0 + CUDA 11.8

## 快速部署

### 1. 上传项目代码

```bash
# 方式1: 使用scp
scp -r ./* root@your-server:/root/autodl-tmp/lifeswarm/

# 方式2: 使用git
cd /root/autodl-tmp
git clone your-repo-url lifeswarm
```

### 2. 运行部署脚本

```bash
cd /root/autodl-tmp/lifeswarm
bash gpu_server/deploy_full_backend.sh
```

### 3. 下载模型

```bash
# 查看可用模型
python gpu_server/download_models.py list

# 下载推荐模型（自动根据显存选择）
python gpu_server/download_models.py recommended

# 或下载指定模型
python gpu_server/download_models.py download --model qwen2.5-7b
```

### 4. 配置环境变量

```bash
vim /root/autodl-tmp/.env.gpu
```

关键配置项：
```bash
# LLM配置
LLM_PROVIDER=local  # 使用本地模型
LOCAL_MODEL_PATH=/root/autodl-tmp/models/base/qwen2.5-7b

# 或使用API
# LLM_PROVIDER=dashscope
# DASHSCOPE_API_KEY=your-api-key

# 安全配置（必须修改！）
API_KEY=your-secure-api-key
JWT_SECRET=your-jwt-secret
```

### 5. 启动服务

```bash
# 前台运行（调试用）
bash /root/autodl-tmp/start_backend.sh

# 后台运行（生产用）
bash /root/autodl-tmp/start_backend_daemon.sh
```

### 6. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
# 浏览器访问: http://your-server:8000/docs
```

## 目录结构

```
/root/autodl-tmp/                    # 数据盘（关机后保留）
├── lifeswarm/                       # 项目代码
│   ├── backend/                     # 后端代码
│   ├── gpu_server/                  # GPU服务器专用代码
│   └── ...
├── models/                          # 模型文件
│   ├── base/                        # 基座模型
│   │   ├── qwen2.5-7b/
│   │   └── embedding/
│   └── lora/                        # 用户LoRA模型
│       └── {user_id}/
│           └── v1/
├── data/                            # 数据文件
│   ├── database/                    # SQLite数据库
│   ├── rag/                         # RAG向量库
│   ├── knowledge_graph/             # 知识图谱
│   ├── decisions/                   # 决策记录
│   └── decision_sessions/           # 决策会话
├── logs/                            # 日志文件
│   ├── backend.log
│   └── monitor.json
├── .env.gpu                         # 环境配置
├── start_backend.sh                 # 启动脚本
├── start_backend_daemon.sh          # 后台启动脚本
└── stop_backend.sh                  # 停止脚本
```

## 常用命令

### 服务管理

```bash
# 启动服务
bash /root/autodl-tmp/start_backend_daemon.sh

# 停止服务
bash /root/autodl-tmp/stop_backend.sh

# 重启服务
bash /root/autodl-tmp/stop_backend.sh && bash /root/autodl-tmp/start_backend_daemon.sh

# 查看日志
tail -f /root/autodl-tmp/logs/backend.log
```

### 监控

```bash
# 查看GPU状态
nvidia-smi

# 查看服务状态
python gpu_server/health_monitor.py status

# 持续监控
python gpu_server/health_monitor.py watch

# 后台监控
python gpu_server/health_monitor.py daemon
```

### 模型管理

```bash
# 列出模型
python gpu_server/download_models.py list

# 下载模型
python gpu_server/download_models.py download --model qwen2.5-14b

# 下载所有模型
python gpu_server/download_models.py download --all
```

## API端点

### 核心API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/v4/chat` | POST | AI对话 |
| `/api/v4/chat/stream` | WebSocket | 流式对话 |

### 决策系统API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/decision/quick` | POST | 快速决策 |
| `/api/decision/enhanced/start` | POST | 增强决策-开始 |
| `/api/decision/enhanced/answer` | POST | 增强决策-回答 |
| `/api/decision/enhanced/result` | GET | 增强决策-结果 |
| `/api/decision/parallel-universe` | POST | 平行宇宙模拟 |

### LoRA训练API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/lora/status/{user_id}` | GET | 训练状态 |
| `/api/lora/train/{user_id}` | POST | 触发训练 |

## 性能优化

### 显存优化

```python
# 在 .env.gpu 中配置
USE_4BIT=true      # 启用4bit量化（节省显存）
USE_8BIT=false     # 或使用8bit量化
```

### 模型选择

| 显存 | 推荐模型 | 量化 |
|------|----------|------|
| 8GB | qwen2.5-3b | 4bit |
| 16GB | qwen2.5-7b | 无 |
| 24GB | qwen2.5-14b | 4bit |
| 32GB | qwen2.5-14b | 无 |

### 批处理优化

```python
# 根据显存调整批处理大小
# 在 gpu_config.py 中自动配置
```

## 故障排除

### 服务无法启动

```bash
# 检查端口占用
lsof -i :8000

# 检查日志
tail -100 /root/autodl-tmp/logs/backend.log

# 检查Python环境
python -c "import torch; print(torch.cuda.is_available())"
```

### GPU内存不足

```bash
# 清理GPU缓存
python -c "import torch; torch.cuda.empty_cache()"

# 使用更小的模型或启用量化
# 修改 .env.gpu:
# DEFAULT_MODEL=qwen2.5-3b
# USE_4BIT=true
```

### 模型加载失败

```bash
# 检查模型文件
ls -la /root/autodl-tmp/models/base/

# 重新下载模型
python gpu_server/download_models.py download --model qwen2.5-7b --force
```

## 成本优化

### AutoDL使用建议

1. **开发测试**: 用完即关机，按小时计费
2. **演示展示**: 提前10分钟开机预热模型
3. **长期运行**: 考虑包周/包月方案
4. **数据保存**: 所有数据存放在 `/root/autodl-tmp/`，关机后保留

### 关机前检查

```bash
# 确保数据已保存
ls -la /root/autodl-tmp/data/

# 停止服务
bash /root/autodl-tmp/stop_backend.sh
```

## 安全建议

1. **修改默认密钥**: 必须修改 `.env.gpu` 中的 `API_KEY` 和 `JWT_SECRET`
2. **限制访问**: 使用AutoDL的安全组限制IP访问
3. **定期备份**: 定期备份 `/root/autodl-tmp/data/` 目录
4. **日志监控**: 定期检查日志文件

## 更新部署

```bash
cd /root/autodl-tmp/lifeswarm

# 拉取最新代码
git pull

# 重新安装依赖（如有更新）
pip install -r requirements.txt

# 重启服务
bash /root/autodl-tmp/stop_backend.sh
bash /root/autodl-tmp/start_backend_daemon.sh
```

## 联系支持

如有问题，请检查：
1. 日志文件: `/root/autodl-tmp/logs/backend.log`
2. 监控状态: `python gpu_server/health_monitor.py status`
3. GPU状态: `nvidia-smi`
