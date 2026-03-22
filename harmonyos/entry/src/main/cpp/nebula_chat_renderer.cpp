/**
 * 星云对话渲染器 - 真正的3D空间对话
 * 
 * 设计：
 * - 中心是AI核心（发光球体）
 * - 消息星云围绕AI核心在3D空间中漂浮
 * - 用户消息蓝色，AI消息紫色
 * - 消息按时间螺旋排列在3D空间
 */
#include "nebula_chat_renderer.h"
#include <hilog/log.h>
#include <cstring>
#include <algorithm>
#include <ctime>

#undef LOG_TAG
#define LOG_TAG "NebulaChatRenderer"
#define LOGE(...) OH_LOG_ERROR(LOG_APP, __VA_ARGS__)
#define LOGI(...) OH_LOG_INFO(LOG_APP, __VA_ARGS__)

namespace nebula {

// 顶点着色器 - 星星（带轻微闪烁）
static const char* STAR_VERTEX_SHADER = R"(#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in float aSize;
layout(location = 2) in float aBrightness;
layout(location = 3) in float aPhase;

uniform mat4 uMVP;
uniform float uTime;

out float vBrightness;

void main() {
    gl_Position = uMVP * vec4(aPosition, 1.0);
    
    // 轻微闪烁效果，使用fract限制时间范围
    float t = fract(uTime * 0.1) * 10.0;
    float twinkle = 0.85 + 0.15 * sin(aPhase + t * 1.5);
    vBrightness = aBrightness * twinkle;
    
    gl_PointSize = aSize;
}
)";

// 片段着色器 - 星星（柔和白点）
static const char* STAR_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in float vBrightness;

out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    if (dist > 0.5) discard;
    
    // 柔和的圆形星点
    float core = smoothstep(0.5, 0.1, dist);
    float glow = smoothstep(0.5, 0.0, dist) * 0.5;
    float alpha = (core + glow) * vBrightness;
    
    // 白色带微微暖色
    vec3 color = vec3(1.0, 0.98, 0.95);
    fragColor = vec4(color, alpha);
}
)";

// 顶点着色器 - AI核心 (点精灵方式 - 模仿知识星图)
static const char* CORE_VERTEX_SHADER = R"(#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;

uniform mat4 uMVP;
uniform float uTime;
uniform float uPointSize;

out float vPulse;
out float vTime;

void main() {
    gl_Position = uMVP * vec4(aPosition, 1.0);
    
    // 脉冲呼吸效果
    float pulse = sin(uTime * 2.0) * 0.15 + 1.0;
    vPulse = pulse;
    vTime = uTime;
    
    // 直接使用点大小，不做复杂的透视缩放
    gl_PointSize = uPointSize * pulse;
}
)";

// 片段着色器 - AI核心 - 普通发光球体效果（模仿知识星图普通节点）
static const char* CORE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in float vPulse;
in float vTime;

out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    // 普通节点的多层发光效果 - 没有光环
    float core = smoothstep(0.08, 0.0, dist);              // 超亮核心
    float inner1 = smoothstep(0.15, 0.0, dist) * 0.9;      // 内层1
    float inner2 = smoothstep(0.25, 0.0, dist) * 0.6;      // 内层2
    float outer1 = smoothstep(0.4, 0.0, dist) * 0.35;      // 外层1
    float outer2 = smoothstep(0.5, 0.0, dist) * 0.2;       // 外层2
    float glow = smoothstep(0.7, 0.0, dist) * 0.1;         // 最外层微光
    
    float alpha = core + inner1 + inner2 + outer1 + outer2 + glow;
    
    // 颜色：核心白色，向外渐变到紫蓝色
    vec3 nodeColor = vec3(0.5, 0.6, 1.0);    // 蓝紫色
    vec3 white = vec3(1.0);
    
    vec3 color = mix(nodeColor * 1.3, white, core * 0.9 + inner1 * 0.5);
    
    fragColor = vec4(color, alpha);
}
)";

// 顶点着色器 - 消息星云 (点精灵方式)
static const char* NEBULA_VERTEX_SHADER = R"(#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aColor;
layout(location = 2) in float aSize;
layout(location = 3) in float aGlow;

uniform mat4 uMVP;
uniform float uTime;

out vec3 vColor;
out float vGlow;

void main() {
    gl_Position = uMVP * vec4(aPosition, 1.0);
    
    // 脉冲效果
    float phase = aPosition.x * 0.1 + aPosition.y * 0.15;
    float pulse = sin(uTime * 2.0 + phase) * 0.1 + 1.0;
    
    // 直接使用点大小
    gl_PointSize = aSize * pulse;
    
    vColor = aColor;
    vGlow = aGlow * pulse;
}
)";

// 片段着色器 - 消息星云 (点精灵方式) - 普通节点样式
static const char* NEBULA_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec3 vColor;
in float vGlow;

out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    // 普通节点的多层发光效果
    float core = smoothstep(0.08, 0.0, dist);
    float inner1 = smoothstep(0.15, 0.0, dist) * 0.9;
    float inner2 = smoothstep(0.25, 0.0, dist) * 0.6;
    float outer1 = smoothstep(0.4, 0.0, dist) * 0.35;
    float outer2 = smoothstep(0.5, 0.0, dist) * 0.2;
    float glow = smoothstep(0.7, 0.0, dist) * 0.1;
    
    float alpha = (core + inner1 + inner2 + outer1 + outer2 + glow) * vGlow;
    
    // 核心白色，向外渐变到消息颜色
    vec3 white = vec3(1.0);
    vec3 color = mix(vColor * 1.3, white, core * 0.9 + inner1 * 0.5);
    
    fragColor = vec4(color, alpha);
}
)";

// 顶点着色器 - 粒子
static const char* PARTICLE_VERTEX_SHADER = R"(#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in float aSize;
layout(location = 2) in vec4 aColor;

uniform mat4 uMVP;

out vec4 vColor;

void main() {
    gl_Position = uMVP * vec4(aPosition, 1.0);
    vColor = aColor;
    
    float depth = gl_Position.z / gl_Position.w;
    gl_PointSize = aSize * (1.0 - depth * 0.4) * 3.0;
}
)";

// 片段着色器 - 粒子
static const char* PARTICLE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec4 vColor;

out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    if (dist > 0.5) discard;
    
    float glow = exp(-dist * 5.0);
    fragColor = vec4(vColor.rgb, vColor.a * glow);
}
)";

// 顶点着色器 - 连接线（消息到核心）
static const char* LINE_VERTEX_SHADER = R"(#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in float aAlpha;

