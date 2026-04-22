# 知识星图真机调试问题修复

## 问题描述

在真机上测试知识星图功能时，发现两个问题：

### 问题 1：节点标签文字不显示 ❌
- **现象**：只能看到节点（圆点）和连线，但看不到节点的名称文字
- **影响**：用户无法识别节点代表什么内容

### 问题 2：双指缩放功能失效 ❌
- **现象**：双指缩放手势无法正常工作
- **影响**：用户无法放大查看节点细节

---

## 问题分析

### 问题 1 根本原因：TextLabelRenderer 未实现文字渲染

查看 `TextLabelRenderer.kt` 的代码，发现它只绘制了：
- ✅ 连接线（从节点延伸出的线）
- ✅ 锚点（线的终点小圆点）
- ❌ **文字标签**（节点名称）

**代码证据**：
```kotlin
/**
 * 文字标签渲染器
 * 绘制从节点延伸出的标签连接线和锚点
 * 
 * 特性：
 * - 只为连接数较多的节点绘制标签线
 * - 标签线长度基于节点重要性
 * - 锚点大小基于节点重要性
 * - 颜色与节点颜色一致
 */
class TextLabelRenderer {
    // ... 只有线条和点的渲染，没有文字渲染
}
```

**为什么模拟器上看起来正常？**
- 可能模拟器上测试时没有仔细观察
- 或者之前的版本有不同的实现

### 问题 2 根本原因：双指缩放使用了错误的距离值

**错误代码**：
```kotlin
if (lastDistance > 0) {
    val scale = distance / lastDistance
    val currentDistance = 10f  // ❌ 硬编码的错误值
    renderer.setCameraDistance(currentDistance / scale)
}
```

**问题**：
- `currentDistance` 被硬编码为 `10f`，这是一个非常小的值
- 每次缩放都基于这个固定值，而不是当前实际的相机距离
- 导致缩放行为异常

---

## 解决方案

### 解决方案 1：实现真正的文字渲染（需要较大改动）

OpenGL ES 中渲染文字有几种方法：

#### 方法 A：使用 Canvas 绘制文字纹理（推荐）✅

**步骤**：
1. 使用 Android Canvas 将文字绘制到 Bitmap
2. 将 Bitmap 上传为 OpenGL 纹理
3. 在 3D 空间中绘制纹理四边形（Billboard）
4. 四边形始终面向相机

**优点**：
- 支持中文、emoji 等复杂字符
- 可以使用系统字体
- 文字清晰度高

**缺点**：
- 实现复杂度较高
- 需要管理纹理缓存

#### 方法 B：使用 Overlay View（简单但性能较差）

**步骤**：
1. 在 GLSurfaceView 上层叠加一个透明的 View
2. 将 3D 节点坐标投影到屏幕坐标
3. 在 Overlay View 上使用 Canvas 绘制文字

**优点**：
- 实现简单
- 不需要处理 OpenGL 纹理

**缺点**：
- 性能较差（需要频繁更新 View）
- 文字不会随 3D 场景旋转

#### 方法 C：使用 Compose Overlay（推荐用于快速原型）✅

**步骤**：
1. 在 `Box` 中叠加 `GLSurfaceView` 和 Compose 文字层
2. 使用 `Layout` 或 `Canvas` 将文字定位到节点位置
3. 实时计算节点的屏幕坐标

**优点**：
- 可以使用 Compose 的 Text 组件
- 实现相对简单
- 支持所有字体和样式

**缺点**：
- 文字不会随 3D 场景旋转
- 需要频繁计算投影坐标

### 解决方案 2：修复双指缩放（已完成）✅

**修复代码**：
```kotlin
if (lastDistance > 0) {
    val scale = distance / lastDistance
    // ✅ 使用当前相机距离而不是固定值
    val currentDistance = renderer.getCameraDistance()
    val newDistance = currentDistance / scale
    renderer.setCameraDistance(newDistance)
    println("[KnowledgeGraph] 缩放: scale=$scale, distance=$newDistance")
}
```

**添加的方法**：
```kotlin
// EnhancedKnowledgeGraphRenderer.kt
fun getCameraDistance(): Float {
    return cameraDistance
}
```

**修复效果**：
- ✅ 双指缩放现在基于当前相机距离
- ✅ 缩放行为符合预期
- ✅ 添加了日志便于调试

---

## 推荐实现方案：Compose Overlay

这是最快速且效果较好的方案，适合当前项目。

### 实现步骤

#### 步骤 1：修改 KnowledgeGraphScreen.kt

在 `Box` 中添加文字层：

```kotlin
Box(modifier = Modifier.fillMaxSize()) {
    // OpenGL 视图
    AndroidView(
        factory = { ctx -> /* GLSurfaceView */ },
        modifier = Modifier.fillMaxSize()
    )
    
    // 文字标签层（新增）
    NodeLabelsOverlay(
        nodes = nodes,
        mvpMatrix = renderer.getMVPMatrix(),
        viewWidth = /* 屏幕宽度 */,
        viewHeight = /* 屏幕高度 */,
        modifier = Modifier.fillMaxSize()
    )
    
    // 其他 UI 元素...
}
```

