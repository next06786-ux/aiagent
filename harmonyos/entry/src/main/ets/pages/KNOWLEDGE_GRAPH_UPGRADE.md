# 知识图谱可视化 - HarmonyOS 6 鸿蒙化升级

## 🎨 设计理念

本次升级完全采用 **HarmonyOS 6 官网风格**，融入鸿蒙设计系统的核心特性：

- **灵动流体设计**：流畅的动画和过渡效果
- **星空美学**：渐变色彩和光晕效果
- **毛玻璃风格**：半透明背景和模糊效果
- **层次化设计**：清晰的视觉层级

## ✨ 核心升级特性

### 1. 动画系统增强

#### 脉冲效果（Pulse Animation）
- 每个节点都有独立的脉冲动画
- 使用正弦波实现平滑的缩放效果
- 增强节点的生命感和动态感

```typescript
// 脉冲计算
let pulseScale = 1 + Math.sin(node.pulsePhase) * 0.15
let effectiveRadius = radius * pulseScale
```

#### 流动效果（Flow Animation）
- 连接线上的光点流动
- 表示知识之间的关系流动
- 增强图谱的动态感

```typescript
// 流动光点
let flowProgress = (Math.sin(link.flowPhase) + 1) / 2
let flowX = source.x + dx * flowProgress
let flowY = source.y + dy * flowProgress
```

#### 粒子系统（Particle System）
- 50个背景粒子
- 随机运动和生命周期
- 增强整体的视觉氛围

### 2. 视觉效果升级

#### 光晕效果（Glow Effect）
- 节点周围的渐变光晕
- 强度随节点类型变化
- 创造深度感和立体感

```typescript
let glowGradient = this.context.createRadialGradient(
  node.x, node.y, effectiveRadius,
  node.x, node.y, glowRadius
)
glowGradient.addColorStop(0, `rgba(10, 89, 247, ${node.glowIntensity * 0.3})`)
glowGradient.addColorStop(1, 'rgba(10, 89, 247, 0)')
```

#### 渐变填充（Gradient Fill）
- 节点使用径向渐变
- 连接线使用线性渐变
- 背景使用多色渐变

#### 阴影系统（Shadow System）
- 多层阴影增强立体感
- 选中状态的多层光环
- 符合鸿蒙设计规范

### 3. 交互体验优化

#### 选中状态
- 多层光环效果
- 平滑的过渡动画
- 详情面板自动弹出

#### 拖动交互
- 节点可拖动固定位置
- 画布可平移
- 缩放功能完整

#### 详情面板
- 毛玻璃背景
- 流畅的进出动画
- 关联记忆展示

## 🎯 节点类型与颜色

| 类型 | 颜色 | 含义 |
|------|------|------|
| Concept | #FF6B6B | 概念 - 珊瑚红 |
| Entity | #4ECDC4 | 实体 - 青绿色 |
| Event | #45B7D1 | 事件 - 天蓝色 |
| Pattern | #FFA07A | 模式 - 浅橙色 |
| Source | #95E1D3 | 来源 - 薄荷绿 |
| Photo | #A8E6CF | 照片 - 浅绿色 |
| Location | #FFD93D | 地点 - 金黄色 |
| Person | #6BCF7F | 人物 - 生机绿 |
| Time | #B19CD9 | 时间 - 薰衣草紫 |

## 🔧 技术实现

### 力导向布局
- 斥力计算：节点之间相互排斥
- 引力计算：连接的节点相互吸引
- 阻尼系统：平滑收敛
- 速度限制：防止过度运动

### 渲染管道
1. 清空画布
2. 绘制背景渐变
3. 绘制粒子系统
4. 应用变换（平移、缩放）
5. 绘制连接线（带流动效果）
6. 绘制节点（带脉冲和光晕）
7. 恢复上下文

### 性能优化
- 使用 Canvas 2D 高效渲染
- 裁剪区域限制绘制范围
- 动画帧率控制在 60fps
- 收敛检测自动停止模拟

## 📱 UI 组件

### 顶部导航栏
- 返回按钮
- 标题和副标题
- 刷新按钮
- 毛玻璃背景

### 控制按钮组
- 放大（+）
- 缩小（−）
- 重置视图（Home）
- 右侧浮动布局

### 底部详情面板
- 节点信息展示
- 关联记忆列表
- 查看详情按钮
- 平滑的进出动画

## 🚀 使用方法

### 基本交互
- **点击节点**：选中并显示详情
- **拖动节点**：固定位置
- **拖动画布**：平移视图
- **缩放按钮**：放大/缩小
- **重置按钮**：恢复初始视图

### API 集成
```typescript
// 加载知识图谱数据
async loadGraphData() {
  // 从后端 API 获取数据
  // 自动解析并渲染
}

// 加载节点来源
async loadNodeSources(nodeName: string) {
  // 获取节点的关联记忆
  // 在详情面板显示
}
```

## 📊 数据结构

### 节点数据
```typescript
interface GraphNode {
  id: string              // 唯一标识
  name: string            // 节点名称
  type: string            // 节点类型
  category?: string       // 分类
  x: number              // X 坐标
  y: number              // Y 坐标
  vx: number             // X 速度
  vy: number             // Y 速度
  fx?: number            // 固定 X 坐标
  fy?: number            // 固定 Y 坐标
  pulsePhase?: number    // 脉冲阶段
  glowIntensity?: number // 光晕强度
}
```

### 连接数据
```typescript
interface GraphLink {
  source: string         // 源节点 ID
  target: string         // 目标节点 ID
  type: string          // 关系类型
  flowPhase?: number    // 流动阶段
}
```

## 🎬 动画参数

| 参数 | 值 | 说明 |
|------|-----|------|
| REPULSION | 3000 | 节点斥力强度 |
| ATTRACTION | 0.05 | 连接引力强度 |
| DAMPING | 0.85 | 阻尼系数 |
| MIN_VELOCITY | 0.1 | 最小速度阈值 |
| MAX_ITERATIONS | 300 | 最大迭代次数 |
| PARTICLE_COUNT | 50 | 粒子数量 |
| GLOW_ANIMATION_SPEED | 0.05 | 光晕动画速度 |

## 🔄 更新日志

### v2.0 - 鸿蒙化升级
- ✨ 添加脉冲动画效果
- ✨ 添加流动光点效果
- ✨ 添加粒子系统
- ✨ 优化光晕效果
- ✨ 升级 UI 设计
- ✨ 增强交互体验
- 🎨 采用鸿蒙6官网风格
- 📱 改进移动端适配

## 💡 最佳实践

1. **节点数量**：建议 5-20 个节点，过多会影响性能
2. **连接数量**：建议不超过 30 条连接
3. **标签长度**：建议不超过 8 个字符
4. **更新频率**：避免频繁重新加载数据

## 🐛 已知限制

- Canvas 在某些设备上可能有性能限制
- 大规模图谱（100+ 节点）需要优化
- 某些旧设备可能不支持高级渐变效果

## 📝 后续改进方向

- [ ] 支持节点分组
- [ ] 添加搜索功能
- [ ] 支持导出为图片
- [ ] 添加更多交互手势
- [ ] 性能优化（WebGL 渲染）
- [ ] 支持自定义主题

---

**设计参考**：[HarmonyOS 6 官网](https://consumer.huawei.com/cn/harmonyos-6/)

**最后更新**：2026年3月15日













