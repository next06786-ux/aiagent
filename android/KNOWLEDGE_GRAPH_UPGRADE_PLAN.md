# 知识星图视觉效果升级计划

## 目标
将 HarmonyOS C++ 实现的高级视觉效果移植到 Android Kotlin 实现，同时保持与 web 端相同的后端对接逻辑。

## 技术栈对比

### HarmonyOS (参考实现)
- **语言**: C++
- **图形 API**: OpenGL ES 3.0
- **着色器**: GLSL 3.0
- **特点**: 原生性能，复杂着色器效果

### Android (目标实现)
- **语言**: Kotlin
- **图形 API**: OpenGL ES 3.0
- **着色器**: GLSL 3.0
- **特点**: 与 HarmonyOS 相同的视觉效果

## 升级任务清单

### ✅ 阶段 1：基础架构（已完成）
- [x] 创建 ViewModel（KnowledgeGraphViewModel.kt）
- [x] 创建 Repository（KnowledgeGraphRepository.kt）
- [x] 对接后端 API（/api/v5/future-os/）
- [x] 数据模型定义（KnowledgeGraphModels.kt）
- [x] 数据转换逻辑（后端数据 → OpenGL 数据）
- [x] 力导向布局算法
- [x] 基础 UI 界面（KnowledgeGraphScreen.kt）

### ✅ 阶段 2：着色器升级（已完成）
- [x] 创建 OpenGL ES 3.0 着色器文件（Shaders.kt）
- [x] 节点着色器
  - [x] 6层发光效果（core, inner1, inner2, outer1, outer2, glow）
  - [x] 脉冲呼吸动画
  - [x] 选中节点光环效果
  - [x] 透视缩放
- [x] 连线着色器
  - [x] 深度感知亮度
  - [x] 渐变色效果
- [x] 背景星空着色器
  - [x] 3D 透视缩放
  - [x] 多层发光
  - [x] 深度感知亮度
- [x] 流光粒子着色器
  - [x] 大小随进度变化
  - [x] 闪烁效果
  - [x] 多层发光

### ✅ 阶段 3：渲染器重构（已完成）

#### 3.1 节点渲染器升级 ✅
**文件**: `EnhancedNodeRenderer.kt`

**已完成**:
- [x] 升级到 OpenGL ES 3.0
- [x] 使用新的节点着色器
- [x] 实现节点大小基于连接数
- [x] 传递时间参数用于动画
- [x] 传递选中节点索引
- [x] 使用加法混合绘制两遍（增强发光）

#### 3.2 连线渲染器升级 ✅
**文件**: `EnhancedLineRenderer.kt`

**已完成**:
- [x] 实现贝塞尔曲线连线（16段）
- [x] 颜色渐变（从源节点到目标节点）
- [x] 透明度渐变（两端淡出，中间柔和）
- [x] 使用加法混合绘制两层（外层柔和光晕 + 核心细线）

#### 3.3 背景星空渲染器 ✅
**文件**: `BackgroundStarRenderer.kt`

**已完成**:
- [x] 生成 3D 球形分布的星星（820颗）
- [x] 4个层次（远景400颗、中景250颗、近景120颗、最近50颗）
- [x] 每颗星星的属性（位置、大小、亮度、颜色、闪烁）
- [x] 实现闪烁动画
- [x] 使用加法混合绘制两遍
- [x] 透视缩放（远处的星星更小）

#### 3.4 流光粒子渲染器 ✅
**文件**: `FlowParticleRenderer.kt`

**已完成**:
- [x] 为每条连线生成 3-5 个粒子
- [x] 粒子沿贝塞尔曲线移动
- [x] 粒子属性（位置、速度、颜色、透明度）
- [x] 更新粒子位置
- [x] 使用加法混合

### ✅ 阶段 4：主渲染器重构（已完成）

**文件**: `EnhancedKnowledgeGraphRenderer.kt`

**已完成**:
- [x] 升级到 OpenGL ES 3.0
- [x] 集成所有子渲染器
  - [x] EnhancedNodeRenderer
  - [x] EnhancedLineRenderer
  - [x] BackgroundStarRenderer
  - [x] FlowParticleRenderer
- [x] 实现平滑缓动动画（ease-in-out cubic）
- [x] 实现相机目标点系统
- [x] 渲染顺序优化
- [x] 聚焦动画（先拉远再推近）
- [x] 自动旋转功能
- [x] 更新 KnowledgeGraphScreen.kt 使用新渲染器

