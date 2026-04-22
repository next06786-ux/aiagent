#include "starmap_renderer.h"
#include "shader_utils.h"
#include <hilog/log.h>
#include <cstring>
#include <algorithm>
#include <random>

#undef LOG_TAG
#define LOG_TAG "StarMapRenderer"
#define LOGE(...) OH_LOG_ERROR(LOG_APP, __VA_ARGS__)
#define LOGI(...) OH_LOG_INFO(LOG_APP, __VA_ARGS__)

// 平滑插值函数
static inline float smoothstep(float edge0, float edge1, float x) {
    float t = std::max(0.0f, std::min(1.0f, (x - edge0) / (edge1 - edge0)));
    return t * t * (3.0f - 2.0f * t);
}

StarMapRenderer::StarMapRenderer() {
    initCategoryColors();
}

StarMapRenderer::~StarMapRenderer() {
    destroy();
}

void StarMapRenderer::initCategoryColors() {
    // 更鲜艳的颜色
    categoryColors_["自己"] = {1.0f, 0.9f, 0.3f};        // 金黄色
    categoryColors_["family"] = {1.0f, 0.35f, 0.35f};    // 红色
    categoryColors_["close_friends"] = {0.3f, 0.9f, 0.85f}; // 青色
    categoryColors_["colleagues"] = {0.3f, 0.7f, 1.0f};  // 蓝色
    categoryColors_["friends"] = {0.5f, 0.95f, 0.6f};    // 绿色
    categoryColors_["weak_ties"] = {0.7f, 0.7f, 0.75f};  // 灰白色
}

bool StarMapRenderer::init(OHNativeWindow* window, int width, int height) {
    width_ = width;
    height_ = height;
    
    if (!initEGL(window)) {
        LOGE("Failed to init EGL");
        return false;
    }
    
    if (!initShaders()) {
        LOGE("Failed to init shaders");
        return false;
    }
    
    // 创建VBO
    glGenBuffers(1, &nodeVBO_);
    glGenBuffers(1, &lineVBO_);
    glGenBuffers(1, &starVBO_);
    glGenBuffers(1, &particleVBO_);
    glGenBuffers(1, &textVBO_);
    glGenBuffers(1, &nebulaVBO_);
    
    // 初始化星云全屏四边形
    float nebulaQuad[] = {
        // 位置        // 纹理坐标
        -1.0f, -1.0f,  0.0f, 0.0f,
         1.0f, -1.0f,  1.0f, 0.0f,
         1.0f,  1.0f,  1.0f, 1.0f,
        -1.0f, -1.0f,  0.0f, 0.0f,
         1.0f,  1.0f,  1.0f, 1.0f,
        -1.0f,  1.0f,  0.0f, 1.0f,
    };
    glBindBuffer(GL_ARRAY_BUFFER, nebulaVBO_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(nebulaQuad), nebulaQuad, GL_STATIC_DRAW);
    
    initBackgroundStars();
    
    // OpenGL设置
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    // GL_PROGRAM_POINT_SIZE 在 OpenGL ES 中默认启用，不需要显式调用
    
    LOGI("StarMapRenderer initialized: %{public}dx%{public}d", width, height);
    return true;
}

bool StarMapRenderer::initEGL(OHNativeWindow* window) {
    eglDisplay_ = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (eglDisplay_ == EGL_NO_DISPLAY) {
        LOGE("eglGetDisplay failed");
        return false;
    }
    
    EGLint major, minor;
    if (!eglInitialize(eglDisplay_, &major, &minor)) {
        LOGE("eglInitialize failed");
        return false;
    }
    
    // 配置属性
    EGLint configAttribs[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 24,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT,
        EGL_NONE
    };
    
    EGLConfig config;
    EGLint numConfigs;
    if (!eglChooseConfig(eglDisplay_, configAttribs, &config, 1, &numConfigs) || numConfigs == 0) {
        LOGE("eglChooseConfig failed");
        return false;
    }
    
    // 创建Surface - 使用 EGLNativeWindowType 转换
    EGLint surfaceAttribs[] = { EGL_NONE };
    eglSurface_ = eglCreateWindowSurface(eglDisplay_, config, 
        reinterpret_cast<EGLNativeWindowType>(window), surfaceAttribs);
    if (eglSurface_ == EGL_NO_SURFACE) {
        LOGE("eglCreateWindowSurface failed");
        return false;
    }
    
    // 创建Context
    EGLint contextAttribs[] = {
        EGL_CONTEXT_CLIENT_VERSION, 3,
        EGL_NONE
    };
    eglContext_ = eglCreateContext(eglDisplay_, config, EGL_NO_CONTEXT, contextAttribs);
    if (eglContext_ == EGL_NO_CONTEXT) {
        LOGE("eglCreateContext failed");
        return false;
    }
    
    if (!eglMakeCurrent(eglDisplay_, eglSurface_, eglSurface_, eglContext_)) {
        LOGE("eglMakeCurrent failed");
        return false;
    }
    
    return true;
}

bool StarMapRenderer::initShaders() {
    LOGI("initShaders: Creating shader programs...");
    
    nodeProgram_ = ShaderUtils::createProgram(NODE_VERTEX_SHADER, NODE_FRAGMENT_SHADER);
    LOGI("nodeProgram: %{public}d", nodeProgram_);
    
    lineProgram_ = ShaderUtils::createProgram(LINE_VERTEX_SHADER, LINE_FRAGMENT_SHADER);
    LOGI("lineProgram: %{public}d", lineProgram_);
    
    starProgram_ = ShaderUtils::createProgram(STAR_VERTEX_SHADER, STAR_FRAGMENT_SHADER);
    LOGI("starProgram: %{public}d", starProgram_);
    
    particleProgram_ = ShaderUtils::createProgram(PARTICLE_VERTEX_SHADER, PARTICLE_FRAGMENT_SHADER);
    LOGI("particleProgram: %{public}d", particleProgram_);
    
    textProgram_ = ShaderUtils::createProgram(TEXT_VERTEX_SHADER, TEXT_FRAGMENT_SHADER);
    LOGI("textProgram: %{public}d", textProgram_);
    
    nebulaProgram_ = ShaderUtils::createProgram(NEBULA_VERTEX_SHADER, NEBULA_FRAGMENT_SHADER);
    LOGI("nebulaProgram: %{public}d", nebulaProgram_);
    
    bool success = nodeProgram_ != 0 && lineProgram_ != 0 && starProgram_ != 0 && particleProgram_ != 0;
    LOGI("initShaders: %{public}s", success ? "SUCCESS" : "FAILED");
    
    return success;
}

