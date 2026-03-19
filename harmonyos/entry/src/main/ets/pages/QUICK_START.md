# 知识图谱可视化 - 快速开始指南

## 🚀 快速开始

### 1. 基本使用

```typescript
// KnowledgeGraphCanvas.ets 已经是完整的组件
// 直接在页面中使用即可

@Entry
@Component
struct MyPage {
  build() {
    KnowledgeGraphCanvas()
  }
}
```

### 2. 数据加载

组件会自动从后端 API 加载数据：

```
GET /api/v4/knowledge-graph/{userId}/export
```

**响应格式**：
```json
{
  "success": true,
  "data": {
    "information": [
      {
        "id": "1",
        "name": "晨跑",
        "type": "Event",
        "category": "健康管理"
      }
    ],
    "relationships": [
      {
        "source": "1",
        "target": "2",
        "type": "OCCURS_AT"
      }
    ]
  }
}
```

### 3. 交互操作

| 操作 | 效果 |
|------|------|
| 点击节点 | 选中并显示详情 |
| 拖动节点 | 固定节点位置 |
| 拖动画布 | 平移视图 |
| 点击 + | 放大视图 |
| 点击 − | 缩小视图 |
| 点击 Home | 重置视图 |

## 🎨 自定义样式

### 修改节点颜色

编辑 `getNodeColor()` 方法：

```typescript
getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    'Concept': '#FF6B6B',      // 修改这里
    'Entity': '#4ECDC4',
    'Event': '#45B7D1',
    // ...
  }
  return colors[type] || '#A0A0A0'
}
```

### 修改动画速度

调整这些参数：

```typescript
// 脉冲速度（越大越快）
node.pulsePhase += 0.02  // 改为 0.05 会更快

// 流动速度（越大越快）
link.flowPhase += 0.03   // 改为 0.06 会更快

// 粒子速度
particle.vx = (Math.random() - 0.5) * 0.5  // 改为 * 1.0 会更快
```

### 修改物理参数

调整力导向布局：

```typescript
private readonly REPULSION = 3000    // 斥力（越大越分散）
private readonly ATTRACTION = 0.05   // 引力（越大越紧凑）
private readonly DAMPING = 0.85      // 阻尼（越小越快停止）
```

## 📊 数据格式

### 完整示例

```typescript
// 节点数据
interface GraphNode {
  id: string              // 唯一ID
  name: string            // 显示名称
  type: string            // 节点类型（Concept/Entity/Event/Pattern/Source/Photo/Location/Person/Time）
  category?: string       // 分类标签
  x: number              // X坐标（自动计算）
  y: number              // Y坐标（自动计算）
  vx: number             // X速度（自动计算）
  vy: number             // Y速度（自动计算）
  fx?: number            // 固定X坐标（拖动时设置）
  fy?: number            // 固定Y坐标（拖动时设置）
  pulsePhase?: number    // 脉冲阶段（自动计算）
  glowIntensity?: number // 光晕强度（自动计算）
}

// 连接数据
interface GraphLink {
  source: string         // 源节点ID
  target: string         // 目标节点ID
  type: string          // 关系类型（OCCURS_AT/REQUIRES/INCLUDES等）
  flowPhase?: number    // 流动阶段（自动计算）
}
```

### 最小化示例

```json
{
  "success": true,
  "data": {
    "information": [
      {"id": "1", "name": "节点1", "type": "Event"},
      {"id": "2", "name": "节点2", "type": "Entity"}
    ],
    "relationships": [
      {"source": "1", "target": "2", "type": "RELATES_TO"}
    ]
  }
}
```

## 🔧 常见问题

### Q1: 如何添加更多节点类型？

**A**: 在 `getNodeColor()` 中添加新类型：

```typescript
getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    'MyCustomType': '#FF00FF',  // 添加新类型
    // ...
  }
  return colors[type] || '#A0A0A0'
}
```

### Q2: 如何改变节点大小？

**A**: 修改 `drawNode()` 中的 `radius`：

```typescript
let radius = 24  // 改为 32 会更大
```

### Q3: 如何禁用粒子系统？

**A**: 注释掉粒子绘制代码：

```typescript
// this.drawParticles()  // 注释这行
```

### Q4: 如何改变背景颜色？

**A**: 修改 `drawBackgroundGradient()` 方法：

