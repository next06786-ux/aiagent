package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES20
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer

/**
 * 线条渲染器 - 用于绘制知识图谱连线
 */
class LineRenderer {
    
    private val vertexShaderCode = """
        uniform mat4 uMVPMatrix;
        attribute vec4 vPosition;
        attribute vec4 vColor;
        varying vec4 fColor;
        
        void main() {
            gl_Position = uMVPMatrix * vPosition;
            fColor = vColor;
        }
    """.trimIndent()
    
    private val fragmentShaderCode = """
        precision mediump float;
        varying vec4 fColor;
        
        void main() {
            gl_FragColor = fColor;
        }
    """.trimIndent()
    
    private val program: Int
    private var positionHandle: Int = 0
    private var colorHandle: Int = 0
    private var mvpMatrixHandle: Int = 0
    
    init {
        // 编译着色器
        val vertexShader = loadShader(GLES20.GL_VERTEX_SHADER, vertexShaderCode)
        val fragmentShader = loadShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderCode)
        
        // 创建程序
        program = GLES20.glCreateProgram().also {
            GLES20.glAttachShader(it, vertexShader)
            GLES20.glAttachShader(it, fragmentShader)
            GLES20.glLinkProgram(it)
        }
    }
    
    /**
     * 绘制所有连线
     */
    fun draw(mvpMatrix: FloatArray, edges: List<Edge>, nodes: List<Node>) {
        if (edges.isEmpty() || nodes.isEmpty()) return
        
        // 构建节点位置映射
        val nodePositions = nodes.associate { it.id to Triple(it.x, it.y, it.z) }
        
        GLES20.glUseProgram(program)
        
        // 获取句柄
        positionHandle = GLES20.glGetAttribLocation(program, "vPosition")
        colorHandle = GLES20.glGetAttribLocation(program, "vColor")
        mvpMatrixHandle = GLES20.glGetUniformLocation(program, "uMVPMatrix")
        
        // 启用顶点数组
        GLES20.glEnableVertexAttribArray(positionHandle)
        GLES20.glEnableVertexAttribArray(colorHandle)
        
        // 传递矩阵
        GLES20.glUniformMatrix4fv(mvpMatrixHandle, 1, false, mvpMatrix, 0)
        
        // 设置线宽
        GLES20.glLineWidth(2.0f)
        
        // 绘制每条连线
        for (edge in edges) {
            val fromPos = nodePositions[edge.from]
            val toPos = nodePositions[edge.to]
            
            if (fromPos != null && toPos != null) {
                drawEdge(edge, fromPos, toPos)
            }
        }
        
        // 禁用顶点数组
        GLES20.glDisableVertexAttribArray(positionHandle)
        GLES20.glDisableVertexAttribArray(colorHandle)
    }
    
    /**
     * 绘制单条连线
     */
    private fun drawEdge(
        edge: Edge,
        fromPos: Triple<Float, Float, Float>,
        toPos: Triple<Float, Float, Float>
    ) {
        val vertices = floatArrayOf(
            fromPos.first, fromPos.second, fromPos.third,  // 起点
            toPos.first, toPos.second, toPos.third         // 终点
        )
        
        val colors = floatArrayOf(
            edge.color[0], edge.color[1], edge.color[2], edge.color[3],
            edge.color[0], edge.color[1], edge.color[2], edge.color[3]
        )
        
        val vertexBuffer = ByteBuffer.allocateDirect(vertices.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(vertices)
        vertexBuffer.position(0)
        
        val colorBuffer = ByteBuffer.allocateDirect(colors.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(colors)
        colorBuffer.position(0)
        
        // 设置顶点位置
        GLES20.glVertexAttribPointer(
            positionHandle, 3,
            GLES20.GL_FLOAT, false,
            3 * 4, vertexBuffer
        )
        
        // 设置顶点颜色
        GLES20.glVertexAttribPointer(
            colorHandle, 4,
            GLES20.GL_FLOAT, false,
            4 * 4, colorBuffer
        )
        
        // 绘制线条
        GLES20.glDrawArrays(GLES20.GL_LINES, 0, 2)
    }
    
    /**
     * 加载着色器
     */
    private fun loadShader(type: Int, shaderCode: String): Int {
        return GLES20.glCreateShader(type).also { shader ->
            GLES20.glShaderSource(shader, shaderCode)
            GLES20.glCompileShader(shader)
        }
    }
}
