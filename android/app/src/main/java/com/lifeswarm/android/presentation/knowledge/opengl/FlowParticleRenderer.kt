package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * 流光粒子渲染器 - OpenGL ES 3.0
 * 移植自 HarmonyOS C++ 实现
 * 
 * 特性：
 * - 沿贝塞尔曲线流动的粒子
 * - 每条连线 3-5 个粒子
 * - 闪烁效果
 * - 颜色插值
 * - 透明度渐变
 */
class FlowParticleRenderer {
    
    private var program: Int = 0
    private var vbo: Int = 0
    
    // Uniform 位置
    private var mvpMatrixLoc: Int = 0
    private var pointSizeLoc: Int = 0
    private var timeLoc: Int = 0
    
    // Attribute 位置
    private var positionLoc: Int = 0
    private var alphaLoc: Int = 0
    private var colorLoc: Int = 0
    private var progressLoc: Int = 0
    
    // 粒子数据
    private data class Particle(
        val linkIdx: Int,
        var progress: Float,
        val speed: Float
    )
    
    private val particles = mutableListOf<Particle>()
    
    init {
        initShaders()
        initBuffers()
    }
    
    private fun initShaders() {
        val vertexShader = loadShader(GLES30.GL_VERTEX_SHADER, PARTICLE_VERTEX_SHADER)
        val fragmentShader = loadShader(GLES30.GL_FRAGMENT_SHADER, PARTICLE_FRAGMENT_SHADER)
        
        program = GLES30.glCreateProgram()
        GLES30.glAttachShader(program, vertexShader)
        GLES30.glAttachShader(program, fragmentShader)
        GLES30.glLinkProgram(program)
        
        // 检查链接状态
        val linkStatus = IntArray(1)
        GLES30.glGetProgramiv(program, GLES30.GL_LINK_STATUS, linkStatus, 0)
        if (linkStatus[0] == 0) {
            val log = GLES30.glGetProgramInfoLog(program)
            GLES30.glDeleteProgram(program)
            throw RuntimeException("Failed to link program: $log")
        }
        
        // 获取位置
        mvpMatrixLoc = GLES30.glGetUniformLocation(program, "uMVPMatrix")
        pointSizeLoc = GLES30.glGetUniformLocation(program, "uPointSize")
        timeLoc = GLES30.glGetUniformLocation(program, "uTime")
        positionLoc = GLES30.glGetAttribLocation(program, "aPosition")
        alphaLoc = GLES30.glGetAttribLocation(program, "aAlpha")
        colorLoc = GLES30.glGetAttribLocation(program, "aColor")
        progressLoc = GLES30.glGetAttribLocation(program, "aProgress")
        
        println("[FlowParticleRenderer] Shader initialized, program=$program")
    }
    
    private fun initBuffers() {
        val buffers = IntArray(1)
        GLES30.glGenBuffers(1, buffers, 0)
        vbo = buffers[0]
    }
    
    /**
     * 初始化粒子
     */
    fun initParticles(edgeCount: Int) {
        particles.clear()
        
        for (i in 0 until edgeCount) {
            // 每条线 3-5 个粒子
            val particleCount = 3 + (i % 3)
            for (j in 0 until particleCount) {
                val progress = j.toFloat() / particleCount + Random.nextFloat() * 0.2f
                val speed = 0.15f + Random.nextFloat() * 0.35f
                particles.add(Particle(i, progress % 1f, speed))
            }
        }
        
        println("[FlowParticleRenderer] Created ${particles.size} particles for $edgeCount links")
    }
    
    /**
     * 更新粒子位置
     */
    fun updateParticles(deltaTime: Float) {
        for (particle in particles) {
            particle.progress += deltaTime * particle.speed
            if (particle.progress > 1f) {
                particle.progress -= 1f
            }
        }
    }
    
