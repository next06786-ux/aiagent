package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt

/**
 * 增强版连线渲染器 - OpenGL ES 3.0
 * 移植自 HarmonyOS C++ 实现
 * 
 * 特性：
 * - 贝塞尔曲线连线（16段）
 * - 颜色渐变
 * - 透明度渐变（两端淡出）
 * - 深度感知亮度
 * - 双层绘制（外层光晕 + 核心细线）
 */
class EnhancedLineRenderer {
    
    private var program: Int = 0
    private var vbo: Int = 0
    private var vertexCount: Int = 0
    
    // Uniform 位置
    private var mvpMatrixLoc: Int = 0
    
    // Attribute 位置
    private var positionLoc: Int = 0
    private var colorLoc: Int = 0
    
    companion object {
        private const val CURVE_SEGMENTS = 16 // 曲线段数
    }
    
    init {
        initShaders()
        initBuffers()
    }
    
    private fun initShaders() {
        val vertexShader = loadShader(GLES30.GL_VERTEX_SHADER, LINE_VERTEX_SHADER)
        val fragmentShader = loadShader(GLES30.GL_FRAGMENT_SHADER, LINE_FRAGMENT_SHADER)
        
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
        colorLoc = GLES30.glGetAttribLocation(program, "aColor")
        
        println("[EnhancedLineRenderer] Shader initialized, program=$program")
    }
    
    private fun initBuffers() {
        val buffers = IntArray(1)
        GLES30.glGenBuffers(1, buffers, 0)
        vbo = buffers[0]
    }
    
    /**
     * 绘制连线
     * @param mvpMatrix MVP 矩阵
     * @param edges 连线列表
     * @param nodes 节点列表（用于获取位置和颜色）
     */
    fun draw(mvpMatrix: FloatArray, edges: List<Edge>, nodes: List<Node>) {
        if (edges.isEmpty() || nodes.isEmpty()) return
        
        // 构建节点映射
        val nodeMap = nodes.associateBy { it.id }
        
        // 准备顶点数据：x, y, z, r, g, b, a
        val lineData = mutableListOf<Float>()
        
        for (edge in edges) {
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
            
            val bendAmount = len * 0.12f
            
            val ctrlX = midX + dy * bendAmount / (len + 0.1f)
            val ctrlY = midY - dx * bendAmount / (len + 0.1f)
            val ctrlZ = midZ + bendAmount * 0.25f
            
            // 源节点和目标节点的颜色（稍微降低饱和度）
            val srcR = srcNode.color[0] * 0.85f + 0.15f
            val srcG = srcNode.color[1] * 0.85f + 0.15f
            val srcB = srcNode.color[2] * 0.85f + 0.15f
            
            val tgtR = tgtNode.color[0] * 0.85f + 0.15f
            val tgtG = tgtNode.color[1] * 0.85f + 0.15f
            val tgtB = tgtNode.color[2] * 0.85f + 0.15f
            
            // 生成曲线上的点
            for (i in 0 until CURVE_SEGMENTS) {
                val t1 = i.toFloat() / CURVE_SEGMENTS
                val t2 = (i + 1).toFloat() / CURVE_SEGMENTS
                
                // 二次贝塞尔曲线
                val u1 = 1f - t1
                val u2 = 1f - t2
                
                val x1 = u1 * u1 * srcNode.x + 2 * u1 * t1 * ctrlX + t1 * t1 * tgtNode.x
                val y1 = u1 * u1 * srcNode.y + 2 * u1 * t1 * ctrlY + t1 * t1 * tgtNode.y
                val z1 = u1 * u1 * srcNode.z + 2 * u1 * t1 * ctrlZ + t1 * t1 * tgtNode.z
                
                val x2 = u2 * u2 * srcNode.x + 2 * u2 * t2 * ctrlX + t2 * t2 * tgtNode.x
                val y2 = u2 * u2 * srcNode.y + 2 * u2 * t2 * ctrlY + t2 * t2 * tgtNode.y
                val z2 = u2 * u2 * srcNode.z + 2 * u2 * t2 * ctrlZ + t2 * t2 * tgtNode.z
                
                // 颜色渐变
                val cr1 = srcR + (tgtR - srcR) * t1
                val cg1 = srcG + (tgtG - srcG) * t1
                val cb1 = srcB + (tgtB - srcB) * t1
                
                val cr2 = srcR + (tgtR - srcR) * t2
                val cg2 = srcG + (tgtG - srcG) * t2
                val cb2 = srcB + (tgtB - srcB) * t2
                
                // 透明度：两端淡出，中间柔和
                val fadeIn1 = smoothstep(0f, 0.15f, t1)
                val fadeOut1 = smoothstep(1f, 0.85f, t1)
                val alpha1 = 0.25f * edge.color[3] * fadeIn1 * fadeOut1
                
                val fadeIn2 = smoothstep(0f, 0.15f, t2)
                val fadeOut2 = smoothstep(1f, 0.85f, t2)
                val alpha2 = 0.25f * edge.color[3] * fadeIn2 * fadeOut2
                
                // 点1
                lineData.add(x1)
                lineData.add(y1)
                lineData.add(z1)
                lineData.add(cr1)
                lineData.add(cg1)
                lineData.add(cb1)
                lineData.add(alpha1)
                
                // 点2
                lineData.add(x2)
                lineData.add(y2)
                lineData.add(z2)
                lineData.add(cr2)
                lineData.add(cg2)
                lineData.add(cb2)
                lineData.add(alpha2)
            }
        }
        
        if (lineData.isEmpty()) return
        
        vertexCount = lineData.size / 7
        
        // 上传数据到 VBO
        val buffer = ByteBuffer.allocateDirect(lineData.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
        lineData.forEach { buffer.put(it) }
        buffer.position(0)
        
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, vbo)
        GLES30.glBufferData(
            GLES30.GL_ARRAY_BUFFER,
            lineData.size * 4,
            buffer,
            GLES30.GL_DYNAMIC_DRAW
        )
        
        // 使用着色器程序
        GLES30.glUseProgram(program)
        
        // 设置 uniform
        GLES30.glUniformMatrix4fv(mvpMatrixLoc, 1, false, mvpMatrix, 0)
        
        // 设置顶点属性
        GLES30.glEnableVertexAttribArray(positionLoc)
        GLES30.glEnableVertexAttribArray(colorLoc)
        
        val stride = 7 * 4 // 7 floats per vertex
        GLES30.glVertexAttribPointer(positionLoc, 3, GLES30.GL_FLOAT, false, stride, 0)
        GLES30.glVertexAttribPointer(colorLoc, 4, GLES30.GL_FLOAT, false, stride, 3 * 4)
        
        // 使用加法混合实现柔和发光效果
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE)
        
        // 画两层：外层柔和光晕 + 核心细线
        GLES30.glLineWidth(2.0f)
        GLES30.glDrawArrays(GLES30.GL_LINES, 0, vertexCount)
        
        GLES30.glLineWidth(1.0f)
        GLES30.glDrawArrays(GLES30.GL_LINES, 0, vertexCount)
        
        // 恢复正常混合
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE_MINUS_SRC_ALPHA)
        
        // 禁用顶点属性
        GLES30.glDisableVertexAttribArray(positionLoc)
        GLES30.glDisableVertexAttribArray(colorLoc)
    }
    
    /**
     * 平滑插值函数
     */
    private fun smoothstep(edge0: Float, edge1: Float, x: Float): Float {
        val t = ((x - edge0) / (edge1 - edge0)).coerceIn(0f, 1f)
        return t * t * (3f - 2f * t)
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
