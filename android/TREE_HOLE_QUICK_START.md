# 树洞世界功能 - 快速开始

## 功能概述
树洞世界是一个匿名社交功能，用户可以创建树洞并匿名分享心情、秘密和梦想。

## 使用流程

### 1. 进入树洞世界
- 打开应用 → 社交功能 → 点击"树洞世界"卡片

### 2. 浏览树洞
- 查看所有可用的树洞列表
- 每个树洞显示标题、描述和消息数量
- 可以查看热门决策（如果有）

### 3. 创建树洞
- 点击右下角的 ➕ 浮动按钮
- 输入树洞标题和描述
- 点击"创建"按钮

### 4. 进入树洞
- 点击任意树洞卡片
- 查看树洞内的所有消息

### 5. 发送消息
- 在底部输入框输入消息
- 选择匿名或实名发送（默认匿名）
- 点击发送按钮

## 主要特性

✅ **匿名保护** - 默认匿名发送，保护隐私  
✅ **实时更新** - 支持刷新获取最新消息  
✅ **简洁设计** - 列表布局，适合移动端  
✅ **森林主题** - 绿色和棕色配色，营造自然氛围  

## 技术栈

- **UI**: Jetpack Compose + Material 3
- **架构**: MVVM (ViewModel + Repository)
- **网络**: OkHttp + Gson
- **导航**: Navigation Compose
- **状态管理**: StateFlow

## 文件结构

```
android/app/src/main/java/com/lifeswarm/android/
├── data/
│   ├── model/TreeHoleModels.kt          # 数据模型
│   └── repository/TreeHoleRepository.kt  # 数据仓库
└── presentation/
    └── treehole/
        ├── TreeHoleViewModel.kt              # 列表 ViewModel
        ├── TreeHoleViewModelFactory.kt       # 列表 ViewModel 工厂
        ├── TreeHoleDetailViewModel.kt        # 详情 ViewModel (在 TreeHoleViewModel.kt 中)
        ├── TreeHoleDetailViewModelFactory.kt # 详情 ViewModel 工厂
        ├── TreeHoleScreen.kt                 # 列表界面
        └── TreeHoleDetailScreen.kt           # 详情界面
```

## API 端点

- `GET /api/tree-hole/tree-holes` - 获取树洞列表
- `POST /api/tree-hole/create` - 创建树洞
- `GET /api/tree-hole/messages/{id}` - 获取消息列表
- `POST /api/tree-hole/messages` - 发送消息
- `GET /api/tree-hole/trending-decisions` - 获取热门决策

## 构建说明

1. 确保 `build.gradle.kts` 中已添加 `kotlin-parcelize` 插件
2. 同步 Gradle
3. 编译运行

## 注意事项

⚠️ **网络权限** - 确保应用有网络访问权限  
⚠️ **用户认证** - 需要先登录才能使用  
⚠️ **API 地址** - 后端地址：`http://82.157.195.238:8000`  

## 与 Web 端对比

| 特性 | Web 端 | Android 端 |
|------|--------|-----------|
| 布局方式 | 2.5D 森林地图 | 列表布局 |
| 导航方式 | 地图节点点击 | 卡片点击 |
| 视觉效果 | Three.js 3D | Compose 动画 |
| 核心功能 | ✅ 完全一致 | ✅ 完全一致 |

## 已知限制

- 消息点赞功能仅显示，未实现交互
- 暂不支持消息删除
- 暂不支持树洞搜索
- 暂不支持富文本编辑

## 后续优化计划

1. 实现消息点赞交互
2. 添加消息分页加载
3. 支持图片上传
4. 添加表情符号
5. 实现推送通知

---

详细文档请参考：[TREE_HOLE_IMPLEMENTATION.md](./TREE_HOLE_IMPLEMENTATION.md)