uniform mat4 uMVP;

out float vAlpha;

void main() {
    gl_Position = uMVP * vec4(aPosition, 1.0);
    vAlpha = aAlpha;
}
)";

// 片段着色器 - 连接线
static const char* LINE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in float vAlpha;

uniform vec3 uColor;

out vec4 fragColor;

void main() {
    fragColor = vec4(uColor, vAlpha * 0.3);
}
)";

// 编译着色器
static GLuint compileShader(GLenum type, const char* source) {
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);
    
    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        char log[1024];
        glGetShaderInfoLog(shader, 1024, nullptr, log);
        LOGE("Nebula: Shader compile error (%{public}s): %{public}s", 
             type == GL_VERTEX_SHADER ? "vertex" : "fragment", log);
        return 0;
    }
    LOGI("Nebula: Shader compiled successfully (%{public}s)", 
         type == GL_VERTEX_SHADER ? "vertex" : "fragment");
    return shader;
}

static GLuint createProgram(const char* vertSrc, const char* fragSrc) {
    GLuint vert = compileShader(GL_VERTEX_SHADER, vertSrc);
    GLuint frag = compileShader(GL_FRAGMENT_SHADER, fragSrc);
    
    if (vert == 0 || frag == 0) {
        LOGE("Nebula: Shader compilation failed, cannot create program");
        return 0;
    }
    
    GLuint program = glCreateProgram();
    glAttachShader(program, vert);
    glAttachShader(program, frag);
    glLinkProgram(program);
    
    GLint success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        char log[1024];
        glGetProgramInfoLog(program, 1024, nullptr, log);
        LOGE("Nebula: Program link error: %{public}s", log);
        return 0;
    }
    
    glDeleteShader(vert);
    glDeleteShader(frag);
    
    LOGI("Nebula: Program created successfully, id=%{public}d", program);
    return program;
}

NebulaChatRenderer::NebulaChatRenderer()
    : width_(0), height_(0), initialized_(false),
      cameraX_(0), cameraY_(0), cameraZ_(8.0f),
      cameraRotX_(0.15f), cameraRotY_(0), cameraTargetZ_(0),
      lastTime_(0), totalTime_(0),
      starRotation_(0), nebulaSpacing_(2.5f),
      starProgram_(0), nebulaProgram_(0), particleProgram_(0),
      starVAO_(0), starVBO_(0),
      nebulaVAO_(0), nebulaVBO_(0),
      particleVAO_(0), particleVBO_(0),
      eglDisplay_(EGL_NO_DISPLAY),
      eglSurface_(EGL_NO_SURFACE),
      eglContext_(EGL_NO_CONTEXT),
      coreProgram_(0), lineProgram_(0),
      coreVAO_(0), coreVBO_(0),
      lineVAO_(0), lineVBO_(0) {
    
    memset(projMatrix_, 0, sizeof(projMatrix_));
    memset(viewMatrix_, 0, sizeof(viewMatrix_));
    memset(mvpMatrix_, 0, sizeof(mvpMatrix_));
    memset(modelMatrix_, 0, sizeof(modelMatrix_));
    
    srand(static_cast<unsigned>(time(nullptr)));
}

NebulaChatRenderer::~NebulaChatRenderer() {
    destroy();
}

bool NebulaChatRenderer::initEGL(OHNativeWindow* window) {
    eglDisplay_ = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (eglDisplay_ == EGL_NO_DISPLAY) {
        LOGE("Nebula: eglGetDisplay failed");
        return false;
    }
    
    EGLint major, minor;
    if (!eglInitialize(eglDisplay_, &major, &minor)) {
        LOGE("Nebula: eglInitialize failed");
        return false;
    }
    
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
        LOGE("Nebula: eglChooseConfig failed");
        return false;
    }
    
    EGLint surfaceAttribs[] = { EGL_NONE };
    eglSurface_ = eglCreateWindowSurface(eglDisplay_, config, 
        reinterpret_cast<EGLNativeWindowType>(window), surfaceAttribs);
    if (eglSurface_ == EGL_NO_SURFACE) {
        LOGE("Nebula: eglCreateWindowSurface failed");
        return false;
    }
    
    EGLint contextAttribs[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
    eglContext_ = eglCreateContext(eglDisplay_, config, EGL_NO_CONTEXT, contextAttribs);
    if (eglContext_ == EGL_NO_CONTEXT) {
        LOGE("Nebula: eglCreateContext failed");
        return false;
    }
    
    if (!eglMakeCurrent(eglDisplay_, eglSurface_, eglSurface_, eglContext_)) {
        LOGE("Nebula: eglMakeCurrent failed");
        return false;
    }
    
    LOGI("Nebula: EGL initialized successfully");
    return true;
}

bool NebulaChatRenderer::init(OHNativeWindow* window, int width, int height) {
    LOGI("Nebula: init() called, size=%{public}dx%{public}d", width, height);
    
    if (initialized_) {
        LOGI("Nebula: Already initialized, returning true");
        return true;
    }
    
    if (!window) {
        LOGE("Nebula: window is null!");
        return false;
    }
    
    width_ = width;
    height_ = height;
    
    LOGI("Nebula: Initializing EGL...");
    if (!initEGL(window)) {
        LOGE("Nebula: Failed to init EGL");
        return false;
    }
    
    LOGI("Nebula: Setting up OpenGL state...");
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    // 禁用背面剔除，确保球体可见
    glDisable(GL_CULL_FACE);
    
    // 查询最大点大小
    GLfloat pointSizeRange[2];
    glGetFloatv(GL_ALIASED_POINT_SIZE_RANGE, pointSizeRange);
    LOGI("Nebula: GL_ALIASED_POINT_SIZE_RANGE = [%.1f, %.1f]", pointSizeRange[0], pointSizeRange[1]);
    
    LOGI("Nebula: Initializing shaders...");
    initShaders();
    
    LOGI("Nebula: Initializing stars...");
    initStars();
    
    LOGI("Nebula: Initializing buffers...");
    initBuffers();
    
    LOGI("Nebula: Setting projection matrix...");
    setProjectionMatrix();
    
    initialized_ = true;
    lastTime_ = 0;
    
    LOGI("Nebula: Renderer initialized successfully: %{public}dx%{public}d", width, height);
    return true;
}

void NebulaChatRenderer::resize(int width, int height) {
    width_ = width;
    height_ = height;
    glViewport(0, 0, width, height);
    setProjectionMatrix();
}