void StarMapRenderer::initBackgroundStars() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> angleDist(0.0f, 6.28318f);
    std::uniform_real_distribution<float> phaseDist(0.0f, 6.28f);
    std::uniform_real_distribution<float> speedDist(0.5f, 2.5f);
    std::uniform_real_distribution<float> randDist(0.0f, 1.0f);
    
    bgStars_.clear();
    
    // 3D球形分布的星星 - 包围整个场景
    float starFieldRadius = 600.0f;  // 星空球体半径（稍微近一点）
    
    // 远景层 - 较小但仍可见的星星（最外层）
    for (int i = 0; i < 400; i++) {
        BackgroundStar star;
        float theta = angleDist(gen);
        float phi = acos(2.0f * randDist(gen) - 1.0f);
        float r = starFieldRadius * (0.8f + randDist(gen) * 0.2f);
        
        star.x = r * sin(phi) * cos(theta);
        star.y = r * sin(phi) * sin(theta);
        star.z = r * cos(phi);
        
        star.size = 3.0f + randDist(gen) * 3.0f;  // 增大基础大小
        star.brightness = 0.4f + randDist(gen) * 0.4f;  // 增加亮度
        star.twinklePhase = phaseDist(gen);
        star.twinkleSpeed = speedDist(gen) * 0.5f;
        // 淡蓝白色
        star.r = 0.85f + randDist(gen) * 0.15f;
        star.g = 0.9f + randDist(gen) * 0.1f;
        star.b = 1.0f;
        bgStars_.push_back(star);
    }
    
    // 中景层 - 中等大小（中间层）
    for (int i = 0; i < 250; i++) {
        BackgroundStar star;
        float theta = angleDist(gen);
        float phi = acos(2.0f * randDist(gen) - 1.0f);
        float r = starFieldRadius * (0.5f + randDist(gen) * 0.3f);
        
        star.x = r * sin(phi) * cos(theta);
        star.y = r * sin(phi) * sin(theta);
        star.z = r * cos(phi);
        
        star.size = 5.0f + randDist(gen) * 5.0f;  // 更大
        star.brightness = 0.5f + randDist(gen) * 0.5f;  // 更亮
        star.twinklePhase = phaseDist(gen);
        star.twinkleSpeed = speedDist(gen);
        // 随机颜色
        float colorType = randDist(gen);
        if (colorType < 0.5f) {
            star.r = 1.0f; star.g = 1.0f; star.b = 1.0f;  // 白
        } else if (colorType < 0.75f) {
            star.r = 0.75f; star.g = 0.88f; star.b = 1.0f;  // 淡蓝
        } else {
            star.r = 1.0f; star.g = 0.95f; star.b = 0.85f;  // 淡黄
        }
        bgStars_.push_back(star);
    }
    
    // 近景层 - 大而亮的星星
    for (int i = 0; i < 120; i++) {
        BackgroundStar star;
        float theta = angleDist(gen);
        float phi = acos(2.0f * randDist(gen) - 1.0f);
        float r = starFieldRadius * (0.3f + randDist(gen) * 0.2f);
        
        star.x = r * sin(phi) * cos(theta);
        star.y = r * sin(phi) * sin(theta);
        star.z = r * cos(phi);
        
        star.size = 8.0f + randDist(gen) * 8.0f;  // 大星星
        star.brightness = 0.7f + randDist(gen) * 0.3f;  // 很亮
        star.twinklePhase = phaseDist(gen);
        star.twinkleSpeed = speedDist(gen) * 1.5f;
        // 更鲜艳的颜色
        float colorType = randDist(gen);
        if (colorType < 0.3f) {
            star.r = 1.0f; star.g = 1.0f; star.b = 1.0f;  // 亮白
        } else if (colorType < 0.5f) {
            star.r = 0.6f; star.g = 0.8f; star.b = 1.0f;  // 蓝色
        } else if (colorType < 0.7f) {
            star.r = 1.0f; star.g = 0.9f; star.b = 0.6f;  // 金黄
        } else if (colorType < 0.85f) {
            star.r = 0.95f; star.g = 0.75f; star.b = 1.0f;  // 淡紫
        } else {
            star.r = 1.0f; star.g = 0.7f; star.b = 0.6f;  // 橙红
        }
        bgStars_.push_back(star);
    }
    
    // 最近层 - 非常亮的大星星
    for (int i = 0; i < 50; i++) {
        BackgroundStar star;
        float theta = angleDist(gen);
        float phi = acos(2.0f * randDist(gen) - 1.0f);
        float r = starFieldRadius * (0.15f + randDist(gen) * 0.15f);
        
        star.x = r * sin(phi) * cos(theta);
        star.y = r * sin(phi) * sin(theta);
        star.z = r * cos(phi);
        
        star.size = 12.0f + randDist(gen) * 10.0f;  // 非常大
        star.brightness = 0.85f + randDist(gen) * 0.15f;  // 非常亮
        star.twinklePhase = phaseDist(gen);
        star.twinkleSpeed = speedDist(gen) * 2.0f;
        // 明亮的颜色
        float colorType = randDist(gen);
        if (colorType < 0.4f) {
            star.r = 1.0f; star.g = 1.0f; star.b = 1.0f;
        } else if (colorType < 0.7f) {
            star.r = 0.55f; star.g = 0.75f; star.b = 1.0f;
        } else {
            star.r = 1.0f; star.g = 0.88f; star.b = 0.55f;
        }
        bgStars_.push_back(star);
    }
    
    LOGI("initBackgroundStars: created %{public}zu bright 3D stars", bgStars_.size());
}

void StarMapRenderer::initFlowParticles() {
    particles_.clear();
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> progDist(0.0f, 1.0f);
    std::uniform_real_distribution<float> speedDist(0.15f, 0.5f);
    
    // 每条连线都有粒子，增加数量
    for (int i = 0; i < (int)links_.size(); i++) {
        // 每条线3-5个粒子，形成流动效果
        int particleCount = 3 + (i % 3);
        for (int j = 0; j < particleCount; j++) {
            FlowParticle p;
            p.linkIdx = i;
            // 均匀分布在连线上
            p.progress = (float)j / particleCount + progDist(gen) * 0.2f;
            if (p.progress > 1.0f) p.progress -= 1.0f;
            p.speed = speedDist(gen);
            particles_.push_back(p);
        }
    }
    
    LOGI("initFlowParticles: created %{public}zu particles for %{public}zu links", 
         particles_.size(), links_.size());
}

