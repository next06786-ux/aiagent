# LifeSwarm 系统启动总结

## 🚀 快速启动（3步）

### 1️⃣ 安装依赖
```bash
cd E:/ai
pip install -r requirements.txt
```

### 2️⃣ 配置环境
编辑 `.env` 文件，至少配置：
```
DASHSCOPE_API_KEY=your_api_key_here
```

### 3️⃣ 启动服务

**Windows 用户（推荐）:**
```bash
# 双击运行
start_backend.bat

# 或用 PowerShell
.\start_backend.ps1
```

**Linux/Mac 用户:**
```bash
python quick_start.py
```

**或直接启动:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## ✅ 验证服务

启动后，打开浏览器访问：
- **API 文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
E:/ai/
├── backend/                    # 后端服务
│   ├── main.py                # FastAPI 主应用
│   ├── llm/                   # LLM 服务 (Qwen)
│   ├── multimodal/            # 多模态融合
│   ├── knowledge/             # 知识图谱 (Neo4j)
│   ├── learning/              # RAG + 强化学习
│   ├── emergence/             # 涌现检测
│   ├── database/              # 数据库管理
│   └── ...
├── harmonyos/                 # HarmonyOS 前端应用
├── requirements.txt           # Python 依赖
├── start_backend.bat          # Windows 启动脚本
├── start_backend.ps1          # PowerShell 启动脚本
├── quick_start.py             # Python 快速启动
├── start_system.py            # 完整启动脚本
└── BACKEND_STARTUP_GUIDE.md   # 详细启动指南
```

## 🔧 核心组件

| 组件 | 功能 | 状态 |
|------|------|------|
| **LLM 服务** | 阿里云通义千问集成 | ✅ 就绪 |
| **多模态融合** | 感知层 + 数据融合 | ✅ 就绪 |
| **知识图谱** | Neo4j 知识存储 | ✅ 就绪 |
| **RAG 系统** | 生产级检索增强生成 | ✅ 就绪 |
| **强化学习** | 用户行为学习 | ✅ 就绪 |
| **涌现检测** | 模式识别和预警 | ✅ 就绪 |

## 📊 API 端点概览

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

### 对话接口
```
POST /api/chat/message
GET  /api/chat/history/{user_id}
```

## 🔌 外部依赖（可选）

这些服务是可选的，系统会自动使用内存存储作为备选：

| 服务 | 端口 | 用途 | 状态 |
|------|------|------|------|
| Neo4j | 7687 | 知识图谱 | 可选 |
| PostgreSQL | 5432 | 主数据库 | 可选 |
| Redis | 6379 | 缓存 | 可选 |

## 🐛 常见问题

### Q: 启动时报错 "ModuleNotFoundError"
**A:** 运行 `pip install -r requirements.txt`

### Q: 无法连接到数据库
**A:** 这是正常的，系统会使用内存存储

### Q: API 密钥错误
**A:** 检查 `.env` 文件中的 `DASHSCOPE_API_KEY`

### Q: 端口 8000 已被占用
**A:** 修改启动命令中的端口号，如 `--port 8001`

## 📝 环境变量配置

创建 `.env` 文件：

```env
# LLM 配置
DASHSCOPE_API_KEY=your_api_key_here

# 数据库配置（可选）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
DATABASE_URL=postgresql://user:password@localhost:5432/lifeswarm

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=True
```

## 🎯 下一步

1. **启动后端服务** - 按照上面的快速启动步骤
2. **测试 API** - 访问 http://localhost:8000/docs
3. **启动前端应用** - 在 HarmonyOS 中编译运行
4. **集成测试** - 前后端联调

## 📚 更多信息

- 详细启动指南: `BACKEND_STARTUP_GUIDE.md`
- 系统架构: `SYSTEM_ARCHITECTURE.md`
- 快速开始: `QUICKSTART.md`
- API 文档: http://localhost:8000/docs (启动后)

## 💡 提示

- 首次启动可能需要初始化数据库，请耐心等待
- 使用 `--reload` 标志可以在代码修改后自动重启
- 生产环境建议使用 Gunicorn + Uvicorn
- 所有日志都会输出到控制台和 `logs/lifeswarm.log`

---

**祝你使用愉快！** 🎉

