# HarmonyOS端开发文档

> 择境 (ChoiceRealm) HarmonyOS客户端 - 智能决策辅助系统

**最后更新**: 2026-04-20

---

## 📋 目录

- [项目概述](#项目概述)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [核心功能](#核心功能)
- [开发进度](#开发进度)
- [重构计划](#重构计划)
- [技术架构](#技术架构)
- [API对接](#api对接)
- [常见问题](#常见问题)

---

## 项目概述

HarmonyOS端是择境系统的移动客户端，对标Web端实现，提供完整的AI决策辅助功能。

### 核心特性

- 🎯 **决策副本** - 7人格智能体协同推演
- 🌟 **知识星图** - 三大知识图谱可视化（职业/教育/关系）
- 💡 **智慧洞察** - 多智能体深度分析
- 🎴 **平行人生** - 塔罗牌决策游戏
- 👥 **好友系统** - 社交互动和树洞
- 📅 **智能日程** - AI辅助日程管理
- 🎨 **玻璃态射UI** - 精美的现代化界面
- ⚡ **实时通信** - WebSocket实时推演

### 技术栈

- **开发语言**: ArkTS (TypeScript-like)
- **UI框架**: ArkUI
- **网络**: HTTP + WebSocket
- **状态管理**: @State/@Observed
- **数据缓存**: Preferences API

---


## 快速开始

### 环境要求

- DevEco Studio 4.0+
- HarmonyOS SDK API 9+
- Node.js 16+

### 启动步骤

#### 1. 启动后端服务

```bash
cd backend
python main.py
```

后端将在 `http://localhost:6006` 启动

#### 2. 配置API地址

修改 `entry/src/main/ets/constants/ApiConstants.ets`:

```typescript
export class ApiConstants {
  // 开发环境：使用你的本地IP
  static readonly BASE_URL: string = 'http://192.168.1.100:6006';
  
  // 生产环境：使用服务器地址
  // static readonly BASE_URL: string = 'https://api.choicerealm.com';
}
```

**重要**: 
- 不要使用 `localhost` 或 `127.0.0.1`（模拟器无法访问）
- 使用你的电脑在局域网的IP地址
- 确保手机/模拟器与电脑在同一网络

#### 3. 运行应用

1. 在DevEco Studio中打开 `harmonyos` 目录
2. 等待依赖安装完成
3. 连接设备或启动模拟器
4. 点击运行按钮

#### 4. 测试账号

```
用户名: test_user_tarot
密码: test123456
```

---


## 项目结构

```
harmonyos/
├── entry/src/main/ets/
│   ├── constants/              # 常量配置
│   │   ├── ApiConstants.ets    # API地址配置
│   │   └── AppConstants.ets    # 应用常量
│   │
│   ├── models/                 # 数据模型
│   │   ├── User.ets           # 用户模型
│   │   ├── Decision.ets       # 决策模型
│   │   ├── Agent.ets          # 智能体模型
│   │   ├── Insight.ets        # 洞察模型
│   │   ├── KnowledgeNode.ets  # 知识节点模型
│   │   ├── Social.ets         # 社交模型（Friend/Post/Comment）
│   │   └── Schedule.ets       # 日程模型
│   │
│   ├── services/               # 服务层（API调用）
│   │   ├── AuthService.ets            # 认证服务
│   │   ├── DecisionService.ets        # 决策服务
│   │   ├── KnowledgeGraphService.ets  # 知识图谱服务
│   │   ├── InsightsService.ets        # 洞察服务
│   │   ├── ParallelLifeService.ets    # 平行人生服务
│   │   ├── SocialService.ets          # 社交服务
│   │   ├── ScheduleService.ets        # 日程服务
│   │   └── AICoreService.ets          # AI核心服务
│   │
│   ├── utils/                  # 工具类
│   │   ├── HttpClient.ets      # HTTP客户端
│   │   ├── WebSocketClient.ets # WebSocket客户端
│   │   ├── DataPreloader.ets   # 数据预加载
│   │   ├── OfflineCache.ets    # 离线缓存
│   │   ├── GeometryUtils.ets   # 几何计算
│   │   ├── ColorUtils.ets      # 颜色工具
│   │   ├── DateUtils.ets       # 日期工具
│   │   └── StringUtils.ets     # 字符串工具
│   │
│   ├── components/             # UI组件
│   │   ├── common/             # 通用组件
│   │   ├── decision/           # 决策组件
│   │   │   ├── DecisionInfoCollector.ets
│   │   │   └── PersonaInteractionView.ets
│   │   └── sphere/             # 球体组件
│   │       ├── SphereView.ets
│   │       └── AgentNode.ets
│   │
│   ├── pages/                  # 页面
│   │   ├── IndexNew.ets               # 主页（待改为五角星）
│   │   ├── LoginPage.ets              # 登录页（待合并）
│   │   ├── RegisterPage.ets           # 注册页（待合并）
│   │   ├── DecisionSimulationPage.ets # 决策推演页
│   │   ├── KnowledgeGraphPage.ets     # 知识图谱页
│   │   ├── InsightsPage.ets           # 洞察页
│   │   ├── ParallelLifePage.ets       # 平行人生页
│   │   ├── FriendsPage.ets            # 好友页（已重构）
│   │   ├── SchedulePage.ets           # 日程页
│   │   └── UserProfilePage.ets        # 个人中心页
│   │
│   └── entryability/
│       └── EntryAbility.ets    # 应用入口
│
├── build.bat                   # Windows构建脚本
├── reinstall_app.bat          # 重装应用脚本
└── README.md                  # 本文档

```

---


## 核心功能

### 1. 决策副本 (DecisionSimulationPage)

**功能**: 7人格智能体协同推演决策

**特点**:
- 7个智能体环形分布，实时推演
- WebSocket实时通信，显示思考过程
- 支持多轮对话和技能调用
- 最终给出综合评分和建议

**对应后端API**:
- `POST /api/decision/persona/start-session` - 开始推演
- WebSocket `/ws/decision/{session_id}` - 实时推演

### 2. 知识星图 (KnowledgeGraphPage)

**功能**: 三大知识图谱可视化

**图谱类型**:
- 职业图谱 - 职业路径和技能关系
- 教育图谱 - 学校、专业、课程关系
- 关系图谱 - 人际关系网络

**特点**:
- 3D球体可视化
- 节点点击查看详情
- 关系线条连接
- 支持搜索和筛选

**对应后端API**:
- `GET /api/kg/career/nodes` - 职业节点
- `GET /api/kg/education/nodes` - 教育节点
- `GET /api/kg/relationship/nodes` - 关系节点

### 3. 智慧洞察 (InsightsPage)

**功能**: 多智能体深度分析

**智能体类型**:
- 关系洞察Agent - 分析人际关系
- 教育洞察Agent - 分析学习路径
- 职业洞察Agent - 分析职业发展

**特点**:
- 实时生成洞察报告
- 可视化数据展示
- 个性化建议

**对应后端API**:
- `POST /api/insights/generate` - 生成洞察
- `GET /api/insights/history` - 历史洞察

### 4. 平行人生 (ParallelLifePage)

**功能**: 塔罗牌决策游戏

**玩法**:
- 选择3张塔罗牌
- AI解读牌面含义
- 探索不同选择的可能性
- 获得启发性建议

**对应后端API**:
- `POST /api/parallel-life/draw-cards` - 抽牌
- `POST /api/parallel-life/interpret` - 解读

### 5. 好友系统 (FriendsPage)

**功能**: 社交互动

**特点**:
- 好友列表管理
- 好友请求处理
- 搜索添加好友
- 树洞入口（跳转到TreeHolePage）

**对应后端API**:
- `GET /api/social/friends` - 好友列表
- `POST /api/social/friend-request` - 发送请求
- `GET /api/social/tree-hole/posts` - 树洞帖子

### 6. 智能日程 (SchedulePage)

**功能**: AI辅助日程管理

**特点**:
- 日程创建和编辑
- 日历视图
- 智能提醒
- 时间冲突检测

**对应后端API**:
- `GET /api/schedule/list` - 日程列表
- `POST /api/schedule/create` - 创建日程

---


## 开发进度

### 已完成 ✅

#### 基础架构
- ✅ 常量配置 (ApiConstants, AppConstants)
- ✅ 数据模型 (7个模型类)
- ✅ 工具类 (9个工具类)
- ✅ HTTP客户端和WebSocket客户端
- ✅ 离线缓存和数据预加载

#### 服务层
- ✅ AuthService - 认证服务
- ✅ DecisionService - 决策服务
- ✅ KnowledgeGraphService - 知识图谱服务
- ✅ InsightsService - 洞察服务
- ✅ ParallelLifeService - 平行人生服务
- ✅ SocialService - 社交服务
- ✅ ScheduleService - 日程服务
- ✅ AICoreService - AI核心服务

#### UI组件
- ✅ 通用组件 (LoadingSpinner, ErrorToast等)
- ✅ 决策组件 (DecisionInfoCollector, PersonaInteractionView)
- ✅ 球体组件 (SphereView, AgentNode)

#### 页面
- ✅ LoginPage - 登录页
- ✅ RegisterPage - 注册页
- ✅ IndexNew - 主页（球体网格）
- ✅ DecisionSimulationPage - 决策推演页
- ✅ KnowledgeGraphPage - 知识图谱页
- ✅ InsightsPage - 洞察页
- ✅ ParallelLifePage - 平行人生页
- ✅ FriendsPage - 好友页（已重构）
- ✅ SchedulePage - 日程页
- ✅ UserProfilePage - 个人中心页

### 最近更新 🔄

**2026-04-20**:
- ✅ 重命名 SocialPage → FriendsPage
- ✅ 添加树洞入口卡片
- ✅ 修改Tab结构：好友列表/好友请求/添加好友
- ✅ 删除冗余的Friend.ets模型
- ✅ 更新路由引用

### 待完成 ⏳

#### 高优先级
1. ⏳ **主页重构** - 将球体网格改为五角星导航（对标Web端）
2. ⏳ **认证页面合并** - 合并LoginPage和RegisterPage为AuthPage
3. ⏳ **创建统一类型定义** - types/ApiTypes.ets

#### 中优先级
4. ⏳ **服务层对齐** - 逐个对齐Web端接口
5. ⏳ **HttpClient优化** - 统一错误处理和类型定义
6. ⏳ **创建AuthManager** - 全局认证状态管理

#### 低优先级
7. ⏳ **组件库优化** - 清理冗余组件
8. ⏳ **EntryAbility优化** - 简化路由逻辑

---


## 重构计划

### 目标

**完全按照Web端架构重构HarmonyOS端**，实现功能对齐，减少冗余代码。

### Web端完整页面列表（来自App.tsx）

Web端共有**26个页面**，以下是完整对比：

#### 核心页面对比

| 路由 | Web端页面 | HarmonyOS端页面 | 优先级 | 状态 |
|------|-----------|----------------|--------|------|
| `/` | HomePage (五角星导航) | IndexNew (球体网格) | 🔴 P0 | ⏳ 待重构 |
| `/auth` | AuthPage (登录/注册合一) | LoginPage + RegisterPage | 🔴 P0 | ⏳ 待合并 |
| `/chat` | AIChatPage | ❌ 缺失 | 🟡 P1 | ⏳ 待开发 |
| `/decision` | DecisionWorkbenchPage | ❌ 缺失 | 🟡 P1 | ⏳ 待开发 |
| `/decision/simulation` | DecisionSimulationPage | DecisionSimulationPage | 🔴 P0 | ✅ 已对齐 |
| `/knowledge-graph` | KnowledgeGraphPage | KnowledgeGraphPage | 🔴 P0 | ✅ 已对齐 |
| `/insights` | DecisionInsightsPage | InsightsPage | 🔴 P0 | ✅ 已对齐 |
| `/parallel-life` | ParallelLifePage | ParallelLifePage | 🔴 P0 | ✅ 已对齐 |
| `/friends` | FriendsPage | FriendsPage | 🔴 P0 | ✅ 已重构 |
| `/tree-hole` | TreeHolePage | ❌ 缺失 | 🟡 P1 | ⏳ 待开发 |
| `/profile` | ProfilePageNew | UserProfilePage | 🔴 P0 | ✅ 已对齐 |
| `/smart-schedule` | SmartSchedulePage | SchedulePage | 🟢 P2 | ⏳ 待对齐 |

#### 高级功能页面（可选）

| 路由 | Web端页面 | HarmonyOS端 | 优先级 | 说明 |
|------|-----------|-------------|--------|------|
| `/ability-islands` | AbilityIslandsPage | ❌ 缺失 | 🟢 P2 | 能力岛屿 |
| `/relationship` | RelationshipDecisionPage | ❌ 缺失 | 🟢 P2 | 关系决策 |
| `/dashboard` | DashboardPage | ❌ 缺失 | 🟢 P2 | 仪表盘 |
| `/meta-agent` | MetaAgentPage | ❌ 缺失 | 🟢 P2 | Meta智能体 |
| `/emergence-patterns` | EmergencePatternsPage | ❌ 缺失 | 🟢 P3 | 涌现模式 |
| `/emergence-dashboard` | EmergenceDashboardPage | ❌ 缺失 | 🟢 P3 | 涌现仪表盘 |
| `/life-domain-insights` | LifeDomainInsightsPage | ❌ 缺失 | 🟢 P3 | 人生领域洞察 |
| `/learning-progress` | LearningProgressPage | ❌ 缺失 | 🟢 P3 | 学习进度 |
| `/lora-training` | LoRATrainingPage | ❌ 缺失 | 🟢 P3 | LoRA训练 |
| `/llm-settings` | LLMSettingsPage | ❌ 缺失 | 🟢 P3 | LLM设置 |

#### 管理员页面（暂不实现）

| 路由 | Web端页面 | HarmonyOS端 | 说明 |
|------|-----------|-------------|------|
| `/admin` | AdminPage | ❌ 不实现 | 管理员功能 |
| `/admin/users` | AdminUsersPage | ❌ 不实现 | 用户管理 |

### 服务层对比

Web端共有**14个服务文件**，HarmonyOS端需要对齐：

| Web端服务 | HarmonyOS端服务 | 状态 | 说明 |
|-----------|----------------|------|------|
| `auth.ts` | `AuthService.ets` | ⏳ 待对齐 | 认证服务 |
| `api.ts` | `HttpClient.ets` | ⏳ 待对齐 | 基础API封装 |
| `decision.ts` | `DecisionService.ets` | ⏳ 待对齐 | 决策服务 |
| `futureOs.ts` | `DecisionService.ets` | ⏳ 待合并 | Future OS（合并到决策） |
| `agentInsightsService.ts` | `InsightsService.ets` | ⏳ 待对齐 | 洞察服务 |
| `parallelLifeService.ts` | `ParallelLifeService.ets` | ⏳ 待对齐 | 平行人生服务 |
| `kgRag.ts` | `KnowledgeGraphService.ets` | ⏳ 待对齐 | 知识图谱服务 |
| `friendService.ts` | `SocialService.ets` | ⏳ 待重命名 | 好友服务 |
| `treeHoleService.ts` | ❌ 缺失 | ⏳ 待创建 | 树洞服务 |
| `scheduleService.ts` | `ScheduleService.ets` | ⏳ 待对齐 | 日程服务 |
| `chat.ts` | `AICoreService.ets` | ⏳ 待对齐 | 聊天服务 |
| `relationship.ts` | ❌ 缺失 | 🟢 P2 | 关系服务 |
| `adminService.ts` | ❌ 不实现 | - | 管理员服务 |
| `llmService.ts` | ❌ 缺失 | 🟢 P3 | LLM服务 |

### 重构优先级说明

#### 🔴 P0 - 核心功能（必须实现）
这些是应用的核心功能，必须完全对齐Web端：
1. **HomePage** - 主页五角星导航（用户入口）
2. **AuthPage** - 统一认证页面（登录/注册）
3. **DecisionSimulationPage** - 决策推演（核心功能）
4. **KnowledgeGraphPage** - 知识图谱
5. **DecisionInsightsPage** - 智慧洞察
6. **ParallelLifePage** - 平行人生
7. **FriendsPage** - 好友系统
8. **ProfilePageNew** - 个人中心

#### 🟡 P1 - 重要功能（优先实现）
这些功能对用户体验很重要：
1. **AIChatPage** - AI对话（重要交互入口）
2. **DecisionWorkbenchPage** - 决策工作台
3. **TreeHolePage** - 树洞世界（社交功能）

#### 🟢 P2 - 增强功能（可选实现）
这些功能可以增强应用体验：
1. **SmartSchedulePage** - 智能日程
2. **DashboardPage** - 数据仪表盘
3. **AbilityIslandsPage** - 能力岛屿
4. **RelationshipDecisionPage** - 关系决策
5. **MetaAgentPage** - Meta智能体

#### 🟢 P3 - 高级功能（后期实现）
这些是高级功能，可以后期添加：
1. **EmergencePatternsPage** - 涌现模式检测
2. **LifeDomainInsightsPage** - 人生领域洞察
3. **LearningProgressPage** - 学习进度追踪
4. **LoRATrainingPage** - LoRA个性化训练
5. **LLMSettingsPage** - LLM设置

### 当前HarmonyOS端缺失的核心功能

根据Web端对比，HarmonyOS端**缺失以下核心功能**：

#### 必须开发（P0-P1）
1. ❌ **AIChatPage** - AI对话页面
   - 对应Web端的核心交互入口
   - 支持多轮对话
   - 实时流式响应
   
2. ❌ **DecisionWorkbenchPage** - 决策工作台
   - 决策信息收集入口
   - 跳转到DecisionSimulationPage
   
3. ❌ **TreeHolePage** - 树洞世界
   - 匿名发帖
   - 2.5D地图展示
   - 评论互动

#### 需要重构（P0）
1. ⏳ **IndexNew → HomePage** - 主页
   - 从球体网格改为五角星导航
   - 5个核心功能节点
   - 中心AI核心按钮
   
2. ⏳ **LoginPage + RegisterPage → AuthPage** - 认证页面
   - 合并为单一页面
   - Tab切换登录/注册
   - 统一表单验证

### 重构步骤（按Web端架构）

#### Phase 1: 核心架构对齐 🔴

**Step 1.1: 创建统一类型定义**
- 创建 `types/ApiTypes.ets`
- 对标 `web/src/types/api.ts`
- 定义所有API请求/响应类型

**Step 1.2: 优化HttpClient**
- 对标 `web/src/services/api.ts`
- 实现 `requestJson<T>()`, `postJson<T>()`, `putJson<T>()`
- 统一错误处理和ApiEnvelope

**Step 1.3: 创建AuthManager**
- 对标 `web/src/context/AuthContext.tsx`
- 全局认证状态管理
- Token自动刷新

#### Phase 2: 页面重构 🔴

**Step 2.1: 主页重构（最高优先级）**
- 文件: `IndexNew.ets` → `HomePage.ets`
- 对标: `web/src/pages/HomePage.tsx`
- 实现五角星导航布局
- 5个核心节点 + 中心AI核心
- 用户头像菜单

**Step 2.2: 认证页面合并**
- 文件: 创建 `AuthPage.ets`
- 对标: `web/src/pages/AuthPage.tsx`
- 合并LoginPage和RegisterPage
- 使用Tabs切换
- 删除旧的LoginPage和RegisterPage

**Step 2.3: AI对话页面**
- 文件: 创建 `AIChatPage.ets`
- 对标: `web/src/pages/AIChatPage.tsx`
- 多轮对话
- 流式响应
- 历史记录

**Step 2.4: 决策工作台**
- 文件: 创建 `DecisionWorkbenchPage.ets`
- 对标: `web/src/pages/DecisionWorkbenchPage.tsx`
- 决策信息收集
- 跳转到推演页面

**Step 2.5: 树洞世界**
- 文件: 创建 `TreeHolePage.ets`
- 对标: `web/src/pages/TreeHolePage.tsx`
- 匿名发帖
- 帖子列表
- 评论互动

#### Phase 3: 服务层对齐 🟡

**Step 3.1: 重命名和对齐服务**
```
SocialService.ets → FriendService.ets (对标 friendService.ts)
创建 TreeHoleService.ets (对标 treeHoleService.ts)
AICoreService.ets → ChatService.ets (对标 chat.ts)
```

**Step 3.2: 对齐每个服务的接口**
- AuthService ← auth.ts
- DecisionService ← decision.ts + futureOs.ts
- InsightsService ← agentInsightsService.ts
- ParallelLifeService ← parallelLifeService.ts
- KnowledgeGraphService ← kgRag.ts
- FriendService ← friendService.ts
- TreeHoleService ← treeHoleService.ts
- ScheduleService ← scheduleService.ts
- ChatService ← chat.ts

#### Phase 4: 增强功能（可选） 🟢

根据需求逐步添加：
- SmartSchedulePage
- DashboardPage
- AbilityIslandsPage
- 等等...

### Web端HomePage五角星导航详解

**参考文件**: `web/src/pages/HomePage.tsx`

#### 五角星布局（Pentagram）

```
        决策副本 (Decision)
              ⭐
             /  \
            /    \
           /      \
    知识星图      智慧洞察
      ⭐          ⭐
     /  \        /  \
    /    \      /    \
   /      \    /      \
  /        \  /        \
好友 ⭐------🌟------⭐ 平行人生
        AI核心
```

#### 5个核心节点配置

```typescript
// 来自 web/src/pages/HomePage.tsx
const pentagramNodes = [
  {
    id: 'decision',
    title: '决策副本',
    subtitle: '分析入口',
    route: '/decision',
    top: '5%',      // 顶部
    left: '50%',
    gradient: ['#E8F4FF', '#B8DCFF'],
    status: 'live',
  },
  {
    id: 'insights',
    title: '智慧洞察',
    subtitle: '决策分析',
    route: '/insights',
    top: '24%',     // 右上
    left: '84%',
    gradient: ['#D4EBFF', '#A8D5FF'],
    status: 'live',
  },
  {
    id: 'parallel-life',
    title: '平行人生',
    subtitle: '塔罗游戏',
    route: '/parallel-life',
    top: '79%',     // 右下
    left: '70%',
    gradient: ['#C2E3FF', '#8FC8FF'],
    status: 'live',
  },
  {
    id: 'social',
    title: '社交',
    subtitle: '好友互动',
    route: '/friends',
    top: '79%',     // 左下
    left: '30%',
    gradient: ['#B0D9FF', '#7DBDFF'],
    status: 'live',
  },
  {
    id: 'knowledge-graph',
    title: '知识星图',
    subtitle: '记忆星空',
    route: '/knowledge-graph',
    top: '24%',     // 左上
    left: '16%',
    gradient: ['#F0F7FF', '#C8E2FF'],
    status: 'live',
  },
];
```

#### 中心AI核心按钮

```typescript
// 中心按钮配置
<button className="pentagram-core" onClick={() => setIsAICoreOpen(true)}>
  <small>Central Engine</small>
  <strong>AI 核心</strong>
  <span>感知 / 分析 / 决策</span>
</button>
```

点击后打开AI对话模态框（AICoreModal）

#### 用户头像菜单

```typescript
// 右上角用户菜单
- 个人中心 → /profile
- 退出登录 → logout()
```

#### HarmonyOS实现要点

1. **布局方式**: 使用Stack + 绝对定位
2. **动画效果**: 
   - 节点呼吸动画
   - 连接线粒子流动
   - 中心光晕效果
3. **交互**:
   - 节点点击跳转
   - 中心按钮打开AI对话
   - 用户菜单弹出

### Web端AuthPage详解

**参考文件**: `web/src/pages/AuthPage.tsx`

#### 页面结构

```typescript
// Tab切换
<Tabs>
  <Tab label="登录">
    <LoginForm />
  </Tab>
  <Tab label="注册">
    <RegisterForm />
  </Tab>
</Tabs>
```

#### 登录表单

```typescript
interface LoginPayload {
  username: string;
  password: string;
}

// 提交后调用
const result = await login(payload);
// 保存token和用户信息
// 跳转到主页
```

#### 注册表单

```typescript
interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  nickname?: string;
}

// 提交后调用
const result = await register(payload);
// 自动登录
// 跳转到主页
```

#### HarmonyOS实现要点

1. **使用Tabs组件**切换登录/注册
2. **统一表单验证**逻辑
3. **统一错误处理**
4. **自动登录**注册成功后
5. **记住密码**功能（可选）

### 已完成的重构 ✅

#### 2026-04-20 (下午)
- ✅ **配置生产服务器地址**
  - 更新 ApiConstants.ets
  - 后端地址: `http://82.157.195.238:6006`
  - WebSocket地址: `ws://82.157.195.238:6006`
  - 补充完整的API端点配置
  
- ✅ **创建统一类型定义**
  - 创建 `types/ApiTypes.ets`
  - 定义所有API请求/响应类型
  - 对标 `web/src/types/api.ts`
  - 包含：认证、决策、知识图谱、洞察、平行人生、社交、日程、AI对话等类型

- ✅ **优化HttpClient**
  - 重写 `utils/HttpClient.ets`
  - 对标 `web/src/services/api.ts`
  - 添加ApiError错误类
  - 实现便捷方法：requestJson, postJson, putJson, getJson, deleteJson
  - 添加withAuth辅助函数
  - 统一错误处理和日志输出

- ✅ **创建AuthPage（合并登录/注册）**
  - 创建 `pages/AuthPage.ets`
  - 对标 `web/src/pages/AuthPage.tsx`
  - 使用Tab切换登录/注册模式
  - 统一表单验证逻辑
  - 渐变背景和现代化UI
  - 自动保存登录状态

- ✅ **创建HomePage（五角星导航）**
  - 创建 `pages/HomePage.ets`
  - 对标 `web/src/pages/HomePage.tsx`
  - 实现五角星布局（5个核心节点）
  - 中心AI核心按钮
  - 用户头像菜单（个人中心、退出登录）
  - 自动检查登录状态

- ✅ **更新路由逻辑**
  - 更新 `EntryAbility.ets`
  - 简化路由判断：未登录→AuthPage，已登录→HomePage
  - 移除Welcome页面逻辑

- ✅ **清理旧文件**
  - 删除 `LoginPage.ets`（已被AuthPage替代）
  - 删除 `RegisterPage.ets`（已被AuthPage替代）
  - 删除 `IndexNew.ets`（已被HomePage替代）

#### 2026-04-20 (上午)
- ✅ SocialPage → FriendsPage
  - 重命名页面文件
  - 添加树洞入口卡片（对标Web端）
  - 修改Tab结构：好友列表/好友请求/添加好友
  - 更新路由引用
- ✅ 删除冗余模型
  - 删除 Friend.ets（使用Social.ets中的定义）
- ✅ 创建统一README文档
  - 整合所有文档到一个文件
  - 详细对比Web端和HarmonyOS端

---


## 技术架构

### 整体架构

```
┌─────────────────────────────────────────┐
│           HarmonyOS Application         │
├─────────────────────────────────────────┤
│  Pages (UI Layer)                       │
│  ├── IndexNew (主页)                    │
│  ├── DecisionSimulationPage             │
│  ├── KnowledgeGraphPage                 │
│  └── ...                                │
├─────────────────────────────────────────┤
│  Components (UI Components)             │
│  ├── common/ (通用组件)                 │
│  ├── decision/ (决策组件)               │
│  └── sphere/ (球体组件)                 │
├─────────────────────────────────────────┤
│  Services (Business Logic)              │
│  ├── AuthService                        │
│  ├── DecisionService                    │
│  ├── KnowledgeGraphService              │
│  └── ...                                │
├─────────────────────────────────────────┤
│  Utils (Utilities)                      │
│  ├── HttpClient (HTTP请求)              │
│  ├── WebSocketClient (WebSocket)        │
│  ├── DataPreloader (数据预加载)         │
│  └── OfflineCache (离线缓存)            │
├─────────────────────────────────────────┤
│  Models (Data Models)                   │
│  ├── User, Decision, Agent              │
│  ├── Insight, KnowledgeNode             │
│  └── Social, Schedule                   │
└─────────────────────────────────────────┘
           ↓ HTTP/WebSocket ↓
┌─────────────────────────────────────────┐
│         Backend API (FastAPI)           │
│         Port: 6006                      │
└─────────────────────────────────────────┘
```

### 数据流

```
User Action (UI)
    ↓
Page Component
    ↓
Service Layer (API Call)
    ↓
HttpClient / WebSocketClient
    ↓
Backend API
    ↓
Response
    ↓
Service Layer (Data Processing)
    ↓
Update @State
    ↓
UI Re-render
```

### 状态管理

使用HarmonyOS的响应式状态管理：

```typescript
@Entry
@Component
struct MyPage {
  @State data: MyData[] = [];  // 响应式状态
  
  aboutToAppear() {
    this.loadData();  // 页面加载时获取数据
  }
  
  async loadData() {
    const service = new MyService();
    this.data = await service.getData();  // 更新状态触发UI刷新
  }
}
```

### 网络通信

#### HTTP请求

```typescript
// HttpClient封装
const client = new HttpClient();
const response = await client.get<ApiResponse>('/api/endpoint');
```

#### WebSocket连接

```typescript
// WebSocketClient封装
const ws = new WebSocketClient();
ws.connect('ws://host/path');
ws.onMessage((data) => {
  // 处理消息
});
```

### 数据缓存

```typescript
// 使用Preferences API
import preferences from '@ohos.data.preferences';

// 保存数据
const prefs = await preferences.getPreferences(context, 'app_data');
await prefs.put('key', 'value');
await prefs.flush();

// 读取数据
const value = await prefs.get('key', 'default');
```

---


## API对接

### 后端地址配置

**文件**: `entry/src/main/ets/constants/ApiConstants.ets`

```typescript
export class ApiConstants {
  // 基础URL - 修改为你的后端地址
  static readonly BASE_URL: string = 'http://192.168.1.100:6006';
  
  // WebSocket URL
  static readonly WS_BASE_URL: string = 'ws://192.168.1.100:6006';
  
  // API端点
  static readonly AUTH = {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/logout',
    VERIFY_TOKEN: '/api/auth/verify-token',
  };
  
  static readonly DECISION = {
    START_SESSION: '/api/decision/persona/start-session',
    WS_CONNECT: '/ws/decision',
  };
  
  // ... 其他端点
}
```

### 主要API端点

#### 认证相关

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/auth/verify-token` | 验证Token |
| GET | `/api/auth/user/{user_id}` | 获取用户信息 |

#### 决策相关

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/decision/persona/start-session` | 开始决策推演 |
| POST | `/api/decision/persona/collect` | 收集决策信息 |
| WS | `/ws/decision/{session_id}` | 实时推演WebSocket |

#### 知识图谱相关

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/kg/career/nodes` | 获取职业图谱节点 |
| GET | `/api/kg/education/nodes` | 获取教育图谱节点 |
| GET | `/api/kg/relationship/nodes` | 获取关系图谱节点 |
| POST | `/api/kg/query` | 查询知识图谱 |

#### 洞察相关

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/insights/generate` | 生成洞察报告 |
| GET | `/api/insights/history` | 获取历史洞察 |
| GET | `/api/insights/realtime` | 实时洞察 |

#### 平行人生相关

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/parallel-life/draw-cards` | 抽取塔罗牌 |
| POST | `/api/parallel-life/interpret` | 解读塔罗牌 |
| GET | `/api/parallel-life/history` | 历史记录 |

#### 社交相关

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/social/friends` | 获取好友列表 |
| POST | `/api/social/friend-request` | 发送好友请求 |
| GET | `/api/social/tree-hole/posts` | 获取树洞帖子 |
| POST | `/api/social/tree-hole/post` | 发布树洞 |

#### 日程相关

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/schedule/list` | 获取日程列表 |
| POST | `/api/schedule/create` | 创建日程 |
| PUT | `/api/schedule/update` | 更新日程 |
| DELETE | `/api/schedule/delete` | 删除日程 |

### API响应格式

所有API响应都遵循统一格式：

```typescript
interface ApiEnvelope<T> {
  code: number;      // 状态码：200成功，其他失败
  message: string;   // 消息
  data?: T;          // 数据（可选）
}
```

**成功响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "xxx",
    "username": "test_user"
  }
}
```

**失败响应示例**:
```json
{
  "code": 400,
  "message": "用户名或密码错误"
}
```

### WebSocket消息格式

决策推演WebSocket消息格式：

```typescript
interface WebSocketEvent {
  type: string;  // 消息类型
  
  // 人格思考消息
  persona_id?: string;
  persona_name?: string;
  persona_data?: {
    score?: number;
    stance?: string;
    key_points?: string[];
    reasoning?: string;
  };
  
  // 交互消息
  interaction_data?: {
    from_persona?: string;
    to_persona?: string;
    content?: string;
  };
  
  // 评估消息
  evaluation_data?: {
    overall_score?: number;
    risk_level?: string;
    recommendation?: string;
  };
}
```

---


## 常见问题

### 1. 无法连接后端

**问题**: 应用启动后无法连接到后端API

**解决方案**:
1. 检查后端是否启动：`python backend/main.py`
2. 检查IP地址配置：不要使用localhost，使用局域网IP
3. 检查防火墙：确保6006端口未被阻止
4. 检查网络：手机/模拟器与电脑在同一网络

**如何获取本机IP**:
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig
```

### 2. WebSocket连接失败

**问题**: 决策推演时WebSocket无法连接

**解决方案**:
1. 检查WebSocket URL配置（ws://而不是http://）
2. 确保后端支持WebSocket
3. 检查session_id是否正确
4. 查看后端日志确认连接状态

### 3. 编译错误

**问题**: DevEco Studio编译失败

**解决方案**:
1. 清理缓存：Build → Clean Project
2. 重新构建：Build → Rebuild Project
3. 检查SDK版本：确保API 9+
4. 检查依赖：oh-package.json5中的依赖是否正确

### 4. 模拟器无法访问localhost

**问题**: 模拟器中应用无法访问localhost

**原因**: 模拟器的localhost指向模拟器自身，不是宿主机

**解决方案**:
- 使用宿主机的局域网IP地址
- 例如：`http://192.168.1.100:6006`

### 5. Token过期

**问题**: 登录后一段时间自动退出

**原因**: Token过期

**解决方案**:
1. 后端配置更长的Token有效期
2. 实现Token自动刷新机制
3. 在AuthService中添加Token验证

### 6. 数据不更新

**问题**: 修改数据后UI不更新

**原因**: 状态未正确更新

**解决方案**:
```typescript
// 错误：直接修改数组
this.data.push(newItem);  // UI不会更新

// 正确：创建新数组
this.data = [...this.data, newItem];  // UI会更新
```

### 7. 图片加载失败

**问题**: 头像或图片无法显示

**解决方案**:
1. 检查图片URL是否正确
2. 检查网络权限配置
3. 使用占位图：显示默认头像

### 8. 性能问题

**问题**: 应用卡顿或响应慢

**优化方案**:
1. 使用LazyForEach代替ForEach（大列表）
2. 避免频繁的状态更新
3. 使用图片缓存
4. 减少不必要的网络请求

### 9. 调试技巧

**如何查看日志**:
```typescript
import { hilog } from '@kit.PerformanceAnalysisKit';

hilog.info(0x0000, 'MyTag', 'Log message: %{public}s', data);
```

**如何调试网络请求**:
1. 在HttpClient中添加日志
2. 使用Charles或Fiddler抓包
3. 查看后端日志

### 10. 打包发布

**如何生成HAP包**:
1. Build → Build Hap(s) / APP(s)
2. 生成的HAP在 `build/outputs/` 目录
3. 可以通过hdc工具安装：
   ```bash
   hdc install app.hap
   ```

---


## 开发规范

### 命名规范

**文件命名**:
- 页面：`XxxPage.ets`
- 组件：`XxxComponent.ets` 或 `XxxView.ets`
- 服务：`XxxService.ets`
- 模型：`Xxx.ets`
- 工具：`XxxUtils.ets`

**变量命名**:
- 驼峰命名：`myVariable`
- 常量：`MY_CONSTANT`
- 私有变量：`_privateVar`

**组件命名**:
- 使用PascalCase：`MyComponent`
- 描述性命名：`UserProfileCard` 而不是 `Card1`

### 代码风格

**缩进**: 2个空格

**导入顺序**:
```typescript
// 1. HarmonyOS系统库
import router from '@ohos.router';
import preferences from '@ohos.data.preferences';

// 2. 项目内部导入
import { MyService } from '../services/MyService';
import { MyModel } from '../models/MyModel';
import { AppConstants } from '../constants/AppConstants';
```

**注释规范**:
```typescript
/**
 * 类或函数的描述
 * @param paramName 参数说明
 * @returns 返回值说明
 */
```

### Git提交规范

**提交消息格式**:
```
<type>(<scope>): <subject>

<body>
```

**Type类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `refactor`: 重构
- `docs`: 文档更新
- `style`: 代码格式调整
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(decision): 添加决策推演实时显示功能

- 实现WebSocket连接
- 添加思考过程动画
- 优化UI布局
```

---

## 性能优化

### 列表优化

**使用LazyForEach**:
```typescript
// 大列表使用LazyForEach
LazyForEach(this.dataSource, (item: Item) => {
  ListItem() {
    ItemCard(item)
  }
})
```

### 图片优化

**使用缓存**:
```typescript
Image(url)
  .objectFit(ImageFit.Cover)
  .cachedImage(true)  // 启用缓存
```

### 网络优化

**请求合并**:
```typescript
// 批量请求
const [data1, data2, data3] = await Promise.all([
  service1.getData(),
  service2.getData(),
  service3.getData()
]);
```

**离线缓存**:
```typescript
// 先返回缓存，再更新
const cached = await cache.get(key);
if (cached) {
  this.data = cached;
}

const fresh = await service.getData();
this.data = fresh;
await cache.set(key, fresh);
```

---

## 测试

### 单元测试

**测试文件位置**: `entry/src/test/ets/`

**测试示例**:
```typescript
import { describe, it, expect } from '@ohos/hypium';
import { MyService } from '../../main/ets/services/MyService';

describe('MyService', () => {
  it('should return correct data', async () => {
    const service = new MyService();
    const result = await service.getData();
    expect(result).not.toBeNull();
  });
});
```

### 集成测试

**测试流程**:
1. 启动后端服务
2. 配置测试环境API地址
3. 运行应用
4. 手动测试各个功能

**测试清单**:
- [ ] 登录/注册流程
- [ ] 决策推演完整流程
- [ ] 知识图谱加载和交互
- [ ] 洞察生成
- [ ] 平行人生游戏
- [ ] 好友功能
- [ ] 日程管理

---

## 部署

### 开发环境

1. 启动后端：`python backend/main.py`
2. 配置API地址为本机IP
3. 在DevEco Studio中运行

### 生产环境

1. 修改API地址为生产服务器
2. 构建Release版本
3. 签名HAP包
4. 上传到应用市场

**构建Release**:
```bash
# 在DevEco Studio中
Build → Build Hap(s) / APP(s) → Build Release
```

---

## 相关文档

- [HarmonyOS官方文档](https://developer.harmonyos.com/cn/docs)
- [ArkTS语法参考](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkts-get-started-0000001504769321-V3)
- [ArkUI组件参考](https://developer.harmonyos.com/cn/docs/documentation/doc-references-V3/arkui-overview-0000001580025861-V3)
- [后端API文档](../BACKEND_README.md)
- [Web端文档](../web/README.md)

---

## 更新日志

### 2026-04-20
- ✅ 重构FriendsPage，对标Web端
- ✅ 添加树洞入口卡片
- ✅ 删除冗余Friend.ets模型
- ✅ 创建统一README文档

### 2026-04-15
- ✅ 完成所有核心页面开发
- ✅ 实现WebSocket实时通信
- ✅ 添加离线缓存功能

### 2026-04-10
- ✅ 完成服务层开发
- ✅ 实现HTTP客户端封装
- ✅ 添加数据预加载

### 2026-04-05
- ✅ 项目初始化
- ✅ 基础架构搭建
- ✅ 常量和模型定义

---

## 贡献者

- 开发团队

---

## 许可证

MIT License

---

<div align="center">

**择境 (ChoiceRealm)** - 让每个决策都有迹可循

Made with ❤️ for HarmonyOS

</div>