void StarMapRenderer::destroy() {
    if (nodeVBO_) glDeleteBuffers(1, &nodeVBO_);
    if (lineVBO_) glDeleteBuffers(1, &lineVBO_);
    if (starVBO_) glDeleteBuffers(1, &starVBO_);
    if (particleVBO_) glDeleteBuffers(1, &particleVBO_);
    if (textVBO_) glDeleteBuffers(1, &textVBO_);
    if (nebulaVBO_) glDeleteBuffers(1, &nebulaVBO_);
    
    if (nodeProgram_) glDeleteProgram(nodeProgram_);
    if (lineProgram_) glDeleteProgram(lineProgram_);
    if (starProgram_) glDeleteProgram(starProgram_);
    if (particleProgram_) glDeleteProgram(particleProgram_);
    if (textProgram_) glDeleteProgram(textProgram_);
    if (nebulaProgram_) glDeleteProgram(nebulaProgram_);
    
    // 删除文字纹理
    for (auto& label : textLabels_) {
        if (label.textureId) glDeleteTextures(1, &label.textureId);
    }
    textLabels_.clear();
    
    if (eglDisplay_ != EGL_NO_DISPLAY) {
        eglMakeCurrent(eglDisplay_, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        if (eglSurface_ != EGL_NO_SURFACE) eglDestroySurface(eglDisplay_, eglSurface_);
        if (eglContext_ != EGL_NO_CONTEXT) eglDestroyContext(eglDisplay_, eglContext_);
        // 不调用 eglTerminate —— EGL display 是进程全局共享的，
        // terminate 会导致其他渲染器（nebulachat）的 EGL 状态被破坏
    }
    
    eglDisplay_ = EGL_NO_DISPLAY;
    eglSurface_ = EGL_NO_SURFACE;
    eglContext_ = EGL_NO_CONTEXT;
}

void StarMapRenderer::setNodes(const std::vector<StarNode>& nodes) {
    nodes_ = nodes;
    
    LOGI("SetNodes: %{public}zu nodes received", nodes.size());
    
    // 为节点设置颜色
    for (auto& node : nodes_) {
        CategoryColor color = getNodeColor(node);
        node.r = color.r;
        node.g = color.g;
        node.b = color.b;
    }
    
    if (!nodes_.empty()) {
        LOGI("First node: name=%{public}s, pos=(%{public}.1f, %{public}.1f, %{public}.1f), color=(%{public}.2f, %{public}.2f, %{public}.2f)",
             nodes_[0].name.c_str(), nodes_[0].x, nodes_[0].y, nodes_[0].z,
             nodes_[0].r, nodes_[0].g, nodes_[0].b);
    }
    
    updateNodeVBO();
}

void StarMapRenderer::setLinks(const std::vector<StarLink>& links) {
    links_ = links;
    initFlowParticles();
    updateLineVBO();
}

CategoryColor StarMapRenderer::getNodeColor(const StarNode& node) {
    auto it = categoryColors_.find(node.category);
    if (it != categoryColors_.end()) {
        return it->second;
    }
    return {0.54f, 0.81f, 0.94f}; // 默认天蓝色
}

void StarMapRenderer::setRotation(float rotX, float rotY) {
    rotationX_ = rotX;
    rotationY_ = rotY;
    autoRotate_ = false;
    
    static int logCount = 0;
    if (logCount++ < 10) {
        LOGI("setRotation: rotX=%{public}.2f rotY=%{public}.2f", rotX, rotY);
    }
}

void StarMapRenderer::setZoom(float zoom) {
    zoom_ = std::max(0.3f, std::min(3.0f, zoom));
}

void StarMapRenderer::setOffset(float offsetX, float offsetY) {
    offsetX_ = offsetX;
    offsetY_ = offsetY;
}

void StarMapRenderer::resetTarget() {
    // 平滑动画回到原点
    focusStartTargetX_ = targetX_;
    focusStartTargetY_ = targetY_;
    focusStartTargetZ_ = targetZ_;
    focusEndTargetX_ = 0.0f;
    focusEndTargetY_ = 0.0f;
    focusEndTargetZ_ = 0.0f;
    
    focusStartRotX_ = rotationX_;
    focusStartRotY_ = rotationY_;
    focusTargetRotX_ = 0.3f;  // 默认旋转角度
    focusTargetRotY_ = 0.0f;
    
    focusStartZoom_ = zoom_;
    focusTargetZoom_ = 1.0f;
    
    focusTargetIdx_ = -1;
    focusProgress_ = 0.0f;
    focusAnimating_ = true;
    autoRotate_ = true;  // 恢复自动旋转
    
    LOGI("resetTarget: animating back to origin");
}

void StarMapRenderer::selectNode(int index) {
    selectedNodeIdx_ = index;
}

std::vector<StarMapRenderer::NodeRelation> StarMapRenderer::getNodeRelations(int nodeIdx) {
    std::vector<NodeRelation> relations;
    
    if (nodeIdx < 0 || nodeIdx >= (int)nodes_.size()) {
        return relations;
    }
    
    // 遍历所有连线，找到与该节点相关的
    for (const auto& link : links_) {
        int otherIdx = -1;
        
        if (link.sourceIdx == nodeIdx) {
            otherIdx = link.targetIdx;
        } else if (link.targetIdx == nodeIdx) {
            otherIdx = link.sourceIdx;
        }
        
        if (otherIdx >= 0 && otherIdx < (int)nodes_.size()) {
            NodeRelation rel;
            rel.targetName = nodes_[otherIdx].name;
            rel.targetCategory = nodes_[otherIdx].category;
            rel.strength = link.strength;
            rel.targetIdx = otherIdx;  // 添加目标节点索引
            relations.push_back(rel);
        }
    }
    
    return relations;
}

void StarMapRenderer::focusOnNode(int index) {
    if (index < 0 || index >= (int)nodes_.size()) {
        LOGI("focusOnNode: invalid index %{public}d", index);
        return;
    }
    
    const auto& node = nodes_[index];
    LOGI("focusOnNode: focusing on node %{public}d '%{public}s' at (%{public}.1f, %{public}.1f, %{public}.1f)",
         index, node.name.c_str(), node.x, node.y, node.z);
    
    // 保存动画起始状态
    focusStartRotX_ = rotationX_;
    focusStartRotY_ = rotationY_;
    focusStartZoom_ = zoom_;
    
    // 保存相机目标点起始位置
    focusStartTargetX_ = targetX_;
    focusStartTargetY_ = targetY_;
    focusStartTargetZ_ = targetZ_;
    
    // 目标点移动到节点位置（节点将成为屏幕中心）
    focusEndTargetX_ = node.x;
    focusEndTargetY_ = node.y;
    focusEndTargetZ_ = node.z;
    
    // 保持当前旋转角度，或者稍微调整让视角更好
    // 这里保持当前角度，让用户感觉是"飞向"节点
    focusTargetRotX_ = rotationX_;
    focusTargetRotY_ = rotationY_;
    
    // 计算目标缩放 - 聚焦后要明显放大，有"推近"的感觉
    // 目标缩放：2.0 到 3.5，让节点在屏幕中心显得更大
    focusTargetZoom_ = std::max(2.0f, std::min(3.5f, 2.5f));
    
    // 开始动画
    focusTargetIdx_ = index;
    focusProgress_ = 0.0f;
    focusAnimating_ = true;
    autoRotate_ = false;  // 停止自动旋转
    
    LOGI("focusOnNode: animation started, target=(%{public}.1f, %{public}.1f, %{public}.1f) -> (%{public}.1f, %{public}.1f, %{public}.1f), zoom=%{public}.2f->%{public}.2f",
         focusStartTargetX_, focusStartTargetY_, focusStartTargetZ_,
         focusEndTargetX_, focusEndTargetY_, focusEndTargetZ_,
         focusStartZoom_, focusTargetZoom_);
}


void StarMapRenderer::computeMVPMatrix(float* mvp) {
    // 使用标准 OpenGL 矩阵计算
    float aspect = (float)width_ / (float)height_;
    float fov = 60.0f * 3.14159265f / 180.0f;
    float tanHalfFov = tan(fov / 2.0f);
    
    float nearPlane = 1.0f;
    float farPlane = 2000.0f;
    
    // 投影矩阵 (列主序)
    float proj[16] = {0};
    proj[0] = 1.0f / (aspect * tanHalfFov);
    proj[5] = 1.0f / tanHalfFov;
    proj[10] = -(farPlane + nearPlane) / (farPlane - nearPlane);
    proj[11] = -1.0f;
    proj[14] = -(2.0f * farPlane * nearPlane) / (farPlane - nearPlane);
    
    // 相机距离 - 拉近相机让整体更大
    float cameraZ = 220.0f / zoom_;
    
    float cosX = cos(rotationX_), sinX = sin(rotationX_);
    float cosY = cos(rotationY_), sinY = sin(rotationY_);
    
    // 视图矩阵构建：
    // 1. 先平移场景，使目标点移到原点
    // 2. 再旋转
    // 3. 最后平移相机到观察位置
    
    // 旋转矩阵 R = Rx * Ry (列主序)
    // Ry: 绕Y轴旋转
    // Rx: 绕X轴旋转
    float rot[16] = {
        cosY,              0,       sinY,              0,
        sinX * sinY,       cosX,    -sinX * cosY,      0,
        -cosX * sinY,      sinX,    cosX * cosY,       0,
        0,                 0,       0,                 1
    };
    
    // 平移向量：先将目标点移到原点，再旋转，最后平移相机
    // T = -R * target + (0, 0, -cameraZ)
    float tx = -(rot[0] * targetX_ + rot[4] * targetY_ + rot[8] * targetZ_);
    float ty = -(rot[1] * targetX_ + rot[5] * targetY_ + rot[9] * targetZ_);
    float tz = -(rot[2] * targetX_ + rot[6] * targetY_ + rot[10] * targetZ_) - cameraZ;
    
    // 完整视图矩阵 (列主序)
    float view[16] = {
        cosY,              0,       sinY,              0,
        sinX * sinY,       cosX,    -sinX * cosY,      0,
        -cosX * sinY,      sinX,    cosX * cosY,       0,
        tx,                ty,      tz,                1
    };
    
    // MVP = Proj * View (列主序矩阵乘法)
    for (int col = 0; col < 4; col++) {
        for (int row = 0; row < 4; row++) {
            mvp[col * 4 + row] = 0;
            for (int k = 0; k < 4; k++) {
                mvp[col * 4 + row] += proj[k * 4 + row] * view[col * 4 + k];
            }
        }
    }
}

void StarMapRenderer::project3D(float x, float y, float z, float& screenX, float& screenY, float& scale) {
    // 绕Y轴旋转
    float cosY = cos(rotationY_), sinY = sin(rotationY_);
    float x1 = x * cosY - z * sinY;
    float z1 = x * sinY + z * cosY;
    
    // 绕X轴旋转
    float cosX = cos(rotationX_), sinX = sin(rotationX_);
    float y1 = y * cosX - z1 * sinX;
    float z2 = y * sinX + z1 * cosX;
    
    // 透视投影
    float depth = z2 + PERSPECTIVE;
    scale = PERSPECTIVE / std::max(depth, 100.0f);
    
    screenX = x1 * scale * zoom_ + offsetX_;
    screenY = y1 * scale * zoom_ + offsetY_;
}

void StarMapRenderer::updateAnimation(float deltaTime) {
    time_ += deltaTime;
    
    // 聚焦动画
    if (focusAnimating_) {
        focusProgress_ += deltaTime / FOCUS_DURATION;
        
        if (focusProgress_ >= 1.0f) {
            // 动画完成
            focusProgress_ = 1.0f;
            focusAnimating_ = false;
            rotationX_ = focusTargetRotX_;
            rotationY_ = focusTargetRotY_;
            zoom_ = focusTargetZoom_;
            // 设置最终目标点位置
            targetX_ = focusEndTargetX_;
            targetY_ = focusEndTargetY_;
            targetZ_ = focusEndTargetZ_;
            selectedNodeIdx_ = focusTargetIdx_;
            LOGI("focusOnNode: animation completed, target=(%{public}.1f, %{public}.1f, %{public}.1f)", 
                 targetX_, targetY_, targetZ_);
        } else {
            float t = focusProgress_;
            
            // 位置/旋转使用 ease-in-out 缓动，更平滑
            // easeInOutCubic
            float posEased;
            if (t < 0.5f) {
                posEased = 4.0f * t * t * t;
            } else {
                float f = 2.0f * t - 2.0f;
                posEased = 0.5f * f * f * f + 1.0f;
            }
            
            // 插值相机目标点（节点将移动到屏幕中心）
            targetX_ = focusStartTargetX_ + (focusEndTargetX_ - focusStartTargetX_) * posEased;
            targetY_ = focusStartTargetY_ + (focusEndTargetY_ - focusStartTargetY_) * posEased;
            targetZ_ = focusStartTargetZ_ + (focusEndTargetZ_ - focusStartTargetZ_) * posEased;
            
            // 插值旋转角度（如果有变化）
            rotationX_ = focusStartRotX_ + (focusTargetRotX_ - focusStartRotX_) * posEased;
            
            // 处理Y轴旋转的环绕问题（选择最短路径）
            float deltaY = focusTargetRotY_ - focusStartRotY_;
            // 归一化到 -PI 到 PI
            while (deltaY > 3.14159f) deltaY -= 6.28318f;
            while (deltaY < -3.14159f) deltaY += 6.28318f;
            rotationY_ = focusStartRotY_ + deltaY * posEased;
            
            // 缩放使用特殊曲线：先拉远（缩小）再推近（放大）
            // 在 t=0.3 时达到最远（zoom 最小），然后推近到目标
            float zoomEased;
            if (t < 0.3f) {
                // 前30%：从起始缩放拉远到最小值
                float pullBackT = t / 0.3f;
                // ease-out for pull back
                float pullEased = 1.0f - (1.0f - pullBackT) * (1.0f - pullBackT);
                // 拉远到起始缩放的 50%
                float minZoom = focusStartZoom_ * 0.5f;
                zoomEased = focusStartZoom_ + (minZoom - focusStartZoom_) * pullEased;
            } else {
                // 后70%：从最小值推近到目标缩放
                float pushT = (t - 0.3f) / 0.7f;
                // ease-out for push in (更快地推近)
                float pushEased = 1.0f - (1.0f - pushT) * (1.0f - pushT) * (1.0f - pushT);
                float minZoom = focusStartZoom_ * 0.5f;
                zoomEased = minZoom + (focusTargetZoom_ - minZoom) * pushEased;
            }
            zoom_ = zoomEased;
        }
    }
    // 自动旋转（聚焦动画时不旋转）
    else if (autoRotate_) {
        rotationY_ += deltaTime * 0.3f;
    }
    
    // 更新星星闪烁
    for (auto& star : bgStars_) {
        star.twinklePhase += deltaTime * star.twinkleSpeed;
    }
    
    // 更新流光粒子
    for (auto& p : particles_) {
        p.progress += deltaTime * p.speed;
        if (p.progress > 1.0f) p.progress -= 1.0f;
    }
}

void StarMapRenderer::updateForceLayout() {
    if (nodes_.empty()) return;
    
    // 重置速度
    for (auto& node : nodes_) {
        node.vx = 0;
        node.vy = 0;
        node.vz = 0;
    }
    
    // 节点间斥力
    for (size_t i = 0; i < nodes_.size(); i++) {
        for (size_t j = i + 1; j < nodes_.size(); j++) {
            float dx = nodes_[j].x - nodes_[i].x;
            float dy = nodes_[j].y - nodes_[i].y;
            float dz = nodes_[j].z - nodes_[i].z;
            float dist = sqrt(dx*dx + dy*dy + dz*dz);
            if (dist < 1.0f) dist = 1.0f;
            
            float force = REPULSION / (dist * dist);
            float fx = (dx / dist) * force;
            float fy = (dy / dist) * force;
            float fz = (dz / dist) * force;
            
            nodes_[i].vx -= fx;
            nodes_[i].vy -= fy;
            nodes_[i].vz -= fz;
            nodes_[j].vx += fx;
            nodes_[j].vy += fy;
            nodes_[j].vz += fz;
        }
    }
    
    // 连线引力
    for (const auto& link : links_) {
        if (link.sourceIdx < 0 || link.sourceIdx >= (int)nodes_.size()) continue;
        if (link.targetIdx < 0 || link.targetIdx >= (int)nodes_.size()) continue;
        
        auto& src = nodes_[link.sourceIdx];
        auto& tgt = nodes_[link.targetIdx];
        
        float dx = tgt.x - src.x;
        float dy = tgt.y - src.y;
        float dz = tgt.z - src.z;
        float dist = sqrt(dx*dx + dy*dy + dz*dz);
        if (dist < 1.0f) dist = 1.0f;
        
        float force = dist * ATTRACTION * link.strength;
        float fx = (dx / dist) * force;
        float fy = (dy / dist) * force;
        float fz = (dz / dist) * force;
        
        src.vx += fx;
        src.vy += fy;
        src.vz += fz;
        tgt.vx -= fx;
        tgt.vy -= fy;
        tgt.vz -= fz;
    }
    
    // 中心引力 + 更新位置
    for (auto& node : nodes_) {
        node.vx -= node.x * CENTER_GRAVITY;
        node.vy -= node.y * CENTER_GRAVITY;
        node.vz -= node.z * CENTER_GRAVITY;
        
        // 速度限制
        float speed = sqrt(node.vx*node.vx + node.vy*node.vy + node.vz*node.vz);
        if (speed > 5.0f) {
            node.vx = (node.vx / speed) * 5.0f;
            node.vy = (node.vy / speed) * 5.0f;
            node.vz = (node.vz / speed) * 5.0f;
        }
        
        node.x += node.vx;
        node.y += node.vy;
        node.z += node.vz;
        
        // 限制节点范围
        float maxRange = 100.0f;  // 缩小范围
        node.x = std::max(-maxRange, std::min(maxRange, node.x));
        node.y = std::max(-maxRange, std::min(maxRange, node.y));
        node.z = std::max(-maxRange, std::min(maxRange, node.z));
        
        node.vx *= DAMPING;
        node.vy *= DAMPING;
        node.vz *= DAMPING;
    }
    
    updateNodeVBO();
    updateLineVBO();
}

int StarMapRenderer::hitTest(float screenX, float screenY) {
    float mvp[16];
    computeMVPMatrix(mvp);
    
    // 找到最大连接数用于计算节点大小
    int maxConnections = 1;
    for (const auto& node : nodes_) {
        if (node.connections > maxConnections) {
            maxConnections = node.connections;
        }
    }
    
    int closestIdx = -1;
    float closestDist = 999999.0f;
    
    // HarmonyOS 触摸坐标可能是 vp 单位，需要转换
    // 假设 density 约为 3.0 (常见的 1080p 设备)
    // 但实际上 Stack 的 onTouch 返回的坐标应该已经是相对于组件的像素坐标
    float touchX = screenX;
    float touchY = screenY;
    
    LOGI("hitTest: touchX=%{public}.1f touchY=%{public}.1f, nodes=%{public}zu, screen=%{public}dx%{public}d", 
         touchX, touchY, nodes_.size(), width_, height_);
    
    for (size_t i = 0; i < nodes_.size(); i++) {
        const auto& node = nodes_[i];
        
        // MVP 矩阵是列主序，变换公式: result = MVP * vec4(pos, 1.0)
        float clipX = mvp[0] * node.x + mvp[4] * node.y + mvp[8] * node.z + mvp[12];
        float clipY = mvp[1] * node.x + mvp[5] * node.y + mvp[9] * node.z + mvp[13];
        float clipW = mvp[3] * node.x + mvp[7] * node.y + mvp[11] * node.z + mvp[15];
        
        if (clipW <= 0.1f) continue;  // 节点在相机后面
        
        float ndcX = clipX / clipW;
        float ndcY = clipY / clipW;
        
        // NDC 到屏幕坐标 (NDC范围是-1到1)
        float nodeScreenX = (ndcX + 1.0f) * 0.5f * width_;
        float nodeScreenY = (1.0f - ndcY) * 0.5f * height_;  // Y轴翻转
        
        float dx = touchX - nodeScreenX;
        float dy = touchY - nodeScreenY;
        float dist = sqrt(dx*dx + dy*dy);
        
        // 使用较大的固定点击半径，确保容易点击
        float hitRadius = 80.0f;  // 增大到 80 像素
        
        // 打印所有节点的调试信息（前10个）
        if (i < 10) {
            LOGI("hitTest: node[%{public}zu] '%{public}s' screen=(%{public}.1f, %{public}.1f), dist=%{public}.1f, radius=%{public}.1f", 
                 i, node.name.c_str(), nodeScreenX, nodeScreenY, dist, hitRadius);
        }
        
        if (dist < hitRadius && dist < closestDist) {
            closestDist = dist;
            closestIdx = (int)i;
            LOGI("hitTest: MATCH! node %{public}d '%{public}s' at dist %{public}.1f", closestIdx, node.name.c_str(), closestDist);
        }
    }
    
    LOGI("hitTest: final result=%{public}d, closestDist=%{public}.1f", closestIdx, closestDist);
    return closestIdx;
}

std::vector<ScreenPosition> StarMapRenderer::getNodeScreenPositions() {
    std::vector<ScreenPosition> positions;
    positions.reserve(nodes_.size());
    
    float mvp[16];
    computeMVPMatrix(mvp);
    
    // 找到最大连接数用于归一化
    int maxConnections = 1;
    for (const auto& node : nodes_) {
        if (node.connections > maxConnections) {
            maxConnections = node.connections;
        }
    }
    
    // 计算所有节点到相机目标点的最大距离（用于归一化）
    float maxDistFromTarget = 1.0f;
    for (const auto& node : nodes_) {
        float dx = node.x - targetX_;
        float dy = node.y - targetY_;
        float dz = node.z - targetZ_;
        float dist = sqrt(dx*dx + dy*dy + dz*dz);
        if (dist > maxDistFromTarget) {
            maxDistFromTarget = dist;
        }
    }
    
    // 屏幕中心
    float centerX = width_ * 0.5f;
    float centerY = height_ * 0.5f;
    float maxDist = sqrt(centerX * centerX + centerY * centerY);
    
    for (const auto& node : nodes_) {
        // 计算节点到相机目标点的3D距离
        float dx3d = node.x - targetX_;
        float dy3d = node.y - targetY_;
        float dz3d = node.z - targetZ_;
        float distFromTarget = sqrt(dx3d*dx3d + dy3d*dy3d + dz3d*dz3d) / maxDistFromTarget;
        
        // 变换到裁剪空间 (列主序矩阵)
        float clipX = mvp[0] * node.x + mvp[4] * node.y + mvp[8] * node.z + mvp[12];
        float clipY = mvp[1] * node.x + mvp[5] * node.y + mvp[9] * node.z + mvp[13];
        float clipW = mvp[3] * node.x + mvp[7] * node.y + mvp[11] * node.z + mvp[15];
        
        // 透视除法得到 NDC
        if (clipW > 0.1f) {
            float ndcX = clipX / clipW;
            float ndcY = clipY / clipW;
            
            // NDC 到屏幕坐标
            float screenX = (ndcX + 1.0f) * 0.5f * width_;
            float screenY = (1.0f - ndcY) * 0.5f * height_;
            
            // 计算缩放（用于透明度，远处的节点更透明）
            float scale = std::min(1.0f, 300.0f / clipW);
            
            // 计算节点在屏幕上的大小 - 与 updateNodeVBO 保持一致
            float connectionRatio = (float)node.connections / (float)maxConnections;
            float baseSize = 40.0f + connectionRatio * 110.0f;
            if (node.connections == maxConnections) {
                baseSize *= 1.6f;
            }
            // 透视缩放
            float depthScale = 350.0f / std::max(clipW, 80.0f);
            float nodeSize = baseSize * 1.8f * depthScale * 0.5f;  // 与 shader 中的计算匹配，增大
            
            // 计算距离屏幕中心的距离（归一化到0-1）
            float dx = screenX - centerX;
            float dy = screenY - centerY;
            float distFromCenter = sqrt(dx * dx + dy * dy) / maxDist;
            
            ScreenPosition pos;
            pos.x = screenX;
            pos.y = screenY;
            pos.scale = scale;
            pos.nodeSize = nodeSize;
            pos.name = node.name;
            pos.category = node.category;
            pos.connections = node.connections;
            pos.distFromCenter = distFromCenter;
            pos.distFromTarget = distFromTarget;  // 新增：距离相机目标点的距离
            // 标签锚点位置（节点右侧）
            pos.labelX = screenX + nodeSize * 0.6f + 5.0f;
            pos.labelY = screenY;
            positions.push_back(pos);
        } else {
            // 节点在相机后面，不显示
            ScreenPosition pos;
            pos.x = -1000;
            pos.y = -1000;
            pos.scale = 0;
            pos.nodeSize = 0;
            pos.name = node.name;
            pos.category = node.category;
            pos.connections = node.connections;
            pos.distFromCenter = 1.0f;
            pos.distFromTarget = 1.0f;
            pos.labelX = -1000;
            pos.labelY = -1000;
            positions.push_back(pos);
        }
    }
    
    return positions;
}


void StarMapRenderer::render() {
    if (eglDisplay_ == EGL_NO_DISPLAY) {
        LOGE("render: eglDisplay is NO_DISPLAY");
        return;
    }
    
    // 确保 EGL context 是当前的
    if (eglGetCurrentContext() != eglContext_) {
        LOGI("render: Making EGL context current");
        if (!eglMakeCurrent(eglDisplay_, eglSurface_, eglSurface_, eglContext_)) {
            LOGE("render: eglMakeCurrent failed: %{public}d", eglGetError());
            return;
        }
    }
    
    static int frameCount = 0;
    frameCount++;
    
    glViewport(0, 0, width_, height_);
    
    // 纯黑背景 - 让星星更明显
    glClearColor(0.0f, 0.0f, 0.02f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    
    // 检查 GL 错误
    GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
        LOGE("GL error after clear: %{public}d", err);
    }
    
    // 检查shader程序是否有效
    if (frameCount == 1) {
        LOGI("Shader programs - node:%{public}d line:%{public}d star:%{public}d particle:%{public}d",
             nodeProgram_, lineProgram_, starProgram_, particleProgram_);
        
        if (!nodes_.empty()) {
            LOGI("First node pos: x=%{public}.1f y=%{public}.1f z=%{public}.1f", 
                 nodes_[0].x, nodes_[0].y, nodes_[0].z);
        }
        
        // 打印 MVP 矩阵的一些值
        float mvp[16];
        computeMVPMatrix(mvp);
        LOGI("MVP[0]=%{public}.3f MVP[5]=%{public}.3f MVP[10]=%{public}.3f MVP[14]=%{public}.3f",
             mvp[0], mvp[5], mvp[10], mvp[14]);
    }
    
    // 不再绘制星云背景（移除紫灰斑点）
    // drawNebula();
    
    // 绘制3D星星背景
    drawBackground();
    // 绘制3D内容
    drawLinks();
    drawParticles();
    drawNodes();
    drawTextLabels();
    
    err = glGetError();
    if (err != GL_NO_ERROR) {
        LOGE("GL error after draw: %{public}d", err);
    }
    
    // 强制刷新
    glFlush();
    
    EGLBoolean result = eglSwapBuffers(eglDisplay_, eglSurface_);
    if (result != EGL_TRUE) {
        LOGE("eglSwapBuffers failed: %{public}d", eglGetError());
    }
    
    if (frameCount == 1) {
        LOGI("First render completed, nodes: %{public}zu, links: %{public}zu, swapResult: %{public}d", 
             nodes_.size(), links_.size(), result);
    }
}

// 纯星空渲染模式 - 只渲染背景星星，用于聊天界面背景
void StarMapRenderer::renderStarfieldOnly() {
    if (eglDisplay_ == EGL_NO_DISPLAY) {
        return;
    }
    
    if (eglGetCurrentContext() != eglContext_) {
        if (!eglMakeCurrent(eglDisplay_, eglSurface_, eglSurface_, eglContext_)) {
            return;
        }
    }
    
    glViewport(0, 0, width_, height_);
    
    // 深蓝色背景
    glClearColor(0.0f, 0.0f, 0.03f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    
    // 只绘制3D星星背景
    drawBackground();
    
    glFlush();
    eglSwapBuffers(eglDisplay_, eglSurface_);
}

void StarMapRenderer::drawBackground() {
    if (bgStars_.empty()) {
        LOGI("drawBackground: no stars");
        return;
    }
    
    static bool firstDraw = true;
    
    // 更新星星数据 - 3D坐标 + 颜色
    std::vector<float> starData;
    starData.reserve(bgStars_.size() * 8);  // x, y, z, size, brightness, r, g, b
    
    for (const auto& star : bgStars_) {
        // 闪烁效果
        float twinkle = sin(star.twinklePhase) * 0.25f + 0.75f;
        float randomFlicker = sin(star.twinklePhase * 3.7f) * 0.1f + 1.0f;
        
        starData.push_back(star.x);
        starData.push_back(star.y);
        starData.push_back(star.z);
        starData.push_back(star.size * randomFlicker);
        starData.push_back(star.brightness * twinkle);
        starData.push_back(star.r);
        starData.push_back(star.g);
        starData.push_back(star.b);
    }
    
    if (firstDraw) {
        LOGI("drawBackground: drawing %{public}zu bright 3D stars", bgStars_.size());
    }
    
    // 计算MVP矩阵
    float mvp[16];
    computeMVPMatrix(mvp);
    
    glBindBuffer(GL_ARRAY_BUFFER, starVBO_);
    glBufferData(GL_ARRAY_BUFFER, starData.size() * sizeof(float), starData.data(), GL_DYNAMIC_DRAW);
    
    glUseProgram(starProgram_);
    
    GLint mvpLoc = glGetUniformLocation(starProgram_, "uMVPMatrix");
    glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp);
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    glEnableVertexAttribArray(2);
    glEnableVertexAttribArray(3);
    
    // 8 floats: x, y, z, size, brightness, r, g, b
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(4 * sizeof(float)));
    glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(5 * sizeof(float)));
    
    // 使用加法混合让星星更亮
    glBlendFunc(GL_SRC_ALPHA, GL_ONE);
    
    // 画两遍增强亮度
    glDrawArrays(GL_POINTS, 0, bgStars_.size());
    glDrawArrays(GL_POINTS, 0, bgStars_.size());
    
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    glDisableVertexAttribArray(2);
    glDisableVertexAttribArray(3);
    
    if (firstDraw) {
        LOGI("drawBackground: completed with bright 3D stars");
        firstDraw = false;
    }
}

