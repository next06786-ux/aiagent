# Android 平行人生功能实现文档

## 功能概述

平行人生是一个基于塔罗牌的决策游戏，通过收集用户的选择来构建决策画像，帮助用户了解自己的决策倾向。

## 实现对照

### Web 端参考
- **页面**: `web/src/pages/ParallelLifePage.tsx`
- **组件**: `web/src/components/parallel-life/TarotGame.tsx`
- **服务**: `web/src/services/parallelLifeService.ts`
- **API**: `/api/v5/parallel-life/*`

### Android 端实现

#### 1. 数据模型 (`ParallelLifeModels.kt`)
```kotlin
- TarotCard: 塔罗牌数据
- TarotOption: 选项数据
- DecisionProfile: 决策画像
- DimensionData: 维度数据
- GameStats: 游戏统计
```

#### 2. 数据仓库 (`ParallelLifeRepository.kt`)
```kotlin
- drawCard(): 抽取塔罗牌
- submitChoice(): 提交选择
- getDecisionProfile(): 获取决策画像
- getGameStats(): 获取游戏统计
```

#### 3. ViewModel (`ParallelLifeViewModel.kt`)
```kotlin
游戏阶段:
- INTRO: 介绍阶段
- DRAWING: 抽牌中
- CHOOSING: 选择中
- RESULT: 结果展示

主要方法:
- startGame(): 开始游戏
- drawCard(): 抽牌
- submitChoice(): 提交选择
- finishEarly(): 提前结束
- restart(): 重新开始
```

#### 4. UI 界面 (`ParallelLifeScreen.kt`)
```kotlin
主要组件:
- ParallelLifeScreen: 主界面
- StarfieldBackground: 星空背景
- IntroPhase: 介绍阶段
- DrawingPhase: 抽牌阶段
- ChoosingPhase: 选择阶段
- ResultPhase: 结果阶段
- TarotCardPreview: 塔罗牌预览
- TarotDeck: 牌堆动画
- RevealedCard: 揭示的卡片
- DimensionCard: 维度卡片
```

## 游戏流程

### 1. 介绍阶段 (INTRO)
- 显示游戏标题和说明
- 展示塔罗牌预览动画
- 点击"开始占卜"按钮进入游戏

### 2. 抽牌阶段 (DRAWING)
- 显示进度条
- 展示牌堆动画
- 自动抽取塔罗牌（2.5秒动画）

### 3. 选择阶段 (CHOOSING)
- 显示揭示的塔罗牌
  - 卡片名称
  - 维度（如：风险偏好、时间观念等）
  - 场景描述
- 显示两个选项按钮
  - 左倾向选项
  - 右倾向选项
- 提供"提前结束"按钮

### 4. 结果阶段 (RESULT)
- 显示决策画像标题
- 展示统计信息
  - 总选择次数
  - 置信度
- 显示各维度数据
  - 维度名称
  - 倾向值（-1 到 1）
  - 置信度
  - 可视化进度条
- 显示决策模式特征列表
- 提供"重新开始"和"返回主页"按钮

## API 接口

