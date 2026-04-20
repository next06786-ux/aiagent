# HarmonyOS 项目使用指南

## 📋 项目概述

这是一个基于HarmonyOS的AI决策辅助应用，集成了后端的7大核心功能模块：
- 🧠 AI核心 - 意图识别和智能路由
- 🎯 决策推演 - 7个人格智能体的多维度决策分析
- 🌟 知识图谱 - 职业、教育、关系三大星图
- 💡 智慧洞察 - 三个专业Agent的深度分析
- 🎴 平行人生 - 塔罗牌游戏
- 👥 社交功能 - 好友和树洞
- 📅 日程管理 - 智能日程规划

---

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- DevEco Studio 4.0+
- HarmonyOS SDK API 10+
- Node.js 16+ (用于运行后端)
- Python 3.9+ (后端依赖)

### 2. 后端配置

#### 启动后端服务器

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务器
python main.py
```

后端默认运行在 `http://localhost:8000`

#### 配置数据库

确保以下数据库服务已启动：
- MySQL (用户数据、决策记录)
- Neo4j (知识图谱)
- Redis (缓存)
- FAISS (向量检索)

详见 `backend/BACKEND_README.md`

### 3. 修改API地址

打开 `harmonyos/entry/src/main/ets/constants/ApiConstants.ets`

```typescript
export class ApiConstants {
  // 修改为你的后端地址
  static readonly BASE_URL: string = 'http://192.168.1.100:8000';
  static readonly WS_URL: string = 'ws://192.168.1.100:8000';
  
  // ...
}
```

**重要**: 
- 如果在模拟器上测试，使用 `http://10.0.2.2:8000`
- 如果在真机上测试，使用局域网IP地址
- 确保手机和电脑在同一网络

### 4. 运行项目

1. 用DevEco Studio打开 `harmonyos` 目录
2. 等待依赖下载完成
3. 连接设备或启动模拟器
4. 点击运行按钮

---

## 📁 项目结构

```
harmonyos/entry/src/main/ets/
├── constants/          # 常量定义
│   ├── ApiConstants.ets       # API端点
│   └── AppConstants.ets       # 应用配置
├── models/            # 数据模型
│   ├── User.ets              # 用户模型
│   ├── Decision.ets          # 决策模型
│   ├── Agent.ets             # 智能体模型
│   ├── KnowledgeNode.ets     # 知识节点模型
│   ├── Insight.ets           # 洞察模型
│   ├── Social.ets            # 社交模型
│   └── Schedule.ets          # 日程模型
├── services/          # 服务层
│   ├── AuthService.ets       # 认证服务
│   ├── DecisionService.ets   # 决策服务
│   ├── KnowledgeGraphService.ets  # 知识图谱服务
│   ├── InsightsService.ets   # 洞察服务
│   ├── ParallelLifeService.ets    # 平行人生服务
│   ├── SocialService.ets     # 社交服务
│   ├── ScheduleService.ets   # 日程服务
│   └── AICoreService.ets     # AI核心服务
├── utils/             # 工具类
│   ├── HttpClient.ets        # HTTP客户端
│   ├── HttpInterceptor.ets   # HTTP拦截器
│   ├── WebSocketClient.ets   # WebSocket客户端
│   ├── GeometryUtils.ets     # 几何计算
│   ├── ColorUtils.ets        # 颜色工具
│   ├── DateUtils.ets         # 日期工具
│   ├── StringUtils.ets       # 字符串工具
│   ├── OfflineCache.ets      # 离线缓存
│   └── DataPreloader.ets     # 数据预加载
├── components/        # UI组件
│   ├── sphere/               # 球体相关组件
│   │   ├── SphereView.ets
│   │   ├── AgentNode.ets
│   │   └── ConnectionLine.ets
│   ├── decision/             # 决策相关组件
│   │   ├── PersonaInteractionView.ets
│   │   └── DecisionInfoCollector.ets
│   └── common/               # 通用组件
│       ├── LoadingSpinner.ets
│       └── ErrorToast.ets
└── pages/             # 页面
    ├── LoginPage.ets         # 登录页
    ├── RegisterPage.ets      # 注册页
    ├── IndexNew.ets          # 主页
    ├── DecisionSimulationPage.ets  # 决策推演页
    ├── KnowledgeGraphPage.ets      # 知识图谱页
    ├── InsightsPage.ets      # 洞察页
    ├── ParallelLifePage.ets  # 平行人生页
    ├── SocialPage.ets        # 社交页
    ├── SchedulePage.ets      # 日程页
    └── UserProfilePage.ets   # 个人资料页
```