void StarMapRenderer::drawNebula() {
    if (nebulaProgram_ == 0) return;
    
    glUseProgram(nebulaProgram_);
    
    GLint timeLoc = glGetUniformLocation(nebulaProgram_, "uTime");
    GLint resLoc = glGetUniformLocation(nebulaProgram_, "uResolution");
    
    glUniform1f(timeLoc, time_);
    glUniform2f(resLoc, (float)width_, (float)height_);
    
    glBindBuffer(GL_ARRAY_BUFFER, nebulaVBO_);
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    
    // 4 floats per vertex: x, y, u, v
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)(2 * sizeof(float)));
    
    // 使用正常混合绘制星云
    glDrawArrays(GL_TRIANGLES, 0, 6);
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
}

void StarMapRenderer::updateLineVBO() {
    if (links_.empty() || nodes_.empty()) return;
    
    std::vector<float> lineData;
    // 增加曲线段数，让曲线更丝滑
    const int CURVE_SEGMENTS = 16;
    lineData.reserve(links_.size() * CURVE_SEGMENTS * 2 * 7);
    
    for (const auto& link : links_) {
        if (link.sourceIdx < 0 || link.sourceIdx >= (int)nodes_.size()) continue;
        if (link.targetIdx < 0 || link.targetIdx >= (int)nodes_.size()) continue;
        
        const auto& src = nodes_[link.sourceIdx];
        const auto& tgt = nodes_[link.targetIdx];
        
        // 使用源节点的颜色，稍微降低饱和度让线条更柔和
        float r = src.r * 0.85f + 0.15f;
        float g = src.g * 0.85f + 0.15f;
        float b = src.b * 0.85f + 0.15f;
        
        // 计算曲线控制点 - 更自然的弯曲
        float midX = (src.x + tgt.x) * 0.5f;
        float midY = (src.y + tgt.y) * 0.5f;
        float midZ = (src.z + tgt.z) * 0.5f;
        
        // 计算垂直于连线的方向
        float dx = tgt.x - src.x;
        float dy = tgt.y - src.y;
        float dz = tgt.z - src.z;
        float len = sqrt(dx*dx + dy*dy + dz*dz);
        
        // 弯曲程度更柔和，基于连线长度
        float bendAmount = len * 0.12f;
        
        // 控制点偏移（使用简单的垂直方向）- 更自然的曲线
        float ctrlX = midX + dy * bendAmount / (len + 0.1f);
        float ctrlY = midY - dx * bendAmount / (len + 0.1f);
        float ctrlZ = midZ + bendAmount * 0.25f;
        
        // 生成曲线上的点
        for (int i = 0; i < CURVE_SEGMENTS; i++) {
            float t1 = (float)i / CURVE_SEGMENTS;
            float t2 = (float)(i + 1) / CURVE_SEGMENTS;
            
            // 二次贝塞尔曲线
            float u1 = 1.0f - t1;
            float u2 = 1.0f - t2;
            
            float x1 = u1*u1*src.x + 2*u1*t1*ctrlX + t1*t1*tgt.x;
            float y1 = u1*u1*src.y + 2*u1*t1*ctrlY + t1*t1*tgt.y;
            float z1 = u1*u1*src.z + 2*u1*t1*ctrlZ + t1*t1*tgt.z;
            
            float x2 = u2*u2*src.x + 2*u2*t2*ctrlX + t2*t2*tgt.x;
            float y2 = u2*u2*src.y + 2*u2*t2*ctrlY + t2*t2*tgt.y;
            float z2 = u2*u2*src.z + 2*u2*t2*ctrlZ + t2*t2*tgt.z;
            
            // 颜色从源到目标柔和渐变
            float cr1 = r + (tgt.r * 0.85f + 0.15f - r) * t1;
            float cg1 = g + (tgt.g * 0.85f + 0.15f - g) * t1;
            float cb1 = b + (tgt.b * 0.85f + 0.15f - b) * t1;
            
            float cr2 = r + (tgt.r * 0.85f + 0.15f - r) * t2;
            float cg2 = g + (tgt.g * 0.85f + 0.15f - g) * t2;
            float cb2 = b + (tgt.b * 0.85f + 0.15f - b) * t2;
            
            // 透明度：两端淡出，中间柔和，整体更轻盈
            float fadeIn = smoothstep(0.0f, 0.15f, t1);
            float fadeOut = smoothstep(1.0f, 0.85f, t1);
            float alpha1 = 0.25f * link.strength * fadeIn * fadeOut;
            
            float fadeIn2 = smoothstep(0.0f, 0.15f, t2);
            float fadeOut2 = smoothstep(1.0f, 0.85f, t2);
            float alpha2 = 0.25f * link.strength * fadeIn2 * fadeOut2;
            
            // 点1
            lineData.push_back(x1);
            lineData.push_back(y1);
            lineData.push_back(z1);
            lineData.push_back(cr1);
            lineData.push_back(cg1);
            lineData.push_back(cb1);
            lineData.push_back(alpha1);
            
            // 点2
            lineData.push_back(x2);
            lineData.push_back(y2);
            lineData.push_back(z2);
            lineData.push_back(cr2);
            lineData.push_back(cg2);
            lineData.push_back(cb2);
            lineData.push_back(alpha2);
        }
    }
    
    glBindBuffer(GL_ARRAY_BUFFER, lineVBO_);
    glBufferData(GL_ARRAY_BUFFER, lineData.size() * sizeof(float), lineData.data(), GL_DYNAMIC_DRAW);
    
    // 保存线段数量用于绘制
    lineVertexCount_ = lineData.size() / 7;
}

