package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES30
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer

/**
 * 文字标签渲染器
 * 绘制从节点延伸出的标签连接线和锚点
 * 
 * 特性：
 * - 只为连接数较多的节点绘制标签线
 * - 标签线长度基于节点重要性
 * - 锚点大小基于节点重要性
 * - 颜色与节点颜色一致
 */
class TextLabelRenderer {
    
    // 着色器程序
    private var lineProgram = 0
    private var pointProgram = 0
    
    // VBO
    private var vbo = 0
    
    // 顶点缓冲
    private var lineBuffer: FloatBuffer? = null
    private var anchorBuffer: FloatBuffer? = null
    
    init {
        initShaders()
        initBuffers()
    }
    
    private fun initShaders() {
        // 线条着色器（复用 EnhancedLineRenderer 的简单着色器）
        val lineVertexShader = """
            #version 300 es
            layout(location = 0) in vec3 aPosition;
            layout(location = 1) in vec4 aColor;
            
            uniform mat4 uMVPMatrix;
            
            out vec4 vColor;
            
            void main() {
                gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
                vColor = aColor;
            }
        """.trimIndent()
        
        val lineFragmentShader = """
            #version 300 es
            precision mediump float;
            
            in vec4 vColor;
            out vec4 fragColor;
            
            void main() {
                fragColor = vColor;
            }
        """.trimIndent()
        
        lineProgram = createProgram(lineVertexShader, lineFragmentShader)
        
        // 点着色器（简化版节点着色器）
        val pointVertexShader = """
            #version 300 es
            layout(location = 0) in vec3 aPosition;
            layout(location = 1) in vec3 aColor;
            layout(location = 2) in float aSize;
            
            uniform mat4 uMVPMatrix;
            uniform float uPointScale;
            
            out vec3 vColor;
            
            void main() {
                gl_Position = uMVPMatrix * vec4(aPosition, 1.0);
                gl_PointSize = aSize * uPointScale;
                vColor = aColor;
            }
        """.trimIndent()
        
        val pointFragmentShader = """
            #version 300 es
            precision mediump float;
            
            in vec3 vColor;
            out vec4 fragColor;
            
            void main() {
                // 圆形点
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                if (dist > 0.5) discard;
                
                // 柔和边缘
                float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
                
                fragColor = vec4(vColor, alpha * 0.8);
            }
        """.trimIndent()
        
        pointProgram = createProgram(pointVertexShader, pointFragmentShader)
        
        if (lineProgram == 0 || pointProgram == 0) {
            throw RuntimeException("Failed to create text label shader programs")
        }
        
        println("[TextLabelRenderer] Shaders initialized")
    }
    
    private fun initBuffers() {
        val vbos = IntArray(1)
        GLES30.glGenBuffers(1, vbos, 0)
        vbo = vbos[0]
        
        println("[TextLabelRenderer] VBO created: $vbo")
    }
    
    /**
     * 绘制文字标签（连接线和锚点）
     */
    fun draw(mvpMatrix: FloatArray, nodes: List<Node>) {
        if (nodes.isEmpty()) return
        
        // 找到最大连接数
        val maxConnections = nodes.maxOfOrNull { it.connections } ?: 1
        
        // 构建连接线数据和锚点数据
        val lineData = mutableListOf<Float>()
        val anchorData = mutableListOf<Float>()
        
        for (node in nodes) {
            // 只为连接数较多的节点绘制标签线
            val connectionRatio = node.connections.toFloat() / maxConnections.toFloat()
            if (connectionRatio < 0.2f) continue  // 跳过连接数少的节点
            
            // 计算标签线的终点（在节点右侧）
            val lineLength = 8.0f + connectionRatio * 12.0f
            
            // 线的起点（节点边缘）
            val startX = node.x + 3.0f
            val startY = node.y
            val startZ = node.z
            
            // 线的终点（标签锚点）
            val endX = node.x + lineLength
            val endY = node.y
            val endZ = node.z
            
            // 颜色
            val r = node.color[0]
            val g = node.color[1]
            val b = node.color[2]
            val alpha = 0.4f + connectionRatio * 0.4f
            
            // 添加线段顶点
            // 起点
            lineData.add(startX)
            lineData.add(startY)
            lineData.add(startZ)
            lineData.add(r)
            lineData.add(g)
            lineData.add(b)
            lineData.add(alpha * 0.3f)  // 起点较淡
            
            // 终点
            lineData.add(endX)
            lineData.add(endY)
            lineData.add(endZ)
            lineData.add(r)
            lineData.add(g)
            lineData.add(b)
            lineData.add(alpha)  // 终点较亮
            
            // 添加锚点（小圆点）
            anchorData.add(endX)
            anchorData.add(endY)
            anchorData.add(endZ)
            anchorData.add(r)
            anchorData.add(g)
            anchorData.add(b)
            anchorData.add(4.0f + connectionRatio * 6.0f)  // 点大小
        }
        
        if (lineData.isEmpty()) return
        
        // 绘制连接线
        drawLines(mvpMatrix, lineData)
        
        // 绘制锚点
        if (anchorData.isNotEmpty()) {
            drawAnchors(mvpMatrix, anchorData)
        }
    }
    
