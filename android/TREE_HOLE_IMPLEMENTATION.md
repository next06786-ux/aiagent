# 树洞世界功能实现文档

## 概述
树洞世界是一个匿名社交功能，用户可以创建树洞并在其中匿名分享心情、秘密和梦想。

## 功能特性

### 1. 树洞列表
- 显示所有可用的树洞
- 每个树洞显示标题、描述、消息数量
- 支持创建新树洞
- 显示热门决策（可选）

### 2. 树洞详情
- 查看树洞的所有消息
- 发送匿名或实名消息
- 消息点赞功能
- 实时刷新消息列表

### 3. 匿名机制
- 用户可以选择匿名或实名发送消息
- 匿名消息显示为"匿名用户"
- 实名消息显示用户ID前6位

## 技术实现

### 数据模型
**文件**: `android/app/src/main/java/com/lifeswarm/android/data/model/TreeHoleModels.kt`

```kotlin
@Parcelize
data class TreeHole(
    val id: String,
    val title: String,
    val description: String,
    val messageCount: Int,
    val createdAt: String?,
    val userId: String?,
    val recommendationScore: Double?
) : Parcelable

data class TreeHoleMessage(
    val id: String,
    val content: String,
    val createdAt: String,
    val likes: Int,
    val isAnonymous: Boolean,
    val userId: String?
)

data class TrendingDecision(
    val rank: Int,
    val decision: String,
    val domain: String,
    val type: String,
    val keywords: List<String>,
    val sentiment: String,
    val description: String,
    val painPoint: String?,
    val score: Double,
    val messageCount: Int,
    val treeHoles: List<TreeHoleRef>,
    val trend: String
)
```

### 数据仓库
**文件**: `android/app/src/main/java/com/lifeswarm/android/data/repository/TreeHoleRepository.kt`

API 端点：
- `GET /api/tree-hole/tree-holes` - 获取所有树洞
- `GET /api/tree-hole/user/{userId}` - 获取用户创建的树洞
- `POST /api/tree-hole/create` - 创建树洞
- `GET /api/tree-hole/messages/{treeHoleId}` - 获取树洞消息
- `POST /api/tree-hole/messages` - 发送消息
- `GET /api/tree-hole/trending-decisions` - 获取热门决策

### ViewModel
**文件**: 
- `android/app/src/main/java/com/lifeswarm/android/presentation/treehole/TreeHoleViewModel.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/treehole/TreeHoleViewModelFactory.kt`

**TreeHoleViewModel** - 管理树洞列表状态：
- `loadTreeHoles()` - 加载树洞列表
- `loadTrendingDecisions()` - 加载热门决策
- `createTreeHole()` - 创建新树洞

**TreeHoleDetailViewModel** - 管理树洞详情状态：
- `loadMessages()` - 加载消息列表
- `sendMessage()` - 发送消息
- `setTreeHole()` - 设置树洞信息

### UI 界面

#### 树洞列表界面
**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/treehole/TreeHoleScreen.kt`

组件：
- `TreeHoleScreen` - 主界面
- `TreeHoleHeroCard` - 英雄卡片
- `TreeHoleCard` - 树洞卡片
- `TrendingDecisionCard` - 热门决策卡片
- `TreeHoleEmptyState` - 空状态
- `CreateTreeHoleDialog` - 创建树洞对话框

特性：
- 森林主题配色（绿色、棕色）
- 浮动操作按钮创建树洞
- 下拉刷新
- 点击卡片进入详情

#### 树洞详情界面
**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/treehole/TreeHoleDetailScreen.kt`

组件：
- `TreeHoleDetailScreen` - 主界面
- `TreeHoleInfoCard` - 树洞信息卡片
- `MessageCard` - 消息卡片
- `MessageEmptyState` - 空状态

特性：
- 消息列表自动滚动到底部
- 匿名/实名切换开关
- 消息输入框
- 发送按钮带加载状态
- 消息点赞显示

### 导航配置
**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/navigation/AppNavigation.kt`

路由：
- `tree-hole` - 树洞列表页面
- `tree-hole-detail/{treeHoleId}` - 树洞详情页面

导航流程：
1. 社交页面 → 点击树洞入口卡片 → 树洞列表
2. 树洞列表 → 点击树洞卡片 → 树洞详情
3. 通过 SavedStateHandle 传递 TreeHole 对象

### 社交页面集成
**文件**: `android/app/src/main/java/com/lifeswarm/android/presentation/social/SocialScreen.kt`

- 添加了 `TreeHoleEntryCard` 组件
- 点击卡片导航到树洞列表
- 森林主题配色与树洞页面一致

## 设计特点

### 视觉设计
1. **森林主题**
   - 主色调：深绿色 `#2D5A4A`
   - 强调色：棕色 `#8B5A2B`
   - 背景渐变：浅绿色透明度渐变