void StarMapRenderer::drawLinks() {
    if (links_.empty() || lineVertexCount_ <= 0) return;
    
    float mvp[16];
    computeMVPMatrix(mvp);
    
    glUseProgram(lineProgram_);
    
    GLint mvpLoc = glGetUniformLocation(lineProgram_, "uMVPMatrix");
    glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp);
    
    glBindBuffer(GL_ARRAY_BUFFER, lineVBO_);
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)(3 * sizeof(float)));
    
    // 使用加法混合实现柔和发光效果
    glBlendFunc(GL_SRC_ALPHA, GL_ONE);
    
    // 画两层，纤细柔和的发光效果
    glLineWidth(2.0f);  // 外层柔和光晕
    glDrawArrays(GL_LINES, 0, lineVertexCount_);
    
    glLineWidth(1.0f);  // 核心细线
    glDrawArrays(GL_LINES, 0, lineVertexCount_);
    
    // 恢复正常混合
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
}

void StarMapRenderer::updateParticleVBO() {
    if (particles_.empty() || links_.empty()) return;
    
    std::vector<float> particleData;
    particleData.reserve(particles_.size() * 8);  // x, y, z, alpha, r, g, b, progress
    
    for (const auto& p : particles_) {
        if (p.linkIdx < 0 || p.linkIdx >= (int)links_.size()) continue;
        
        const auto& link = links_[p.linkIdx];
        if (link.sourceIdx < 0 || link.sourceIdx >= (int)nodes_.size()) continue;
        if (link.targetIdx < 0 || link.targetIdx >= (int)nodes_.size()) continue;
        
        const auto& src = nodes_[link.sourceIdx];
        const auto& tgt = nodes_[link.targetIdx];
        
        // 使用贝塞尔曲线计算粒子位置（与连线一致）
        float midX = (src.x + tgt.x) * 0.5f;
        float midY = (src.y + tgt.y) * 0.5f;
        float midZ = (src.z + tgt.z) * 0.5f;
        
        float dx = tgt.x - src.x;
        float dy = tgt.y - src.y;
        float dz = tgt.z - src.z;
        float len = sqrt(dx*dx + dy*dy + dz*dz);
        float bendAmount = len * 0.15f;
        
        float ctrlX = midX + dy * bendAmount / (len + 0.1f);
        float ctrlY = midY - dx * bendAmount / (len + 0.1f);
        float ctrlZ = midZ + bendAmount * 0.3f;
        
        // 二次贝塞尔曲线
        float t = p.progress;
        float u = 1.0f - t;
        float x = u*u*src.x + 2*u*t*ctrlX + t*t*tgt.x;
        float y = u*u*src.y + 2*u*t*ctrlY + t*t*tgt.y;
        float z = u*u*src.z + 2*u*t*ctrlZ + t*t*tgt.z;
        
        // 粒子颜色插值
        float r = src.r + (tgt.r - src.r) * p.progress;
        float g = src.g + (tgt.g - src.g) * p.progress;
        float b = src.b + (tgt.b - src.b) * p.progress;
        
        // 粒子在中间最亮，两端渐隐
        float alpha = sin(p.progress * 3.14159f) * 0.95f;
        
        particleData.push_back(x);
        particleData.push_back(y);
        particleData.push_back(z);
        particleData.push_back(alpha);
        particleData.push_back(r);
        particleData.push_back(g);
        particleData.push_back(b);
        particleData.push_back(p.progress);  // 传递进度用于着色器
    }
    
    glBindBuffer(GL_ARRAY_BUFFER, particleVBO_);
    glBufferData(GL_ARRAY_BUFFER, particleData.size() * sizeof(float), particleData.data(), GL_DYNAMIC_DRAW);
}