void NebulaChatRenderer::initShaders() {
    LOGI("Nebula: Creating star shader...");
    starProgram_ = createProgram(STAR_VERTEX_SHADER, STAR_FRAGMENT_SHADER);
    if (starProgram_ == 0) {
        LOGE("Nebula: Failed to create star program!");
    }
    starMVPLoc_ = glGetUniformLocation(starProgram_, "uMVP");
    starTimeLoc_ = glGetUniformLocation(starProgram_, "uTime");
    
    LOGI("Nebula: Creating core shader (point sprite)...");
    coreProgram_ = createProgram(CORE_VERTEX_SHADER, CORE_FRAGMENT_SHADER);
    if (coreProgram_ == 0) {
        LOGE("Nebula: Failed to create core program!");
    }
    coreMVPLoc_ = glGetUniformLocation(coreProgram_, "uMVP");
    coreTimeLoc_ = glGetUniformLocation(coreProgram_, "uTime");
    corePointSizeLoc_ = glGetUniformLocation(coreProgram_, "uPointSize");
    LOGI("Nebula: Core uniforms - MVP=%{public}d, Time=%{public}d, PointSize=%{public}d",
         coreMVPLoc_, coreTimeLoc_, corePointSizeLoc_);
    
    LOGI("Nebula: Creating nebula shader (point sprite)...");
    nebulaProgram_ = createProgram(NEBULA_VERTEX_SHADER, NEBULA_FRAGMENT_SHADER);
    if (nebulaProgram_ == 0) {
        LOGE("Nebula: Failed to create nebula program!");
    }
    nebulaMVPLoc_ = glGetUniformLocation(nebulaProgram_, "uMVP");
    nebulaTimeLoc_ = glGetUniformLocation(nebulaProgram_, "uTime");
    
    LOGI("Nebula: Creating particle shader...");
    particleProgram_ = createProgram(PARTICLE_VERTEX_SHADER, PARTICLE_FRAGMENT_SHADER);
    particleMVPLoc_ = glGetUniformLocation(particleProgram_, "uMVP");
    
    LOGI("Nebula: Creating line shader...");
    lineProgram_ = createProgram(LINE_VERTEX_SHADER, LINE_FRAGMENT_SHADER);
    lineMVPLoc_ = glGetUniformLocation(lineProgram_, "uMVP");
    lineColorLoc_ = glGetUniformLocation(lineProgram_, "uColor");
    
    LOGI("Nebula: All shaders initialized - star=%{public}d, core=%{public}d, nebula=%{public}d, particle=%{public}d, line=%{public}d",
         starProgram_, coreProgram_, nebulaProgram_, particleProgram_, lineProgram_);
}

void NebulaChatRenderer::initStars() {
    stars_.clear();
    
    // 创建500颗星星，分布在远处球形空间
    for (int i = 0; i < 500; i++) {
        Star3D star;
        
        // 随机球面分布
        float theta = static_cast<float>(rand()) / RAND_MAX * 2.0f * M_PI;
        float phi = acos(2.0f * static_cast<float>(rand()) / RAND_MAX - 1.0f);
        float r = 25.0f + static_cast<float>(rand()) / RAND_MAX * 45.0f;
        
        star.x = r * sin(phi) * cos(theta);
        star.y = r * sin(phi) * sin(theta);
        star.z = r * cos(phi);
        
        // 大小：整体增大
        float sizeRand = static_cast<float>(rand()) / RAND_MAX;
        if (sizeRand < 0.6f) {
            star.size = 2.0f + sizeRand * 2.0f;  // 小星星 2-4
        } else if (sizeRand < 0.9f) {
            star.size = 4.0f + (sizeRand - 0.6f) * 6.0f;  // 中等 4-6
        } else {
            star.size = 6.0f + (sizeRand - 0.9f) * 20.0f;  // 亮星 6-8
        }
        
        // 亮度
        star.brightness = 0.5f + static_cast<float>(rand()) / RAND_MAX * 0.5f;
        
        // 闪烁相位（随机）
        star.twinklePhase = static_cast<float>(rand()) / RAND_MAX * 6.28f;
        
        star.twinkleSpeed = 0;
        star.r = 1.0f;
        star.g = 1.0f;
        star.b = 1.0f;
        
        stars_.push_back(star);
    }
}

void NebulaChatRenderer::initBuffers() {
    // 点精灵方式不需要复杂的球体mesh，只需要简单的VAO/VBO
    glGenVertexArrays(1, &starVAO_);
    glGenBuffers(1, &starVBO_);
    
    glGenVertexArrays(1, &coreVAO_);
    glGenBuffers(1, &coreVBO_);
    
    glGenVertexArrays(1, &nebulaVAO_);
    glGenBuffers(1, &nebulaVBO_);
    
    glGenVertexArrays(1, &particleVAO_);
    glGenBuffers(1, &particleVBO_);
    
    glGenVertexArrays(1, &lineVAO_);
    glGenBuffers(1, &lineVBO_);
    
    LOGI("Nebula: Buffers initialized (point sprite mode)");
}


