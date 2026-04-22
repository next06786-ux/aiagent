package com.lifeswarm.android.presentation.knowledge.opengl

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.opengl.GLES20
import android.opengl.GLUtils
import android.opengl.Matrix
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer

/**
 * 文字渲染器 - 用于在 3D 空间中绘制节点标签
 */
class TextRenderer {
    
    private val vertexShaderCode = """
        uniform mat4 uMVPMatrix;
        attribute vec4 vPosition;
        attribute vec2 vTexCoord;
        varying vec2 fTexCoord;
        
        void main() {
            gl_Position = uMVPMatrix * vPosition;
            fTexCoord = vTexCoord;
        }
    """.trimIndent()
    
    private val fragmentShaderCode = """
        precision mediump float;
        uniform sampler2D uTexture;
        varying vec2 fTexCoord;
        
        void main() {
            vec4 texColor = texture2D(uTexture, fTexCoord);
            // 只显示不透明的部分
            if (texColor.a < 0.1) {
                discard;
            }
            gl_FragColor = texColor;
        }
    """.trimIndent()
    
    private val program: Int
    private var positionHandle: Int = 0
    private var texCoordHandle: Int = 0
    private var mvpMatrixHandle: Int = 0
    private var textureHandle: Int = 0
    
    // 文字纹理缓存
    private val textureCache = mutableMapOf<String, Int>()
    
    // Paint 用于绘制文字
    private val textPaint = Paint().apply {
        textSize = 48f
        isAntiAlias = true
        color = android.graphics.Color.WHITE
        textAlign = Paint.Align.CENTER
    }
    
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
     * 绘制所有节点标签
     */
    fun drawLabels(mvpMatrix: FloatArray, nodes: List<Node>) {
        if (nodes.isEmpty()) return
        
        GLES20.glUseProgram(program)
        
        // 获取句柄
        positionHandle = GLES20.glGetAttribLocation(program, "vPosition")
        texCoordHandle = GLES20.glGetAttribLocation(program, "vTexCoord")
        mvpMatrixHandle = GLES20.glGetUniformLocation(program, "uMVPMatrix")
        textureHandle = GLES20.glGetUniformLocation(program, "uTexture")
        
        // 启用顶点数组
        GLES20.glEnableVertexAttribArray(positionHandle)
        GLES20.glEnableVertexAttribArray(texCoordHandle)
        
        // 启用纹理
        GLES20.glEnable(GLES20.GL_TEXTURE_2D)
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
        GLES20.glUniform1i(textureHandle, 0)
        
        // 绘制每个标签
        for (node in nodes) {
            drawLabel(mvpMatrix, node)
        }
        
        // 禁用顶点数组
        GLES20.glDisableVertexAttribArray(positionHandle)
        GLES20.glDisableVertexAttribArray(texCoordHandle)
        GLES20.glDisable(GLES20.GL_TEXTURE_2D)
    }
    
    /**
     * 绘制单个标签
     */
    private fun drawLabel(mvpMatrix: FloatArray, node: Node) {
        // 获取或创建文字纹理
        val textureId = getOrCreateTexture(node.label)
        
        // 绑定纹理
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureId)
        
        // 标签位置（在节点上方）
        val labelY = node.y + node.radius + 0.3f
        val labelSize = 0.5f
        
        // 创建一个始终面向相机的四边形（Billboard）
        val vertices = floatArrayOf(
            node.x - labelSize, labelY + labelSize, node.z,  // 左上
            node.x - labelSize, labelY - labelSize, node.z,  // 左下
            node.x + labelSize, labelY - labelSize, node.z,  // 右下
            node.x + labelSize, labelY + labelSize, node.z   // 右上
        )
        
        val texCoords = floatArrayOf(
            0f, 0f,  // 左上
            0f, 1f,  // 左下
            1f, 1f,  // 右下
            1f, 0f   // 右上
        )
        
        val indices = shortArrayOf(0, 1, 2, 0, 2, 3)
        
        val vertexBuffer = ByteBuffer.allocateDirect(vertices.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(vertices)
        vertexBuffer.position(0)
        
        val texCoordBuffer = ByteBuffer.allocateDirect(texCoords.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .put(texCoords)
        texCoordBuffer.position(0)
        
        val indexBuffer = ByteBuffer.allocateDirect(indices.size * 2)
            .order(ByteOrder.nativeOrder())
            .asShortBuffer()
            .put(indices)
        indexBuffer.position(0)
        
        // 设置顶点位置
        GLES20.glVertexAttribPointer(
            positionHandle, 3,
            GLES20.GL_FLOAT, false,
            3 * 4, vertexBuffer
        )
        
        // 设置纹理坐标
        GLES20.glVertexAttribPointer(
            texCoordHandle, 2,
            GLES20.GL_FLOAT, false,
            2 * 4, texCoordBuffer
        )
        
        // 传递矩阵
        GLES20.glUniformMatrix4fv(mvpMatrixHandle, 1, false, mvpMatrix, 0)
        
        // 绘制
        GLES20.glDrawElements(
            GLES20.GL_TRIANGLES,
            indices.size,
            GLES20.GL_UNSIGNED_SHORT,
            indexBuffer
        )
    }
    
    /**
     * 获取或创建文字纹理
     */
    private fun getOrCreateTexture(text: String): Int {
        // 检查缓存
        textureCache[text]?.let { return it }
        
        // 创建 Bitmap
        val textWidth = textPaint.measureText(text).toInt()
        val textHeight = (textPaint.textSize * 1.5f).toInt()
        
        val bitmap = Bitmap.createBitmap(
            textWidth.coerceAtLeast(1),
            textHeight.coerceAtLeast(1),
            Bitmap.Config.ARGB_8888
        )
        
        val canvas = Canvas(bitmap)
        canvas.drawColor(android.graphics.Color.TRANSPARENT)
        
        // 绘制文字
        val x = textWidth / 2f
        val y = textHeight / 2f - (textPaint.descent() + textPaint.ascent()) / 2f
        canvas.drawText(text, x, y, textPaint)
        
        // 创建 OpenGL 纹理
        val textureIds = IntArray(1)
        GLES20.glGenTextures(1, textureIds, 0)
        val textureId = textureIds[0]
        
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureId)
        
        // 设置纹理参数
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        
        // 上传纹理
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bitmap, 0)
        
        bitmap.recycle()
        
        // 缓存纹理
        textureCache[text] = textureId
        
        return textureId
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
    
    /**
     * 清理资源
     */
    fun cleanup() {
        // 删除所有纹理
        val textureIds = textureCache.values.toIntArray()
        GLES20.glDeleteTextures(textureIds.size, textureIds, 0)
        textureCache.clear()
    }
}