    /**
     * 绘制连接线
     */
    private fun drawLines(mvpMatrix: FloatArray, lineData: List<Float>) {
        GLES30.glUseProgram(lineProgram)
        
        // 设置 MVP 矩阵
        val mvpLoc = GLES30.glGetUniformLocation(lineProgram, "uMVPMatrix")
        GLES30.glUniformMatrix4fv(mvpLoc, 1, false, mvpMatrix, 0)
        
        // 准备顶点数据
        if (lineBuffer == null || lineBuffer!!.capacity() < lineData.size) {
            lineBuffer = ByteBuffer.allocateDirect(lineData.size * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer()
        }
        lineBuffer!!.clear()
        lineBuffer!!.put(lineData.toFloatArray())
        lineBuffer!!.position(0)
        
        // 上传数据到 VBO
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, vbo)
        GLES30.glBufferData(
            GLES30.GL_ARRAY_BUFFER,
            lineData.size * 4,
            lineBuffer,
            GLES30.GL_DYNAMIC_DRAW
        )
        
        // 设置顶点属性
        GLES30.glEnableVertexAttribArray(0)
        GLES30.glEnableVertexAttribArray(1)
        
        GLES30.glVertexAttribPointer(0, 3, GLES30.GL_FLOAT, false, 7 * 4, 0)
        GLES30.glVertexAttribPointer(1, 4, GLES30.GL_FLOAT, false, 7 * 4, 3 * 4)
        
        // 绘制线条
        GLES30.glLineWidth(1.5f)
        GLES30.glDrawArrays(GLES30.GL_LINES, 0, lineData.size / 7)
        
        // 清理
        GLES30.glDisableVertexAttribArray(0)
        GLES30.glDisableVertexAttribArray(1)
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, 0)
    }
    
    /**
     * 绘制锚点
     */
    private fun drawAnchors(mvpMatrix: FloatArray, anchorData: List<Float>) {
        GLES30.glUseProgram(pointProgram)
        
        // 设置 MVP 矩阵
        val mvpLoc = GLES30.glGetUniformLocation(pointProgram, "uMVPMatrix")
        GLES30.glUniformMatrix4fv(mvpLoc, 1, false, mvpMatrix, 0)
        
        // 设置点缩放
        val scaleLoc = GLES30.glGetUniformLocation(pointProgram, "uPointScale")
        GLES30.glUniform1f(scaleLoc, 0.5f)
        
        // 准备顶点数据
        if (anchorBuffer == null || anchorBuffer!!.capacity() < anchorData.size) {
            anchorBuffer = ByteBuffer.allocateDirect(anchorData.size * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer()
        }
        anchorBuffer!!.clear()
        anchorBuffer!!.put(anchorData.toFloatArray())
        anchorBuffer!!.position(0)
        
        // 上传数据到 VBO
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, vbo)
        GLES30.glBufferData(
            GLES30.GL_ARRAY_BUFFER,
            anchorData.size * 4,
            anchorBuffer,
            GLES30.GL_DYNAMIC_DRAW
        )
        
        // 设置顶点属性
        GLES30.glEnableVertexAttribArray(0)
        GLES30.glEnableVertexAttribArray(1)
        GLES30.glEnableVertexAttribArray(2)
        
        GLES30.glVertexAttribPointer(0, 3, GLES30.GL_FLOAT, false, 7 * 4, 0)
        GLES30.glVertexAttribPointer(1, 3, GLES30.GL_FLOAT, false, 7 * 4, 3 * 4)
        GLES30.glVertexAttribPointer(2, 1, GLES30.GL_FLOAT, false, 7 * 4, 6 * 4)
        
        // 绘制点
        GLES30.glDrawArrays(GLES30.GL_POINTS, 0, anchorData.size / 7)
        
        // 清理
        GLES30.glDisableVertexAttribArray(0)
        GLES30.glDisableVertexAttribArray(1)
        GLES30.glDisableVertexAttribArray(2)
        GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER, 0)
    }
    
    /**
     * 创建着色器程序
     */
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
    
    /**
     * 加载着色器
     */
    private fun loadShader(type: Int, shaderCode: String): Int {
        val shader = GLES30.glCreateShader(type)
        GLES30.glShaderSource(shader, shaderCode)
        GLES30.glCompileShader(shader)
        
        val compileStatus = IntArray(1)
        GLES30.glGetShaderiv(shader, GLES30.GL_COMPILE_STATUS, compileStatus, 0)
        if (compileStatus[0] == 0) {
            val error = GLES30.glGetShaderInfoLog(shader)
            GLES30.glDeleteShader(shader)
            throw RuntimeException("Failed to compile shader: $error")
        }
        
        return shader
    }
    
    /**
     * 清理资源
     */
    fun cleanup() {
        if (vbo != 0) {
            GLES30.glDeleteBuffers(1, intArrayOf(vbo), 0)
            vbo = 0
        }
        
        if (lineProgram != 0) {
            GLES30.glDeleteProgram(lineProgram)
            lineProgram = 0
        }
        
        if (pointProgram != 0) {
            GLES30.glDeleteProgram(pointProgram)
            pointProgram = 0
        }
        
        lineBuffer = null
        anchorBuffer = null
        
        println("[TextLabelRenderer] Cleaned up")
    }
}
