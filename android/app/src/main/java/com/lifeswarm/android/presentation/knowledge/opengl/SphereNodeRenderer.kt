package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES30
import android.opengl.Matrix
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.ShortBuffer
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/**
 * 3D 球体节点渲染器 - 星球效果
 * 
 * 特性：
 * - 真实的 3D 球体几何体
 * - 基于物理的渲染（PBR-like）
 * - 大气层光晕效果
 * - 表面纹理和光照
 * - 脉冲呼吸动画
 * - 选中高亮效果
 */
class SphereNodeRenderer {
    
    private var sphereProgram: Int = 0
    private var glowProgram: Int = 0
    
    // VBO 和 IBO
    private var sphereVbo: Int = 0
    private var sphereIbo: Int = 0
    private var indexCount: Int = 0
    
    // 球体几何数据
    private var vertexBuffer: FloatBuffer? = null
    private var indexBuffer: ShortBuffer? = null
    
    // 球体细分参数
    private val latitudeBands = 16  // 纬度分段
    private val longitudeBands = 16 // 经度分段
    
    init {
        try {
            initShaders()
            initSphereGeometry()
        } catch (e: Exception) {
            println("[SphereNodeRenderer] ❌❌❌ 初始化失败 ❌❌❌")
            println("[SphereNodeRenderer] 错误: ${e.message}")
            e.printStackTrace()
            // 不抛出异常，让应用继续运行（只是不显示球体）
        }
    }
    
    private fun initShaders() {
        println("[SphereNodeRenderer] ========== 开始初始化着色器 ==========")
        
        // 球体着色器
        val sphereVertexShader = """#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uMVPMatrix;
uniform mat4 uModelMatrix;
uniform mat4 uNormalMatrix;
uniform vec3 uNodePosition;
uniform float uNodeSize;
uniform float uTime;
uniform highp int uIsSelected;  // 添加精度修饰符

out vec3 vNormal;
out vec3 vViewDir;
out vec3 vWorldPos;
out vec3 vPosition;
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
    vNormal = normalize(mat3(uNormalMatrix) * aNormal);
    vWorldPos = worldPos;
    vPosition = worldPos;
    
    // 计算视图方向（简化版，假设相机在远处）
    vec4 mv = uMVPMatrix * vec4(worldPos, 1.0);
    vViewDir = normalize(-mv.xyz);
    
    vTexCoord = aTexCoord;
    vPulse = pulse;
}
"""
        
        println("[SphereNodeRenderer] 球体顶点着色器长度: ${sphereVertexShader.length}")
        
        val sphereFragmentShader = """#version 300 es
precision highp float;

in vec3 vNormal;
in vec3 vViewDir;
in vec3 vWorldPos;
in vec3 vPosition;
in vec2 vTexCoord;
in float vPulse;

uniform vec3 uNodeColor;
uniform vec3 uLightDir;
uniform vec3 uCameraPos;
uniform highp int uIsSelected;  // 添加精度修饰符
uniform float uTime;

out vec4 fragColor;

// ============ 噪声函数（生成星球表面） ============
float hash1(float n) {
    return fract(sin(n) * 43758.5453123);
}

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
    float term = smoothstep(-0.05, 0.18, diff);  // 昼夜分界线
    
    // ============ 云层 ============
    vec3 cp = rotY(normalize(vWorldPos), uTime * 0.13 + 1.5);
    float cloud = smoothstep(0.52, 0.72, wfbm(cp * 2.8 + vec3(0.0, 2.0, 0.0)));
    vec3 cloudCol = vec3(0.95, 0.97, 1.0) * (diff * 0.7 + 0.3);
    
    // ============ 城市灯光（夜晚面） ============
    float city = smoothstep(0.70, 0.76, vnoise(sp * 9.0)) * (1.0 - ice) * (1.0 - term);
    
    // 夜晚颜色（城市灯光）
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
    float sp2 = sin(uTime * 2.5) * 0.5 + 0.5;
    planet += vec3(0.3, 1.0, 0.85) * float(uIsSelected) * rim * (1.0 + sp2 * 0.6);
    
    fragColor = vec4(planet, 1.0);
}
"""
        
        println("[SphereNodeRenderer] 球体片段着色器长度: ${sphereFragmentShader.length}")
        println("[SphereNodeRenderer] 开始创建球体着色器程序...")
        
        sphereProgram = createProgram(sphereVertexShader, sphereFragmentShader)
        println("[SphereNodeRenderer] 球体着色器程序ID: $sphereProgram")
        
        // 光晕着色器（外层大气效果）
        val glowVertexShader = """#version 300 es
precision highp float;

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;

uniform mat4 uMVPMatrix;
uniform vec3 uNodePosition;
uniform float uNodeSize;
uniform float uTime;
uniform highp int uIsSelected;  // 添加精度修饰符

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
"""
        
        println("[SphereNodeRenderer] 光晕顶点着色器长度: ${glowVertexShader.length}")
        
        val glowFragmentShader = """#version 300 es
precision highp float;

in vec3 vNormal;
in vec3 vPosition;
in float vPulse;

uniform vec3 uNodeColor;
uniform vec3 uCameraPos;
uniform highp int uIsSelected;  // 添加精度修饰符

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
"""
        
        println("[SphereNodeRenderer] 光晕片段着色器长度: ${glowFragmentShader.length}")
        println("[SphereNodeRenderer] 开始创建光晕着色器程序...")
        
        glowProgram = createProgram(glowVertexShader, glowFragmentShader)
        println("[SphereNodeRenderer] 光晕着色器程序ID: $glowProgram")
        
        if (sphereProgram == 0 || glowProgram == 0) {
            println("[SphereNodeRenderer] ❌ 着色器程序创建失败!")
            println("[SphereNodeRenderer]    sphereProgram = $sphereProgram")
            println("[SphereNodeRenderer]    glowProgram = $glowProgram")
            throw RuntimeException("Failed to create sphere shader programs")
        }
        
        println("[SphereNodeRenderer] ✅ 着色器初始化成功")
        println("[SphereNodeRenderer] ========================================")
    }
    
