#ifndef STARMAP_RENDERER_H
#define STARMAP_RENDERER_H

#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <native_window/external_window.h>
#include <vector>
#include <map>
#include <string>
#include <cmath>
#include "starmap_types.h"

class StarMapRenderer {
public:
    StarMapRenderer();
    ~StarMapRenderer();
    
    // 初始化
    bool init(OHNativeWindow* window, int width, int height);
    void destroy();
    
    // 设置数据
    void setNodes(const std::vector<StarNode>& nodes);
    void setLinks(const std::vector<StarLink>& links);
    void setTextTexture(int nodeIdx, const uint8_t* pixels, int width, int height);
    
    // 视角控制
    void setRotation(float rotX, float rotY);
    void setZoom(float zoom);
    void setOffset(float offsetX, float offsetY);
    void resetTarget();  // 重置相机目标点到原点
    
    // 选中节点
    void selectNode(int index);
    int getSelectedNode() const { return selectedNodeIdx_; }
    
    // 聚焦到节点（平滑动画）
    void focusOnNode(int index);
    bool isFocusAnimating() const { return focusAnimating_; }
    
    // 获取节点关系信息
    struct NodeRelation {
        std::string targetName;
        std::string targetCategory;
        float strength;
        int targetIdx;  // 添加目标节点索引
    };
    std::vector<NodeRelation> getNodeRelations(int nodeIdx);
    
    // 渲染
    void render();
    void renderStarfieldOnly();  // 纯星空渲染模式（无节点、无连线）
    void updateAnimation(float deltaTime);
    
    // 力导向布局
    void updateForceLayout();
    
    // 点击检测
    int hitTest(float screenX, float screenY);
    
    // 获取节点屏幕坐标（用于文字标签）
    std::vector<ScreenPosition> getNodeScreenPositions();
    
private:
    // EGL
    EGLDisplay eglDisplay_ = EGL_NO_DISPLAY;
    EGLSurface eglSurface_ = EGL_NO_SURFACE;
    EGLContext eglContext_ = EGL_NO_CONTEXT;
    
    // 窗口尺寸
    int width_ = 0;
    int height_ = 0;
    
    // 着色器程序
    GLuint nodeProgram_ = 0;
    GLuint lineProgram_ = 0;
    GLuint starProgram_ = 0;
    GLuint particleProgram_ = 0;
    GLuint textProgram_ = 0;
    GLuint nebulaProgram_ = 0;  // 星云背景
    
    // VBO
    GLuint nodeVBO_ = 0;
    GLuint lineVBO_ = 0;
    GLuint starVBO_ = 0;
    GLuint particleVBO_ = 0;
    GLuint textVBO_ = 0;
    GLuint nebulaVBO_ = 0;  // 星云全屏四边形
    
    // 数据
    std::vector<StarNode> nodes_;
    std::vector<StarLink> links_;
    std::vector<BackgroundStar> bgStars_;
    std::vector<FlowParticle> particles_;
    std::vector<TextLabel> textLabels_;
    GLuint textAtlasTexture_ = 0;
    
    // 视角
    float rotationX_ = 0.3f;
    float rotationY_ = 0.0f;
    float zoom_ = 1.0f;
    float offsetX_ = 0.0f;
    float offsetY_ = 0.0f;
    
    // 相机观察目标点（世界坐标）
    float targetX_ = 0.0f;
    float targetY_ = 0.0f;
    float targetZ_ = 0.0f;
    
    // 选中
    int selectedNodeIdx_ = -1;
    
    // 聚焦动画状态
    bool focusAnimating_ = false;
    int focusTargetIdx_ = -1;
    float focusProgress_ = 0.0f;
    float focusStartRotX_ = 0.0f;
    float focusStartRotY_ = 0.0f;
    float focusTargetRotX_ = 0.0f;
    float focusTargetRotY_ = 0.0f;
    float focusStartZoom_ = 1.0f;
    float focusTargetZoom_ = 1.0f;
    // 相机目标点动画
    float focusStartTargetX_ = 0.0f;
    float focusStartTargetY_ = 0.0f;
    float focusStartTargetZ_ = 0.0f;
    float focusEndTargetX_ = 0.0f;
    float focusEndTargetY_ = 0.0f;
    float focusEndTargetZ_ = 0.0f;
    static constexpr float FOCUS_DURATION = 0.8f;  // 动画持续时间（秒）- 稍长一点更有感觉
    
    // 动画
    float time_ = 0.0f;
    bool autoRotate_ = true;
    
    // 曲线线段顶点数
    int lineVertexCount_ = 0;
    
    // 力导向参数 - 调整为更小的坐标范围
    static constexpr float REPULSION = 800.0f;
    static constexpr float ATTRACTION = 0.05f;
    static constexpr float DAMPING = 0.85f;
    static constexpr float CENTER_GRAVITY = 0.02f;
    
    // 透视参数
    static constexpr float PERSPECTIVE = 500.0f;
    static constexpr float NEAR_PLANE = 0.1f;
    static constexpr float FAR_PLANE = 1000.0f;
    
    // 颜色映射
    std::map<std::string, CategoryColor> categoryColors_;
    
    // 私有方法
    bool initEGL(OHNativeWindow* window);
    bool initShaders();
    void initBackgroundStars();
    void initFlowParticles();
    void initCategoryColors();
    
    void computeMVPMatrix(float* mvp);
    void project3D(float x, float y, float z, float& screenX, float& screenY, float& scale);
    
    void drawBackground();
    void drawNebula();  // 星云背景
    void drawLinks();
    void drawParticles();
    void drawNodes();
    void drawTextLabels();
    
    void updateNodeVBO();
    void updateLineVBO();
    void updateParticleVBO();
    void updateTextVBO();
    
    CategoryColor getNodeColor(const StarNode& node);
};

#endif // STARMAP_RENDERER_H
