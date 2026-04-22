# HarmonyOS 知识星图实现方案

## 当前状态
- Android版本使用OpenGL ES 3.0实现了完整的3D知识星图
- HarmonyOS版本需要实现类似功能

## Android实现特性
1. **三种视图模式**：
   - 人际关系图谱（people）
   - 职业发展图谱（career）
   - 升学规划图谱（education）

2. **OpenGL ES 3.0渲染**：
   - 背景星空（BackgroundStarRenderer）
   - 贝塞尔曲线连线（EnhancedLineRenderer）
   - 流光粒子系统（FlowParticleRenderer）
   - 3D球体节点（SphereNodeRenderer）
   - 文字标签（TextLabelRenderer）

3. **交互功能**：
   - 单指拖动旋转视角
   - 双指缩放
   - 点击节点查看详情
   - 聚焦动画
   - 自动旋转

## HarmonyOS实现方案

### 方案A：使用XComponent + Native C++（推荐）
类似Android的OpenGL实现，使用HarmonyOS的XComponent调用Native层的OpenGL ES渲染。

**优点**：
- 性能最好
- 可以完全复用Android的渲染逻辑
- 支持复杂的3D效果

**缺点**：
- 需要编写C++代码
- 开发复杂度高
- 需要配置Native开发环境

### 方案B：使用Canvas 2D（当前实现）
使用ArkTS的Canvas API实现2D版本的知识图谱。

**优点**：
- 纯ArkTS实现，无需Native代码
- 开发简单快速
- 易于维护

**缺点**：
- 性能较差
- 无法实现复杂的3D效果
- 交互体验不如3D版本

### 方案C：使用Web组件加载Three.js（临时方案）
使用Web组件加载Web版本的Three.js实现。

**优点**：
- 可以直接复用Web端代码
- 快速实现
- 支持3D效果

**缺点**：
- 性能中等
- 依赖Web组件
- 与原生UI集成较差

## 推荐实现步骤

### 第一阶段：快速可用（使用方案C）
1. 修复KnowledgeGraphPage，使用Web组件
2. 加载Web端的Three.js实现
3. 实现基本的数据加载和显示

### 第二阶段：优化体验（使用方案B）
1. 使用Canvas 2D实现简化版
2. 实现基本的节点和连线渲染
3. 添加交互功能（拖动、缩放、点击）

### 第三阶段：完整功能（使用方案A）
1. 配置Native C++开发环境
2. 移植Android的OpenGL渲染器
3. 实现完整的3D效果和动画

## 当前问题

查看 `harmonyos/entry/src/main/ets/pages/KnowledgeGraphPage.ets` 发现可能的问题：
1. 数据加载失败
2. 渲染逻辑错误
3. 服务调用问题

## 下一步行动

1. 检查KnowledgeGraphPage的当前实现
2. 修复数据加载问题
3. 实现基本的Canvas 2D渲染
4. 添加三种视图切换功能

## API端点

根据Android实现，需要调用以下API：
- `/api/v5/future-os/people-graph` - 人际关系图谱
- `/api/v5/future-os/career-graph` - 职业发展图谱
- `/api/v5/future-os/education-graph` - 升学规划图谱

## 数据结构

```typescript
interface KnowledgeGraphView {
  nodes: KnowledgeGraphNode[];
  links: KnowledgeGraphLink[];
}

interface KnowledgeGraphNode {
  id: string;
  name: string;
  type: string;
  isSelf: boolean;
  metadata: Record<string, Object>;
}

interface KnowledgeGraphLink {
  source: string;
  target: string;
  type: string;
  strength: number;
}
```