---

## 🎨 核心功能说明

### 1. 决策推演 (DecisionSimulationPage)

**功能**: 7个人格智能体环形分布，实时推演决策过程

**使用流程**:
1. 输入决策问题
2. 添加2-5个选项
3. 补充背景信息（可选）
4. 开始推演
5. 观察7个智能体的实时思考
6. 查看最终推荐结果

**技术要点**:
- WebSocket实时通信
- 环形布局算法
- 玻璃态射效果
- 动画过渡

### 2. 知识图谱 (KnowledgeGraphPage)

**功能**: 三个星图（职业、教育、关系）的可视化展示

**使用流程**:
1. 选择星图类型（职业/教育/关系）
2. 查看节点分布
3. 点击节点查看详情
4. 探索节点关系

**技术要点**:
- Canvas绘制
- Fibonacci球面分布
- 节点交互
- 关系连线

### 3. 智慧洞察 (InsightsPage)

**功能**: 三个专业Agent提供深度分析

**Agent类型**:
- 关系洞察Agent
- 教育洞察Agent
- 职业洞察Agent

**技术要点**:
- Tab切换
- 洞察卡片展示
- 置信度可视化

### 4. 平行人生 (ParallelLifePage)

**功能**: 塔罗牌游戏，探索不同选择的可能性

**使用流程**:
1. 输入问题
2. 选择3张牌
3. 查看解读和建议

---

## 🔧 常见问题

### Q1: 无法连接后端

**解决方案**:
1. 检查后端是否正常运行
2. 检查API地址配置是否正确
3. 检查网络权限是否已授予
4. 检查防火墙设置

### Q2: WebSocket连接失败

**解决方案**:
1. 确认WebSocket地址正确
2. 检查后端WebSocket服务是否启动
3. 查看控制台错误日志

### Q3: 页面跳转失败

**解决方案**:
1. 检查 `main_pages.json` 是否包含该页面
2. 检查页面路径是否正确
3. 重新编译项目

### Q4: 图标资源缺失

**解决方案**:
1. 在 `resources/base/media/` 添加所需图标
2. 或使用系统图标替代
3. 更新资源引用

---

## 📝 开发建议

### 1. 代码规范

- 类名: PascalCase (例如: `DecisionService`)
- 方法名: camelCase (例如: `getDecisions`)
- 常量: UPPER_SNAKE_CASE (例如: `BASE_URL`)
- 私有成员: 以下划线开头 (例如: `_token`)

### 2. 错误处理

所有网络请求都应该包含错误处理：

```typescript
try {
  const result = await SomeService.someMethod();
  // 处理成功结果
} catch (error) {
  this.errorMessage = error.message || '操作失败';
  this.showError = true;
}
```

### 3. 性能优化

- 使用离线缓存减少网络请求
- 使用数据预加载提升用户体验
- 合理使用 `@State` 避免不必要的重渲染
- 大列表使用 `LazyForEach`

### 4. UI设计

- 遵循HarmonyOS设计规范
- 保持与Web端一致的玻璃态射效果
- 注意深色模式适配
- 确保触摸区域足够大（至少44x44dp）

---

## 🔄 更新日志

### v1.0.0 (2026-04-20)

- ✅ 完成所有核心功能模块
- ✅ 实现7个人格智能体决策推演
- ✅ 实现三大知识图谱
- ✅ 实现智慧洞察功能
- ✅ 实现平行人生游戏
- ✅ 实现社交和日程功能
- ✅ 完成UI组件库
- ✅ 完成网络层封装

---

## 📚 相关文档

- [后端API文档](../BACKEND_README.md)
- [架构设计文档](./HARMONYOS_BACKEND_INTEGRATION.md)
- [重构进度文档](./REFACTOR_PROGRESS.md)
- [HarmonyOS官方文档](https://developer.harmonyos.com/)

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License
