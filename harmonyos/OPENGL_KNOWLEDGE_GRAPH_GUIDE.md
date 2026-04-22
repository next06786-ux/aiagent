# HarmonyOS OpenGL ES 知识星图实现指南

## 架构设计

模仿Android实现，使用以下架构：
- **ArkTS层**：UI和交互逻辑
- **Native C++层**：OpenGL ES 3.0渲染引擎
- **XComponent**：连接ArkTS和Native层

## 文件结构

```
harmonyos/entry/src/main/
├── ets/
│   ├── pages/
│   │   └── KnowledgeGraphPage.ets          # 主页面（使用XComponent）
│   ├── components/
│   │   └── knowledge/
│   │       ├── KnowledgeGraphView.ets      # OpenGL视图组件
│   │       └── NodeDetailPanel.ets         # 节点详情面板
│   └── napi/
│       └── KnowledgeGraphNapi.ets          # Native接口封装
└── cpp/
    ├── types/
    │   └── libentry/
    │       ├── index.d.ts                   # TypeScript类型定义
    │       └── oh-package.json5
    ├── knowledge_graph/
    │   ├── KnowledgeGraphRenderer.h/cpp     # 主渲染器
    │   ├── BackgroundStarRenderer.h/cpp     # 背景星空
    │   ├── EnhancedLineRenderer.h/cpp       # 连线渲染
    │   ├── FlowParticleRenderer.h/cpp       # 粒子系统
    │   ├── SphereNodeRenderer.h/cpp         # 球体节点
    │   └── TextLabelRenderer.h/cpp          # 文字标签
    ├── CMakeLists.txt
    └── hello.cpp                            # NAPI入口
```

## 实现步骤

### 第一步：配置Native开发环境

1. 在 `entry/build-profile.json5` 中启用Native支持：
```json
{
  "apiType": "stageMode",
  "buildOption": {
    "externalNativeOptions": {
      "path": "./src/main/cpp/CMakeLists.txt",
      "arguments": "",
      "cppFlags": ""
    }
  }
}
```

2. 创建 `CMakeLists.txt`

### 第二步：创建Native渲染器

移植Android的以下渲染器：
1. `EnhancedKnowledgeGraphRenderer` - 主渲染器
2. `BackgroundStarRenderer` - 背景星空
3. `EnhancedLineRenderer` - 贝塞尔曲线连线
4. `FlowParticleRenderer` - 流光粒子
5. `SphereNodeRenderer` - 3D球体节点
6. `TextLabelRenderer` - 文字标签

### 第三步：创建NAPI接口

暴露以下接口给ArkTS：
- `initRenderer()` - 初始化渲染器
- `updateGraph(nodes, edges)` - 更新图谱数据
- `rotateCamera(deltaX, deltaY)` - 旋转相机
- `setCameraDistance(distance)` - 设置相机距离
- `focusOnNode(nodeId)` - 聚焦节点
- `resetCamera()` - 重置相机
- `detectNodeClick(x, y, width, height)` - 检测点击

### 第四步：创建ArkTS组件

使用XComponent承载OpenGL渲染：

```typescript
@Component
export struct KnowledgeGraphView {
  @State nodes: Node[] = [];
  @State edges: Edge[] = [];
  
  private xComponentId: string = 'knowledge_graph_xcomponent';
  
  build() {
    XComponent({
      id: this.xComponentId,
      type: 'surface',
      libraryname: 'entry'
    })
    .onLoad((context) => {
      // 初始化Native渲染器
      this.initNativeRenderer(context);
    })
    .onDestroy(() => {
      // 清理资源
    })
    .gesture(
      // 添加手势处理
    )
  }
}
```

## 简化方案（推荐先实现）

由于完整的OpenGL实现较复杂，建议先实现一个简化版本：

### 使用XComponent + Canvas 2D

不使用Native C++，而是使用XComponent的Canvas 2D API：

```typescript
XComponent({
  id: 'knowledge_graph',
  type: 'surface'
})
.onLoad((context) => {
  const canvas = context.getCanvas();
  const ctx = canvas.getContext('2d');
  
  // 使用Canvas 2D绘制
  this.drawKnowledgeGraph(ctx);
})
```

优点：
- 无需Native开发
- 开发速度快
- 易于调试

缺点：
- 性能不如OpenGL
- 无法实现复杂3D效果

## 当前实现建议

鉴于时间和复杂度，建议采用以下方案：

### 方案：增强的Canvas 2D实现

1. **保持当前Canvas 2D架构**
2. **添加以下增强功能**：
   - 力导向布局算法
   - 平滑动画过渡
   - 交互手势（拖动、缩放、点击）
   - 节点详情面板
   - 三种视图切换

3. **性能优化**：
   - 使用离屏Canvas
   - 实现脏矩形更新
   - 节点LOD（细节层次）

## 代码示例

### 增强的KnowledgeGraphPage

```typescript
@Entry
@Component
struct KnowledgeGraphPage {
  @State selectedView: string = 'people';
  @State nodes: KnowledgeNode[] = [];
  @State edges: KnowledgeEdge[] = [];
  @State selectedNode: KnowledgeNode | null = null;
  
  // 相机状态
  @State cameraX: number = 0;
  @State cameraY: number = 0;
  @State cameraScale: number = 1;
  
  // 动画状态
  private animationId: number = 0;
  
  build() {
    Stack() {
      // Canvas渲染层
      Canvas(this.context)
        .width('100%')
        .height('100%')
        .onReady(() => {
          this.startAnimation();
        })
        .gesture(
          GestureGroup(GestureMode.Parallel,
            // 拖动手势
            PanGesture()
              .onActionUpdate((event) => {
                this.cameraX += event.offsetX;
                this.cameraY += event.offsetY;
              }),
            // 缩放手势
            PinchGesture()
              .onActionUpdate((event) => {
                this.cameraScale *= event.scale;
              })
          )
        )
        .onClick((event) => {
          this.handleClick(event.x, event.y);
        })
      
      // UI层
      Column() {
        // 顶部栏
        this.buildTopBar()
        
        Blank()
        
        // 节点详情面板
        if (this.selectedNode) {
          this.buildNodeDetail()
        }
      }
    }
  }
  
  private startAnimation() {
    const animate = () => {
      this.updatePhysics();
      this.render();
      this.animationId = requestAnimationFrame(animate);
    };
    animate();
  }
  
  private updatePhysics() {
    // 力导向布局更新
    this.applyForces();
  }
  
  private render() {
    const ctx = this.context;
    ctx.clearRect(0, 0, ctx.width, ctx.height);
    
    // 应用相机变换
    ctx.save();
    ctx.translate(this.cameraX, this.cameraY);
    ctx.scale(this.cameraScale, this.cameraScale);
    
    // 绘制连线
    this.drawEdges(ctx);
    
    // 绘制节点
    this.drawNodes(ctx);
    
    ctx.restore();
  }
}
```

## 下一步行动

1. ✅ 创建实现指南文档
2. ⏳ 增强当前Canvas 2D实现
3. ⏳ 添加力导向布局
4. ⏳ 实现交互手势
5. ⏳ 添加节点详情面板
6. ⏳ 实现三种视图切换
7. 🔄 （可选）迁移到Native OpenGL

## 参考资料

- HarmonyOS XComponent开发指南
- HarmonyOS Native开发指南
- Android OpenGL ES实现（参考）
- 力导向布局算法（D3-force）
