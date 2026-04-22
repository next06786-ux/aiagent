package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.acos
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * 背景星空渲染器 - OpenGL ES 3.0
 * 移植自 HarmonyOS C++ 实现
 * 
 * 特性：
 * - 3D 球形分布的星星（800+颗）
 * - 4个层次（远景、中景、近景、最近）
 * - 闪烁动画
 * - 透视缩放
 * - 多种颜色
 */
class BackgroundStarRenderer {
    
    private var program: Int = 0
    private var vbo: Int = 0
    
    // Uniform 位置
    private var mvpMatrixLoc: Int = 0
    
    // Attribute 位置
    private var positionLoc: Int = 0
    private var sizeLoc: Int = 0
    private var brightnessLoc: Int = 0
    private var colorLoc: Int = 0
    
    // 星星数据
    private data class Star(
        val x: Float,
        val y: Float,
        val z: Float,
        val size: Float,
        val brightness: Float,
        val r: Float,
        val g: Float,
        val b: Float,
        val twinklePhase: Float,
        val twinkleSpeed: Float
    )
    
    private val stars = mutableListOf<Star>()
    
    companion object {
        private const val STAR_FIELD_RADIUS = 600f
    }
    
    init {
        initShaders()
        initBuffers()
        initStars()
    }
    
    private fun initShaders() {
        val vertexShader = loadShader(GLES30.GL_VERTEX_SHADER, STAR_VERTEX_SHADER)
        val fragmentShader = loadShader(GLES30.GL_FRAGMENT_SHADER, STAR_FRAGMENT_SHADER)
        
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
        positionLoc = GLES30.glGetAttribLocation(program, "aPosition")
        sizeLoc = GLES30.glGetAttribLocation(program, "aSize")
        brightnessLoc = GLES30.glGetAttribLocation(program, "aBrightness")
        colorLoc = GLES30.glGetAttribLocation(program, "aColor")
        
        println("[BackgroundStarRenderer] Shader initialized, program=$program")
    }
    
    private fun initBuffers() {
        val buffers = IntArray(1)
        GLES30.glGenBuffers(1, buffers, 0)
        vbo = buffers[0]
    }
    
    /**
     * 初始化星星 - 3D 球形分布
     */
    private fun initStars() {
        stars.clear()
        
        // 远景层（400颗）- 较小但可见
        repeat(400) {
            val theta = Random.nextFloat() * 2f * Math.PI.toFloat()
            val phi = acos(2f * Random.nextFloat() - 1f)
            val r = STAR_FIELD_RADIUS * (0.8f + Random.nextFloat() * 0.2f)
            
            val x = r * sin(phi) * cos(theta)
            val y = r * sin(phi) * sin(theta)
            val z = r * cos(phi)
            
            val size = 3f + Random.nextFloat() * 3f
            val brightness = 0.15f + Random.nextFloat() * 0.2f  // 降低亮度：0.4-0.8 → 0.15-0.35
            val twinklePhase = Random.nextFloat() * 2f * Math.PI.toFloat()
            val twinkleSpeed = (0.5f + Random.nextFloat() * 2f) * 0.5f
            
            // 淡蓝白色
            val starR = 0.85f + Random.nextFloat() * 0.15f
            val starG = 0.9f + Random.nextFloat() * 0.1f
            val starB = 1f
            
            stars.add(Star(x, y, z, size, brightness, starR, starG, starB, twinklePhase, twinkleSpeed))
        }
        
        // 中景层（250颗）- 中等大小
        repeat(250) {
            val theta = Random.nextFloat() * 2f * Math.PI.toFloat()
            val phi = acos(2f * Random.nextFloat() - 1f)
            val r = STAR_FIELD_RADIUS * (0.5f + Random.nextFloat() * 0.3f)
            
            val x = r * sin(phi) * cos(theta)
            val y = r * sin(phi) * sin(theta)
            val z = r * cos(phi)
            
            val size = 5f + Random.nextFloat() * 5f
            val brightness = 0.2f + Random.nextFloat() * 0.25f  // 降低亮度：0.5-1.0 → 0.2-0.45
            val twinklePhase = Random.nextFloat() * 2f * Math.PI.toFloat()
            val twinkleSpeed = 0.5f + Random.nextFloat() * 2f
            
            // 随机颜色
            val colorType = Random.nextFloat()
            val (starR, starG, starB) = when {
                colorType < 0.5f -> Triple(1f, 1f, 1f)  // 白
                colorType < 0.75f -> Triple(0.75f, 0.88f, 1f)  // 淡蓝
                else -> Triple(1f, 0.95f, 0.85f)  // 淡黄
            }
            
            stars.add(Star(x, y, z, size, brightness, starR, starG, starB, twinklePhase, twinkleSpeed))
        }
        
        // 近景层（120颗）- 大而亮
        repeat(120) {
            val theta = Random.nextFloat() * 2f * Math.PI.toFloat()
            val phi = acos(2f * Random.nextFloat() - 1f)
            val r = STAR_FIELD_RADIUS * (0.3f + Random.nextFloat() * 0.2f)
            
            val x = r * sin(phi) * cos(theta)
            val y = r * sin(phi) * sin(theta)
            val z = r * cos(phi)
            
            val size = 8f + Random.nextFloat() * 8f
            val brightness = 0.3f + Random.nextFloat() * 0.25f  // 降低亮度：0.7-1.0 → 0.3-0.55
            val twinklePhase = Random.nextFloat() * 2f * Math.PI.toFloat()
            val twinkleSpeed = (0.5f + Random.nextFloat() * 2f) * 1.5f
            
            // 更鲜艳的颜色
            val colorType = Random.nextFloat()
            val (starR, starG, starB) = when {
                colorType < 0.3f -> Triple(1f, 1f, 1f)  // 亮白
                colorType < 0.5f -> Triple(0.6f, 0.8f, 1f)  // 蓝色
                colorType < 0.7f -> Triple(1f, 0.9f, 0.6f)  // 金黄
                colorType < 0.85f -> Triple(0.95f, 0.75f, 1f)  // 淡紫
                else -> Triple(1f, 0.7f, 0.6f)  // 橙红
            }
            
            stars.add(Star(x, y, z, size, brightness, starR, starG, starB, twinklePhase, twinkleSpeed))
        }
        
        // 最近层（50颗）- 非常亮
        repeat(50) {
            val theta = Random.nextFloat() * 2f * Math.PI.toFloat()
            val phi = acos(2f * Random.nextFloat() - 1f)
            val r = STAR_FIELD_RADIUS * (0.15f + Random.nextFloat() * 0.15f)
            
            val x = r * sin(phi) * cos(theta)
            val y = r * sin(phi) * sin(theta)
            val z = r * cos(phi)
            
            val size = 12f + Random.nextFloat() * 10f
            val brightness = 0.4f + Random.nextFloat() * 0.2f  // 降低亮度：0.85-1.0 → 0.4-0.6
            val twinklePhase = Random.nextFloat() * 2f * Math.PI.toFloat()
            val twinkleSpeed = (0.5f + Random.nextFloat() * 2f) * 2f
            
            // 明亮的颜色
            val colorType = Random.nextFloat()
            val (starR, starG, starB) = when {
                colorType < 0.4f -> Triple(1f, 1f, 1f)
                colorType < 0.7f -> Triple(0.55f, 0.75f, 1f)
                else -> Triple(1f, 0.88f, 0.55f)
            }
            
            stars.add(Star(x, y, z, size, brightness, starR, starG, starB, twinklePhase, twinkleSpeed))
        }
        
        println("[BackgroundStarRenderer] Created ${stars.size} stars")
    }
    
