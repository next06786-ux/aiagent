package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES20
import android.opengl.Matrix
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import kotlin.math.cos
import kotlin.math.sin

/**
 * 球体渲染器 - 用于绘制知识图谱节点
 */
class SphereRenderer {
    
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
    
    // 球体顶点数据
    private val sphereVertices: FloatBuffer
    private val sphereColors: FloatBuffer
    private val vertexCount: Int
    
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
        
        // 生成球体顶点
        val (vertices, colors, count) = generateSphere(1.0f, 16, 16)
        sphereVertices = vertices
        sphereColors = colors
        vertexCount = count
    }
    
    /**
     * 绘制所有节点
     */
    fun draw(mvpMatrix: FloatArray, nodes: List<Node>) {
        GLES20.glUseProgram(program)
        
        // 获取句柄
        positionHandle = GLES20.glGetAttribLocation(program, "vPosition")
        colorHandle = GLES20.glGetAttribLocation(program, "vColor")
        mvpMatrixHandle = GLES20.glGetUniformLocation(program, "uMVPMatrix")
        
        // 启用顶点数组
        GLES20.glEnableVertexAttribArray(positionHandle)
        GLES20.glEnableVertexAttribArray(colorHandle)
        
        // 绘制每个节点
        for (node in nodes) {
            drawNode(mvpMatrix, node)
        }
        
        // 禁用顶点数组
        GLES20.glDisableVertexAttribArray(positionHandle)
        GLES20.glDisableVertexAttribArray(colorHandle)
    }
    
    /**
     * 绘制单个节点
     */
    private fun drawNode(mvpMatrix: FloatArray, node: Node) {
        val modelMatrix = FloatArray(16)
        val finalMatrix = FloatArray(16)
        
        // 设置模型矩阵（位置和缩放）
        Matrix.setIdentityM(modelMatrix, 0)
        Matrix.translateM(modelMatrix, 0, node.x, node.y, node.z)
        Matrix.scaleM(modelMatrix, 0, node.radius, node.radius, node.radius)
        
        // 计算最终矩阵
        Matrix.multiplyMM(finalMatrix, 0, mvpMatrix, 0, modelMatrix, 0)
        
        // 创建颜色缓冲（所有顶点使用相同颜色）
        val colorBuffer = createColorBuffer(node.color, vertexCount)
        
        // 设置顶点位置
        sphereVertices.position(0)
        GLES20.glVertexAttribPointer(
            positionHandle, 3,
            GLES20.GL_FLOAT, false,
            3 * 4, sphereVertices
        )
        
        // 设置顶点颜色
        colorBuffer.position(0)
        GLES20.glVertexAttribPointer(
            colorHandle, 4,
            GLES20.GL_FLOAT, false,
            4 * 4, colorBuffer
        )
        
        // 传递矩阵
        GLES20.glUniformMatrix4fv(mvpMatrixHandle, 1, false, finalMatrix, 0)
        
        // 绘制
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, vertexCount)
    }
    
    /**
     * 生成球体顶点
     */
    private fun generateSphere(radius: Float, latitudeBands: Int, longitudeBands: Int): Triple<FloatBuffer, FloatBuffer, Int> {
        val vertices = mutableListOf<Float>()
        val colors = mutableListOf<Float>()
        
        for (lat in 0 until latitudeBands) {
            val theta1 = lat * Math.PI / latitudeBands
            val theta2 = (lat + 1) * Math.PI / latitudeBands
            
            for (lon in 0 until longitudeBands) {
                val phi1 = lon * 2 * Math.PI / longitudeBands
                val phi2 = (lon + 1) * 2 * Math.PI / longitudeBands
                
                // 四个顶点
                val v1 = sphereVertex(radius, theta1, phi1)
                val v2 = sphereVertex(radius, theta1, phi2)
                val v3 = sphereVertex(radius, theta2, phi2)
                val v4 = sphereVertex(radius, theta2, phi1)
                
                // 第一个三角形
                vertices.addAll(v1)
                vertices.addAll(v2)
                vertices.addAll(v3)
                
                // 第二个三角形
                vertices.addAll(v1)
                vertices.addAll(v3)
                vertices.addAll(v4)
            }
        }
        
        val vertexCount = vertices.size / 3
        
        val vertexBuffer = ByteBuffer.allocateDirect(vertices.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(vertices.toFloatArray())
        vertexBuffer.position(0)
        
        // 颜色缓冲（占位，实际颜色在绘制时设置）
        val colorBuffer = ByteBuffer.allocateDirect(vertexCount * 4 * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
        
        return Triple(vertexBuffer, colorBuffer, vertexCount)
    }
    
    /**
     * 计算球面上的顶点
     */
    private fun sphereVertex(radius: Float, theta: Double, phi: Double): List<Float> {
        val x = radius * sin(theta) * cos(phi)
        val y = radius * cos(theta)
        val z = radius * sin(theta) * sin(phi)
        return listOf(x.toFloat(), y.toFloat(), z.toFloat())
    }
    
    /**
     * 创建颜色缓冲
     */
    private fun createColorBuffer(color: FloatArray, vertexCount: Int): FloatBuffer {
        val colors = FloatArray(vertexCount * 4)
        for (i in 0 until vertexCount) {
            colors[i * 4] = color[0]
            colors[i * 4 + 1] = color[1]
            colors[i * 4 + 2] = color[2]
            colors[i * 4 + 3] = color[3]
        }
        
        return ByteBuffer.allocateDirect(colors.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(colors)
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