void NebulaChatRenderer::render() {
    if (!initialized_) {
        LOGE("Nebula: render() called but not initialized!");
        return;
    }
    
    if (!eglMakeCurrent(eglDisplay_, eglSurface_, eglSurface_, eglContext_)) {
        LOGE("Nebula: eglMakeCurrent failed in render()");
        return;
    }
    
    float deltaTime = 0.033f;
    totalTime_ += deltaTime;
    // 限制时间范围，避免数值溢出导致亮度问题
    if (totalTime_ > 1000.0f) totalTime_ -= 1000.0f;
    
    // 每3秒输出一次日志
    static int frameCount = 0;
    frameCount++;
    if (frameCount % 90 == 0) {
        LOGI("Nebula: Rendering frame %{public}d, nebulas=%{public}zu, time=%.1f, coreProgram=%{public}d", 
             frameCount, nebulas_.size(), totalTime_, coreProgram_);
    }
    
    updateAnimation(deltaTime);
    
    // 清屏 - 深空背景
    glClearColor(0.01f, 0.005f, 0.03f, 1.0f);
    glClearDepthf(1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    
    glViewport(0, 0, width_, height_);
    
    setViewMatrix();
    multiplyMatrix(mvpMatrix_, projMatrix_, viewMatrix_);
    
    // 1. 先渲染背景星星（标准混合，避免亮度累积）
    glDisable(GL_DEPTH_TEST);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    renderStars();
    
    // 2. 渲染AI核心（标准混合）
    glDisable(GL_DEPTH_TEST);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    renderCore();
    
    // 3. 渲染连接线
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    glDepthMask(GL_FALSE);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    renderLines();
    
    // 4. 渲染消息星云（标准混合）
    glDisable(GL_DEPTH_TEST);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    renderNebulas();
    
    // 5. 渲染功能球体
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    renderFeatureOrbs();
    
    // 6. 渲染粒子（标准混合）
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    renderParticles();
    
    if (!eglSwapBuffers(eglDisplay_, eglSurface_)) {
        LOGE("Nebula: eglSwapBuffers failed");
    }
}

void NebulaChatRenderer::updateAnimation(float deltaTime) {
    starRotation_ += deltaTime * 0.03f;
    // 限制时间范围，避免数值溢出
    if (starRotation_ > 628.0f) starRotation_ -= 628.0f;  // 约100个2π周期
    
    // 更新消息球体位置和动画
    for (size_t i = 0; i < nebulas_.size(); i++) {
        auto& nebula = nebulas_[i];
        
        // 计算目标位置 - 围绕中心缓慢旋转
        float baseAngle = i * 0.9f;  // 每个消息间隔约50度
        float rotationSpeed = 0.06f;  // 缓慢旋转
        float currentAngle = baseAngle + totalTime_ * rotationSpeed;
        
        // 半径 - 保持较小以便在屏幕上可见
        float radius = 0.8f + (i % 5) * 0.15f;
        
        // 高度分布 - 上下交错
        float height = (static_cast<float>(i % 6) - 2.5f) * 0.25f;
        
        // 添加轻微的上下浮动
        float floatOffset = sin(totalTime_ * 0.5f + i * 0.5f) * 0.08f;
        
        nebula.targetX = cos(currentAngle) * radius;
        nebula.targetY = height + floatOffset;
        nebula.targetZ = sin(currentAngle) * radius;
        
        // 平滑移动到目标位置
        float moveSpeed = 0.06f;
        nebula.x += (nebula.targetX - nebula.x) * moveSpeed;
        nebula.y += (nebula.targetY - nebula.y) * moveSpeed;
        nebula.z += (nebula.targetZ - nebula.z) * moveSpeed;
        
        // 光晕呼吸效果
        nebula.glowPhase += deltaTime * 1.5f;
        
        // 更新粒子
        for (auto it = nebula.particles.begin(); it != nebula.particles.end();) {
            it->x += it->vx * deltaTime;
            it->y += it->vy * deltaTime;
            it->z += it->vz * deltaTime;
            it->vx *= 0.97f;
            it->vy *= 0.97f;
            it->vz *= 0.97f;
            it->life -= deltaTime / it->maxLife;
            it->a = it->life;
            
            if (it->life <= 0) {
                it = nebula.particles.erase(it);
            } else {
                ++it;
            }
        }
    }
}

void NebulaChatRenderer::renderStars() {
    if (starProgram_ == 0 || stars_.empty()) return;
    
    glUseProgram(starProgram_);
    
    // 使用简单的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴（加上缓慢自动旋转）
    float cosY = cos(cameraRotY_ + starRotation_);
    float sinY = sin(cameraRotY_ + starRotation_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float starMVP[16];
    multiplyMatrix(starMVP, proj, rot);
    
    glUniformMatrix4fv(starMVPLoc_, 1, GL_FALSE, starMVP);
    glUniform1f(starTimeLoc_, totalTime_);
    
    // 顶点数据：position(3) + size(1) + brightness(1) + phase(1)
    std::vector<float> starData;
    for (const auto& star : stars_) {
        starData.push_back(star.x);
        starData.push_back(star.y);
        starData.push_back(star.z);
        starData.push_back(star.size);
        starData.push_back(star.brightness);
        starData.push_back(star.twinklePhase);
    }
    
    glBindVertexArray(starVAO_);
    glBindBuffer(GL_ARRAY_BUFFER, starVBO_);
    glBufferData(GL_ARRAY_BUFFER, starData.size() * sizeof(float), starData.data(), GL_DYNAMIC_DRAW);
    
    int stride = 6 * sizeof(float);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, (void*)0);
    glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, stride, (void*)(3 * sizeof(float)));
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, (void*)(4 * sizeof(float)));
    glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, (void*)(5 * sizeof(float)));
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    glEnableVertexAttribArray(2);
    glEnableVertexAttribArray(3);
    
    glDrawArrays(GL_POINTS, 0, stars_.size());
    glBindVertexArray(0);
}

void NebulaChatRenderer::renderCore() {
    if (coreProgram_ == 0) {
        LOGE("Nebula: renderCore - coreProgram_ is 0!");
        return;
    }
    
    glUseProgram(coreProgram_);
    
    // 使用与星星相同的正交投影方式
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;  // 与星星相同的缩放
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float mvp[16];
    multiplyMatrix(mvp, proj, rot);
    
    glUniformMatrix4fv(coreMVPLoc_, 1, GL_FALSE, mvp);
    glUniform1f(coreTimeLoc_, totalTime_);
    glUniform1f(corePointSizeLoc_, 200.0f);  // 大点大小
    
    // 准备单个点的顶点数据（原点位置）
    float coreVertex[] = { 0.0f, 0.0f, 0.0f };
    
    glBindVertexArray(coreVAO_);
    glBindBuffer(GL_ARRAY_BUFFER, coreVBO_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(coreVertex), coreVertex, GL_DYNAMIC_DRAW);
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    
    // 绘制一遍
    glDrawArrays(GL_POINTS, 0, 1);
    
    glBindVertexArray(0);
    
    // 调试日志
    static int coreFrameCount = 0;
    coreFrameCount++;
    if (coreFrameCount % 90 == 0) {
        LOGI("Nebula: renderCore - program=%{public}d, pointSize=200, time=%.2f", 
             coreProgram_, totalTime_);
    }
}

void NebulaChatRenderer::renderCoreGlow() {
    // 点精灵方式已经内置发光效果，不需要额外的光晕层
    // 保留空函数以保持接口兼容
}

