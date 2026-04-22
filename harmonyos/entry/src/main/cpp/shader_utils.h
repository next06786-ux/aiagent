#ifndef SHADER_UTILS_H
#define SHADER_UTILS_H

#include <GLES3/gl3.h>
#include <string>

class ShaderUtils {
public:
    static GLuint createProgram(const char* vertexSource, const char* fragmentSource);
    static GLuint loadShader(GLenum type, const char* source);
};

// ============ 球体节点着色器 - 真实3D球体（仿Android，推荐使用） ============
const char* const SPHERE_VERTEX_SHADER = R"(#version 300 es
precision highp float;
precision highp int;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uMVPMatrix;
uniform vec3 uNodePosition;
uniform float uNodeSize;
uniform float uTime;
uniform highp int uIsSelected;

out vec3 vNormal;
out vec3 vViewDir;
out vec3 vWorldPos;
out vec2 vTexCoord;
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
    
    // 传递法线和位置
    vNormal = normalize(aNormal);
    vWorldPos = worldPos;
    
    // 计算视图方向（简化版）
    vec4 mv = uMVPMatrix * vec4(worldPos, 1.0);
    vViewDir = normalize(-mv.xyz);
    
    vTexCoord = aTexCoord;
    vPulse = pulse;
}
)";

const char* const SPHERE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;
precision highp int;

in vec3 vNormal;
in vec3 vViewDir;
in vec3 vWorldPos;
in vec2 vTexCoord;
in float vPulse;

uniform vec3 uNodeColor;
uniform vec3 uLightDir;
uniform highp int uIsSelected;
uniform float uTime;

out vec4 fragColor;

// ============ 噪声函数（生成星球表面） ============
float hash3(vec3 p) {
    return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float vnoise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    
    return mix(
        mix(
            mix(hash3(i), hash3(i + vec3(1,0,0)), u.x),
            mix(hash3(i + vec3(0,1,0)), hash3(i + vec3(1,1,0)), u.x),
            u.y
        ),
        mix(
            mix(hash3(i + vec3(0,0,1)), hash3(i + vec3(1,0,1)), u.x),
            mix(hash3(i + vec3(0,1,1)), hash3(i + vec3(1,1,1)), u.x),
            u.y
        ),
        u.z
    );
}

// 分形布朗运动（FBM）
float fbm(vec3 p) {
    float v = 0.0;
    float a = 0.55;
    for(int i = 0; i < 5; i++) {
        v += a * vnoise(p);
        p = p * 2.03 + vec3(1.7, 9.2, 3.4);
        a *= 0.48;
    }
    return v;
}

// 扭曲的 FBM（生成更复杂的地形）
float wfbm(vec3 p) {
    vec3 q = vec3(
        fbm(p),
        fbm(p + vec3(5.2, 1.3, 2.8)),
        fbm(p + vec3(1.7, 9.2, 3.4))
    );
    return fbm(p + 1.8 * q);
}

// Y轴旋转
vec3 rotY(vec3 p, float a) {
    float c = cos(a);
    float s = sin(a);
    return vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z);
}

