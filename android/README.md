# 择境 Android 端

## 项目简介

择境（ChoiceRealm）Android 端是一个基于 AI 的人生决策辅助应用，完全对应 Web 端功能。

### 核心功能
- 🤖 **AI 对话**：与 AI 核心实时协作，支持多轮上下文理解
- 🎯 **决策副本**：多维度智能评估，决策分析工作台
- 🌐 **知识星图**：多维关系映射，记忆网络构建
- 🎴 **平行人生**：塔罗牌决策游戏，探索人生选择的多元可能性

## 技术栈

- **UI**: Jetpack Compose + Material 3
- **架构**: MVVM + Repository Pattern
- **网络**: Retrofit + OkHttp + WebSocket
- **存储**: DataStore Preferences
- **异步**: Kotlin Coroutines + StateFlow

## 快速开始

### 环境要求
- Android Studio Ladybug 2024.2.1+
- JDK 11+
- Android SDK API 26+ (Android 8.0+)

### 运行步骤

1. 在 Android Studio 中打开 `android` 文件夹
2. 等待 Gradle 同步完成
3. 连接设备或启动模拟器
4. 点击 Run 按钮

### 命令行编译

```bash
# 编译 Debug 版本
./gradlew assembleDebug

# 安装到设备
./gradlew installDebug
```

## 项目结构

```
android/app/src/main/java/com/lifeswarm/android/
├── data/                    # 数据层
│   ├── local/              # 本地存储 (DataStore)
│   │   └── AuthStorage.kt
│   ├── model/              # 数据模型
│   │   ├── ApiModels.kt    # 认证和聊天模型
│   │   └── DecisionModels.kt # 决策模型
│   ├── remote/             # 网络请求 (Retrofit + WebSocket)
│   │   ├── ApiClient.kt    # API 接口定义
│   │   ├── ApiConfig.kt    # API 配置
│   │   └── WebSocketClient.kt # WebSocket 客户端
│   └── repository/         # 数据仓库
│       ├── AuthRepository.kt
│       ├── ChatRepository.kt
│       └── DecisionRepository.kt
├── presentation/           # 表现层
│   ├── auth/              # 认证模块 (登录/注册)
│   │   ├── AuthScreen.kt
│   │   ├── AuthViewModel.kt
│   │   └── AuthViewModelFactory.kt
│   ├── chat/              # AI 对话模块
│   │   ├── ChatScreen.kt
│   │   ├── ChatViewModel.kt
│   │   └── ConversationListScreen.kt
│   ├── decision/          # 决策副本模块
│   │   ├── DecisionScreen.kt              # 决策主页
│   │   ├── DecisionCollectionScreen.kt    # 信息采集
│   │   ├── DecisionCollectionViewModel.kt # 采集逻辑
│   │   ├── DecisionHistoryScreen.kt       # 历史记录
│   │   ├── DecisionSimulationScreen.kt    # 推演页面
│   │   └── DecisionResultScreen.kt        # 结果展示
│   ├── knowledge/         # 知识星图模块
│   │   └── KnowledgeGraphScreen.kt
│   ├── parallel/          # 平行人生模块
│   │   └── ParallelLifeScreen.kt
│   ├── profile/           # 个人中心模块
│   │   └── ProfileScreen.kt
│   ├── settings/          # 设置模块
│   │   └── SettingsScreen.kt
│   ├── common/            # 通用组件
│   │   └── LoadingScreen.kt
│   ├── navigation/        # 导航配置
│   │   └── AppNavigation.kt
│   └── theme/             # 主题配置
│       ├── Color.kt
│       ├── Theme.kt
│       └── Type.kt
├── LifeSwarmApp.kt        # Application 类
└── MainActivity.kt        # 主 Activity
```

## 已完成功能

### 基础架构 ✅
- [x] MVVM 架构搭建
- [x] Retrofit + OkHttp 网络层
- [x] WebSocket 实时通信
- [x] DataStore 本地存储
- [x] Navigation Compose 导航
- [x] Material 3 主题系统