void StarMapRenderer::drawParticles() {
    if (particles_.empty()) return;
    
    updateParticleVBO();
    
    float mvp[16];
    computeMVPMatrix(mvp);
    
    glUseProgram(particleProgram_);
    
    GLint mvpLoc = glGetUniformLocation(particleProgram_, "uMVPMatrix");
    GLint sizeLoc = glGetUniformLocation(particleProgram_, "uPointSize");
    GLint timeLoc = glGetUniformLocation(particleProgram_, "uTime");
    glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp);
    glUniform1f(sizeLoc, 20.0f);  // 更大的粒子
    glUniform1f(timeLoc, time_);  // 传递时间用于闪烁
    
    glBindBuffer(GL_ARRAY_BUFFER, particleVBO_);
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    glEnableVertexAttribArray(2);
    glEnableVertexAttribArray(3);
    
    // 8 floats: x, y, z, alpha, r, g, b, progress
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(4 * sizeof(float)));
    glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(7 * sizeof(float)));
    
    // 加法混合
    glBlendFunc(GL_SRC_ALPHA, GL_ONE);
    glDrawArrays(GL_POINTS, 0, particles_.size());
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    glDisableVertexAttribArray(2);
    glDisableVertexAttribArray(3);
}

void StarMapRenderer::updateNodeVBO() {
    if (nodes_.empty()) return;
    
    std::vector<float> nodeData;
    nodeData.reserve(nodes_.size() * 7);
    
    // 找到连接数最多的节点
    int maxConnections = 1;
    for (const auto& node : nodes_) {
        if (node.connections > maxConnections) {
            maxConnections = node.connections;
        }
    }
    
    static bool firstUpdate = true;
    
    for (const auto& node : nodes_) {
        // 节点大小基于连接数，核心节点更大
        float connectionRatio = (float)node.connections / (float)maxConnections;
        // 增大基础大小: 40-150，让节点更明显
        float baseSize = 40.0f + connectionRatio * 110.0f;
        
        // 如果是连接最多的节点，额外放大
        if (node.connections == maxConnections) {
            baseSize *= 1.6f;
        }
        
        if (firstUpdate && nodeData.size() < 7 * 3) {
            LOGI("updateNodeVBO: node '%{public}s' connections=%{public}d ratio=%{public}.2f size=%{public}.1f",
                 node.name.c_str(), node.connections, connectionRatio, baseSize);
        }
        
        nodeData.push_back(node.x);
        nodeData.push_back(node.y);
        nodeData.push_back(node.z);
        nodeData.push_back(node.r);
        nodeData.push_back(node.g);
        nodeData.push_back(node.b);
        nodeData.push_back(baseSize);
    }
    
    firstUpdate = false;
    
    glBindBuffer(GL_ARRAY_BUFFER, nodeVBO_);
    glBufferData(GL_ARRAY_BUFFER, nodeData.size() * sizeof(float), nodeData.data(), GL_DYNAMIC_DRAW);
}