void NebulaChatRenderer::renderNebulas() {
    if (nebulas_.empty()) {
        return;
    }
    
    glUseProgram(nebulaProgram_);
    
    // 使用与renderCore完全相同的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float nebulaMVP[16];
    multiplyMatrix(nebulaMVP, proj, rot);
    
    glUniformMatrix4fv(nebulaMVPLoc_, 1, GL_FALSE, nebulaMVP);
    glUniform1f(nebulaTimeLoc_, totalTime_);
    
    // 构建所有消息星云的顶点数据
    // 格式: position(3) + color(3) + size(1) + glow(1)
    std::vector<float> nebulaData;
    
    for (size_t i = 0; i < nebulas_.size(); i++) {
        const auto& nebula = nebulas_[i];
        
        // 位置 - 使用更大的缩放因子
        float posScale = 20.0f;
        nebulaData.push_back(nebula.x * posScale);
        nebulaData.push_back(nebula.y * posScale);
        nebulaData.push_back(nebula.z * posScale);
        
        // 颜色 - 淡化，降低饱和度
        if (nebula.isUser) {
            nebulaData.push_back(0.2f);  // R - 更淡
            nebulaData.push_back(0.4f);  // G
            nebulaData.push_back(0.7f);  // B - 淡蓝色
        } else {
            nebulaData.push_back(0.5f);  // R
            nebulaData.push_back(0.3f);  // G
            nebulaData.push_back(0.7f);  // B - 淡紫色
        }
        
        // 大小 - 稍微小一些
        nebulaData.push_back(80.0f);
        
        // 呼吸效果 - 降低亮度
        float glow = 0.4f + 0.1f * sin(nebula.glowPhase);  // 降低到0.4-0.5
        nebulaData.push_back(glow);
    }
    
    glBindVertexArray(nebulaVAO_);
    glBindBuffer(GL_ARRAY_BUFFER, nebulaVBO_);
    glBufferData(GL_ARRAY_BUFFER, nebulaData.size() * sizeof(float), nebulaData.data(), GL_DYNAMIC_DRAW);
    
    int stride = 8 * sizeof(float);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, (void*)(6 * sizeof(float)));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, (void*)(7 * sizeof(float)));
    glEnableVertexAttribArray(3);
    
    // 只绘制一遍（淡化效果）
    glDrawArrays(GL_POINTS, 0, nebulas_.size());
    
    glBindVertexArray(0);
}

void NebulaChatRenderer::renderLines() {
    if (nebulas_.empty()) return;
    
    glUseProgram(lineProgram_);
    
    // 使用与renderNebulas相同的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float lineMVP[16];
    multiplyMatrix(lineMVP, proj, rot);
    
    glUniformMatrix4fv(lineMVPLoc_, 1, GL_FALSE, lineMVP);
    
    // 从每个星云到中心的曲线连接
    std::vector<float> lineData;
    float posScale = 20.0f;  // 与renderNebulas相同的位置缩放
    
    for (const auto& nebula : nebulas_) {
        // 使用贝塞尔曲线连接星云到中心
        float startX = nebula.x * posScale;
        float startY = nebula.y * posScale;
        float startZ = nebula.z * posScale;
        float endX = 0.0f, endY = 0.0f, endZ = 0.0f;
        
        // 控制点 - 在中间位置向上弯曲
        float ctrlX = (startX + endX) * 0.5f;
        float ctrlY = (startY + endY) * 0.5f + 3.0f;  // 向上弯曲
        float ctrlZ = (startZ + endZ) * 0.5f;
        
        // 生成曲线上的点
        const int segments = 12;
        for (int i = 0; i < segments; i++) {
            float t1 = static_cast<float>(i) / segments;
            float t2 = static_cast<float>(i + 1) / segments;
            
            // 二次贝塞尔曲线
            float x1 = (1-t1)*(1-t1)*startX + 2*(1-t1)*t1*ctrlX + t1*t1*endX;
            float y1 = (1-t1)*(1-t1)*startY + 2*(1-t1)*t1*ctrlY + t1*t1*endY;
            float z1 = (1-t1)*(1-t1)*startZ + 2*(1-t1)*t1*ctrlZ + t1*t1*endZ;
            
            float x2 = (1-t2)*(1-t2)*startX + 2*(1-t2)*t2*ctrlX + t2*t2*endX;
            float y2 = (1-t2)*(1-t2)*startY + 2*(1-t2)*t2*ctrlY + t2*t2*endY;
            float z2 = (1-t2)*(1-t2)*startZ + 2*(1-t2)*t2*ctrlZ + t2*t2*endZ;
            
            // 透明度从外到内渐变
            float alpha1 = 0.6f * (1.0f - t1);
            float alpha2 = 0.6f * (1.0f - t2);
            
            lineData.push_back(x1);
            lineData.push_back(y1);
            lineData.push_back(z1);
            lineData.push_back(alpha1);
            
            lineData.push_back(x2);
            lineData.push_back(y2);
            lineData.push_back(z2);
            lineData.push_back(alpha2);
        }
    }
    
    if (lineData.empty()) return;
    
    glBindVertexArray(lineVAO_);
    glBindBuffer(GL_ARRAY_BUFFER, lineVBO_);
    glBufferData(GL_ARRAY_BUFFER, lineData.size() * sizeof(float), lineData.data(), GL_DYNAMIC_DRAW);
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    
    // 设置线条颜色 - 紫蓝色
    glUniform3f(lineColorLoc_, 0.5f, 0.4f, 0.9f);
    
    glLineWidth(1.5f);
    glDrawArrays(GL_LINES, 0, lineData.size() / 4);
    
    glBindVertexArray(0);
}

void NebulaChatRenderer::renderParticles() {
    std::vector<float> particleData;
    float posScale = 20.0f;  // 与renderNebulas相同的位置缩放
    
    for (const auto& nebula : nebulas_) {
        for (const auto& p : nebula.particles) {
            particleData.push_back((nebula.x + p.x * 0.05f) * posScale);
            particleData.push_back((nebula.y + p.y * 0.05f) * posScale);
            particleData.push_back((nebula.z + p.z * 0.05f) * posScale);
            particleData.push_back(p.size);
            particleData.push_back(p.r);
            particleData.push_back(p.g);
            particleData.push_back(p.b);
            particleData.push_back(p.a);
        }
    }
    
    if (particleData.empty()) return;
    
    glUseProgram(particleProgram_);
    
    // 使用与renderNebulas相同的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float particleMVP[16];
    multiplyMatrix(particleMVP, proj, rot);
    
    glUniformMatrix4fv(particleMVPLoc_, 1, GL_FALSE, particleMVP);
    
    glBindVertexArray(particleVAO_);
    glBindBuffer(GL_ARRAY_BUFFER, particleVBO_);
    glBufferData(GL_ARRAY_BUFFER, particleData.size() * sizeof(float), particleData.data(), GL_DYNAMIC_DRAW);
    
    int stride = 8 * sizeof(float);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, (void*)0);
    glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, stride, (void*)(3 * sizeof(float)));
    glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, stride, (void*)(4 * sizeof(float)));
    
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);
    glEnableVertexAttribArray(2);
    
    glDrawArrays(GL_POINTS, 0, particleData.size() / 8);
    glBindVertexArray(0);
}