    /**
     * 生成球体几何数据
     */
    private fun initSphereGeometry() {
        val vertices = mutableListOf<Float>()
        val indices = mutableListOf<Short>()
        
        // 生成顶点
        for (lat in 0..latitudeBands) {
            val theta = lat * PI / latitudeBands
            val sinTheta = sin(theta).toFloat()
            val cosTheta = cos(theta).toFloat()
            
            for (lon in 0..longitudeBands) {
                val phi = lon * 2 * PI / longitudeBands
                val sinPhi = sin(phi).toFloat()
                val cosPhi = cos(phi).toFloat()
                
                // 位置（单位球）
                val x = cosPhi * sinTheta
                val y = cosTheta
                val z = sinPhi * sinTheta
                
                // 法线（与位置相同，因为是单位球）
                val nx = x
                val ny = y
                val nz = z
                
                // 纹理坐标
                val u = 1f - (lon.toFloat() / longitudeBands)
                val v = 1f - (lat.toFloat() / latitudeBands)
                
                vertices.add(x)
                vertices.add(y)
                vertices.add(z)
                vertices.add(nx)
                vertices.add(ny)
                vertices.add(nz)
                vertices.add(u)
                vertices.add(v)
            }
        }
        
        // 生成索引
        for (lat in 0 until latitudeBands) {
            for (lon in 0 until longitudeBands) {
                val first = (lat * (longitudeBands + 1) + lon).toShort()
                val second = (first + longitudeBands + 1).toShort()
                
                indices.add(first)
                indices.add(second)
                indices.add((first + 1).toShort())
                
                indices.add(second)
                indices.add((second + 1).toShort())
                indices.add((first + 1).toShort())
            }
        }
        
        indexCount = indices.size
        
        // 创建缓冲区
        vertexBuffer = ByteBuffer.allocateDirect(vertices.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(vertices.toFloatArray())
        vertexBuffer!!.position(0)
        
        indexBuffer = ByteBuffer.allocateDirect(indices.size * 2)
            .order(ByteOrder.nativeOrder())
            .asShortBuffer()
            .put(indices.toShortArray())
        indexBuffer!!.position(0)
        
        // 创建 VBO 和 IBO
        val buffers = IntArray(2)
        GLES30.glGenBuffers(2, buffers, 0)
        sphereVbo = buffers[0]
        sphereIbo = buffers[1]
        
        // 上传顶点数据
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, sphereVbo)
        GLES30.glBufferData(
            GLES30.GL_ARRAY_BUFFER,
            vertices.size * 4,
            vertexBuffer,
            GLES30.GL_STATIC_DRAW
        )
        
        // 上传索引数据
        GLES30.glBindBuffer(GLES30.GL_ELEMENT_ARRAY_BUFFER, sphereIbo)
        GLES30.glBufferData(
            GLES30.GL_ELEMENT_ARRAY_BUFFER,
            indices.size * 2,
            indexBuffer,
            GLES30.GL_STATIC_DRAW
        )
        
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, 0)
        GLES30.glBindBuffer(GLES30.GL_ELEMENT_ARRAY_BUFFER, 0)
        
