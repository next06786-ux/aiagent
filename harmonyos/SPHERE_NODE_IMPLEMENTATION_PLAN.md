# 球体节点实施计划

## 当前状态
- 使用 `GL_POINTS` (点精灵) 渲染节点
- shader已经有星球效果，但受限于点精灵

## 目标
- 改用真实3D球体几何体（mesh）
- 完全对齐Android实现

## 需要修改的文件

### 1. `starmap_renderer.h`
添加球体几何数据成员：
```cpp
// 球体几何
GLuint sphereVBO_ = 0;
GLuint sphereIBO_ = 0;
int sphereIndexCount_ = 0;

// 球体shader程序
GLuint sphereProgram_ = 0;
GLuint glowProgram_ = 0;

// 初始化球体几何
void initSphereGeometry();
```

### 2. `starmap_renderer.cpp`
- 添加 `initSphereGeometry()` 方法
- 修改 `initShaders()` 创建球体shader
- 完全重写 `drawNodes()` 方法

### 3. `shader_utils.h`
- 添加 `SPHERE_VERTEX_SHADER`
- 添加 `SPHERE_FRAGMENT_SHADER`
- 添加 `GLOW_VERTEX_SHADER`
- 添加 `GLOW_FRAGMENT_SHADER`
- 保留原有的 `NODE_*_SHADER` 作为备份

## 实施步骤

1. ✅ 在shader_utils.h添加新的球体shader
2. ⏳ 在starmap_renderer.h添加成员变量
3. ⏳ 在starmap_renderer.cpp实现initSphereGeometry()
4. ⏳ 修改initShaders()
5. ⏳ 重写drawNodes()
6. ⏳ 测试编译