void StarMapRenderer::drawNodes() {
    if (nodes_.empty()) {
        LOGI("drawNodes: no nodes to draw");
        return;
    }
    
    static bool firstDraw = true;
    
    float mvp[16];
    computeMVPMatrix(mvp);
    
    glUseProgram(nodeProgram_);
    
    GLint mvpLoc = glGetUniformLocation(nodeProgram_, "uMVPMatrix");
    GLint scaleLoc = glGetUniformLocation(nodeProgram_, "uPointScale");
    GLint timeLoc = glGetUniformLocation(nodeProgram_, "uTime");
    GLint selectedLoc = glGetUniformLocation(nodeProgram_, "uSelectedIdx");
    
    if (mvpLoc < 0 || scaleLoc < 0) {
        LOGE("drawNodes: uniform location failed - mvp:%{public}d scale:%{public}d", mvpLoc, scaleLoc);
    }
    
    glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp);
    glUniform1f(scaleLoc, 1.5f);  // 增大缩放因子
    glUniform1f(timeLoc, time_);  // 传递时间用于动画
    glUniform1i(selectedLoc, selectedNodeIdx_);  // 传递选中节点索引
    
    glBindBuffer(GL_ARRAY_BUFFER, nodeVBO_);
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    glEnableVertexAttribArray(2);
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)(3 * sizeof(float)));
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)(6 * sizeof(float)));
    
    // 使用加法混合增强发光效果
    glBlendFunc(GL_SRC_ALPHA, GL_ONE);
    
    // 画两遍增强发光
    glDrawArrays(GL_POINTS, 0, nodes_.size());
    glDrawArrays(GL_POINTS, 0, nodes_.size());
    
    // 恢复正常混合
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    glDisableVertexAttribArray(2);
    
    GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
        LOGE("drawNodes GL error: %{public}d", err);
    }
    
    if (firstDraw) {
        if (!nodes_.empty()) {
            // 正确的列主序矩阵乘法
            float x = nodes_[0].x, y = nodes_[0].y, z = nodes_[0].z;
            float clipX = mvp[0]*x + mvp[4]*y + mvp[8]*z + mvp[12];
            float clipY = mvp[1]*x + mvp[5]*y + mvp[9]*z + mvp[13];
            float clipZ = mvp[2]*x + mvp[6]*y + mvp[10]*z + mvp[14];
            float clipW = mvp[3]*x + mvp[7]*y + mvp[11]*z + mvp[15];
            float ndcX = clipX / clipW;
            float ndcY = clipY / clipW;
            float ndcZ = clipZ / clipW;
            LOGI("drawNodes: first node pos=(%{public}.1f,%{public}.1f,%{public}.1f) NDC=(%{public}.2f, %{public}.2f, %{public}.2f) w=%{public}.1f",
                 x, y, z, ndcX, ndcY, ndcZ, clipW);
        }
        LOGI("drawNodes: drawing %{public}zu nodes with program %{public}d", nodes_.size(), nodeProgram_);
        firstDraw = false;
    }
}