### 功能模块 ✅
- [x] 用户认证（登录/注册）
- [x] 主页导航
- [x] AI 对话界面
- [x] 会话列表管理
- [x] 新建会话功能
- [x] 决策副本框架
- [x] 决策 API 集成
- [x] 决策数据模型
- [x] 决策信息采集界面
- [x] 决策采集对话流程
- [x] 决策历史记录页面
- [x] 决策推演页面（WebSocket）
- [x] 决策结果展示页面
- [x] 知识星图框架
- [x] 平行人生框架
- [x] 个人中心
- [x] 应用设置页面

## 开发中功能 🚧

- [ ] 历史消息加载
- [ ] 路由分析 API 集成
- [ ] 知识图谱可视化
- [ ] 平行人生游戏逻辑
- [ ] 深色模式切换
- [ ] 通知设置
- [ ] 隐私设置
- [ ] 主题设置
- [ ] 语言设置
- [ ] 缓存管理

## 对应 Web 端

| 功能 | Web 端 | Android 端 | 状态 |
|-----|--------|-----------|------|
| UI 框架 | React + TypeScript | Kotlin + Compose | ✅ |
| 路由 | react-router-dom | Navigation Compose | ✅ |
| 网络 | fetch API | Retrofit | ✅ |
| WebSocket | 原生 WebSocket | OkHttp WebSocket | ✅ |
| 存储 | localStorage | DataStore | ✅ |
| 样式 | CSS | Material 3 | ✅ |

## API 配置

后端 API 地址在 `app/build.gradle.kts` 中配置：

```kotlin
buildConfigField(
    "String",
    "API_BASE_URL",
    "\"http://82.157.195.238:8000\""
)
```

**当前配置**：
- **生产环境**：`http://82.157.195.238:8000`（云服务器部署）
- **协议**：HTTP（明文传输）
- **WebSocket**：`ws://82.157.195.238:8000`
- **Web 前端**：`http://82.157.195.328`（知识星图 WebView）

**历史配置**：
- 测试环境：`https://u821458-a197-3cecd37e.westc.seetacloud.com:8443`

**注意事项**：
1. 使用 HTTP 协议需要在 `AndroidManifest.xml` 中设置 `android:usesCleartextTraffic="true"`
2. WebSocket 地址会自动从 HTTP 转换为 WS 协议
3. 修改后需要重新编译项目（Clean Project → Rebuild Project）

## 开发规范

### 命名规范
- **Screen**: `XxxScreen.kt` - 页面级 Composable
- **ViewModel**: `XxxViewModel.kt` - 状态管理
- **Repository**: `XxxRepository.kt` - 数据仓库
- **UiState**: `XxxUiState` - UI 状态数据类

### 代码组织
- 每个模块独立文件夹
- 数据层与表现层分离
- 使用 StateFlow 管理状态
- 使用 Coroutines 处理异步

### 注释规范
- 文件顶部注释对应的 Web 端文件
- 复杂逻辑添加中文注释
- 公开 API 使用 KDoc

## 常见问题

### Gradle 同步失败
- File → Invalidate Caches → Invalidate and Restart
- 删除 `.gradle` 文件夹后重新同步

### 应用闪退
- 查看 Logcat 中的 `FATAL EXCEPTION`
- 检查 ViewModel 是否正确初始化
- 确认网络权限已添加

### 网络请求失败
- 检查 `AndroidManifest.xml` 中的网络权限
- 确认 API 地址正确
- 查看后端服务是否运行

## 更新日志

### 2026-04-20

#### API 配置更新 ✅
- ✅ 切换到云服务器后端：`http://82.157.195.238:8000`
- ✅ 配置 HTTP 明文流量支持
- ✅ 更新 WebSocket 地址配置

## 知识星图模块 - 技术方案说明

### 当前状态 🚧

Android 端知识星图正在从基础 OpenGL ES 2.0 升级到高级 OpenGL ES 3.0 实现，移植 HarmonyOS 的视觉效果。

**详细升级计划**: 请查看 [KNOWLEDGE_GRAPH_UPGRADE_PLAN.md](KNOWLEDGE_GRAPH_UPGRADE_PLAN.md)

### HarmonyOS 技术栈（参考实现）

HarmonyOS 使用 C++ + OpenGL ES 3.0 实现了高级视觉效果：