    /**
     * 绘制流光粒子
     */
    fun draw(mvpMatrix: FloatArray, edges: List<Edge>, nodes: List<Node>, time: Float) {
        if (particles.isEmpty() || edges.isEmpty() || nodes.isEmpty()) return
        
        // 构建节点映射
        val nodeMap = nodes.associateBy { it.id }
        
        // 准备顶点数据：x, y, z, alpha, r, g, b, progress
        val particleData = mutableListOf<Float>()
        
        for (particle in particles) {
            if (particle.linkIdx < 0 || particle.linkIdx >= edges.size) continue
            
            val edge = edges[particle.linkIdx]
            val srcNode = nodeMap[edge.from] ?: continue
            val tgtNode = nodeMap[edge.to] ?: continue
            
            // 计算贝塞尔曲线控制点
            val midX = (srcNode.x + tgtNode.x) * 0.5f
            val midY = (srcNode.y + tgtNode.y) * 0.5f
            val midZ = (srcNode.z + tgtNode.z) * 0.5f
            
            val dx = tgtNode.x - srcNode.x
            val dy = tgtNode.y - srcNode.y
            val dz = tgtNode.z - srcNode.z
            val len = sqrt(dx * dx + dy * dy + dz * dz)
            
            val bendAmount = len * 0.15f
            
            val ctrlX = midX + dy * bendAmount / (len + 0.1f)
            val ctrlY = midY - dx * bendAmount / (len + 0.1f)
            val ctrlZ = midZ + bendAmount * 0.3f
            
            // 二次贝塞尔曲线计算粒子位置
            val t = particle.progress
            val u = 1f - t
            val x = u * u * srcNode.x + 2 * u * t * ctrlX + t * t * tgtNode.x
            val y = u * u * srcNode.y + 2 * u * t * ctrlY + t * t * tgtNode.y
            val z = u * u * srcNode.z + 2 * u * t * ctrlZ + t * t * tgtNode.z
            
            // 粒子颜色插值
            val r = srcNode.color[0] + (tgtNode.color[0] - srcNode.color[0]) * t
            val g = srcNode.color[1] + (tgtNode.color[1] - srcNode.color[1]) * t
            val b = srcNode.color[2] + (tgtNode.color[2] - srcNode.color[2]) * t
            
            // 粒子在中间最亮，两端渐隐
            val alpha = sin(t * Math.PI.toFloat()) * 0.95f
            
            particleData.add(x)
            particleData.add(y)
            particleData.add(z)
            particleData.add(alpha)
            particleData.add(r)
            particleData.add(g)
            particleData.add(b)
            particleData.add(t)
        }
        
        if (particleData.isEmpty()) return
        
        // 上传数据到 VBO
        val buffer = ByteBuffer.allocateDirect(particleData.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
        particleData.forEach { buffer.put(it) }
        buffer.position(0)
        
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, vbo)
        GLES30.glBufferData(
            GLES30.GL_ARRAY_BUFFER,
            particleData.size * 4,
            buffer,
            GLES30.GL_DYNAMIC_DRAW
        )
        
        // 使用着色器程序
        GLES30.glUseProgram(program)
        
        // 设置 uniform
        GLES30.glUniformMatrix4fv(mvpMatrixLoc, 1, false, mvpMatrix, 0)
        GLES30.glUniform1f(pointSizeLoc, 20f)
        GLES30.glUniform1f(timeLoc, time)
        
        // 设置顶点属性
        GLES30.glEnableVertexAttribArray(positionLoc)
        GLES30.glEnableVertexAttribArray(alphaLoc)
        GLES30.glEnableVertexAttribArray(colorLoc)
        GLES30.glEnableVertexAttribArray(progressLoc)
        
        val stride = 8 * 4 // 8 floats per vertex
        GLES30.glVertexAttribPointer(positionLoc, 3, GLES30.GL_FLOAT, false, stride, 0)
        GLES30.glVertexAttribPointer(alphaLoc, 1, GLES30.GL_FLOAT, false, stride, 3 * 4)
        GLES30.glVertexAttribPointer(colorLoc, 3, GLES30.GL_FLOAT, false, stride, 4 * 4)
        GLES30.glVertexAttribPointer(progressLoc, 1, GLES30.GL_FLOAT, false, stride, 7 * 4)
        
        // 使用加法混合
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE)
        
        GLES30.glDrawArrays(GLES30.GL_POINTS, 0, particles.size)
        
        // 恢复正常混合
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE_MINUS_SRC_ALPHA)
        
        // 禁用顶点属性
        GLES30.glDisableVertexAttribArray(positionLoc)
        GLES30.glDisableVertexAttribArray(alphaLoc)
        GLES30.glDisableVertexAttribArray(colorLoc)
        GLES30.glDisableVertexAttribArray(progressLoc)
    }
    
    private fun loadShader(type: Int, shaderCode: String): Int {
        val shader = GLES30.glCreateShader(type)
        GLES30.glShaderSource(shader, shaderCode)
        GLES30.glCompileShader(shader)
        
        // 检查编译状态
        val compileStatus = IntArray(1)
        GLES30.glGetShaderiv(shader, GLES30.GL_COMPILE_STATUS, compileStatus, 0)
        if (compileStatus[0] == 0) {
            val log = GLES30.glGetShaderInfoLog(shader)
            GLES30.glDeleteShader(shader)
            throw RuntimeException("Failed to compile shader: $log")
        }
        
        return shader
    }
    
    fun cleanup() {
        if (vbo != 0) {
            GLES30.glDeleteBuffers(1, intArrayOf(vbo), 0)
            vbo = 0
        }
        if (program != 0) {
            GLES30.glDeleteProgram(program)
            program = 0
        }
    }
}