        println("[SphereNodeRenderer] Sphere geometry created: ${vertices.size / 8} vertices, ${indices.size / 3} triangles")
    }
    
    /**
     * 绘制所有节点
     */
    fun draw(mvpMatrix: FloatArray, viewMatrix: FloatArray, nodes: List<Node>, time: Float, selectedIdx: Int, cameraPos: FloatArray) {
        if (nodes.isEmpty()) return
        
        // 检查着色器程序是否有效
        if (sphereProgram == 0 || glowProgram == 0) {
            println("[SphereNodeRenderer] ❌ 着色器程序无效，跳过绘制")
            return
        }
        
        // 光源方向（从右上方照射）
        val lightDir = floatArrayOf(0.5f, 0.8f, 0.3f)
        
        // 计算最大连接数
        val maxConnections = nodes.maxOfOrNull { it.connections } ?: 1
        
        // 绑定球体几何
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, sphereVbo)
        GLES30.glBindBuffer(GLES30.GL_ELEMENT_ARRAY_BUFFER, sphereIbo)
        
        // 为每个节点绘制球体
        nodes.forEachIndexed { index, node ->
            val isSelected = if (index == selectedIdx) 1 else 0
            
            // 计算节点大小
            val connectionRatio = node.connections.toFloat() / maxConnections.toFloat()
            var nodeSize = 3f + connectionRatio * 8f
            if (node.connections == maxConnections) {
                nodeSize *= 1.4f
            }
            
            // 1. 绘制球体本体
            drawSphere(mvpMatrix, viewMatrix, node, nodeSize, time, isSelected, lightDir, cameraPos)
            
            // 2. 绘制光晕（大气层）
            drawGlow(mvpMatrix, node, nodeSize, time, isSelected, cameraPos)
        }
        
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, 0)
        GLES30.glBindBuffer(GLES30.GL_ELEMENT_ARRAY_BUFFER, 0)
    }
    
    /**
     * 绘制单个球体
     */
    private fun drawSphere(
        mvpMatrix: FloatArray,
        viewMatrix: FloatArray,
        node: Node,
        size: Float,
        time: Float,
        isSelected: Int,
        lightDir: FloatArray,
        cameraPos: FloatArray
    ) {
        GLES30.glUseProgram(sphereProgram)
        
        // 模型矩阵（单位矩阵，因为位置在着色器中处理）
        val modelMatrix = FloatArray(16)
        Matrix.setIdentityM(modelMatrix, 0)
        
        // 法线矩阵（用于变换法线）
        val normalMatrix = FloatArray(16)
        Matrix.setIdentityM(normalMatrix, 0)
        
        // 设置 uniforms
        val mvpLoc = GLES30.glGetUniformLocation(sphereProgram, "uMVPMatrix")
        val modelLoc = GLES30.glGetUniformLocation(sphereProgram, "uModelMatrix")
        val normalLoc = GLES30.glGetUniformLocation(sphereProgram, "uNormalMatrix")
        val posLoc = GLES30.glGetUniformLocation(sphereProgram, "uNodePosition")
        val sizeLoc = GLES30.glGetUniformLocation(sphereProgram, "uNodeSize")
        val colorLoc = GLES30.glGetUniformLocation(sphereProgram, "uNodeColor")
        val timeLoc = GLES30.glGetUniformLocation(sphereProgram, "uTime")
        val selectedLoc = GLES30.glGetUniformLocation(sphereProgram, "uIsSelected")
        val lightLoc = GLES30.glGetUniformLocation(sphereProgram, "uLightDir")
        val cameraLoc = GLES30.glGetUniformLocation(sphereProgram, "uCameraPos")
        
        GLES30.glUniformMatrix4fv(mvpLoc, 1, false, mvpMatrix, 0)
        GLES30.glUniformMatrix4fv(modelLoc, 1, false, modelMatrix, 0)
        GLES30.glUniformMatrix4fv(normalLoc, 1, false, normalMatrix, 0)
        GLES30.glUniform3f(posLoc, node.x, node.y, node.z)
        GLES30.glUniform1f(sizeLoc, size)
        GLES30.glUniform3f(colorLoc, node.color[0], node.color[1], node.color[2])
        GLES30.glUniform1f(timeLoc, time)
        GLES30.glUniform1i(selectedLoc, isSelected)
        GLES30.glUniform3fv(lightLoc, 1, lightDir, 0)
        GLES30.glUniform3fv(cameraLoc, 1, cameraPos, 0)
        
        // 设置顶点属性
        val stride = 8 * 4 // 8 floats per vertex
        GLES30.glEnableVertexAttribArray(0)
        GLES30.glEnableVertexAttribArray(1)
        GLES30.glEnableVertexAttribArray(2)
        
        GLES30.glVertexAttribPointer(0, 3, GLES30.GL_FLOAT, false, stride, 0)
        GLES30.glVertexAttribPointer(1, 3, GLES30.GL_FLOAT, false, stride, 3 * 4)
        GLES30.glVertexAttribPointer(2, 2, GLES30.GL_FLOAT, false, stride, 6 * 4)
        
        // 绘制
        GLES30.glDrawElements(GLES30.GL_TRIANGLES, indexCount, GLES30.GL_UNSIGNED_SHORT, 0)
        
        GLES30.glDisableVertexAttribArray(0)
        GLES30.glDisableVertexAttribArray(1)
        GLES30.glDisableVertexAttribArray(2)
    }
    
    /**
     * 绘制光晕（大气层效果）
     */
    private fun drawGlow(
        mvpMatrix: FloatArray,
        node: Node,
        size: Float,
        time: Float,
        isSelected: Int,
        cameraPos: FloatArray
    ) {
        GLES30.glUseProgram(glowProgram)
        
        // 设置 uniforms
        val mvpLoc = GLES30.glGetUniformLocation(glowProgram, "uMVPMatrix")
        val posLoc = GLES30.glGetUniformLocation(glowProgram, "uNodePosition")
        val sizeLoc = GLES30.glGetUniformLocation(glowProgram, "uNodeSize")
        val colorLoc = GLES30.glGetUniformLocation(glowProgram, "uNodeColor")
        val timeLoc = GLES30.glGetUniformLocation(glowProgram, "uTime")
        val selectedLoc = GLES30.glGetUniformLocation(glowProgram, "uIsSelected")
        val cameraLoc = GLES30.glGetUniformLocation(glowProgram, "uCameraPos")
        
        GLES30.glUniformMatrix4fv(mvpLoc, 1, false, mvpMatrix, 0)
        GLES30.glUniform3f(posLoc, node.x, node.y, node.z)
        GLES30.glUniform1f(sizeLoc, size)
        GLES30.glUniform3f(colorLoc, node.color[0], node.color[1], node.color[2])
        GLES30.glUniform1f(timeLoc, time)
        GLES30.glUniform1i(selectedLoc, isSelected)
        GLES30.glUniform3fv(cameraLoc, 1, cameraPos, 0)
        
        // 设置顶点属性（只需要位置和法线）
        val stride = 8 * 4
        GLES30.glEnableVertexAttribArray(0)
        GLES30.glEnableVertexAttribArray(1)
        
        GLES30.glVertexAttribPointer(0, 3, GLES30.GL_FLOAT, false, stride, 0)
        GLES30.glVertexAttribPointer(1, 3, GLES30.GL_FLOAT, false, stride, 3 * 4)
        
        // 启用加法混合绘制光晕
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE)
        
        // 绘制
        GLES30.glDrawElements(GLES30.GL_TRIANGLES, indexCount, GLES30.GL_UNSIGNED_SHORT, 0)
        
        // 恢复正常混合
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE_MINUS_SRC_ALPHA)
        
        GLES30.glDisableVertexAttribArray(0)
        GLES30.glDisableVertexAttribArray(1)
    }
    
    private fun createProgram(vertexShaderCode: String, fragmentShaderCode: String): Int {
        val vertexShader = loadShader(GLES30.GL_VERTEX_SHADER, vertexShaderCode)
        val fragmentShader = loadShader(GLES30.GL_FRAGMENT_SHADER, fragmentShaderCode)
        
        if (vertexShader == 0 || fragmentShader == 0) {
            return 0
        }
        
        val program = GLES30.glCreateProgram()
        GLES30.glAttachShader(program, vertexShader)
        GLES30.glAttachShader(program, fragmentShader)
        GLES30.glLinkProgram(program)
        
        val linkStatus = IntArray(1)
        GLES30.glGetProgramiv(program, GLES30.GL_LINK_STATUS, linkStatus, 0)
        if (linkStatus[0] == 0) {
            val error = GLES30.glGetProgramInfoLog(program)
            GLES30.glDeleteProgram(program)
            throw RuntimeException("Failed to link program: $error")
        }
        
        GLES30.glDeleteShader(vertexShader)
        GLES30.glDeleteShader(fragmentShader)
        
        return program
    }
    
    private fun loadShader(type: Int, shaderCode: String): Int {
        val typeName = if (type == GLES30.GL_VERTEX_SHADER) "顶点" else "片段"
        println("[SphereNodeRenderer] 编译${typeName}着色器...")
        
        val shader = GLES30.glCreateShader(type)
        if (shader == 0) {
            println("[SphereNodeRenderer] ❌ 创建着色器对象失败")
            return 0
        }
        
        GLES30.glShaderSource(shader, shaderCode)
        GLES30.glCompileShader(shader)
        
        val compileStatus = IntArray(1)
        GLES30.glGetShaderiv(shader, GLES30.GL_COMPILE_STATUS, compileStatus, 0)
        if (compileStatus[0] == 0) {
            val error = GLES30.glGetShaderInfoLog(shader)
            println("[SphereNodeRenderer] ❌ ${typeName}着色器编译失败:")
            println("[SphereNodeRenderer]    $error")
            GLES30.glDeleteShader(shader)
            throw RuntimeException("Failed to compile shader: $error")
        }
        
        println("[SphereNodeRenderer] ✅ ${typeName}着色器编译成功 (ID: $shader)")
        return shader
    }
    
    fun cleanup() {
        if (sphereVbo != 0 || sphereIbo != 0) {
            GLES30.glDeleteBuffers(2, intArrayOf(sphereVbo, sphereIbo), 0)
            sphereVbo = 0
            sphereIbo = 0
        }
        
        if (sphereProgram != 0) {
            GLES30.glDeleteProgram(sphereProgram)
            sphereProgram = 0
        }
        
        if (glowProgram != 0) {
            GLES30.glDeleteProgram(glowProgram)
            glowProgram = 0
        }
        
        vertexBuffer = null
        indexBuffer = null
        
        println("[SphereNodeRenderer] Cleaned up")
    }
}
