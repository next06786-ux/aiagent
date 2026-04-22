#ifndef KNOWLEDGE_GRAPH_RENDERER_H
#define KNOWLEDGE_GRAPH_RENDERER_H

#include <GLES3/gl3.h>
#include <vector>
#include <string>
#include <memory>

// 前向声明
class BackgroundStarRenderer;
class EnhancedLineRenderer;
class FlowParticleRenderer;
class SphereNodeRenderer;
class TextLabelRenderer;

/**
 * 节点数据结构
 */
struct Node {
    std::string id;
    std::string label;
    float x, y, z;
    float radius;
    float color[4];  // RGBA
    int layer;
    bool isSelf;
};

/**
 * 连线数据结构
 */
struct Edge {
    std::string id;
    std::string source;
    std::string target;
    float strength;
    float color[4];  // RGBA
};

/**
 * 增强版知识图谱渲染器 - OpenGL ES 3.0
 * 移植自 Android Kotlin 实现
 */
class KnowledgeGraphRenderer {
public:
    KnowledgeGraphRenderer();
    ~KnowledgeGraphRenderer();
    
    // 初始化
    void init();
    
    // 渲染
    void render(int width, int height);
    
    // 更新数据
    void updateGraph(const std::vector<Node>& nodes, const std::vector<Edge>& edges);
    
    // 相机控制
    void rotateCamera(float deltaX, float deltaY);
    void setCameraDistance(float distance);
    float getCameraDistance() const { return cameraDistance; }
    void focusOnNode(const std::string& nodeId);
    void resetCamera();
    
    // 交互
    std::string detectNodeClick(float screenX, float screenY, int screenWidth, int screenHeight);
    
    // 清理
    void cleanup();
    
private:
    // 子渲染器
    std::unique_ptr<BackgroundStarRenderer> backgroundStarRenderer;
    std::unique_ptr<EnhancedLineRenderer> enhancedLineRenderer;
    std::unique_ptr<FlowParticleRenderer> flowParticleRenderer;
    std::unique_ptr<SphereNodeRenderer> sphereNodeRenderer;
    std::unique_ptr<TextLabelRenderer> textLabelRenderer;
    
    // 数据
    std::vector<Node> nodes;
    std::vector<Edge> edges;
    
    // 矩阵
    float viewMatrix[16];
    float projectionMatrix[16];
    float mvpMatrix[16];
    
    // 相机参数
    float cameraDistance;
    float cameraAngleX;
    float cameraAngleY;
    float targetX, targetY, targetZ;
    
    // 选中节点
    int selectedNodeIdx;
    
    // 聚焦动画
    bool focusAnimating;
    float focusProgress;
    float focusStartTargetX, focusStartTargetY, focusStartTargetZ;
    float focusEndTargetX, focusEndTargetY, focusEndTargetZ;
    float focusStartRotX, focusStartRotY;
    float focusTargetRotX, focusTargetRotY;
    float focusStartZoom, focusTargetZoom;
    
    // 时间
    float time;
    long long lastFrameTime;
    
    // 自动旋转
    bool autoRotate;
    
    // 私有方法
    void computeMVPMatrix();
    void updateAnimation(float deltaTime);
    float easeInOutCubic(float t);
    int findNodeIndex(const std::string& nodeId);
};

#endif // KNOWLEDGE_GRAPH_RENDERER_H