void StarMapRenderer::setTextTexture(int nodeIdx, const uint8_t* pixels, int width, int height) {
    if (nodeIdx < 0 || nodeIdx >= (int)nodes_.size()) return;
    
    // 查找或创建标签
    TextLabel* label = nullptr;
    for (auto& l : textLabels_) {
        if (l.nodeIdx == nodeIdx) {
            label = &l;
            break;
        }
    }
    
    if (!label) {
        textLabels_.push_back(TextLabel());
        label = &textLabels_.back();
        label->nodeIdx = nodeIdx;
        label->textureId = 0;
    }
    
    label->width = width;
    label->height = height;
    
    // 创建或更新纹理
    if (label->textureId == 0) {
        glGenTextures(1, &label->textureId);
    }
    
    glBindTexture(GL_TEXTURE_2D, label->textureId);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
    
    LOGI("setTextTexture: node %{public}d, texture %{public}d, size %{public}dx%{public}d", 
         nodeIdx, label->textureId, width, height);
}

void StarMapRenderer::drawTextLabels() {
    // 绘制从节点延伸出的标签连接线和锚点
    // 这些线和点与节点在同一个 3D 空间中渲染
    
    if (nodes_.empty()) return;
    
    float mvp[16];
    computeMVPMatrix(mvp);
    
    // 找到最大连接数
    int maxConnections = 1;
    for (const auto& node : nodes_) {
        if (node.connections > maxConnections) {
            maxConnections = node.connections;
        }
    }
    
    // 构建连接线数据
    std::vector<float> lineData;
    std::vector<float> anchorData;
    
    for (size_t i = 0; i < nodes_.size(); i++) {
        const auto& node = nodes_[i];
        
        // 只为连接数较多的节点绘制标签线
        float connectionRatio = (float)node.connections / (float)maxConnections;
        if (connectionRatio < 0.2f) continue;  // 跳过连接数少的节点
        
        // 计算标签线的终点（在节点右侧）
        float lineLength = 8.0f + connectionRatio * 12.0f;
        
        // 线的起点（节点边缘）
        float startX = node.x + 3.0f;
        float startY = node.y;
        float startZ = node.z;
        
        // 线的终点（标签锚点）
        float endX = node.x + lineLength;
        float endY = node.y;
        float endZ = node.z;
        
        // 颜色
        float r = node.r;
        float g = node.g;
        float b = node.b;
        float alpha = 0.4f + connectionRatio * 0.4f;
        
        // 添加线段顶点
        // 起点
        lineData.push_back(startX);
        lineData.push_back(startY);
        lineData.push_back(startZ);
        lineData.push_back(r);
        lineData.push_back(g);
        lineData.push_back(b);
        lineData.push_back(alpha * 0.3f);  // 起点较淡
        
        // 终点
        lineData.push_back(endX);
        lineData.push_back(endY);
        lineData.push_back(endZ);
        lineData.push_back(r);
        lineData.push_back(g);
        lineData.push_back(b);
        lineData.push_back(alpha);  // 终点较亮
        
        // 添加锚点（小圆点）
        anchorData.push_back(endX);
        anchorData.push_back(endY);
        anchorData.push_back(endZ);
        anchorData.push_back(r);
        anchorData.push_back(g);
        anchorData.push_back(b);
        anchorData.push_back(4.0f + connectionRatio * 6.0f);  // 点大小
    }
    
    if (lineData.empty()) return;
    
    // 绘制连接线
    glUseProgram(lineProgram_);
    
    GLint mvpLoc = glGetUniformLocation(lineProgram_, "uMVPMatrix");
    glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp);
    
    glBindBuffer(GL_ARRAY_BUFFER, textVBO_);
    glBufferData(GL_ARRAY_BUFFER, lineData.size() * sizeof(float), lineData.data(), GL_DYNAMIC_DRAW);
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)(3 * sizeof(float)));
    
    glLineWidth(1.5f);
    glDrawArrays(GL_LINES, 0, lineData.size() / 7);
    
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    
    // 绘制锚点
    if (!anchorData.empty()) {
        glUseProgram(nodeProgram_);
        
        mvpLoc = glGetUniformLocation(nodeProgram_, "uMVPMatrix");
        GLint scaleLoc = glGetUniformLocation(nodeProgram_, "uPointScale");
        glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp);
        glUniform1f(scaleLoc, 0.5f);
        
        glBindBuffer(GL_ARRAY_BUFFER, textVBO_);
        glBufferData(GL_ARRAY_BUFFER, anchorData.size() * sizeof(float), anchorData.data(), GL_DYNAMIC_DRAW);
        
        glEnableVertexAttribArray(0);
        glEnableVertexAttribArray(1);
        glEnableVertexAttribArray(2);
        
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)0);
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)(3 * sizeof(float)));
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 7 * sizeof(float), (void*)(6 * sizeof(float)));
        
        glDrawArrays(GL_POINTS, 0, anchorData.size() / 7);
        
        glDisableVertexAttribArray(0);
        glDisableVertexAttribArray(1);
        glDisableVertexAttribArray(2);
    }
}

void StarMapRenderer::updateTextVBO() {
    // 文字VBO在drawTextLabels中动态更新
}