void NebulaChatRenderer::addMessage(const std::string& id, bool isUser) {
    MessageNebula nebula;
    nebula.id = id;
    nebula.isUser = isUser;
    
    // 计算在3D空间中的位置 - 围绕AI核心螺旋排列
    // 使用较小的坐标值，因为正交投影会放大
    int index = nebulas_.size();
    float angle = index * 0.9f;  // 每个消息间隔约50度
    
    // 半径从0.8开始，逐渐增大，但保持较小以便在屏幕上可见
    float radius = 0.8f + (index % 5) * 0.15f;
    
    // 高度分布 - 上下交错
    float height = (static_cast<float>(index % 6) - 2.5f) * 0.25f;
    
    // 目标位置
    nebula.targetX = cos(angle) * radius;
    nebula.targetY = height;
    nebula.targetZ = sin(angle) * radius;
    
    // 初始位置 - 从屏幕外飞入
    if (isUser) {
        // 用户消息从右下方飞入
        nebula.x = 2.0f;
        nebula.y = -1.0f;
        nebula.z = 1.0f;
    } else {
        // AI消息从中心扩散出去
        nebula.x = 0.1f;
        nebula.y = 0.1f;
        nebula.z = 0.1f;
    }
    
    nebula.glowPhase = static_cast<float>(rand()) / RAND_MAX * 2.0f * M_PI;
    nebula.scale = 1.0f;
    nebula.birthTime = totalTime_;
    
    // 创建粒子爆发效果
    spawnParticleBurst(nebula);
    
    nebulas_.push_back(nebula);
    LOGI("Nebula: Added message id=%{public}s (isUser=%{public}d), index=%{public}d, target=(%.2f, %.2f, %.2f), total=%{public}zu", 
         id.c_str(), isUser, index, nebula.targetX, nebula.targetY, nebula.targetZ, nebulas_.size());
}

void NebulaChatRenderer::spawnParticleBurst(MessageNebula& nebula) {
    float r, g, b;
    if (nebula.isUser) {
        r = 0.4f; g = 0.7f; b = 1.0f;
    } else {
        r = 0.7f; g = 0.4f; b = 1.0f;
    }
    
    for (int i = 0; i < 50; i++) {
        NebulaParticle p;
        
        float theta = static_cast<float>(rand()) / RAND_MAX * 2.0f * M_PI;
        float phi = acos(2.0f * static_cast<float>(rand()) / RAND_MAX - 1.0f);
        float speed = 2.0f + static_cast<float>(rand()) / RAND_MAX * 4.0f;
        
        p.x = 0;
        p.y = 0;
        p.z = 0;
        p.vx = sin(phi) * cos(theta) * speed;
        p.vy = sin(phi) * sin(theta) * speed;
        p.vz = cos(phi) * speed;
        
        p.life = 1.0f;
        p.maxLife = 2.0f + static_cast<float>(rand()) / RAND_MAX * 1.5f;
        p.size = 3.0f + static_cast<float>(rand()) / RAND_MAX * 5.0f;
        
        p.r = r + static_cast<float>(rand()) / RAND_MAX * 0.2f;
        p.g = g + static_cast<float>(rand()) / RAND_MAX * 0.2f;
        p.b = b + static_cast<float>(rand()) / RAND_MAX * 0.1f;
        p.a = 1.0f;
        
        nebula.particles.push_back(p);
    }
}

void NebulaChatRenderer::removeMessage(const std::string& id) {
    nebulas_.erase(
        std::remove_if(nebulas_.begin(), nebulas_.end(),
            [&id](const MessageNebula& n) { return n.id == id; }),
        nebulas_.end()
    );
}

void NebulaChatRenderer::clearMessages() {
    nebulas_.clear();
}

void NebulaChatRenderer::addFeatureOrb(const std::string& id, float r, float g, float b) {
    FeatureOrb orb;
    orb.id = id;
    orb.r = r;
    orb.g = g;
    orb.b = b;
    orb.glowPhase = static_cast<float>(rand()) / RAND_MAX * 2.0f * M_PI;
    
    // 功能球体固定位置 - 围绕AI核心均匀分布
    int index = featureOrbs_.size();
    float angle = index * (2.0f * M_PI / 4.0f) + M_PI / 4.0f;  // 4个球体，从45度开始
    float radius = 1.2f;  // 固定半径
    
    orb.baseAngle = angle;
    orb.x = cos(angle) * radius;
    orb.y = 0.0f;  // 水平面上
    orb.z = sin(angle) * radius;
    
    featureOrbs_.push_back(orb);
    LOGI("Nebula: Added feature orb id=%{public}s, color=(%.1f,%.1f,%.1f), pos=(%.2f,%.2f,%.2f)", 
         id.c_str(), r, g, b, orb.x, orb.y, orb.z);
}

void NebulaChatRenderer::clearFeatureOrbs() {
    featureOrbs_.clear();
}

void NebulaChatRenderer::renderFeatureOrbs() {
    if (featureOrbs_.empty()) return;
    
    glUseProgram(nebulaProgram_);  // 复用星云着色器
    
    // 使用与renderCore相同的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float mvp[16];
    multiplyMatrix(mvp, proj, rot);
    
    glUniformMatrix4fv(nebulaMVPLoc_, 1, GL_FALSE, mvp);
    glUniform1f(nebulaTimeLoc_, totalTime_);
    
    // 构建功能球体顶点数据
    std::vector<float> orbData;
    float posScale = 20.0f;
    
    for (size_t i = 0; i < featureOrbs_.size(); i++) {
        auto& orb = featureOrbs_[i];
        
        // 缓慢旋转
        float rotSpeed = 0.15f;
        float currentAngle = orb.baseAngle + totalTime_ * rotSpeed;
        float radius = 1.2f;
        
        orb.x = cos(currentAngle) * radius;
        orb.z = sin(currentAngle) * radius;
        
        // 轻微上下浮动
        float floatY = sin(totalTime_ * 0.8f + i * 1.5f) * 0.15f;
        orb.y = floatY;
        
        // 位置
        orbData.push_back(orb.x * posScale);
        orbData.push_back(orb.y * posScale);
        orbData.push_back(orb.z * posScale);
        
        // 颜色 - 更亮
        orbData.push_back(orb.r);
        orbData.push_back(orb.g);
        orbData.push_back(orb.b);
        
        // 大小 - 比消息球体大
        orbData.push_back(140.0f);
        
        // 呼吸效果 - 更明显
        orb.glowPhase += 0.033f * 2.0f;
        float glow = 0.9f + 0.1f * sin(orb.glowPhase);
        orbData.push_back(glow);
    }
    
    glBindVertexArray(nebulaVAO_);
    glBindBuffer(GL_ARRAY_BUFFER, nebulaVBO_);
    glBufferData(GL_ARRAY_BUFFER, orbData.size() * sizeof(float), orbData.data(), GL_DYNAMIC_DRAW);
    
    int stride = 8 * sizeof(float);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, (void*)(6 * sizeof(float)));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, stride, (void*)(7 * sizeof(float)));
    glEnableVertexAttribArray(3);
    
    // 绘制两遍增强发光
    glDrawArrays(GL_POINTS, 0, featureOrbs_.size());
    glDrawArrays(GL_POINTS, 0, featureOrbs_.size());
    
    glBindVertexArray(0);
}