### 1. 抽取塔罗牌
```
POST /api/v5/parallel-life/draw-card
Body: {
  "user_id": "string",
  "drawn_cards": ["string"] // 可选，已抽取的牌
}
Response: {
  "success": true,
  "data": {
    "card": "命运之轮",
    "card_key": "wheel_of_fortune",
    "dimension": "风险偏好",
    "dimension_key": "risk_tolerance",
    "scenario": "你面临一个重要决策...",
    "options": [
      {
        "id": "1",
        "text": "选择稳妥方案",
        "tendency": "left"
      },
      {
        "id": "2",
        "text": "选择冒险方案",
        "tendency": "right"
      }
    ],
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### 2. 提交选择
```
POST /api/v5/parallel-life/submit-choice
Body: {
  "user_id": "string",
  "card": "命运之轮",
  "card_key": "wheel_of_fortune",
  "dimension": "风险偏好",
  "dimension_key": "risk_tolerance",
  "scenario": "你面临一个重要决策...",
  "choice": "选择稳妥方案",
  "tendency": "left"
}
Response: {
  "success": true,
  "data": {}
}
```

### 3. 获取决策画像
```
GET /api/v5/parallel-life/decision-profile/{user_id}
Response: {
  "success": true,
  "data": {
    "dimensions": {
      "风险偏好": {
        "value": -0.5,
        "count": 10,
        "confidence": 0.85
      },
      "时间观念": {
        "value": 0.3,
        "count": 8,
        "confidence": 0.75
      }
    },
    "patterns": [
      "倾向于选择稳妥方案",
      "注重长期规划"
    ],
    "confidence": 0.8,
    "total_choices": 21
  }
}
```

## UI 设计特点

### 1. 视觉风格
- **背景**: 深蓝色渐变 (#0A0E27 → #1A1F3A)
- **星空**: 100个随机分布的白色星点
- **主色调**: 紫色 (#6B48FF)
- **卡片**: 圆角矩形，半透明背景

### 2. 动画效果
- **发光效果**: 塔罗牌周围的脉冲光晕
- **旋转动画**: 抽牌时的卡片旋转
- **进度条**: 平滑的进度更新
- **渐变**: 按钮和卡片的渐变色

### 3. 交互设计
- **触摸反馈**: 所有按钮都有点击效果
- **加载状态**: 抽牌时显示加载动画
- **错误提示**: Snackbar 显示错误信息
- **流畅过渡**: 各阶段之间的平滑切换

## 导航集成

### 路由配置
```kotlin
// AppNavigation.kt
composable("parallel-life") {
    val user by authViewModel.user.collectAsState()
    val userId = user?.userId ?: ""
    
    ParallelLifeScreen(
        userId = userId,
        onNavigateBack = { navController.popBackStack() }
    )
}
```

### 主页入口
```kotlin
// HomeScreen.kt
FeatureCardData(
    id = "parallel-life",
    title = "平行人生",
    description = "探索人生可能性",
    icon = Icons.Default.Psychology
)
```

## 技术要点

### 1. 状态管理
- 使用 `StateFlow` 管理 UI 状态
- 单一数据源原则
- 不可变数据结构

### 2. 异步处理
- 使用 Kotlin Coroutines
- `viewModelScope` 管理生命周期
- `withContext(Dispatchers.IO)` 处理网络请求

### 3. 错误处理
- `Result<T>` 封装返回值
- 统一的错误提示机制
- 网络异常捕获和重试

### 4. 性能优化
- 懒加载列表（LazyColumn）
- 记忆化组件（remember）
- 避免不必要的重组

## 测试建议

### 1. 单元测试
- ViewModel 逻辑测试
- Repository 数据处理测试
- 模型序列化/反序列化测试

### 2. UI 测试
- 各阶段界面渲染测试
- 用户交互流程测试
- 动画效果测试

### 3. 集成测试
- 完整游戏流程测试
- API 接口调用测试
- 错误场景测试

## 未来优化方向

1. **本地缓存**: 缓存已抽取的牌和决策画像
2. **离线支持**: 支持离线游戏模式
3. **社交分享**: 分享决策画像到社交平台
4. **个性化**: 根据用户画像推荐相关功能
5. **动画增强**: 更丰富的卡片翻转和过渡动画
6. **音效**: 添加抽牌和选择的音效
7. **多语言**: 支持多语言界面

## 依赖项

```gradle
// 已包含在项目中
implementation "androidx.compose.material3:material3"
implementation "androidx.lifecycle:lifecycle-viewmodel-compose"
implementation "androidx.navigation:navigation-compose"
implementation "com.google.code.gson:gson"
implementation "com.squareup.okhttp3:okhttp"
```

## 文件清单

```
android/app/src/main/java/com/lifeswarm/android/
├── data/
│   ├── model/
│   │   └── ParallelLifeModels.kt          # 数据模型
│   └── repository/
│       └── ParallelLifeRepository.kt      # 数据仓库
└── presentation/
    ├── parallellife/
    │   ├── ParallelLifeScreen.kt          # UI 界面
    │   ├── ParallelLifeViewModel.kt       # ViewModel
    │   └── ParallelLifeViewModelFactory.kt # Factory
    ├── navigation/
    │   └── AppNavigation.kt               # 路由配置（已更新）
    └── home/
        └── HomeScreen.kt                  # 主页（已包含入口）
```

## 总结

Android 端的平行人生功能已完整实现，与 Web 端保持功能对等：
- ✅ 完整的游戏流程（介绍→抽牌→选择→结果）
- ✅ 美观的 UI 设计（星空背景、塔罗牌动画）
- ✅ 完善的状态管理（ViewModel + StateFlow）
- ✅ 可靠的网络请求（Repository + Result）
- ✅ 流畅的导航集成（NavHost + Composable）
- ✅ 主页功能入口（FeatureCard）

用户可以通过主页的"平行人生"卡片进入游戏，体验完整的塔罗牌决策游戏流程。
