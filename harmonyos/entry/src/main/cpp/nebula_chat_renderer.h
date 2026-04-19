/**
 * 星云对话渲染器 - 真正的3D OpenGL ES
 * 
 * 设计：
 * - 中心是AI核心（发光球体）
 * - 消息星云围绕AI核心在3D空间中螺旋排列
 * - 用户消息蓝色，AI消息紫色
 * - 消息通过光线连接到中心
 */
#ifndef NEBULA_CHAT_RENDERER_H
#define NEBULA_CHAT_RENDERER_H

#include <GLES3/gl3.h>
#include <EGL/egl.h>
#include <native_window/external_window.h>
#include <vector>
#include <string>
#include <cmath>
#include <cstdlib>

namespace nebula {

// 3D星星
struct Star3D {
    float x, y, z;
    float size;
    float brightness;
    float twinklePhase;
    float twinkleSpeed;
    float r, g, b;
};

// 3D星云粒子
struct NebulaParticle {
    float x, y, z;
    float vx, vy, vz;
    float life;
    float maxLife;
    float size;
    float r, g, b, a;
};

// 消息星云
struct MessageNebula {
    std::string id;
    float x, y, z;
    float targetX, targetY, targetZ;
    float glowPhase;
    float scale;
    bool isUser;
    std::vector<NebulaParticle> particles;
    float birthTime;
};

// 功能球体
struct FeatureOrb {
    std::string id;
    float x, y, z;
    float r, g, b;      // 颜色
    float glowPhase;
    float baseAngle;    // 基础角度
};

class NebulaChatRenderer {
public:
    NebulaChatRenderer();
    ~NebulaChatRenderer();
    
    bool init(OHNativeWindow* window, int width, int height);
    void resize(int width, int height);
    void render();
    void destroy();
    
    void setCameraPosition(float x, float y, float z);
    void rotateCamera(float deltaX, float deltaY);
    void zoom(float delta);
    
    void addMessage(const std::string& id, bool isUser);
    void removeMessage(const std::string& id);
    void clearMessages();
    
    void addFeatureOrb(const std::string& id, float r, float g, float b);
    void clearFeatureOrbs();
    
    void scroll(float deltaY);
    void onTouch(float x, float y);
    int hitTest(float screenX, float screenY);  // 返回点击的消息索引，-1表示没点中
    int hitTestFeature(float screenX, float screenY);  // 返回点击的功能球体索引，-1表示没点中
    
private:
    bool initEGL(OHNativeWindow* window);
    void initShaders();
    void initStars();
    void initBuffers();
    
    void renderStars();
    void renderCore();
    void renderCoreGlow();
    void renderNebulas();
    void renderFeatureOrbs();
    void renderLines();
    void renderParticles();
    
    void updateAnimation(float deltaTime);
    void spawnParticleBurst(MessageNebula& nebula);
    
    void setProjectionMatrix();
    void setViewMatrix();
    void multiplyMatrix(float* result, const float* a, const float* b);
    void translateMatrix(float* m, float x, float y, float z);
    void rotateMatrixY(float* m, float angle);
    void rotateMatrixX(float* m, float angle);
    
    int width_, height_;
    bool initialized_;
    
    float cameraX_, cameraY_, cameraZ_;
    float cameraRotX_, cameraRotY_;
    float cameraTargetZ_;
    
    float lastTime_;
    float totalTime_;
    
    std::vector<Star3D> stars_;
    float starRotation_;
    
    std::vector<MessageNebula> nebulas_;
    std::vector<FeatureOrb> featureOrbs_;
    float nebulaSpacing_;
    
    // Shader programs
    GLuint starProgram_;
    GLuint coreProgram_;
    GLuint nebulaProgram_;
    GLuint particleProgram_;
    GLuint lineProgram_;
    
    // VAO/VBO (点精灵方式，不需要EBO)
    GLuint starVAO_, starVBO_;
    GLuint coreVAO_, coreVBO_;
    GLuint nebulaVAO_, nebulaVBO_;
    GLuint particleVAO_, particleVBO_;
    GLuint lineVAO_, lineVBO_;
    
    // Uniforms
    GLint starMVPLoc_, starTimeLoc_;
    GLint coreMVPLoc_, coreTimeLoc_, corePointSizeLoc_;
    GLint nebulaMVPLoc_, nebulaTimeLoc_;
    GLint particleMVPLoc_;
    GLint lineMVPLoc_, lineColorLoc_;
    
    float projMatrix_[16];
    float viewMatrix_[16];
    float mvpMatrix_[16];
    float modelMatrix_[16];
    
    // EGL
    EGLDisplay eglDisplay_;
    EGLSurface eglSurface_;
    EGLContext eglContext_;
};

} // namespace nebula

#endif // NEBULA_CHAT_RENDERER_H
