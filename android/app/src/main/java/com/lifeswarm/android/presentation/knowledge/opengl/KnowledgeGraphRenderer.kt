package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * 知识图谱 OpenGL ES 渲染器
 * 对应 web/src/components/KnowledgeGraph3D.tsx 的 Three.js 实现
 */
class KnowledgeGraphRenderer : GLSurfaceView.Renderer {
    
    // 视图矩阵
    private val viewMatrix = FloatArray(16)
    private val projectionMatrix = FloatArray(16)
    private val mvpMatrix = FloatArray(16)
    
    // 相机参数
    private var cameraDistance = 10f
    private var cameraAngleX = 0f
    private var cameraAngleY = 0f
    
    // 相机目标（用于聚焦节点）
    private var cameraTargetX = 0f
    private var cameraTargetY = 0f
    private var cameraTargetZ = 0f
    
    // 选中的节点
    private var selectedNodeId: String? = null
    
    // 节点和连线
    private val nodes = mutableListOf<Node>()
    private val edges = mutableListOf<Edge>()
    
    // OpenGL 对象
    private var sphereRenderer: SphereRenderer? = null
    private var lineRenderer: LineRenderer? = null
    private var textRenderer: TextRenderer? = null
    
    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        // 设置背景色（深色主题）
        GLES20.glClearColor(0.05f, 0.05f, 0.1f, 1.0f)
        