1. **OpenGL ES 3.0** - 更强大的图形 API
2. **GLSL 3.0 着色器** - 支持更复杂的着色器效果
3. **多层发光效果** - 节点有核心、内层、外层、光晕多层发光
4. **贝塞尔曲线连线** - 柔和弯曲的连线（16段曲线）
5. **流光粒子系统** - 沿连线流动的发光粒子
6. **3D 球形背景星空** - 800+ 颗星星分布在 3D 球体上
7. **加法混合** - 实现真实的发光效果
8. **脉冲动画** - 节点呼吸效果，选中节点更强
9. **平滑缓动动画** - 聚焦时的 ease-in-out 动画
10. **节点大小基于连接数** - 重要节点更大更亮

### Android 端实现进度

**阶段 1：基础架构** ✅
- ✅ ViewModel + Repository 架构
- ✅ 后端 API 对接（/api/v5/future-os/）
- ✅ 数据转换逻辑
- ✅ 力导向布局算法
- ✅ 基础 OpenGL ES 2.0 渲染

**阶段 2：视觉效果升级** ✅（已完成）
- ✅ 创建 OpenGL ES 3.0 着色器（Shaders.kt）
- ✅ 升级节点渲染器（EnhancedNodeRenderer.kt）
- ✅ 升级连线渲染器（EnhancedLineRenderer.kt）
- ✅ 添加流光粒子系统（FlowParticleRenderer.kt）
- ✅ 添加 3D 球形背景星空（BackgroundStarRenderer.kt）
- 🚧 实现平滑缓动动画（进行中）

**阶段 3：主渲染器重构** �（当前）
- 集成所有子渲染器
- 实现平滑缓动动画
- 优化渲染顺序

### 技术对比

| 特性 | HarmonyOS (C++) | Android (Kotlin) | 状态 |
|-----|----------------|------------------|------|
| OpenGL 版本 | ES 3.0 | ES 3.0 | ✅ |
| 着色器语言 | GLSL 3.0 | GLSL 3.0 | ✅ |
| 节点发光 | 6层发光 | 6层发光 | 🚧 |
| 连线效果 | 贝塞尔曲线 | 直线 | 🚧 |
| 粒子系统 | 有 | 无 | 🚧 |
| 背景星空 | 3D球形 | 无 | 🚧 |
| 动画效果 | 缓动动画 | 线性动画 | 🚧 |
| 后端对接 | ✅ | ✅ | ✅ |

### 为什么不用 WebView？

我们尝试过 WebView 方案，但遇到以下问题：
- Android WebView 在某些环境下无法加载 HTTP URL
- 性能不如原生 OpenGL
- 无法充分利用 GPU 加速
- 难以实现复杂的 3D 交互

因此采用原生 OpenGL ES 实现，可以：
- 完全控制渲染流程
- 充分利用 GPU 性能
- 实现更流畅的动画
- 更好的触摸交互体验

### 下一步工作

1. **完成着色器集成** - 将新的 GLSL 3.0 着色器集成到渲染器
2. **实现贝塞尔曲线连线** - 让连线更柔和自然
3. **添加背景星空** - 增强视觉深度感
4. **添加流光粒子** - 让图谱更有生命力
5. **优化动画效果** - 实现平滑的缓动动画

详细任务清单请查看 [KNOWLEDGE_GRAPH_UPGRADE_PLAN.md](KNOWLEDGE_GRAPH_UPGRADE_PLAN.md)

#### 基础架构 ✅
- ✅ 完成基础架构搭建（MVVM + Repository Pattern）
- ✅ 配置 Retrofit + OkHttp + WebSocket
- ✅ 配置 DataStore 本地存储
- ✅ 配置 Navigation Compose 导航
- ✅ 配置 Material 3 主题系统

#### 用户认证模块 ✅
- ✅ 实现登录/注册界面
- ✅ 实现 Token 自动管理
- ✅ 实现用户信息持久化
- ✅ 实现自动登录检查

#### AI 对话模块 ✅
- ✅ 实现 WebSocket 流式对话
- ✅ 实现消息气泡界面
- ✅ 实现会话列表管理
- ✅ 实现新建会话功能
- ✅ 实现路由建议展示