int NebulaChatRenderer::hitTestFeature(float screenX, float screenY) {
    if (featureOrbs_.empty()) return -1;
    
    // 将屏幕坐标转换为归一化设备坐标
    float ndcX = (2.0f * screenX / width_) - 1.0f;
    float ndcY = 1.0f - (2.0f * screenY / height_);
    
    // 使用与renderFeatureOrbs相同的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float mvp[16];
    multiplyMatrix(mvp, proj, rot);
    
    int closestIdx = -1;
    float closestDist = 0.2f;  // 点击阈值
    float posScale = 20.0f;
    
    for (size_t i = 0; i < featureOrbs_.size(); i++) {
        const auto& orb = featureOrbs_[i];
        
        float scaledX = orb.x * posScale;
        float scaledY = orb.y * posScale;
        float scaledZ = orb.z * posScale;
        
        float clipX = mvp[0] * scaledX + mvp[4] * scaledY + mvp[8] * scaledZ + mvp[12];
        float clipY = mvp[1] * scaledX + mvp[5] * scaledY + mvp[9] * scaledZ + mvp[13];
        
        float dx = clipX - ndcX;
        float dy = clipY - ndcY;
        float dist = sqrt(dx * dx + dy * dy);
        
        if (dist < closestDist) {
            closestDist = dist;
            closestIdx = static_cast<int>(i);
        }
    }
    
    if (closestIdx >= 0) {
        LOGI("Nebula: hitTestFeature - hit orb index %{public}d", closestIdx);
    }
    
    return closestIdx;
}

void NebulaChatRenderer::scroll(float deltaY) {
    cameraRotX_ += deltaY * 0.002f;
    if (cameraRotX_ > 1.2f) cameraRotX_ = 1.2f;
    if (cameraRotX_ < -0.5f) cameraRotX_ = -0.5f;
}

void NebulaChatRenderer::setCameraPosition(float x, float y, float z) {
    cameraX_ = x;
    cameraY_ = y;
    cameraZ_ = z;
}

void NebulaChatRenderer::rotateCamera(float deltaX, float deltaY) {
    cameraRotY_ += deltaX * 0.005f;
    cameraRotX_ += deltaY * 0.005f;
    
    if (cameraRotX_ > 1.2f) cameraRotX_ = 1.2f;
    if (cameraRotX_ < -0.5f) cameraRotX_ = -0.5f;
}

void NebulaChatRenderer::zoom(float delta) {
    cameraZ_ += delta;
    if (cameraZ_ < 4.0f) cameraZ_ = 4.0f;
    if (cameraZ_ > 20.0f) cameraZ_ = 20.0f;
}

void NebulaChatRenderer::onTouch(float x, float y) {
    // 点击检测
}

int NebulaChatRenderer::hitTest(float screenX, float screenY) {
    if (nebulas_.empty()) {
        LOGI("Nebula: hitTest - nebulas_ is empty");
        return -1;
    }
    
    LOGI("Nebula: hitTest called with screen (%.1f, %.1f), width=%{public}d, height=%{public}d", 
         screenX, screenY, width_, height_);
    
    // 将屏幕坐标转换为归一化设备坐标
    float ndcX = (2.0f * screenX / width_) - 1.0f;
    float ndcY = 1.0f - (2.0f * screenY / height_);
    
    LOGI("Nebula: NDC coordinates: (%.3f, %.3f)", ndcX, ndcY);
    
    // 使用与renderNebulas相同的正交投影
    float aspect = (float)width_ / (float)height_;
    float scale = 0.02f;
    
    float proj[16];
    memset(proj, 0, sizeof(proj));
    proj[0] = scale / aspect;
    proj[5] = scale;
    proj[10] = scale;
    proj[15] = 1.0f;
    
    // 旋转矩阵 - 绕Y轴
    float cosY = cos(cameraRotY_);
    float sinY = sin(cameraRotY_);
    float rotY[16];
    memset(rotY, 0, sizeof(rotY));
    rotY[0] = cosY;   rotY[2] = sinY;
    rotY[5] = 1.0f;
    rotY[8] = -sinY;  rotY[10] = cosY;
    rotY[15] = 1.0f;
    
    // 旋转矩阵 - 绕X轴
    float cosX = cos(cameraRotX_);
    float sinX = sin(cameraRotX_);
    float rotX[16];
    memset(rotX, 0, sizeof(rotX));
    rotX[0] = 1.0f;
    rotX[5] = cosX;   rotX[6] = -sinX;
    rotX[9] = sinX;   rotX[10] = cosX;
    rotX[15] = 1.0f;
    
    // 组合
    float rot[16];
    multiplyMatrix(rot, rotX, rotY);
    
    float mvp[16];
    multiplyMatrix(mvp, proj, rot);
    
    // 检测每个星云
    int closestIdx = -1;
    float closestDist = 0.25f;  // 增大点击阈值
    
    float posScale = 20.0f;  // 与renderNebulas相同的位置缩放
    
    for (size_t i = 0; i < nebulas_.size(); i++) {
        const auto& nebula = nebulas_[i];
        
        // 应用位置缩放
        float scaledX = nebula.x * posScale;
        float scaledY = nebula.y * posScale;
        float scaledZ = nebula.z * posScale;
        
        // 变换到裁剪空间（正交投影，w=1）
        float clipX = mvp[0] * scaledX + mvp[4] * scaledY + mvp[8] * scaledZ + mvp[12];
        float clipY = mvp[1] * scaledX + mvp[5] * scaledY + mvp[9] * scaledZ + mvp[13];
        
        // 计算距离
        float dx = clipX - ndcX;
        float dy = clipY - ndcY;
        float dist = sqrt(dx * dx + dy * dy);
        
        if (i == 0) {
            LOGI("Nebula: Nebula[0] pos=(%.2f,%.2f,%.2f) -> clip=(%.3f,%.3f), dist=%.3f", 
                 nebula.x, nebula.y, nebula.z, clipX, clipY, dist);
        }
        
        if (dist < closestDist) {
            closestDist = dist;
            closestIdx = static_cast<int>(i);
        }
    }
    
    LOGI("Nebula: hitTest result: closestIdx=%{public}d, closestDist=%.3f", closestIdx, closestDist);
    
    return closestIdx;
}