void main() {
    vec3 N = normalize(vNormal);
    vec3 V = normalize(vViewDir);
    vec3 L = normalize(uLightDir);
    
    // 旋转的球面坐标（让星球自转）
    vec3 sp = rotY(normalize(vWorldPos), uTime * 0.06);
    
    // 生成地形高度（0-1）
    float h = smoothstep(0.30, 0.72, wfbm(sp * 2.2));
    
    // 极地冰盖
    float lat = abs(sp.y);
    float iceBase = smoothstep(0.60, 0.82, lat);
    float ice = clamp(iceBase + vnoise(sp * 8.0) * 0.15 * (1.0 - iceBase), 0.0, 1.0);
    
    // ============ 地形分层着色 ============
    vec3 deepSea = vec3(0.04, 0.10, 0.28) * (uNodeColor * 0.6 + vec3(0.4));
    vec3 shallow = vec3(0.08, 0.22, 0.52) * (uNodeColor * 0.5 + vec3(0.5));
    vec3 beach = vec3(0.76, 0.70, 0.50) * (uNodeColor * 0.3 + vec3(0.7));
    vec3 low = uNodeColor * 0.75 + vec3(0.05, 0.08, 0.02);
    vec3 mid = uNodeColor * 0.95 + vec3(0.02, 0.05, 0.01);
    vec3 high = uNodeColor * 1.15 + vec3(0.06, 0.06, 0.06);
    vec3 snow = vec3(0.90, 0.93, 1.00);
    
    vec3 sc;
    if (h < 0.18) {
        sc = mix(deepSea, shallow, smoothstep(0.0, 0.18, h));
    } else if (h < 0.24) {
        sc = mix(shallow, beach, smoothstep(0.18, 0.24, h));
    } else if (h < 0.42) {
        sc = mix(beach, low, smoothstep(0.24, 0.42, h));
    } else if (h < 0.65) {
        sc = mix(low, mid, smoothstep(0.42, 0.65, h));
    } else if (h < 0.82) {
        sc = mix(mid, high, smoothstep(0.65, 0.82, h));
    } else {
        sc = mix(high, snow, smoothstep(0.82, 1.0, h));
    }
    
    // 混合冰盖
    sc = mix(sc, snow, ice * 0.9);
    
    // ============ 光照计算 ============
    float isOcean = 1.0 - smoothstep(0.18, 0.26, h);
    
    // 镜面反射（海洋）
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(N, H), 0.0), 120.0) * 0.9 * isOcean;
    
    // 漫反射
    float diff = max(dot(N, L), 0.0);
    float term = smoothstep(-0.05, 0.18, diff);
    
    // ============ 云层 ============
    vec3 cp = rotY(normalize(vWorldPos), uTime * 0.13 + 1.5);
    float cloud = smoothstep(0.52, 0.72, wfbm(cp * 2.8 + vec3(0.0, 2.0, 0.0)));
    vec3 cloudCol = vec3(0.95, 0.97, 1.0) * (diff * 0.7 + 0.3);
    
    // ============ 城市灯光（夜晚面） ============
    float city = smoothstep(0.70, 0.76, vnoise(sp * 9.0)) * (1.0 - ice) * (1.0 - term);
    
    // 夜晚颜色
    vec3 nightCol = sc * 0.04 + uNodeColor * 1.2 * city * (1.0 - cloud * 0.8);
    
    // 白天颜色
    vec3 dayCol = sc * (diff * 0.85 + 0.12) * (1.0 - cloud * 0.35) + 
                  vec3(0.0, 0.15, 0.4) * isOcean * 0.3;
    dayCol = mix(dayCol, cloudCol, cloud * term);
    
    // 混合昼夜
    vec3 planet = mix(nightCol, dayCol, term) + vec3(spec) * term;
    
    // ============ 大气层边缘光 ============
    float rim = pow(1.0 - max(dot(N, V), 0.0), 3.5);
    vec3 atm = mix(vec3(0.25, 0.55, 1.0), uNodeColor * 0.6, 0.35) * 
               rim * mix(0.15, 0.65, smoothstep(0.0, 0.5, diff));
    planet = mix(planet, atm, rim * 0.55);
    planet += atm * 0.4;
    
    // ============ 选中高亮 ============
    if (uIsSelected == 1) {
        float sp2 = sin(uTime * 2.5) * 0.5 + 0.5;
        planet += vec3(0.3, 1.0, 0.85) * rim * (1.0 + sp2 * 0.6);
    }
    
    fragColor = vec4(planet, 1.0);
}
)";

// ============ 节点着色器 - 改进的星球效果（点精灵版本，备用） ============
const char* const NODE_VERTEX_SHADER = R"(#version 300 es
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aColor;
layout(location = 2) in float aSize;

uniform mat4 uMVPMatrix;
uniform float uPointScale;
uniform float uTime;
uniform int uSelectedIdx;

out vec3 vColor;
out vec3 vWorldPos;
out float vSize;
out float vSelected;
out float vPulse;

void main() {
    vWorldPos = aPosition;
    gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
    
    // 脉冲呼吸效果
    float phase = float(gl_VertexID) * 0.5;
    float pulse = sin(uTime * 2.0 + phase) * 0.08 + 1.0;
    
    // 选中节点有更强的脉冲
    float selected = (gl_VertexID == uSelectedIdx) ? 1.0 : 0.0;
    if (selected > 0.5) {
        pulse = sin(uTime * 4.0) * 0.15 + 1.15;
    }
    
    // 透视缩放
    float depthScale = 350.0 / max(gl_Position.w, 80.0);
    float pointSize = aSize * uPointScale * depthScale * pulse * 1.8;
    
    if (selected > 0.5) {
        pointSize *= 1.4;
    }
    
    gl_PointSize = clamp(pointSize, 30.0, 500.0);
    vColor = aColor;
    vSize = aSize;
    vSelected = selected;
    vPulse = pulse;
}
)";

