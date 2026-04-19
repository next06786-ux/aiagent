#ifndef SHADER_UTILS_H
#define SHADER_UTILS_H

#include <GLES3/gl3.h>
#include <string>

class ShaderUtils {
public:
    static GLuint createProgram(const char* vertexSource, const char* fragmentSource);
    static GLuint loadShader(GLenum type, const char* source);
};

// ============ 节点着色器 - 超强发光效果 + 脉冲动画 ============
const char* const NODE_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aColor;
layout(location = 2) in float aSize;

uniform mat4 uMVPMatrix;
uniform float uPointScale;
uniform float uTime;
uniform int uSelectedIdx;
uniform int uVertexIdx;

out vec3 vColor;
out float vSize;
out float vSelected;
out float vPulse;

void main() {
    gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
    
    // 脉冲呼吸效果 - 每个节点有不同的相位
    float phase = float(gl_VertexID) * 0.5;
    float pulse = sin(uTime * 2.0 + phase) * 0.12 + 1.0;
    
    // 选中节点有更强的脉冲
    float selected = (gl_VertexID == uSelectedIdx) ? 1.0 : 0.0;
    if (selected > 0.5) {
        pulse = sin(uTime * 4.0) * 0.2 + 1.15;
    }
    
    // 透视缩放：近大远小，整体放大1.5倍
    float depthScale = 350.0 / max(gl_Position.w, 80.0);
    float pointSize = aSize * uPointScale * depthScale * pulse * 1.5;
    
    // 选中节点更大
    if (selected > 0.5) {
        pointSize *= 1.4;
    }
    
    gl_PointSize = clamp(pointSize, 20.0, 400.0);
    vColor = aColor;
    vSize = aSize;
    vSelected = selected;
    vPulse = pulse;
}
)";

const char* const NODE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec3 vColor;
in float vSize;
in float vSelected;
in float vPulse;

out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    // 精致的多层发光效果 - 更柔和的过渡
    float core = smoothstep(0.06, 0.0, dist);              // 超亮核心
    float inner1 = smoothstep(0.12, 0.0, dist) * 0.85;     // 内层1
    float inner2 = smoothstep(0.22, 0.0, dist) * 0.55;     // 内层2
    float outer1 = smoothstep(0.35, 0.0, dist) * 0.3;      // 外层1
    float outer2 = smoothstep(0.45, 0.0, dist) * 0.18;     // 外层2
    float glow = smoothstep(0.6, 0.0, dist) * 0.08;        // 最外层微光
    
    float alpha = core + inner1 + inner2 + outer1 + outer2 + glow;
    
    // 选中节点添加高级光环效果
    if (vSelected > 0.5) {
        // 柔和的内层辉光 - 从核心向外扩散
        float innerBloom = exp(-dist * dist * 12.0) * 0.4 * vPulse;
        alpha += innerBloom;
        
        // 精致的薄光环 - 用高斯函数而非硬边
        float ringDist = abs(dist - 0.38);
        float thinRing = exp(-ringDist * ringDist * 800.0) * 0.7 * vPulse;
        alpha += thinRing;
        
        // 外层柔和呼吸光晕 - 大范围低强度
        float outerBloom = exp(-dist * dist * 4.0) * 0.12 * (0.7 + 0.3 * vPulse);
        alpha += outerBloom;
    }
    
    // 核心纯白，向外渐变到节点颜色，更柔和的过渡
    vec3 white = vec3(1.0);
    vec3 brightColor = vColor * 1.4;  // 颜色更鲜艳
    vec3 color = mix(brightColor, white, core * 0.95 + inner1 * 0.6 + inner2 * 0.2);
    
    // 选中节点颜色更亮但保持自然
    if (vSelected > 0.5) {
        color = mix(color, white, 0.15 + 0.1 * vPulse);
    }
    
    fragColor = vec4(color, alpha);
}
)";

// ============ 连线着色器 - 发光射线 ============
const char* const LINE_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec4 aColor;

uniform mat4 uMVPMatrix;

out vec4 vColor;
out float vDepth;

void main() {
    gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
    vColor = aColor;
    vDepth = gl_Position.w;
}
)";

const char* const LINE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec4 vColor;
in float vDepth;
out vec4 fragColor;

void main() {
    // 根据深度调整亮度，近处更亮，整体更亮
    float depthFactor = 350.0 / max(vDepth, 80.0);
    vec3 color = vColor.rgb * (1.4 + depthFactor * 0.4);
    // 增加线条透明度
    float alpha = vColor.a * depthFactor * 1.2;
    fragColor = vec4(color, clamp(alpha, 0.0, 1.0));
}
)";

// ============ 背景星空着色器 - 3D版本 增强亮度 ============
const char* const STAR_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec3 aPosition;
layout(location = 1) in float aSize;
layout(location = 2) in float aBrightness;
layout(location = 3) in vec3 aColor;

uniform mat4 uMVPMatrix;

out float vBrightness;
out vec3 vColor;
out float vDepth;

void main() {
    gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
    
    // 透视缩放 - 远处的星星更小，但保持最小可见大小
    float depthScale = 600.0 / max(gl_Position.w, 50.0);
    gl_PointSize = clamp(aSize * depthScale, 2.0, 25.0);
    
    vBrightness = aBrightness;
    vColor = aColor;
    vDepth = gl_Position.w;
}
)";