void NebulaChatRenderer::destroy() {
    if (!initialized_) return;
    
    if (starProgram_) glDeleteProgram(starProgram_);
    if (coreProgram_) glDeleteProgram(coreProgram_);
    if (nebulaProgram_) glDeleteProgram(nebulaProgram_);
    if (particleProgram_) glDeleteProgram(particleProgram_);
    if (lineProgram_) glDeleteProgram(lineProgram_);
    
    if (starVAO_) glDeleteVertexArrays(1, &starVAO_);
    if (starVBO_) glDeleteBuffers(1, &starVBO_);
    if (coreVAO_) glDeleteVertexArrays(1, &coreVAO_);
    if (coreVBO_) glDeleteBuffers(1, &coreVBO_);
    if (nebulaVAO_) glDeleteVertexArrays(1, &nebulaVAO_);
    if (nebulaVBO_) glDeleteBuffers(1, &nebulaVBO_);
    if (particleVAO_) glDeleteVertexArrays(1, &particleVAO_);
    if (particleVBO_) glDeleteBuffers(1, &particleVBO_);
    if (lineVAO_) glDeleteVertexArrays(1, &lineVAO_);
    if (lineVBO_) glDeleteBuffers(1, &lineVBO_);
    
    if (eglDisplay_ != EGL_NO_DISPLAY) {
        eglMakeCurrent(eglDisplay_, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
        if (eglSurface_ != EGL_NO_SURFACE) {
            eglDestroySurface(eglDisplay_, eglSurface_);
        }
        if (eglContext_ != EGL_NO_CONTEXT) {
            eglDestroyContext(eglDisplay_, eglContext_);
        }
        eglTerminate(eglDisplay_);
    }
    
    initialized_ = false;
    LOGI("Nebula: Renderer destroyed");
}


// 矩阵运算
void NebulaChatRenderer::setProjectionMatrix() {
    float aspect = static_cast<float>(width_) / height_;
    float fov = 60.0f * M_PI / 180.0f;  // 增大FOV
    float near = 0.1f;
    float far = 200.0f;  // 增大远平面
    
    float f = 1.0f / tan(fov / 2.0f);
    
    memset(projMatrix_, 0, sizeof(projMatrix_));
    projMatrix_[0] = f / aspect;
    projMatrix_[5] = f;
    projMatrix_[10] = (far + near) / (near - far);
    projMatrix_[11] = -1.0f;
    projMatrix_[14] = (2.0f * far * near) / (near - far);
    
    LOGI("Nebula: Projection - aspect=%.2f, fov=60, near=0.1, far=200", aspect);
}

void NebulaChatRenderer::setViewMatrix() {
    // 简单的视图矩阵 - 相机在Z轴正方向看向原点
    memset(viewMatrix_, 0, sizeof(viewMatrix_));
    viewMatrix_[0] = 1.0f;
    viewMatrix_[5] = 1.0f;
    viewMatrix_[10] = 1.0f;
    viewMatrix_[15] = 1.0f;
    
    // 平移相机（相机在 (0, 0, cameraZ_) 位置看向原点）
    viewMatrix_[14] = -cameraZ_;
    
    // 应用旋转
    if (cameraRotX_ != 0.0f) {
        rotateMatrixX(viewMatrix_, cameraRotX_);
    }
    if (cameraRotY_ != 0.0f) {
        rotateMatrixY(viewMatrix_, cameraRotY_);
    }
    
    // 调试输出
    static int viewFrameCount = 0;
    viewFrameCount++;
    if (viewFrameCount % 90 == 0) {
        LOGI("Nebula: ViewMatrix - camZ=%.1f, rotX=%.2f, rotY=%.2f, m14=%.2f", 
             cameraZ_, cameraRotX_, cameraRotY_, viewMatrix_[14]);
    }
}

void NebulaChatRenderer::multiplyMatrix(float* result, const float* a, const float* b) {
    float temp[16];
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            temp[i * 4 + j] = 0;
            for (int k = 0; k < 4; k++) {
                temp[i * 4 + j] += a[i * 4 + k] * b[k * 4 + j];
            }
        }
    }
    memcpy(result, temp, sizeof(temp));
}

void NebulaChatRenderer::translateMatrix(float* m, float x, float y, float z) {
    m[12] += m[0] * x + m[4] * y + m[8] * z;
    m[13] += m[1] * x + m[5] * y + m[9] * z;
    m[14] += m[2] * x + m[6] * y + m[10] * z;
    m[15] += m[3] * x + m[7] * y + m[11] * z;
}

void NebulaChatRenderer::rotateMatrixY(float* m, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    
    float m0 = m[0], m4 = m[4], m8 = m[8], m12 = m[12];
    float m2 = m[2], m6 = m[6], m10 = m[10], m14 = m[14];
    
    m[0] = m0 * c + m2 * s;
    m[4] = m4 * c + m6 * s;
    m[8] = m8 * c + m10 * s;
    m[12] = m12 * c + m14 * s;
    
    m[2] = m2 * c - m0 * s;
    m[6] = m6 * c - m4 * s;
    m[10] = m10 * c - m8 * s;
    m[14] = m14 * c - m12 * s;
}

void NebulaChatRenderer::rotateMatrixX(float* m, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    
    float m1 = m[1], m5 = m[5], m9 = m[9], m13 = m[13];
    float m2 = m[2], m6 = m[6], m10 = m[10], m14 = m[14];
    
    m[1] = m1 * c - m2 * s;
    m[5] = m5 * c - m6 * s;
    m[9] = m9 * c - m10 * s;
    m[13] = m13 * c - m14 * s;
    
    m[2] = m1 * s + m2 * c;
    m[6] = m5 * s + m6 * c;
    m[10] = m9 * s + m10 * c;
    m[14] = m13 * s + m14 * c;
}

} // namespace nebula