        // 启用深度测试
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        
        // 启用混合（用于透明度）
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)
        
        // 初始化渲染器
        sphereRenderer = SphereRenderer()
        lineRenderer = LineRenderer()
        textRenderer = TextRenderer()
        
        // 不再创建示例数据，等待从后端加载
        println("[KnowledgeGraph] OpenGL ES 初始化完成，等待后端数据")
    }
    
    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        GLES20.glViewport(0, 0, width, height)
        
        val ratio = width.toFloat() / height.toFloat()
        
        // 设置投影矩阵（透视投影）
        Matrix.frustumM(projectionMatrix, 0, -ratio, ratio, -1f, 1f, 3f, 50f)
        
        println("[KnowledgeGraph] 视口大小: ${width}x${height}")
    }
    
    override fun onDrawFrame(gl: GL10?) {
        // 清除颜色和深度缓冲
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        
        // 更新相机角度（自动旋转）
        cameraAngleY += 0.5f
        
        // 设置相机位置
        val eyeX = cameraTargetX + cameraDistance * sin(Math.toRadians(cameraAngleY.toDouble())).toFloat()
        val eyeZ = cameraTargetZ + cameraDistance * cos(Math.toRadians(cameraAngleY.toDouble())).toFloat()
        val eyeY = cameraTargetY + cameraDistance * sin(Math.toRadians(cameraAngleX.toDouble())).toFloat()
        
        Matrix.setLookAtM(
            viewMatrix, 0,
            eyeX, eyeY, eyeZ,           // 相机位置
            cameraTargetX, cameraTargetY, cameraTargetZ,  // 看向目标点
            0f, 1f, 0f                  // 上方向
        )
        
        // 计算 MVP 矩阵
        Matrix.multiplyMM(mvpMatrix, 0, projectionMatrix, 0, viewMatrix, 0)
        
        // 绘制连线（需要传入节点列表以获取位置）
        lineRenderer?.draw(mvpMatrix, edges, nodes)
        
        // 绘制节点
        sphereRenderer?.draw(mvpMatrix, nodes)
        
        // 绘制文字标签
        textRenderer?.drawLabels(mvpMatrix, nodes)
    }
    
    /**
     * 更新图谱数据（从后端数据）
     */
    fun updateGraph(newNodes: List<Node>, newEdges: List<Edge>) {
        nodes.clear()
        nodes.addAll(newNodes)
        edges.clear()
        edges.addAll(newEdges)
        
        println("[KnowledgeGraph] 更新图谱: ${nodes.size} 个节点, ${edges.size} 条连线")
    }
    
    /**
     * 获取节点位置（用于连线绘制）
     */
    fun getNodePosition(nodeId: String): Triple<Float, Float, Float>? {
        val node = nodes.find { it.id == nodeId }
        return node?.let { Triple(it.x, it.y, it.z) }
    }
    
    /**
     * 检测点击的节点
     */
    fun detectNodeClick(screenX: Float, screenY: Float, screenWidth: Int, screenHeight: Int): Node? {
        // 简化的点击检测：找到最近的节点
        // 实际应该使用射线投射，但这里用简化算法
        
        // 将屏幕坐标转换为归一化设备坐标
        val ndcX = (2.0f * screenX) / screenWidth - 1.0f
        val ndcY = 1.0f - (2.0f * screenY) / screenHeight
        
        var closestNode: Node? = null
        var minDistance = Float.MAX_VALUE
        
        // 遍历所有节点，找到最近的
        for (node in nodes) {
            // 将节点的世界坐标转换到屏幕空间
            val nodePos = FloatArray(4)
            nodePos[0] = node.x
            nodePos[1] = node.y
            nodePos[2] = node.z
            nodePos[3] = 1.0f
            
            val clipPos = FloatArray(4)
            Matrix.multiplyMV(clipPos, 0, mvpMatrix, 0, nodePos, 0)
            
            if (clipPos[3] != 0f) {
                val screenNodeX = clipPos[0] / clipPos[3]
                val screenNodeY = clipPos[1] / clipPos[3]
                
                // 计算距离
                val dx = screenNodeX - ndcX
                val dy = screenNodeY - ndcY
                val distance = sqrt(dx * dx + dy * dy)
                
                // 检查是否在节点半径内
                val threshold = 0.15f // 点击阈值
                if (distance < threshold && distance < minDistance) {
                    minDistance = distance
                    closestNode = node
                }
            }
        }
        
        return closestNode
    }
    
    /**
     * 聚焦到指定节点
     */
    fun focusOnNode(nodeId: String) {
        val node = nodes.find { it.id == nodeId }
        if (node != null) {
            selectedNodeId = nodeId
            cameraTargetX = node.x
            cameraTargetY = node.y
            cameraTargetZ = node.z
            cameraDistance = 5f // 拉近相机
            println("[KnowledgeGraph] 聚焦到节点: ${node.label}")
        }
    }
    
    /**
     * 重置相机视角
     */
    fun resetCamera() {
        selectedNodeId = null
        cameraTargetX = 0f
        cameraTargetY = 0f
        cameraTargetZ = 0f
        cameraDistance = 10f
        cameraAngleX = 0f
        cameraAngleY = 0f
        println("[KnowledgeGraph] 重置相机视角")
    }
    
    /**
     * 获取选中的节点
     */
    fun getSelectedNode(): Node? {
        return selectedNodeId?.let { id -> nodes.find { it.id == id } }
    }
    
    /**
     * 设置相机距离
     */
    fun setCameraDistance(distance: Float) {
        cameraDistance = distance.coerceIn(5f, 20f)
    }
    
    /**
     * 旋转相机
     */
    fun rotateCamera(deltaX: Float, deltaY: Float) {
        cameraAngleY += deltaX * 0.5f
        cameraAngleX += deltaY * 0.5f
        cameraAngleX = cameraAngleX.coerceIn(-89f, 89f)
    }
}

/**
 * 节点数据类
 */
data class Node(
    val id: String,
    var x: Float,
    var y: Float,
    var z: Float,
    val radius: Float,
    val color: FloatArray,
    val label: String,
    val connections: Int = 0  // 连接数，用于计算节点大小
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as Node
        return id == other.id
    }
    
    override fun hashCode(): Int = id.hashCode()
}

/**
 * 连线数据类
 */
data class Edge(
    val from: String,
    val to: String,
    val color: FloatArray
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as Edge
        return from == other.from && to == other.to
    }
    
    override fun hashCode(): Int = 31 * from.hashCode() + to.hashCode()
}
