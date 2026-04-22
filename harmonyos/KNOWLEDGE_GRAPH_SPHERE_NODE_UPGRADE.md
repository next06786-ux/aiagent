# 知识图谱节点升级：从点精灵到3D球体

## 问题分析

当前HarmonyOS知识图谱使用`GL_POINTS`（点精灵）渲染节点，而Android端使用真实的3D球体几何体（mesh）。这导致：

1. **视觉效果差异大**：点精灵是2D的，无法实现真实的3D星球效果
2. **光照效果受限**：点精灵无法正确计算法线，光照效果不真实
3. **细节不足**：点精灵分辨率有限，无法展现星球表面细节

## Android端实现方式

Android使用`SphereNodeRenderer.kt`，核心特点：

1. **真实3D几何体**：生成球体mesh（16x16细分）
2. **顶点属性**：位置、法线、纹理坐标
3. **每个节点独立绘制**：使用`glDrawElements`绘制三角形
4. **完整的光照计算**：基于法线的漫反射、镜面反射
5. **程序化纹理**：使用噪声函数生成星球表面

## 修改方案

### 方案1：完全重写（推荐，效果最好）

创建新的球体渲染器类，仿照Android实现：

```cpp
// 新文件：sphere_node_renderer.h/cpp
class SphereNodeRenderer {
private:
    GLuint sphereVBO_;
    GLuint sphereIBO_;
    int indexCount_;
    
    // 生成球体几何数据
    void initSphereGeometry();
    
    // 绘制单个球体
    void drawSphere(const StarNode& node, const float* mvpMatrix, float time);
    
public:
    void init();
    void draw(const std::vector<StarNode>& nodes, const float* mvpMatrix, float time);
    void cleanup();
};
```

**优点**：
- 效果与Android完全一致
- 真实的3D光照
- 可以添加更多细节（环、卫星等）

**缺点**：
- 需要较多代码改动
- 性能开销稍大（但可接受）

### 方案2：改进点精灵shader（快速方案）

保持`GL_POINTS`，但改进fragment shader，模拟球体效果：

**优点**：
- 代码改动最小
- 性能最好

**缺点**：
- 效果不如真实球体
- 光照计算简化
- 无法添加复杂装饰

## 推荐实施步骤（方案1）

### 第1步：创建球体几何生成器

```cpp
// sphere_node_renderer.cpp
void SphereNodeRenderer::initSphereGeometry() {
    const int latBands = 16;
    const int lonBands = 16;
    std::vector<float> vertices;
    std::vector<uint16_t> indices;
    
    // 生成顶点（位置+法线+纹理坐标）
    for (int lat = 0; lat <= latBands; lat++) {
        float theta = lat * M_PI / latBands;
        float sinTheta = sin(theta);
        float cosTheta = cos(theta);
        
        for (int lon = 0; lon <= lonBands; lon++) {
            float phi = lon * 2 * M_PI / lonBands;
            float sinPhi = sin(phi);
            float cosPhi = cos(phi);
            
            // 位置（单位球）
            float x = cosPhi * sinTheta;
            float y = cosTheta;
            float z = sinPhi * sinTheta;
            
            // 法线（与位置相同）
            float nx = x, ny = y, nz = z;
            
            // 纹理坐标
            float u = 1.0f - (float)lon / lonBands;
            float v = 1.0f - (float)lat / latBands;
            
            vertices.push_back(x);
            vertices.push_back(y);
            vertices.push_back(z);
            vertices.push_back(nx);
            vertices.push_back(ny);
            vertices.push_back(nz);
            vertices.push_back(u);
            vertices.push_back(v);
        }
    }
    
    // 生成索引
    for (int lat = 0; lat < latBands; lat++) {
        for (int lon = 0; lon < lonBands; lon++) {
            int first = lat * (lonBands + 1) + lon;
            int second = first + lonBands + 1;
            
            indices.push_back(first);
            indices.push_back(second);
            indices.push_back(first + 1);
            
            indices.push_back(second);
            indices.push_back(second + 1);
            indices.push_back(first + 1);
        }
    }
    
    indexCount_ = indices.size();
    
    // 创建VBO和IBO
    glGenBuffers(1, &sphereVBO_);
    glGenBuffers(1, &sphereIBO_);
    
    glBindBuffer(GL_ARRAY_BUFFER, sphereVBO_);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(float), 
                 vertices.data(), GL_STATIC_DRAW);
    
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sphereIBO_);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.size() * sizeof(uint16_t), 
                 indices.data(), GL_STATIC_DRAW);
}
```