const char* const NODE_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;

in vec3 vColor;
in vec3 vWorldPos;
in float vSize;
in float vSelected;
in float vPulse;

uniform float uTime;

out vec4 fragColor;

// ============ 噪声函数 ============
float hash3(vec3 p) {
    return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

float vnoise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    
    return mix(
        mix(
            mix(hash3(i), hash3(i + vec3(1,0,0)), f.x),
            mix(hash3(i + vec3(0,1,0)), hash3(i + vec3(1,1,0)), f.x),
            f.y
        ),
        mix(
            mix(hash3(i + vec3(0,0,1)), hash3(i + vec3(1,0,1)), f.x),
            mix(hash3(i + vec3(0,1,1)), hash3(i + vec3(1,1,1)), f.x),
            f.y
        ),
        f.z
    );
}

// 分形布朗运动
float fbm(vec3 p) {
    float v = 0.0;
    float a = 0.55;
    for(int i = 0; i < 4; i++) {
        v += a * vnoise(p);
        p = p * 2.03 + vec3(1.7, 9.2, 3.4);
        a *= 0.48;
    }
    return v;
}

// 扭曲FBM
float wfbm(vec3 p) {
    vec3 q = vec3(
        fbm(p),
        fbm(p + vec3(5.2, 1.3, 2.8)),
        fbm(p + vec3(1.7, 9.2, 3.4))
    );
    return fbm(p + 1.8 * q);
}

// Y轴旋转
vec3 rotY(vec3 p, float a) {
    float c = cos(a);
    float s = sin(a);
    return vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z);
}