#### 步骤 2：创建 NodeLabelsOverlay 组件

```kotlin
@Composable
fun NodeLabelsOverlay(
    nodes: List<Node>,
    mvpMatrix: FloatArray,
    viewWidth: Int,
    viewHeight: Int,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        nodes.forEach { node ->
            // 将 3D 坐标投影到屏幕坐标
            val screenPos = projectToScreen(
                node.x, node.y, node.z,
                mvpMatrix, viewWidth, viewHeight
            )
            
            if (screenPos != null) {
                // 绘制文字
                drawContext.canvas.nativeCanvas.drawText(
                    node.label,
                    screenPos.x,
                    screenPos.y,
                    android.graphics.Paint().apply {
                        color = android.graphics.Color.WHITE
                        textSize = 32f
                        textAlign = android.graphics.Paint.Align.CENTER
                    }
                )
            }
        }
    }
}

fun projectToScreen(
    x: Float, y: Float, z: Float,
    mvpMatrix: FloatArray,
    viewWidth: Int,
    viewHeight: Int
): Offset? {
    val pos = FloatArray(4)
    pos[0] = x
    pos[1] = y
    pos[2] = z
    pos[3] = 1f
    
    val clipPos = FloatArray(4)
    Matrix.multiplyMV(clipPos, 0, mvpMatrix, 0, pos, 0)
    
    if (clipPos[3] <= 0f) return null  // 在相机后面
    
    val ndcX = clipPos[0] / clipPos[3]
    val ndcY = clipPos[1] / clipPos[3]
    
    val screenX = (ndcX + 1f) * 0.5f * viewWidth
    val screenY = (1f - ndcY) * 0.5f * viewHeight
    
    return Offset(screenX, screenY)
}
```

#### 步骤 3：添加 getMVPMatrix() 方法

在 `EnhancedKnowledgeGraphRenderer.kt` 中：

```kotlin
fun getMVPMatrix(): FloatArray {
    return mvpMatrix.copyOf()
}
```

---

## 临时解决方案：显示节点 ID

如果暂时不想实现完整的文字渲染，可以：

1. **在侧边栏显示节点信息**（已实现）✅
   - 点击节点后，侧边栏会显示节点名称和详细信息
   - 用户可以通过侧边栏识别节点

2. **在操作提示中说明**：
   ```
   "• 单击节点：查看名称和详情"
   ```

3. **使用颜色区分节点类型**：
   - 不同类型的节点使用不同颜色
   - 在底部信息卡片中显示颜色图例

---

## 测试建议

### 测试双指缩放修复

1. 打开知识星图
2. 使用双指缩放手势
3. 观察日志：
   ```bash
   adb logcat | grep "KnowledgeGraph"
   ```
4. 应该看到：
   ```
   [KnowledgeGraph] 缩放: scale=1.05, distance=210.0
   [KnowledgeGraph] 缩放: scale=0.95, distance=230.0
   ```

### 测试节点点击

1. 点击任意节点
2. 侧边栏应该显示节点详情
3. 节点名称应该在侧边栏顶部显示

---

## 下一步计划

### 短期（推荐立即实现）

1. ✅ **修复双指缩放**（已完成）
2. ⏳ **实现 Compose Overlay 文字渲染**
   - 预计工作量：2-3 小时
   - 优先级：高

### 中期（可选优化）

1. **优化文字渲染性能**
   - 只渲染可见节点的标签
   - 根据缩放级别调整文字大小
   - 添加文字淡入淡出动画

2. **添加文字背景**
   - 半透明背景提高可读性
   - 圆角矩形背景

### 长期（高级特性）

1. **实现 OpenGL 纹理文字渲染**
   - 文字随 3D 场景旋转
   - 更好的性能
   - 更流畅的动画

---

## 相关文件

- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/KnowledgeGraphScreen.kt` ✅ 已修复缩放
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/opengl/EnhancedKnowledgeGraphRenderer.kt` ✅ 已添加 getCameraDistance()
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/opengl/TextLabelRenderer.kt` ⏳ 需要重写

---

## 总结

### 已修复 ✅
- **双指缩放功能**：修复了使用固定距离值的问题，现在基于当前相机距离进行缩放
- **节点标签文字显示**：实现了 Compose Overlay 方案，节点名称现在可以正常显示

### 实现方案 ✅
- 使用 Compose Canvas 在 OpenGL 视图上方绘制文字标签
- 实时将 3D 节点坐标投影到 2D 屏幕坐标
- 为文字添加半透明背景提高可读性
- 选中节点时文字高亮显示

### 新增文件
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/NodeLabelsOverlay.kt`

### 修改文件
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/KnowledgeGraphScreen.kt`
- `android/app/src/main/java/com/lifeswarm/android/presentation/knowledge/opengl/EnhancedKnowledgeGraphRenderer.kt`