```typescript
private drawBackgroundGradient() {
  let gradient = this.context.createLinearGradient(0, 0, this.canvasWidth, this.canvasHeight)
  gradient.addColorStop(0, '#FFFFFF')      // 改为你想要的颜色
  gradient.addColorStop(0.5, '#F0F0F0')
  gradient.addColorStop(1, '#E0E0E0')
  // ...
}
```

### Q5: 如何加快/减慢布局收敛？

**A**: 调整 `DAMPING` 参数：

```typescript
private readonly DAMPING = 0.85  // 改为 0.9 会更慢，0.8 会更快
```

## 🎯 性能优化

### 优化建议

1. **减少节点数量**
   - 建议不超过 20 个节点
   - 过多节点会影响性能

2. **减少连接数量**
   - 建议不超过 30 条连接
   - 过多连接会增加计算量

3. **简化标签**
   - 建议不超过 8 个字符
   - 长标签会影响渲染性能

4. **禁用不需要的效果**
   - 注释掉粒子系统
   - 简化渐变效果

### 性能监测

```typescript
// 在 updateAnimations() 中添加性能监测
console.time('render')
this.render()
console.timeEnd('render')
```

## 🐛 调试技巧

### 启用调试日志

所有关键操作都有日志输出：

```typescript
console.info('[KnowledgeGraphCanvas] 已加载: ${this.nodes.length}个节点')
console.error('[KnowledgeGraphCanvas] 加载失败:', error)
```

### 检查数据加载

```typescript
// 在 loadGraphData() 中检查响应
console.info('API 响应:', result)
console.info('节点数:', this.nodes.length)
console.info('连接数:', this.links.length)
```

### 检查渲染状态

```typescript
// 在 render() 中检查状态
console.info('Canvas 大小:', this.canvasWidth, this.canvasHeight)
console.info('缩放级别:', this.zoomScale)
console.info('偏移量:', this.offsetX, this.offsetY)
```

## 📱 移动端适配

### 屏幕尺寸

```typescript
// 自动适配屏幕大小
this.canvasWidth = 360   // 标准宽度
this.canvasHeight = 600  // 标准高度

// 在 onReady 回调中更新
.onReady(() => {
  this.canvasWidth = 360
  this.canvasHeight = 600
  this.render()
})
```

### 触摸优化

```typescript
// 触摸事件已优化
.onTouch((event) => {
  if (event.type === TouchType.Down) {
    this.handleTouchStart(event)
  } else if (event.type === TouchType.Move) {
    this.handleTouchMove(event)
  } else if (event.type === TouchType.Up) {
    this.handleTouchEnd()
  }
})
```

## 🎓 进阶用法

### 自定义节点样式

```typescript
// 在 drawNode() 中修改样式
private drawNode(node: GraphNode) {
  // 修改节点大小
  let radius = node.type === 'Concept' ? 32 : 24
  
  // 修改节点颜色
  let color = this.getNodeColor(node.type)
  
  // 修改光晕强度
  let glowIntensity = node.glowIntensity || 0.5
  
  // ... 绘制代码
}
```

### 自定义连接样式

```typescript
// 在 drawLink() 中修改样式
private drawLink(source: GraphNode, target: GraphNode, link: GraphLink) {
  // 根据关系类型改变线条宽度
  let lineWidth = link.type === 'STRONG' ? 3 : 2.5
  
  // 根据关系类型改变颜色
  let color = link.type === 'STRONG' ? '#FF0000' : '#0A59F7'
  
  // ... 绘制代码
}
```

### 添加自定义事件

```typescript
// 在节点选中时触发事件
if (clickedNode) {
  this.selectedNode = clickedNode
  // 触发自定义事件
  this.onNodeSelected?.(clickedNode)
}
```

## 📚 相关资源

- [HarmonyOS 6 官网](https://consumer.huawei.com/cn/harmonyos-6/)
- [Canvas API 文档](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [力导向图算法](https://en.wikipedia.org/wiki/Force-directed_graph_drawing)

## 💬 获取帮助

如有问题，请检查：

1. ✅ API 响应格式是否正确
2. ✅ 节点和连接数据是否完整
3. ✅ 是否有 JavaScript 错误（查看控制台）
4. ✅ 是否有网络连接问题

---

**最后更新**：2026年3月15日