    /**
     * 绘制背景星空
     * @param mvpMatrix MVP 矩阵
     * @param time 当前时间（秒）
     */
    fun draw(mvpMatrix: FloatArray, time: Float) {
        if (stars.isEmpty()) return
        
        // 准备顶点数据：x, y, z, size, brightness, r, g, b
        val starData = FloatArray(stars.size * 8)
        var offset = 0
        
        for (star in stars) {
            // 闪烁效果
            val twinkle = sin(star.twinklePhase + time * star.twinkleSpeed) * 0.25f + 0.75f
            val randomFlicker = sin((star.twinklePhase + time * star.twinkleSpeed) * 3.7f) * 0.1f + 1f
            
            starData[offset++] = star.x
            starData[offset++] = star.y
            starData[offset++] = star.z
            starData[offset++] = star.size * randomFlicker
            starData[offset++] = star.brightness * twinkle
            starData[offset++] = star.r
            starData[offset++] = star.g
            starData[offset++] = star.b
        }
        
        // 上传数据到 VBO
        val buffer = ByteBuffer.allocateDirect(starData.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(starData)
        buffer.position(0)
        
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, vbo)
        GLES30.glBufferData(
            GLES30.GL_ARRAY_BUFFER,
            starData.size * 4,
            buffer,
            GLES30.GL_DYNAMIC_DRAW
        )
        
        // 使用着色器程序
        GLES30.glUseProgram(program)
        
        // 设置 uniform
        GLES30.glUniformMatrix4fv(mvpMatrixLoc, 1, false, mvpMatrix, 0)
        
        // 设置顶点属性
        GLES30.glEnableVertexAttribArray(positionLoc)
        GLES30.glEnableVertexAttribArray(sizeLoc)
        GLES30.glEnableVertexAttribArray(brightnessLoc)
        GLES30.glEnableVertexAttribArray(colorLoc)
        
        val stride = 8 * 4 // 8 floats per vertex
        GLES30.glVertexAttribPointer(positionLoc, 3, GLES30.GL_FLOAT, false, stride, 0)
        GLES30.glVertexAttribPointer(sizeLoc, 1, GLES30.GL_FLOAT, false, stride, 3 * 4)
        GLES30.glVertexAttribPointer(brightnessLoc, 1, GLES30.GL_FLOAT, false, stride, 4 * 4)
        GLES30.glVertexAttribPointer(colorLoc, 3, GLES30.GL_FLOAT, false, stride, 5 * 4)
        
        // 使用加法混合让星星更亮
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE)
        
        // 画两遍增强亮度
        GLES30.glDrawArrays(GLES30.GL_POINTS, 0, stars.size)
        GLES30.glDrawArrays(GLES30.GL_POINTS, 0, stars.size)
        
        // 恢复正常混合
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE_MINUS_SRC_ALPHA)
        
        // 禁用顶点属性
        GLES30.glDisableVertexAttribArray(positionLoc)
        GLES30.glDisableVertexAttribArray(sizeLoc)
        GLES30.glDisableVertexAttribArray(brightnessLoc)
        GLES30.glDisableVertexAttribArray(colorLoc)
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