2. **图标**
   - 树洞：盾牌图标 (Shield)
   - 匿名：隐藏图标 (VisibilityOff)
   - 实名：可见图标 (Visibility)

3. **卡片样式**
   - 圆角：16-24dp
   - 阴影：2-4dp elevation
   - 间距：12-16dp

### 用户体验
1. **简化设计**
   - 相比 Web 端的 2.5D 森林地图，Android 采用列表布局
   - 更适合移动端操作和浏览

2. **匿名保护**
   - 默认匿名发送
   - 清晰的匿名/实名标识
   - 匿名用户统一显示

3. **即时反馈**
   - 加载状态指示
   - 发送成功提示
   - 错误消息显示

## 与 Web 端对比

### 相同功能
- 创建树洞
- 查看树洞列表
- 发送匿名/实名消息
- 查看消息列表
- 热门决策展示

### 差异
| 功能 | Web 端 | Android 端 |
|------|--------|-----------|
| 布局 | 2.5D 森林地图 | 列表布局 |
| 导航 | 地图节点点击 | 卡片点击 |
| 动画 | Three.js 3D 动画 | Compose 动画 |
| 消息点赞 | 支持 | 显示但未实现交互 |

## API 对接

### 后端地址
- Base URL: `http://82.157.195.238:8000`
- API 前缀: `/api/tree-hole`

### 请求示例

#### 获取树洞列表
```http
GET /api/tree-hole/tree-holes?hours=168
```

#### 创建树洞
```http
POST /api/tree-hole/create
Content-Type: application/json

{
  "user_id": "user123",
  "title": "我的树洞",
  "description": "这是一个分享心情的地方"
}
```

#### 发送消息
```http
POST /api/tree-hole/messages
Content-Type: application/json

{
  "tree_hole_id": "hole123",
  "user_id": "user123",
  "content": "今天心情不错",
  "is_anonymous": true
}
```

## 构建配置

### Gradle 插件
在 `android/app/build.gradle.kts` 中添加了 `kotlin-parcelize` 插件：

```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    id("kotlin-parcelize")
}
```

这是为了支持 TreeHole 数据模型的 Parcelable 序列化，用于在导航时传递对象。

## 测试建议

### 功能测试
1. 创建树洞
   - 输入标题和描述
   - 验证创建成功
   - 检查列表中是否出现

2. 查看树洞
   - 点击树洞卡片
   - 验证详情页面加载
   - 检查消息列表

3. 发送消息
   - 匿名发送
   - 实名发送
   - 验证消息出现在列表中

4. 刷新功能
   - 下拉刷新树洞列表
   - 点击刷新按钮更新消息

### UI 测试
1. 空状态显示
2. 加载状态显示
3. 错误提示显示
4. 卡片布局和样式
5. 响应式设计

## 未来优化

### 功能增强
1. 消息点赞交互
2. 消息删除功能
3. 树洞搜索
4. 树洞分类/标签
5. 推送通知

### 性能优化
1. 消息分页加载
2. 图片缓存
3. 离线缓存
4. 增量更新

### 用户体验
1. 下拉刷新
2. 上拉加载更多
3. 消息长按操作
4. 表情符号支持
5. 富文本编辑

## 文件清单

### 新增文件
1. `TreeHoleModels.kt` - 数据模型
2. `TreeHoleRepository.kt` - 数据仓库
3. `TreeHoleViewModel.kt` - ViewModel
4. `TreeHoleViewModelFactory.kt` - ViewModel 工厂
5. `TreeHoleDetailViewModelFactory.kt` - 详情 ViewModel 工厂
6. `TreeHoleScreen.kt` - 列表界面
7. `TreeHoleDetailScreen.kt` - 详情界面

### 修改文件
1. `AppNavigation.kt` - 添加树洞路由
2. `SocialScreen.kt` - 添加树洞入口和导航回调
3. `build.gradle.kts` - 添加 parcelize 插件

## 总结

树洞世界功能已完整实现，包括：
- ✅ 数据模型和 API 对接
- ✅ 树洞列表和详情界面
- ✅ 创建树洞功能
- ✅ 匿名/实名消息发送
- ✅ 导航集成
- ✅ 社交页面入口

功能与 Web 端保持一致，同时针对移动端进行了优化，提供了更好的用户体验。