#### 决策副本模块 ✅（完整实现）
- ✅ 实现决策主页（功能介绍和入口）
- ✅ 实现信息采集（多轮对话收集决策信息）
- ✅ 实现历史记录（查看所有历史决策）
- ✅ 实现实时推演（WebSocket 推演各个方案）
- ✅ 实现结果展示（时间线、评分、风险评估）
- ✅ 集成完整 API（所有决策相关接口）
- ✅ 修复 DecisionRepository 的 ApiService 引用问题
- ✅ 修复所有决策模块的空安全问题
- ✅ 修复 DecisionSimulationScreen 的 WebSocket 连接问题
- ✅ 修复 DecisionOption 构造函数缺少参数问题

#### 个人中心模块 ✅（完整实现）
- ✅ 实现个人中心页面（用户信息展示、功能菜单）
- ✅ 实现用户资料编辑功能（昵称、手机号、头像）
- ✅ 实现修改密码功能（密码强度验证）
- ✅ 修复 UserInfo 缺少 phone 字段
- ✅ 修复 UpdateProfilePayload 缺少 phone 字段
- ✅ 修复 ChangePasswordScreen 语法错误
- ✅ 修复 EditProfileScreen 空安全问题和方法名错误
- ✅ 修复 Icons.Filled.ArrowBack 弃用警告
- ✅ 完成导航集成（ProfileScreen → EditProfileScreen/ChangePasswordScreen）

#### 其他
- ✅ 添加应用设置页面（基础框架）
- ✅ 整合所有核心模块
- ✅ 清理多余文档，只保留 README.md

## 项目总结

### 🎯 核心架构

Android 端完全按照 web 端的架构设计，使用现代化的 Android 开发技术栈：

- **架构模式**：MVVM + Repository Pattern
- **UI 框架**：Jetpack Compose + Material 3
- **网络层**：Retrofit + OkHttp + WebSocket
- **异步处理**：Kotlin Coroutines + Flow
- **本地存储**：DataStore Preferences
- **导航**：Navigation Compose

### 📱 已实现功能

#### 1. 用户认证模块 ✅
- 登录/注册界面
- Token 自动管理
- 用户信息持久化
- 自动登录检查

#### 2. AI 对话模块 ✅
- WebSocket 流式对话
- 消息气泡界面
- 会话列表管理
- 新建会话功能
- 路由建议展示

#### 3. 决策副本模块 ✅（完整实现）
- **决策主页** - 功能介绍和入口
- **信息采集** - 多轮对话收集决策信息
- **历史记录** - 查看所有历史决策
- **实时推演** - WebSocket 推演各个方案
- **结果展示** - 时间线、评分、风险评估
- **完整 API** - 所有决策相关接口已集成

#### 4. 个人中心模块 ✅
- **个人中心页面** ✅ - 用户信息展示、功能菜单
- **用户资料编辑** ✅ - 昵称、手机号、头像
- **修改密码** ✅ - 密码强度验证、安全检查
- **导航集成** ✅ - 完整的页面跳转流程

#### 5. 知识星图模块 🚧（OpenGL ES 3D 实现中）
- **视图模式选择** ✅ - 人际关系、职业发展、升学规划
- **OpenGL ES 3D 可视化** ✅ - 原生 3D 渲染引擎
- **ViewModel 集成** ✅ - 完整的状态管理和数据流
- **后端 API 对接** ✅ - 调用真实的知识图谱 API
- **数据转换** ✅ - 后端数据 → OpenGL 渲染数据
- **力导向布局** ✅ - 自动计算节点位置
- **节点着色** ✅ - 根据类型、类别、影响力着色
- **连线着色** ✅ - 根据关系类型和强度着色
- **3D 交互** ✅ - 单指旋转、双指缩放
- **节点点击** ✅ - 点击节点聚焦查看
- **节点标签** ✅ - 显示节点名称（OpenGL 文字渲染）
- **相机聚焦** ✅ - 点击节点后相机自动聚焦到节点
- **节点信息卡片** ✅ - 显示节点详细信息
- **加载状态** ✅ - Loading/Success/Error 状态管理
- **真实数据** ✅ - 只使用后端真实数据，移除示例数据
- **待测试** 🚧 - 等待后端 API 返回真实数据
- **工作流程**：
  1. 用户选择视图模式（人际关系/职业发展/升学规划）
  2. ViewModel 调用对应的后端 API
  3. 后端返回节点和连线数据
  4. 数据转换为 OpenGL 渲染格式
  5. OpenGL ES 渲染 3D 图谱（节点、连线、标签）
  6. 用户可以通过手势交互（旋转、缩放、点击节点）
  7. 点击节点后相机聚焦，显示节点详细信息