### 🚧 阶段 5：交互优化和文字渲染（进行中）

**当前任务**:
1. ✅ 优化点击检测（已在 EnhancedKnowledgeGraphRenderer 中实现）
2. ✅ 优化聚焦动画（已实现缩放动画和平滑旋转）
3. ✅ 实现节点文字标签渲染
   - ✅ 创建 TextLabelRenderer.kt（标签连接线和锚点）
   - ✅ 创建 TextRenderer.kt（3D 文字标签）
   - ✅ 文字始终面向相机（Billboard 效果）
4. ✅ **3D 星球节点效果**（新增）
   - ✅ 创建 SphereNodeRenderer.kt
   - ✅ 真实的 3D 球体几何体（16x16 细分）
   - ✅ 基于物理的光照（漫反射 + 镜面反射 + 边缘光）
   - ✅ 表面纹理（噪声函数模拟星球表面）
   - ✅ 大气层光晕效果
   - ✅ 脉冲呼吸动画
   - ✅ 选中高亮效果
5. ⏳ 节点信息卡片优化
   - 显示更多信息（类别、连接数、影响力）
   - 显示关系列表
6. ⏳ 性能优化
   - VBO 缓存
   - 减少不必要的数据更新
   - 使用 instanced rendering（如果支持）

**下一步**: 优化节点信息卡片

### 📋 阶段 6：测试和调优（待开发）

**任务**:
1. 测试不同设备性能
2. 调整参数（节点大小、颜色、动画速度）
3. 优化内存使用
4. 添加性能监控
5. 用户体验测试

## 关键技术点

### 1. OpenGL ES 3.0 vs 2.0

**主要区别**:
- GLSL 3.0 语法（`#version 300 es`, `in/out` 代替 `attribute/varying`）
- 更强大的着色器功能（更多内置函数）
- 支持多个渲染目标
- 更好的性能

**迁移要点**:
```kotlin
// ES 2.0
attribute vec3 aPosition;
varying vec3 vColor;
gl_FragColor = vec4(color, 1.0);

// ES 3.0
layout(location = 0) in vec3 aPosition;
out vec3 vColor;
out vec4 fragColor;
fragColor = vec4(color, 1.0);
```

### 2. 加法混合

**用途**: 实现真实的发光效果

**实现**:
```kotlin
// 启用加法混合
glBlendFunc(GL_SRC_ALPHA, GL_ONE)

// 绘制发光对象
draw()

// 恢复正常混合
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
```

### 3. 贝塞尔曲线

**公式**: 二次贝塞尔曲线
```
P(t) = (1-t)² * P0 + 2(1-t)t * P1 + t² * P2
```

**实现**:
```kotlin
val u = 1f - t
val x = u*u*p0.x + 2*u*t*p1.x + t*t*p2.x
val y = u*u*p0.y + 2*u*t*p1.y + t*t*p2.y
val z = u*u*p0.z + 2*u*t*p1.z + t*t*p2.z
```

### 4. 缓动函数

**ease-in-out cubic**:
```kotlin
fun easeInOutCubic(t: Float): Float {
    return if (t < 0.5f) {
        4f * t * t * t
    } else {
        val f = 2f * t - 2f
        0.5f * f * f * f + 1f
    }
}
```

## 预期效果

完成后，Android 端知识星图将具有：
- ✨ 华丽的多层发光效果
- 🌟 真实的 3D 星空背景
- 💫 流动的光粒子
- 🎨 柔和的贝塞尔曲线连线
- 🎭 平滑的动画效果
- 🎯 精准的交互体验

同时保持：
- 📡 与 web 端相同的后端 API
- 🏗️ MVVM 架构
- 🔄 响应式数据流
- 📊 完整的状态管理

## 开发建议

1. **逐步迁移**: 先完成一个渲染器，测试通过后再继续下一个
2. **保留旧代码**: 在新文件中实现，便于对比和回退
3. **性能监控**: 使用 Android Profiler 监控 GPU 和 CPU 使用
4. **设备测试**: 在不同性能的设备上测试
5. **参数调优**: 根据实际效果调整参数

## 参考资料

- HarmonyOS 实现: `harmonyos/entry/src/main/cpp/starmap_renderer.cpp`
- 着色器定义: `harmonyos/entry/src/main/cpp/shader_utils.h`
- OpenGL ES 3.0 文档: https://www.khronos.org/opengles/
- GLSL 3.0 规范: https://www.khronos.org/registry/OpenGL/specs/es/3.0/GLSL_ES_Specification_3.00.pdf