const char* const STAR_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in float vBrightness;
in vec3 vColor;
in float vDepth;
out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    // 更强的发光效果
    float core = smoothstep(0.15, 0.0, dist);
    float inner = smoothstep(0.3, 0.0, dist) * 0.7;
    float glow = smoothstep(0.5, 0.0, dist) * 0.4;
    
    // 根据深度调整亮度 - 近处更亮
    float depthFactor = clamp(600.0 / vDepth, 0.5, 2.0);
    
    float alpha = (core + inner + glow) * vBrightness * depthFactor;
    
    // 核心更白更亮
    vec3 color = mix(vColor * 1.2, vec3(1.0), core * 0.9);
    
    fragColor = vec4(color, alpha);
}
)";

// ============ 星云背景着色器 ============
const char* const NEBULA_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec2 aPosition;
layout(location = 1) in vec2 aTexCoord;

out vec2 vTexCoord;

void main() {
    gl_Position = vec4(aPosition, 0.0, 1.0);
    vTexCoord = aTexCoord;
}
)";

const char* const NEBULA_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec2 vTexCoord;
uniform float uTime;
uniform vec2 uResolution;

out vec4 fragColor;

// 简化的噪声函数
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    for (int i = 0; i < 4; i++) {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

void main() {
    vec2 uv = vTexCoord;
    
    // 缓慢移动的星云
    float t = uTime * 0.02;
    
    // 多层星云
    float n1 = fbm(uv * 2.0 + vec2(t * 0.3, t * 0.2));
    float n2 = fbm(uv * 3.0 - vec2(t * 0.2, t * 0.4));
    float n3 = fbm(uv * 1.5 + vec2(t * 0.1, -t * 0.15));
    
    // 星云颜色 - 深蓝紫色调
    vec3 color1 = vec3(0.1, 0.05, 0.2);   // 深紫
    vec3 color2 = vec3(0.05, 0.1, 0.25);  // 深蓝
    vec3 color3 = vec3(0.15, 0.08, 0.18); // 紫红
    
    vec3 nebula = color1 * n1 * 0.4 + color2 * n2 * 0.3 + color3 * n3 * 0.3;
    
    // 添加一些亮点
    float sparkle = pow(noise(uv * 50.0 + t), 8.0) * 0.3;
    nebula += vec3(sparkle * 0.5, sparkle * 0.3, sparkle);
    
    // 边缘渐暗
    float vignette = 1.0 - length(uv - 0.5) * 0.8;
    vignette = clamp(vignette, 0.0, 1.0);
    
    fragColor = vec4(nebula * vignette, 0.6);
}
)";

// ============ 流光粒子着色器 - 带拖尾效果 ============
const char* const PARTICLE_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec3 aPosition;
layout(location = 1) in float aAlpha;
layout(location = 2) in vec3 aColor;
layout(location = 3) in float aProgress;

uniform mat4 uMVPMatrix;
uniform float uPointSize;
uniform float uTime;

out float vAlpha;
out vec3 vColor;
out float vProgress;

void main() {
    gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
    
    // 粒子大小随进度变化 - 中间最大
    float sizeMod = sin(aProgress * 3.14159) * 0.5 + 0.8;
    // 添加闪烁效果
    float flicker = sin(uTime * 10.0 + aProgress * 20.0) * 0.1 + 1.0;
    
    gl_PointSize = uPointSize * sizeMod * flicker / max(gl_Position.w, 1.0);
    vAlpha = aAlpha;
    vColor = aColor;
    vProgress = aProgress;
}
)";

const char* const PARTICLE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in float vAlpha;
in vec3 vColor;
in float vProgress;
out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    // 多层发光
    float core = smoothstep(0.2, 0.0, dist);
    float glow = smoothstep(0.5, 0.0, dist) * 0.6;
    float outer = smoothstep(0.7, 0.0, dist) * 0.3;
    
    float alpha = (core + glow + outer) * vAlpha;
    
    // 颜色：核心更亮
    vec3 color = mix(vColor * 1.5, vec3(1.0), core * 0.7);
    
    fragColor = vec4(color, alpha);
}
)";

// ============ 文字标签着色器 - Billboard 四边形 ============
const char* const TEXT_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec3 aPosition;    // 节点3D位置
layout(location = 1) in vec2 aOffset;      // 四边形顶点偏移
layout(location = 2) in vec2 aTexCoord;    // 纹理坐标
layout(location = 3) in vec4 aColor;       // 颜色
layout(location = 4) in float aScale;      // 缩放

uniform mat4 uMVPMatrix;
uniform mat4 uViewMatrix;
uniform vec2 uScreenSize;

out vec2 vTexCoord;
out vec4 vColor;

void main() {
    // 先变换到裁剪空间
    vec4 clipPos = uMVPMatrix * vec4(aPosition, 1.0);
    
    // 在屏幕空间添加偏移（billboard效果）
    vec2 screenOffset = aOffset * aScale / uScreenSize * clipPos.w * 2.0;
    clipPos.xy += screenOffset;
    
    gl_Position = clipPos;
    vTexCoord = aTexCoord;
    vColor = aColor;
}
)";

const char* const TEXT_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec2 vTexCoord;
in vec4 vColor;

uniform sampler2D uTexture;

out vec4 fragColor;

void main() {
    float alpha = texture(uTexture, vTexCoord).a;
    
    // 添加发光效果
    float glow = smoothstep(0.0, 0.5, alpha) * 0.3;
    float core = smoothstep(0.4, 0.6, alpha);
    
    vec3 color = vColor.rgb;
    float finalAlpha = (core + glow) * vColor.a;
    
    fragColor = vec4(color, finalAlpha);
}
)";

#endif // SHADER_UTILS_H