### 第2步：修改shader（使用Android的shader）

直接复制Android的shader代码到`shader_utils.h`：

```cpp
// 球体顶点着色器
const char* const SPHERE_VERTEX_SHADER = R"(#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uMVPMatrix;
uniform vec3 uNodePosition;
uniform float uNodeSize;
uniform float uTime;
uniform int uIsSelected;

out vec3 vNormal;
out vec3 vViewDir;
out vec3 vWorldPos;
out float vPulse;

void main() {
    // 脉冲动画
    float pulse = sin(uTime * 2.0) * 0.08 + 1.0;
    if (uIsSelected == 1) {
        pulse = sin(uTime * 4.0) * 0.15 + 1.15;
    }
    
    // 缩放球体
    vec3 scaledPos = aPosition * uNodeSize * pulse;
    vec3 worldPos = scaledPos + uNodePosition;
    
    gl_Position = uMVPMatrix * vec4(worldPos, 1.0);
    
    vNormal = normalize(aNormal);
    vWorldPos = worldPos;
    vViewDir = normalize(-worldPos);  // 简化版
    vPulse = pulse;
}
)";

// 球体片段着色器（完整复制Android版本）
const char* const SPHERE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec3 vNormal;
in vec3 vViewDir;
in vec3 vWorldPos;
in float vPulse;

uniform vec3 uNodeColor;
uniform vec3 uLightDir;
uniform int uIsSelected;
uniform float uTime;

out vec4 fragColor;

// [复制Android的完整shader代码]
// 包括：噪声函数、FBM、地形着色、光照计算等
)";
```

### 第3步：修改渲染循环

```cpp
void StarMapRenderer::drawNodes() {
    if (nodes_.empty()) return;
    
    glUseProgram(sphereProgram_);
    
    // 绑定球体几何
    glBindBuffer(GL_ARRAY_BUFFER, sphereVBO_);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sphereIBO_);
    
    // 设置顶点属性
    glEnableVertexAttribArray(0);  // 位置
    glEnableVertexAttribArray(1);  // 法线
    glEnableVertexAttribArray(2);  // 纹理坐标
    
    int stride = 8 * sizeof(float);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, 0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, (void*)(3 * sizeof(float)));
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, (void*)(6 * sizeof(float)));
    
    // 光源方向
    float lightDir[3] = {0.5f, 0.8f, 0.3f};
    
    // 为每个节点绘制球体
    for (size_t i = 0; i < nodes_.size(); i++) {
        const auto& node = nodes_[i];
        int isSelected = (i == selectedNodeIdx_) ? 1 : 0;
        
        // 计算节点大小
        float nodeSize = 3.0f + (node.connections / 10.0f) * 8.0f;
        
        // 设置uniforms
        GLint mvpLoc = glGetUniformLocation(sphereProgram_, "uMVPMatrix");
        GLint posLoc = glGetUniformLocation(sphereProgram_, "uNodePosition");
        GLint sizeLoc = glGetUniformLocation(sphereProgram_, "uNodeSize");
        GLint colorLoc = glGetUniformLocation(sphereProgram_, "uNodeColor");
        GLint timeLoc = glGetUniformLocation(sphereProgram_, "uTime");
        GLint selectedLoc = glGetUniformLocation(sphereProgram_, "uIsSelected");
        GLint lightLoc = glGetUniformLocation(sphereProgram_, "uLightDir");
        
        glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvpMatrix);
        glUniform3f(posLoc, node.x, node.y, node.z);
        glUniform1f(sizeLoc, nodeSize);
        glUniform3f(colorLoc, node.r, node.g, node.b);
        glUniform1f(timeLoc, time_);
        glUniform1i(selectedLoc, isSelected);
        glUniform3fv(lightLoc, 1, lightDir);
        
        // 绘制球体
        glDrawElements(GL_TRIANGLES, indexCount_, GL_UNSIGNED_SHORT, 0);
    }
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    glDisableVertexAttribArray(2);
}
```