#### 6. 其他模块
- 应用设置页面（基础框架）
- 平行人生页面（基础框架）

### 🚀 技术亮点

1. **完整的 WebSocket 支持** - 实时推演和流式对话
2. **类型安全** - Kotlin 空安全特性
3. **响应式 UI** - Compose 声明式 UI
4. **模块化设计** - 清晰的分层架构
5. **错误处理** - 完善的异常处理机制

### 📊 代码统计

- **数据模型**：20+ 数据类
- **API 接口**：15+ 接口定义
- **页面组件**：15+ Composable 函数
- **ViewModel**：5+ 状态管理类
- **Repository**：3 个数据仓库

### 🎨 UI/UX 特点

- Material 3 设计语言
- 流畅的动画效果
- 响应式布局
- 深色主题支持（待实现）
- 无障碍支持

## 当前开发重点

### 已完成的核心模块 ✅

1. **认证系统** - 完整的登录/注册/Token 管理
2. **AI 对话** - WebSocket 流式对话、会话管理
3. **决策副本** - 完整的决策分析工作流
   - 信息采集（多轮对话）
   - 历史记录查看
   - WebSocket 实时推演
   - 结果展示（时间线、评分、风险）

### 下一步开发计划

#### 优先级 1：完善现有功能 ✅
- [x] 用户中心：资料编辑
- [x] 用户中心：修改密码
- [x] 用户中心：个人信息展示
- [x] 导航：完整的页面跳转流程

#### 优先级 2：聊天和决策功能增强
- [ ] 聊天模块：历史消息分页加载
- [ ] 聊天模块：会话删除/重命名（后端 API 待实现）
- [ ] 决策模块：选项编辑功能

#### 优先级 3：新功能模块
- [ ] 知识图谱：节点列表展示（简化版）
- [ ] 平行人生：基础游戏流程
- [ ] 系统设置：深色模式、通知设置、语言切换

#### 优先级 4：高级功能
- [ ] 知识图谱：3D 可视化（使用 Canvas 或 WebView）
- [ ] 平行人生：完整塔罗牌游戏
- [ ] 离线缓存
- [ ] 推送通知
- [ ] 数据同步

## 如何运行

### 前置要求
- Android Studio Ladybug 2024.2.1+
- JDK 11+
- Android SDK API 26+（Android 8.0+）

### 后端连接配置

**当前后端地址**：`http://82.157.195.238:8000`

**验证后端连接**：
```bash
# 测试后端是否可访问
curl http://82.157.195.238:8000/api/health

# 或在浏览器中访问
http://82.157.195.238:8000/docs
```

**如需修改后端地址**：
1. 编辑 `android/app/build.gradle.kts`
2. 修改 `API_BASE_URL` 的值
3. 在 Android Studio 中执行：Build → Clean Project
4. 然后执行：Build → Rebuild Project

### 运行步骤

1. **在 Android Studio 中打开项目**
   ```bash
   # 打开 android 文件夹
   File → Open → 选择 android 文件夹
   ```

2. **等待 Gradle 同步**
   - 首次打开会自动同步依赖
   - 如果失败，点击 File → Invalidate Caches → Invalidate and Restart

3. **配置 SDK 路径**（如果需要）
   - File → Project Structure → SDK Location
   - 设置 Android SDK 路径

4. **连接设备或启动模拟器**
   - 真机：开启 USB 调试
   - 模拟器：Tools → Device Manager → Create Device

5. **运行应用**
   - 点击工具栏的 Run 按钮（绿色三角形）
   - 或使用快捷键：Shift + F10

### 命令行编译

```bash
# 进入 android 目录
cd android

# 编译 Debug 版本
./gradlew assembleDebug

# 安装到设备
./gradlew installDebug

# 运行测试
./gradlew test
```

## 常见问题

### 1. Gradle 同步失败
**解决方案**：
- File → Invalidate Caches → Invalidate and Restart
- 删除 `.gradle` 和 `build` 文件夹后重新同步
- 检查网络连接，确保可以访问 Maven 仓库