void main() {
    // 将点坐标映射到球面
    vec2 coord = (gl_PointCoord - vec2(0.5)) * 2.0;
    float dist = length(coord);
    
    // 球体外部裁剪
    if (dist > 1.0) {
        discard;
    }
    
    // 计算球面法线
    float z = sqrt(1.0 - dist * dist);
    vec3 N = normalize(vec3(coord.x, coord.y, z));
    
    // 光照方向
    vec3 L = normalize(vec3(1.2, 0.9, 0.7));
    vec3 V = vec3(0.0, 0.0, 1.0);
    
    // 旋转的球面坐标（让星球自转）
    vec3 sp = rotY(N, uTime * 0.06);
    
    // 生成地形高度
    float h = smoothstep(0.30, 0.72, wfbm(sp * 2.2));
    
    // 极地冰盖
    float lat = abs(sp.y);
    float iceBase = smoothstep(0.60, 0.82, lat);
    float ice = clamp(iceBase + vnoise(sp * 8.0) * 0.15 * (1.0 - iceBase), 0.0, 1.0);
    
    // ============ 地形分层着色 ============
    vec3 deepSea = vec3(0.04, 0.10, 0.28) * (vColor * 0.6 + vec3(0.4));
    vec3 shallow = vec3(0.08, 0.22, 0.52) * (vColor * 0.5 + vec3(0.5));
    vec3 beach = vec3(0.76, 0.70, 0.50) * (vColor * 0.3 + vec3(0.7));
    vec3 low = vColor * 0.75 + vec3(0.05, 0.08, 0.02);
    vec3 mid = vColor * 0.95 + vec3(0.02, 0.05, 0.01);
    vec3 high = vColor * 1.15 + vec3(0.06, 0.06, 0.06);
    vec3 snow = vec3(0.90, 0.93, 1.00);
    
    vec3 sc;
    if (h < 0.18) {
        sc = mix(deepSea, shallow, smoothstep(0.0, 0.18, h));
    } else if (h < 0.24) {
        sc = mix(shallow, beach, smoothstep(0.18, 0.24, h));
    } else if (h < 0.42) {
        sc = mix(beach, low, smoothstep(0.24, 0.42, h));
    } else if (h < 0.65) {
        sc = mix(low, mid, smoothstep(0.42, 0.65, h));
    } else if (h < 0.82) {
        sc = mix(mid, high, smoothstep(0.65, 0.82, h));
    } else {
        sc = mix(high, snow, smoothstep(0.82, 1.0, h));
    }
    
    // 混合冰盖
    sc = mix(sc, snow, ice * 0.9);
    
    // ============ 光照计算 ============
    float isOcean = 1.0 - smoothstep(0.18, 0.26, h);
    
    // 镜面反射（海洋）
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(N, H), 0.0), 120.0) * 0.9 * isOcean;
    
    // 漫反射
    float diff = max(dot(N, L), 0.0);
    float term = smoothstep(-0.05, 0.18, diff);
    
    // ============ 云层 ============
    vec3 cp = rotY(N, uTime * 0.13 + 1.5);
    float cloud = smoothstep(0.52, 0.72, wfbm(cp * 2.8 + vec3(0.0, 2.0, 0.0)));
    vec3 cloudCol = vec3(0.95, 0.97, 1.0) * (diff * 0.7 + 0.3);
    
    // ============ 城市灯光（夜晚面） ============
    float city = smoothstep(0.70, 0.76, vnoise(sp * 9.0)) * (1.0 - ice) * (1.0 - term);
    
    // 夜晚颜色
    vec3 nightCol = sc * 0.04 + vColor * 1.2 * city * (1.0 - cloud * 0.8);
    
    // 白天颜色
    vec3 dayCol = sc * (diff * 0.85 + 0.12) * (1.0 - cloud * 0.35) + 
                  vec3(0.0, 0.15, 0.4) * isOcean * 0.3;
    dayCol = mix(dayCol, cloudCol, cloud * term);
    
    // 混合昼夜
    vec3 planet = mix(nightCol, dayCol, term) + vec3(spec) * term;
    
    // ============ 大气层边缘光 ============
    float rim = pow(1.0 - max(dot(N, V), 0.0), 3.5);
    vec3 atm = mix(vec3(0.25, 0.55, 1.0), vColor * 0.6, 0.35) * 
               rim * mix(0.15, 0.65, smoothstep(0.0, 0.5, diff));
    planet = mix(planet, atm, rim * 0.55);
    planet += atm * 0.4;
    
    // ============ 选中高亮 ============
    if (vSelected > 0.5) {
        float sp2 = sin(uTime * 2.5) * 0.5 + 0.5;
        planet += vec3(0.3, 1.0, 0.85) * rim * (1.0 + sp2 * 0.6);
    }
    
    fragColor = vec4(planet, 1.0);
}
)";

// ============ 光晕着色器（大气层效果） ============
const char* const GLOW_VERTEX_SHADER = R"(#version 300 es
precision highp float;
precision highp int;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;

uniform mat4 uMVPMatrix;
uniform vec3 uNodePosition;
uniform float uNodeSize;
uniform float uTime;
uniform highp int uIsSelected;

out vec3 vNormal;
out vec3 vPosition;
out float vPulse;

void main() {
    float pulse = sin(uTime * 2.0) * 0.08 + 1.0;
    if (uIsSelected == 1) {
        pulse = sin(uTime * 4.0) * 0.15 + 1.15;
    }
    
    // 光晕比球体稍大
    vec3 scaledPos = aPosition * uNodeSize * pulse * 1.3;
    vec3 worldPos = scaledPos + uNodePosition;
    
    gl_Position = uMVPMatrix * vec4(worldPos, 1.0);
    vNormal = normalize(aNormal);
    vPosition = worldPos;
    vPulse = pulse;
}
)";

const char* const GLOW_FRAGMENT_SHADER = R"(#version 300 es
precision highp float;
precision highp int;

in vec3 vNormal;
in vec3 vPosition;
in float vPulse;

uniform vec3 uNodeColor;
uniform vec3 uCameraPos;
uniform highp int uIsSelected;

out vec4 fragColor;

void main() {
    vec3 viewDir = normalize(uCameraPos - vPosition);
    vec3 normal = normalize(vNormal);
    
    // 边缘发光（大气层效果）
    float rim = 1.0 - max(dot(viewDir, normal), 0.0);
    rim = pow(rim, 2.0);
    
    vec3 glowColor = uNodeColor * 1.8;
    float alpha = rim * 0.4;
    
    if (uIsSelected == 1) {
        alpha *= 1.5 * vPulse;
        glowColor += vec3(0.2);
    }
    
    fragColor = vec4(glowColor, alpha);
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