## 性能考虑

- **顶点数**：16x16球体 = 289顶点，1536三角形
- **50个节点**：约14,450顶点，76,800三角形
- **现代GPU**：完全可以流畅运行（60fps+）

## 后续优化

1. **实例化渲染**：使用`glDrawElementsInstanced`一次绘制所有球体
2. **LOD**：远处节点使用低细分球体
3. **光晕效果**：添加外层大气层（Android已实现）
4. **装饰元素**：环、卫星等（参考Web端）

## 时间估算

- **方案1（完整实现）**：4-6小时
- **方案2（改进shader）**：1-2小时

## 建议

**立即采用方案2**（改进shader），快速改善视觉效果。然后在后续版本中实施方案1，达到Android的完整效果。


---

## 实施进度

### ✅ 已完成

1. **添加球体着色器**（`shader_utils.h`）
   - `SPHERE_VERTEX_SHADER` - 3D球体顶点着色器
   - `SPHERE_FRAGMENT_SHADER` - 行星表面着色器（FBM噪声、地形层、云层、城市灯光、大气层）
   - `GLOW_VERTEX_SHADER` - 大气光晕顶点着色器
   - `GLOW_FRAGMENT_SHADER` - 边缘光照片段着色器

2. **修改渲染器头文件**（`starmap_renderer.h`）
   - 添加 `sphereProgram_` 和 `glowProgram_` 着色器程序
   - 添加 `sphereVBO_`, `sphereIBO_`, `sphereIndexCount_` 球体几何数据
   - 添加 `initSphereGeometry()` 方法声明
   - 添加 `drawSphereNodes()` 方法声明

3. **实现球体几何生成**（`starmap_renderer.cpp`）
   - 实现 `initSphereGeometry()` 方法
   - 生成16x16细分的球体网格
   - 包含位置、法线、纹理坐标
   - 创建VBO和IBO

4. **实现球体节点绘制**（`starmap_renderer.cpp`）
   - 实现 `drawSphereNodes()` 方法
   - 为每个节点绘制3D球体本体
   - 绘制大气光晕效果
   - 根据连接数动态调整节点大小
   - 支持选中状态高亮

5. **修改render()方法**（`starmap_renderer.cpp`）
   - 将 `drawNodes()` 替换为 `drawSphereNodes()`
   - 现在使用真实的3D球体渲染，而不是点精灵

### 🔄 下一步

1. **编译测试**
   - 编译HarmonyOS项目
   - 检查是否有编译错误
   - 修复任何shader或OpenGL相关错误

2. **运行时测试**
   - 启动应用并进入知识图谱页面
   - 验证球体节点是否正确显示
   - 检查3D交互（旋转、缩放）是否正常
   - 测试节点选择功能

3. **性能优化**（可选）
   - 实现实例化渲染（`glDrawElementsInstanced`）
   - 添加LOD（远处节点使用低细分）
   - 优化shader性能

4. **视觉调优**（可选）
   - 调整星球表面细节参数
   - 优化光照和大气效果
   - 匹配Android端的视觉风格

## 实施说明

采用了**方案1（完整3D球体实现）**，与Android端保持一致：

- ✅ 真实3D几何体（16x16细分球体mesh）
- ✅ 完整的顶点属性（位置、法线、纹理坐标）
- ✅ 每个节点独立绘制（`glDrawElements`）
- ✅ 完整的光照计算（基于法线）
- ✅ 程序化纹理（噪声函数生成星球表面）
- ✅ 大气光晕效果（边缘光照）

这将提供与Android端完全一致的视觉效果。