### 2. 应用闪退
**解决方案**：
- 查看 Logcat 中的 `FATAL EXCEPTION`
- 检查 ViewModel 是否正确初始化
- 确认网络权限已添加到 AndroidManifest.xml

### 3. 网络请求失败
**解决方案**：
- 检查 `AndroidManifest.xml` 中的网络权限
- 确认 API 地址正确（在 `app/build.gradle.kts` 中）
- 查看后端服务是否运行
- 检查设备网络连接
- 查看 Logcat 中的网络错误日志

### 4. 输入框无法输入文字

#### 问题 A：电脑键盘无法输入到模拟器

**原因**：Android 模拟器默认使用虚拟键盘，需要启用物理键盘支持。

**解决方案**：

**方法1：在模拟器设置中启用（推荐）**
1. 打开 Android 模拟器
2. 点击模拟器右侧的 `...`（更多）按钮
3. 选择 `Settings`（设置）
4. 找到 `General` → `Send keyboard input to`
5. 选择 `Hardware keyboard` 或勾选 `Enable physical keyboard`
6. 重启模拟器

**方法2：通过 AVD Manager 配置**
1. Android Studio → Tools → Device Manager
2. 点击模拟器右侧的 ✏️（编辑）按钮
3. 点击 `Show Advanced Settings`
4. 找到 `Keyboard` 部分
5. 勾选 `Enable keyboard input`
6. 点击 `Finish` 保存
7. 重启模拟器

**方法3：快捷键切换**
- 在模拟器中按 `Ctrl + Shift + K`（Windows）或 `Cmd + Shift + K`（Mac）
- 这会在虚拟键盘和物理键盘之间切换

**验证是否成功**：
- 在模拟器的任意输入框中，用电脑键盘输入文字
- 如果能看到文字出现，说明配置成功

#### 问题 B：输入后无法发送

**可能原因**：
- 用户未登录（userId 为空）
- 输入框被禁用（`enabled = false`）
- 状态更新问题
- 网络连接问题

**解决方案**：
1. **查看 Logcat 日志**：
   ```
   过滤标签：ChatScreen 或 ChatViewModel
   查找以下日志：
   - [ChatScreen] 发送按钮被点击
   - [ChatViewModel] sendMessage 被调用
   - [ChatViewModel] ✅ 开始发送消息
   - 或 [ChatViewModel] ❌ 错误原因
   ```

2. **检查登录状态**：
   - 确认已经登录
   - 查看个人中心是否显示用户信息
   - 如果未登录，先退出重新登录

3. **检查网络连接**：
   - 确认后端服务正在运行
   - 测试后端连接：`curl http://82.157.195.238:8000/api/health`
   - 查看 Logcat 中的网络错误

4. **检查按钮状态**：
   - 发送按钮是否可点击（不是灰色）
   - 输入框中是否有文字
   - 是否显示"发送中..."

**调试步骤**：
```
1. 打开 Logcat（Android Studio → Logcat）
2. 过滤标签：ChatViewModel
3. 在输入框中输入 "nihao"
4. 点击发送按钮
5. 查看日志输出：
   - 如果看到 "❌ 用户ID为空" → 重新登录
   - 如果看到 "❌ 输入为空" → 检查输入框状态
   - 如果看到 "✅ 开始发送消息" → 检查网络连接
   - 如果没有任何日志 → 按钮点击事件没有触发
```

### 4. WebSocket 连接失败
**解决方案**：
- 确认后端 WebSocket 服务正常
- 检查 URL 格式（ws:// 或 wss://）
- 查看 Logcat 中的 WebSocket 日志

### 5. 编译错误
**解决方案**：
- 确保使用 Android Studio 而不是命令行编译
- 检查 JDK 版本（需要 JDK 11+）
- 清理项目：Build → Clean Project
- 重新构建：Build → Rebuild Project

## 联系方式

- 项目地址：[https://gitee.com/next12321/aiagent](https://gitee.com/next12321/aiagent)
- 问题反馈：[Issues](https://gitee.com/next12321/aiagent/issues)

---

<div align="center">
Made with ❤️ by LifeSwarm Team
</div>
