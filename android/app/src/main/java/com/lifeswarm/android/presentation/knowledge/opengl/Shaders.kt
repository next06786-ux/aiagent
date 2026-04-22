package com.lifeswarm.android.presentation.knowledge.opengl

/**
 * OpenGL ES 3.0 着色器定义
 * 移植自 HarmonyOS C++ 实现，提供高级视觉效果
 * 
 * 注意：节点着色器已移至 SphereNodeRenderer.kt 中（3D 球体渲染）
 */

// ============ 连线着色器 - 发光射线 ============
const val LINE_VERTEX_SHADER = """#version 300 es
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
"""

const val LINE_FRAGMENT_SHADER = """#version 300 es
precision highp float;

in vec4 vColor;
in float vDepth;
out vec4 fragColor;

void main() {
    float depthFactor = 350.0 / max(vDepth, 80.0);
    vec3 color = vColor.rgb * (1.4 + depthFactor * 0.4);
    float alpha = vColor.a * depthFactor * 1.2;
    fragColor = vec4(color, clamp(alpha, 0.0, 1.0));
}
"""

// ============ 背景星空着色器 - 3D版本 ============
const val STAR_VERTEX_SHADER = """#version 300 es
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
    
    float depthScale = 600.0 / max(gl_Position.w, 50.0);
    gl_PointSize = clamp(aSize * depthScale, 2.0, 25.0);
    
    vBrightness = aBrightness;
    vColor = aColor;
    vDepth = gl_Position.w;
}
"""

const val STAR_FRAGMENT_SHADER = """#version 300 es
precision highp float;

in float vBrightness;
in vec3 vColor;
in float vDepth;
out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    float core = smoothstep(0.15, 0.0, dist);
    float inner = smoothstep(0.3, 0.0, dist) * 0.7;
    float glow = smoothstep(0.5, 0.0, dist) * 0.4;
    
    float depthFactor = clamp(600.0 / vDepth, 0.5, 2.0);
    float alpha = (core + inner + glow) * vBrightness * depthFactor;
    
    vec3 color = mix(vColor * 1.2, vec3(1.0), core * 0.9);
    
    fragColor = vec4(color, alpha);
}
"""

// ============ 流光粒子着色器 ============
const val PARTICLE_VERTEX_SHADER = """#version 300 es
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
    
    float sizeMod = sin(aProgress * 3.14159) * 0.5 + 0.8;
    float flicker = sin(uTime * 10.0 + aProgress * 20.0) * 0.1 + 1.0;
    
    gl_PointSize = uPointSize * sizeMod * flicker / max(gl_Position.w, 1.0);
    vAlpha = aAlpha;
    vColor = aColor;
    vProgress = aProgress;
}
"""

const val PARTICLE_FRAGMENT_SHADER = """#version 300 es
precision highp float;

in float vAlpha;
in vec3 vColor;
in float vProgress;
out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    
    float core = smoothstep(0.2, 0.0, dist);
    float glow = smoothstep(0.5, 0.0, dist) * 0.6;
    float outer = smoothstep(0.7, 0.0, dist) * 0.3;
    
    float alpha = (core + glow + outer) * vAlpha;
    vec3 color = mix(vColor * 1.5, vec3(1.0), core * 0.7);
    
    fragColor = vec4(color, alpha);
}
"""
