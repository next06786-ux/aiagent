# LifeSwarm 后端系统启动指南

## 系统架构概览

LifeSwarm 是一个多层次的智能生活助手系统，包含以下核心组件：

```
┌─────────────────────────────────────────────────────────┐
│                    HarmonyOS 前端应用                      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI 后端服务                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   LLM服务    │  │  多模态融合   │  │  知识图谱    │  │
│  │  (Qwen)      │  │  (感知层)    │  │  (Neo4j)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  RAG系统     │  │  强化学习    │  │  涌现检测    │  │
│  │  (记忆)      │  │  (优化)      │  │  (预测)      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼──┐    ┌───▼──┐    ┌───▼──┐
    │Neo4j │    │ PostgreSQL │ Redis │
    │      │    │            │      │
    └──────┘    └────────────┘ └──────┘
```

## 前置要求

### 1. Python 环境
- Python 3.8 或更高版本
- pip 包管理器

### 2. 外部服务（可选，但推荐）
- **Neo4j**: 知识图谱数据库 (端口 7687)
- **PostgreSQL**: 主数据库 (端口 5432)
- **Redis**: 缓存服务 (端口 6379)

### 3. API 密钥
- **DASHSCOPE_API_KEY**: 阿里云通义千问 LLM API 密钥

## 快速启动步骤

### 步骤 1: 安装依赖

```bash
cd E:/ai
pip install -r requirements.txt
```

### 步骤 2: 配置环境变量

创建 `.env` 文件（在 `E:/ai` 目录下）：

```bash
# 复制模板
copy .env.example .env

# 编辑 .env 文件，填入实际配置
# 最少需要配置:
DASHSCOPE_API_KEY=your_api_key_here
```

### 步骤 3: 启动后端服务

**方式 A: 快速启动（推荐）**
```bash
cd E:/ai
python quick_start.py
```

**方式 B: 完整启动（带检查）**
```bash
cd E:/ai
python start_system.py
```

**方式 C: 直接启动**
```bash
cd E:/ai/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 步骤 4: 验证服务

打开浏览器访问：
- **API 文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 核心 API 端点

### 生活分析
```
GET  /api/v4/life-analysis/{user_id}
GET  /api/v4/domain-analysis/{user_id}/{domain}
```

### 涌现检测
```
GET  /api/emergence/patterns/{user_id}
GET  /api/emergence/report/{user_id}
```

### 多模态数据
```
POST /api/v4/multimodal/data
POST /api/hybrid/feedback
```

### 知识图谱
```
GET  /api/knowledge/graph/{user_id}
POST /api/knowledge/update
```

## 系统组件说明

### 1. LLM 服务 (`backend/llm/`)
- 集成阿里云通义千问 LLM
- 提供对话、分析、生成等功能
- 支持流式响应

### 2. 多模态融合 (`backend/multimodal/`)
- 感知层: 处理多种输入数据
- 融合系统: 整合不同模态的信息
- 文本处理、图像处理、传感器数据处理

### 3. 知识图谱 (`backend/knowledge/`)
- Neo4j 知识图谱存储
- 自动知识提取和构建
- 关系推理和查询

### 4. RAG 系统 (`backend/learning/`)
- 生产级 RAG 实现
- 多种记忆类型支持
- 向量化和检索优化

### 5. 强化学习 (`backend/learning/`)
- 用户行为学习
- 决策优化
- 个性化推荐

### 6. 涌现检测 (`backend/emergence/`)
- 模式识别
- 跨域关联分析
- 风险预警

## 常见问题

### Q1: 启动时报错 "ModuleNotFoundError"
**解决**: 确保已安装所有依赖
```bash
pip install -r requirements.txt
```

### Q2: 无法连接到 Neo4j/PostgreSQL
**解决**: 这些服务是可选的，系统会使用内存存储作为备选

### Q3: DASHSCOPE_API_KEY 错误
**解决**: 
1. 检查 `.env` 文件中的 API 密钥是否正确
2. 从阿里云控制台获取新的 API 密钥
3. 重启服务

### Q4: 端口 8000 已被占用
**解决**: 使用其他端口启动
```bash
uvicorn main:app --port 8001
```

## 开发模式

启动时使用 `--reload` 标志，代码修改后会自动重启：

```bash
uvicorn main:app --reload
```

## 生产部署

### 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用 Docker

```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 监控和日志

日志文件位置: `logs/lifeswarm.log`

查看实时日志:
```bash
tail -f logs/lifeswarm.log
```

## 停止服务

按 `Ctrl+C` 停止服务器

## 更多信息

- API 文档: http://localhost:8000/docs
- 项目架构: 查看 `SYSTEM_ARCHITECTURE.md`
- 快速开始: 查看 `QUICKSTART.md`

