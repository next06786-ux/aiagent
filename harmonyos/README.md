# HarmonyOS AI决策辅助应用

<div align="center">

🧠 基于HarmonyOS的智能决策辅助系统

[快速开始](./GETTING_STARTED.md) • [架构文档](./HARMONYOS_BACKEND_INTEGRATION.md) • [进度追踪](./REFACTOR_PROGRESS.md)

</div>

---

## ✨ 特性

- 🎯 **7人格决策推演** - 多维度智能体协同分析
- 🌟 **三大知识图谱** - 职业、教育、关系星图可视化
- 💡 **智慧洞察** - 专业Agent深度分析
- 🎴 **平行人生** - 塔罗牌探索不同可能性
- 👥 **社交互动** - 好友系统和树洞功能
- 📅 **智能日程** - AI辅助的日程管理
- 🎨 **玻璃态射UI** - 模仿Web端的精美界面
- ⚡ **实时通信** - WebSocket支持实时推演

---

## 🚀 快速开始

### 1. 启动后端

```bash
cd backend
python main.py
```

### 2. 配置API地址

修改 `entry/src/main/ets/constants/ApiConstants.ets`:

```typescript
static readonly BASE_URL: string = 'http://你的IP:6006';
```

**注意**: 后端端口是 6006

### 3. 运行应用

在DevEco Studio中打开项目并运行

详细步骤请查看 [使用指南](./GETTING_STARTED.md)

---

## 📁 项目结构

```
harmonyos/
├── entry/src/main/ets/
│   ├── constants/      # 常量配置
│   ├── models/         # 数据模型
│   ├── services/       # 服务层（8个服务）
│   ├── utils/          # 工具类（9个工具）
│   ├── components/     # UI组件（7个组件）
│   └── pages/          # 页面（10个页面）
├── GETTING_STARTED.md  # 使用指南
├── HARMONYOS_BACKEND_INTEGRATION.md  # 架构文档
└── REFACTOR_PROGRESS.md  # 进度追踪
```

---

## 🎨 核心功能

### 决策推演
7个人格智能体环形分布，实时推演决策过程，提供多维度分析和建议。

### 知识图谱
三大星图（职业、教育、关系）的3D可视化，支持节点探索和关系查询。

### 智慧洞察
三个专业Agent（关系、教育、职业）提供深度洞察和个性化建议。

### 平行人生
通过塔罗牌游戏探索不同选择的可能性，获得启发性建议。

---

## 📊 完成情况

- ✅ 常量定义: 2/2
- ✅ 数据模型: 7/7
- ✅ 工具类: 9/9
- ✅ 服务层: 8/8
- ✅ UI组件: 7/7
- ✅ 页面: 10/10
- ✅ 配置文件: 2/2

**总体完成度: 100%**

---

## 🔧 技术栈

- **前端框架**: HarmonyOS ArkTS
- **网络通信**: HTTP + WebSocket
- **数据存储**: 离线缓存 + 后端数据库
- **UI设计**: 玻璃态射 + 3D效果
- **后端**: Python FastAPI
- **数据库**: MySQL + Neo4j + Redis + FAISS

---

## 📝 开发状态

当前版本: v1.0.0  
开发进度: 100%  
状态: 待测试

---

## 📚 文档

- [使用指南](./GETTING_STARTED.md) - 如何运行和使用
- [架构文档](./HARMONYOS_BACKEND_INTEGRATION.md) - 完整的技术架构
- [进度追踪](./REFACTOR_PROGRESS.md) - 开发进度和计划
- [后端文档](../BACKEND_README.md) - 后端API说明

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

<div align="center">

Made with ❤️ for HarmonyOS

</div>
